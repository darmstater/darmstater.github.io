import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict

import pytz

from config import TIMEZONE, MONTH_NAMES_ID, DAY_NAMES_ID
from database import get_today_transactions, get_week_transactions, get_stock_summary, get_cash_summary, get_all_groups
from sheets_service import rebuild_month_sheet, update_summary_sheet

logger = logging.getLogger(__name__)
TZ     = pytz.timezone(TIMEZONE)


def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


# ─── Formatters ───────────────────────────────────────────────────────────────

def format_daily_summary(chat_id: str) -> str:
    now   = datetime.now(TZ)
    txns  = get_today_transactions(chat_id)
    day   = DAY_NAMES_ID.get(now.strftime("%A"), "")
    date  = f"{now.day} {MONTH_NAMES_ID[now.month]} {now.year}"

    if not txns:
        return (
            f"📊 *Ringkasan Harian — {day}, {date}*\n\n"
            f"Belum ada transaksi hari ini."
        )

    total_in  = sum(t["total_price"] for t in txns if t["type"] == "IN")
    total_out = sum(t["total_price"] for t in txns if t["type"] == "OUT")
    net       = total_in - total_out

    # Breakdown per produk
    prod_in:  dict = defaultdict(float)
    prod_out: dict = defaultdict(float)
    prod_qty_in:  dict = defaultdict(float)
    prod_qty_out: dict = defaultdict(float)
    biaya_lain = 0.0

    for t in txns:
        if t["type"] == "IN":
            prod_in[t["product"] or "-"] += t["total_price"]
            prod_qty_in[t["product"] or "-"] += t["quantity"]
        else:
            if t["product"]:
                prod_out[t["product"]] += t["total_price"]
                prod_qty_out[t["product"]] += t["quantity"]
            else:
                biaya_lain += t["total_price"]

    lines = [
        f"📊 *Ringkasan Harian*",
        f"_{day}, {date}_\n",
    ]

    if prod_in:
        lines.append("🛒 *Penjualan:*")
        for p, amt in prod_in.items():
            qty = int(prod_qty_in[p]) if prod_qty_in[p].is_integer() else prod_qty_in[p]
            lines.append(f"  • {p}: {qty} unit → *{fmt_rp(amt)}*")
        lines.append(f"  Total: *+{fmt_rp(total_in)}*\n")

    if prod_out:
        lines.append("📦 *Restock:*")
        for p, amt in prod_out.items():
            qty = int(prod_qty_out[p]) if prod_qty_out[p].is_integer() else prod_qty_out[p]
            lines.append(f"  • {p}: {qty} unit → *{fmt_rp(amt)}*")

    if biaya_lain:
        if not prod_out:
            lines.append("💸 *Pengeluaran:*")
        lines.append(f"  • Lain-lain: *{fmt_rp(biaya_lain)}*")

    if prod_out or biaya_lain:
        lines.append(f"  Total: *-{fmt_rp(total_out)}*\n")

    sign = "+" if net >= 0 else ""
    icon = "📈" if net >= 0 else "📉"
    lines.append(f"{icon} *NET Hari Ini: {sign}{fmt_rp(net)}*\n")

    # Stok saat ini
    stok = get_stock_summary(chat_id)
    if stok:
        lines.append("📦 *Stok Sekarang:*")
        for p in ["Gas LPG 3kg", "Sunlight"]:
            s = stok.get(p, {"stok": 0})
            stok_val = int(s["stok"]) if float(s["stok"]).is_integer() else s["stok"]
            lines.append(f"  • {p}: *{stok_val} unit*")

    lines.append(f"\n_Total transaksi: {len(txns)}_")
    return "\n".join(lines)


def format_weekly_summary(chat_id: str) -> str:
    now  = datetime.now(TZ)
    txns = get_week_transactions(chat_id)

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

    prod_in:      dict = defaultdict(float)
    prod_qty_in:  dict = defaultdict(float)
    prod_qty_out: dict = defaultdict(float)

    for t in txns:
        if t["type"] == "IN" and t["product"]:
            prod_in[t["product"]]     += t["total_price"]
            prod_qty_in[t["product"]] += t["quantity"]
        elif t["type"] == "OUT" and t["product"]:
            prod_qty_out[t["product"]] += t["quantity"]

    sign = "+" if net >= 0 else ""
    icon = "📈" if net >= 0 else "📉"

    lines = [
        f"📅 *Ringkasan Mingguan*",
        f"_{period}_\n",
        f"💰 *Total Penjualan :* +{fmt_rp(total_in)}",
        f"💸 *Total Keluar    :* -{fmt_rp(total_out)}",
        f"{icon} *NET Minggu       :* {sign}{fmt_rp(net)}\n",
    ]

    if prod_in or prod_qty_out:
        lines.append("*Detail Produk:*")
        for p in ["Gas LPG 3kg", "Sunlight"]:
            qi  = prod_qty_in.get(p, 0.0)
            qo  = prod_qty_out.get(p, 0.0)
            omz = prod_in.get(p, 0.0)
            if qi > 0 or qo > 0:
                lines.append(
                    f"  • {p}: beli {int(qo)} | jual {int(qi)} | omzet {fmt_rp(omz)}"
                )

    # Overall stok
    stok = get_stock_summary(chat_id)
    if stok:
        lines.append("\n*Stok Saat Ini:*")
        for p in ["Gas LPG 3kg", "Sunlight"]:
            s = stok.get(p, {"stok": 0})
            lines.append(f"  • {p}: *{int(s['stok'])} unit*")

    lines.append(f"\n_Total transaksi: {len(txns)}_")
    return "\n".join(lines)


# ─── Scheduled jobs ───────────────────────────────────────────────────────────

async def send_daily_summary(bot):
    groups = get_all_groups()
    for g in groups:
        cid = g["chat_id"]
        try:
            text = format_daily_summary(cid)
            await bot.send_message(chat_id=cid, text=text, parse_mode="Markdown")
            logger.info(f"Daily summary sent to {cid}")
        except Exception as e:
            logger.error(f"send_daily_summary error {cid}: {e}")


async def send_weekly_summary_and_sync(bot):
    now    = datetime.now(TZ)
    groups = get_all_groups()
    for g in groups:
        cid = g["chat_id"]
        sid = g["spreadsheet_id"]
        try:
            text = format_weekly_summary(cid)
            await bot.send_message(chat_id=cid, text=text, parse_mode="Markdown")
            await bot.send_message(chat_id=cid, text="🔄 Sinkronisasi ke Google Sheets...")

            loop = asyncio.get_event_loop()
            ok1 = await loop.run_in_executor(
                None, lambda c=cid, s=sid: rebuild_month_sheet(now.year, now.month, c, s)
            )
            ok2 = await loop.run_in_executor(
                None, lambda c=cid, s=sid: update_summary_sheet(c, s)
            )

            if ok1 and ok2:
                await bot.send_message(chat_id=cid, text="✅ Google Sheets diperbarui!")
            else:
                await bot.send_message(chat_id=cid, text="⚠️ Sebagian sync Sheets gagal. Coba /sync manual.")

        except Exception as e:
            logger.error(f"send_weekly_summary_and_sync error {cid}: {e}")
