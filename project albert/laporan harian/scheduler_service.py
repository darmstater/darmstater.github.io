import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import pytz

from config import TIMEZONE, MONTH_NAMES_ID, DAY_NAMES_ID
from database import get_today_transactions, get_week_transactions, get_all_users
from sheets_service import rebuild_month_sheet, update_summary_sheet

logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)


def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


# ─── Formatters ───────────────────────────────────────────────────────────────

def format_daily_summary(user_id: str = None) -> str:
    now  = datetime.now(TZ)
    txns = get_today_transactions(user_id=user_id)
    day  = DAY_NAMES_ID.get(now.strftime("%A"), "")
    date = f"{now.day} {MONTH_NAMES_ID[now.month]} {now.year}"

    if not txns:
        return (
            f"📊 *Ringkasan Harian*\n"
            f"_{day}, {date}_\n\n"
            f"Tidak ada transaksi hari ini."
        )

    total_in  = sum(t["total_price"] for t in txns if t["type"] == "IN")
    total_out = sum(t["total_price"] for t in txns if t["type"] == "OUT")
    net       = total_in - total_out
    sign      = "+" if net >= 0 else ""

    cat_out: dict = defaultdict(float)
    cat_in: dict  = defaultdict(float)
    for t in txns:
        if t["type"] == "OUT":
            cat_out[t["category"]] += t["total_price"]
        else:
            cat_in[t["category"]] += t["total_price"]

    lines = [
        f"📊 *Ringkasan Harian*",
        f"_{day}, {date}_",
        f"",
        f"💰 *Masuk  :* +{fmt_rp(total_in)}",
        f"💸 *Keluar :* -{fmt_rp(total_out)}",
        f"{'📈' if net >= 0 else '📉'} *Net      :* {sign}{fmt_rp(net)}",
        f"",
    ]

    if cat_out:
        lines.append("*Pengeluaran per kategori:*")
        for cat, amt in sorted(cat_out.items(), key=lambda x: -x[1]):
            pct = amt / total_out * 100 if total_out else 0
            lines.append(f"  • {cat}: {fmt_rp(amt)} _{pct:.0f}%_")

    if cat_in:
        lines.append("")
        lines.append("*Pemasukan per kategori:*")
        for cat, amt in sorted(cat_in.items(), key=lambda x: -x[1]):
            lines.append(f"  • {cat}: {fmt_rp(amt)}")

    lines.append(f"\n_Total transaksi: {len(txns)}_")
    return "\n".join(lines)


def format_weekly_summary(user_id: str = None) -> str:
    now  = datetime.now(TZ)
    txns = get_week_transactions(user_id=user_id)

    monday = now - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=6)
    period = (
        f"{monday.day} {MONTH_NAMES_ID[monday.month]} – "
        f"{sunday.day} {MONTH_NAMES_ID[sunday.month]} {sunday.year}"
    )

    if not txns:
        return f"📅 *Ringkasan Mingguan*\n_{period}_\n\nBelum ada transaksi minggu ini."

    total_in  = sum(t["total_price"] for t in txns if t["type"] == "IN")
    total_out = sum(t["total_price"] for t in txns if t["type"] == "OUT")
    net       = total_in - total_out
    sign      = "+" if net >= 0 else ""

    cat_out: dict   = defaultdict(float)
    day_spend: dict = defaultdict(float)
    biggest_item    = None

    for t in txns:
        if t["type"] == "OUT":
            cat_out[t["category"]] += t["total_price"]
            day_spend[t["date"]]   += t["total_price"]
            if biggest_item is None or t["total_price"] > biggest_item["total_price"]:
                biggest_item = t

    lines = [
        f"📅 *Ringkasan Mingguan*",
        f"_{period}_",
        f"",
        f"💰 *Masuk  :* +{fmt_rp(total_in)}",
        f"💸 *Keluar :* -{fmt_rp(total_out)}",
        f"{'📈' if net >= 0 else '📉'} *Net      :* {sign}{fmt_rp(net)}",
        f"",
    ]

    if day_spend:
        tb_date = max(day_spend, key=day_spend.get)
        tb_d    = datetime.strptime(tb_date, "%Y-%m-%d")
        tb_day  = DAY_NAMES_ID.get(tb_d.strftime("%A"), "")
        lines.append(f"🔥 *Hari terboros:* {tb_day} ({fmt_rp(day_spend[tb_date])})")

    if biggest_item:
        lines.append(
            f"💣 *Pengeluaran terbesar:* "
            f"{biggest_item['description']} — {fmt_rp(biggest_item['total_price'])}"
        )

    if cat_out:
        lines.append(f"\n*Breakdown kategori:*")
        for cat, amt in sorted(cat_out.items(), key=lambda x: -x[1]):
            pct = amt / total_out * 100 if total_out else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            lines.append(f"  `{bar}` {cat}: {fmt_rp(amt)} _{pct:.0f}%_")

    lines.append(f"\n_Total transaksi: {len(txns)}_")
    return "\n".join(lines)


# ─── Scheduled jobs ───────────────────────────────────────────────────────────

async def send_daily_summary(bot):
    users = get_all_users()
    for user in users:
        uid = user["telegram_user_id"]
        try:
            text = format_daily_summary(user_id=uid)
            await bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
            logger.info(f"Daily summary sent to {uid}")
        except Exception as e:
            logger.error(f"send_daily_summary error for {uid}: {e}")


async def send_weekly_summary_and_sync(bot):
    now   = datetime.now(TZ)
    users = get_all_users()

    for user in users:
        uid            = user["telegram_user_id"]
        spreadsheet_id = user["spreadsheet_id"]
        try:
            text = format_weekly_summary(user_id=uid)
            await bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
            await bot.send_message(chat_id=uid, text="🔄 Menyinkronkan ke Google Sheets...")

            loop = asyncio.get_event_loop()
            ok_month = await loop.run_in_executor(
                None,
                lambda u=uid, s=spreadsheet_id: rebuild_month_sheet(
                    now.year, now.month, user_id=u, spreadsheet_id=s
                )
            )
            ok_summary = await loop.run_in_executor(
                None,
                lambda u=uid, s=spreadsheet_id: update_summary_sheet(
                    user_id=u, spreadsheet_id=s
                )
            )

            if ok_month and ok_summary:
                await bot.send_message(chat_id=uid, text="✅ Google Sheets berhasil diperbarui!")
            else:
                await bot.send_message(
                    chat_id=uid,
                    text="⚠️ Sebagian update Sheets gagal. Coba /sync manual."
                )

            logger.info(f"Weekly summary sent + sheets synced for {uid}")
        except Exception as e:
            logger.error(f"send_weekly_summary_and_sync error for {uid}: {e}")
