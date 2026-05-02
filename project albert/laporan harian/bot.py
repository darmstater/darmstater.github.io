import asyncio
import logging
import pytz
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE,
    CATEGORIES_OUT, CATEGORIES_IN,
)
from database import (
    init_db, add_transaction, delete_transaction,
    get_today_transactions, get_transaction_by_id,
)
from sheets_service import (
    rebuild_month_sheet, update_summary_sheet, append_transaction_row,
)
from scheduler_service import (
    format_daily_summary, format_weekly_summary,
    send_daily_summary, send_weekly_summary_and_sync,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)


def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Bot Laporan Harian* siap!\n\n"
        "*Catat transaksi:*\n"
        "`/out [kategori] [qty] [harga] [keterangan]`\n"
        "`/in [kategori] [nominal] [keterangan]`\n\n"
        "*Contoh:*\n"
        "`/out makan 2 25000 makan siang`\n"
        "`/out transport 1 35000 grab ke kantor`\n"
        "`/in freelance 500000 transfer klien`\n\n"
        "*Lihat summary:*\n"
        "`/today` — ringkasan hari ini\n"
        "`/week` — ringkasan minggu ini\n\n"
        "*Lainnya:*\n"
        "`/hapus [id]` — hapus transaksi\n"
        "`/list` — daftar transaksi hari ini\n"
        "`/sync` — sinkronkan ke Google Sheets\n"
        "`/kategori` — lihat daftar kategori"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /out ─────────────────────────────────────────────────────────────────────

async def cmd_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/out [kategori] [qty] [harga\\_satuan] [keterangan]`\n\n"
            "Contoh:\n"
            "`/out makan 2 25000 makan siang`\n"
            "`/out transport 1 35000 grab ke kantor`\n"
            "`/out belanja 3 15000 beli air mineral`\n\n"
            "Ketik /kategori untuk melihat daftar kategori.",
            parse_mode="Markdown"
        )
        return

    category_raw = args[0].lower()

    try:
        qty        = float(args[1])
        unit_price = float(args[2])
    except ValueError:
        await update.message.reply_text("❌ Qty dan harga satuan harus angka!\nContoh: `/out makan 2 25000 makan siang`", parse_mode="Markdown")
        return

    if qty <= 0 or unit_price <= 0:
        await update.message.reply_text("❌ Qty dan harga satuan harus lebih dari 0.")
        return

    description = " ".join(args[3:]) if len(args) > 3 else "-"
    category    = CATEGORIES_OUT.get(category_raw, "Lain-lain")
    total       = qty * unit_price

    now     = datetime.now(TZ)
    trans_id = add_transaction("OUT", category, qty, unit_price, description)

    # Async append to Sheets (non-blocking)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: append_transaction_row(
        trans_id, now.strftime("%Y-%m-%d"),
        now.strftime("%A").upper(),
        "OUT", category, qty, unit_price, total,
        description, now.year, now.month
    ))

    qty_str = int(qty) if qty.is_integer() else qty
    await update.message.reply_text(
        f"✅ *Pengeluaran dicatat!*\n"
        f"ID        : `#{trans_id}`\n"
        f"Kategori  : {category}\n"
        f"Jumlah    : {qty_str} × {fmt_rp(unit_price)} = *{fmt_rp(total)}*\n"
        f"Keterangan: {description}",
        parse_mode="Markdown"
    )


# ─── /in ──────────────────────────────────────────────────────────────────────

async def cmd_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Format: `/in [kategori] [nominal] [keterangan]`\n\n"
            "Contoh:\n"
            "`/in freelance 500000 transfer klien`\n"
            "`/in gaji 5000000 gaji bulan ini`",
            parse_mode="Markdown"
        )
        return

    category_raw = args[0].lower()

    try:
        nominal = float(args[1])
    except ValueError:
        await update.message.reply_text("❌ Nominal harus angka!\nContoh: `/in freelance 500000 transfer klien`", parse_mode="Markdown")
        return

    if nominal <= 0:
        await update.message.reply_text("❌ Nominal harus lebih dari 0.")
        return

    description = " ".join(args[2:]) if len(args) > 2 else "-"
    category    = CATEGORIES_IN.get(category_raw, "Lain-lain")

    now      = datetime.now(TZ)
    trans_id = add_transaction("IN", category, 1, nominal, description)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: append_transaction_row(
        trans_id, now.strftime("%Y-%m-%d"),
        now.strftime("%A").upper(),
        "IN", category, 1, nominal, nominal,
        description, now.year, now.month
    ))

    await update.message.reply_text(
        f"✅ *Pemasukan dicatat!*\n"
        f"ID        : `#{trans_id}`\n"
        f"Kategori  : {category}\n"
        f"Nominal   : *{fmt_rp(nominal)}*\n"
        f"Keterangan: {description}",
        parse_mode="Markdown"
    )


# ─── /today ───────────────────────────────────────────────────────────────────

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_daily_summary()
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /week ────────────────────────────────────────────────────────────────────

async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_weekly_summary()
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /list ────────────────────────────────────────────────────────────────────

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txns = get_today_transactions()
    if not txns:
        await update.message.reply_text("Belum ada transaksi hari ini.")
        return

    now  = datetime.now(TZ)
    lines = [f"📋 *Transaksi {now.day}/{now.month}/{now.year}:*\n"]
    for t in txns:
        icon = "💰" if t["type"] == "IN" else "💸"
        qty  = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
        lines.append(
            f"{icon} `#{t['id']}` {t['category']}\n"
            f"    {qty} × {fmt_rp(t['unit_price'])} = *{fmt_rp(t['total_price'])}*\n"
            f"    _{t['description']}_\n"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /hapus ───────────────────────────────────────────────────────────────────

async def cmd_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Format: `/hapus [id]`\nContoh: `/hapus 5`\n\nGunakan /list untuk melihat ID transaksi.",
            parse_mode="Markdown"
        )
        return

    try:
        trans_id = int(args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("❌ ID harus angka. Contoh: `/hapus 5`", parse_mode="Markdown")
        return

    t = get_transaction_by_id(trans_id)
    if not t:
        await update.message.reply_text(f"❌ Transaksi `#{trans_id}` tidak ditemukan.", parse_mode="Markdown")
        return

    # Confirm with inline button
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ya, hapus", callback_data=f"del_confirm_{trans_id}"),
            InlineKeyboardButton("❌ Batal", callback_data="del_cancel"),
        ]
    ])
    qty = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
    await update.message.reply_text(
        f"Hapus transaksi ini?\n\n"
        f"`#{t['id']}` {t['category']} — {qty} × {fmt_rp(t['unit_price'])} = *{fmt_rp(t['total_price'])}*\n"
        f"_{t['description']}_",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def hapus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "del_cancel":
        await query.edit_message_text("Dibatalkan.")
        return

    trans_id = int(query.data.split("_")[-1])
    success  = delete_transaction(trans_id)
    if success:
        await query.edit_message_text(f"✅ Transaksi `#{trans_id}` dihapus.", parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ Transaksi `#{trans_id}` tidak ditemukan.", parse_mode="Markdown")


# ─── /kategori ────────────────────────────────────────────────────────────────

async def cmd_kategori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Kategori untuk /out (pengeluaran):*\n"
        "`makan` `makanan` `minum` `kopi` `snack` → Makan & Minum\n"
        "`transport` `grab` `gojek` `ojek` `bensin` `parkir` `tol` → Transport\n"
        "`belanja` `shopping` `baju` `sepatu` → Belanja\n"
        "`tagihan` `listrik` `air` `wifi` `internet` `pulsa` `sewa` `kos` → Tagihan\n"
        "`hiburan` `nonton` `game` `spotify` `netflix` → Hiburan\n"
        "`kesehatan` `obat` `dokter` `vitamin` `gym` → Kesehatan\n"
        "`lain` `other` `dll` → Lain-lain\n\n"
        "*Kategori untuk /in (pemasukan):*\n"
        "`gaji` `salary` → Gaji\n"
        "`freelance` `proyek` `project` → Freelance\n"
        "`transfer` → Transfer\n"
        "`bisnis` → Bisnis\n"
        "`investasi` → Investasi\n"
        "`lain` `other` → Lain-lain"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /sync ────────────────────────────────────────────────────────────────────

async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Menyinkronkan ke Google Sheets, harap tunggu...")
    now  = datetime.now(TZ)
    loop = asyncio.get_event_loop()

    ok_month   = await loop.run_in_executor(None, lambda: rebuild_month_sheet(now.year, now.month))
    ok_summary = await loop.run_in_executor(None, update_summary_sheet)

    if ok_month and ok_summary:
        await update.message.reply_text("✅ Sinkronisasi berhasil!")
    else:
        await update.message.reply_text(
            "⚠️ Sinkronisasi gagal sebagian. Pastikan:\n"
            "1. `GOOGLE_CREDENTIALS_JSON` sudah diset\n"
            "2. `SPREADSHEET_ID` benar\n"
            "3. Service account sudah diberi akses ke spreadsheet"
        )


# ─── Unknown command ──────────────────────────────────────────────────────────

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Perintah tidak dikenal. Ketik /start untuk melihat daftar perintah."
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    init_db()
    logger.info("Database initialized")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("out",      cmd_out))
    app.add_handler(CommandHandler("in",       cmd_in))
    app.add_handler(CommandHandler("today",    cmd_today))
    app.add_handler(CommandHandler("week",     cmd_week))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("hapus",    cmd_hapus))
    app.add_handler(CommandHandler("kategori", cmd_kategori))
    app.add_handler(CommandHandler("sync",     cmd_sync))
    app.add_handler(CallbackQueryHandler(hapus_callback, pattern=r"^del_"))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=TZ)

    # 23:59 every day — daily summary
    scheduler.add_job(
        send_daily_summary,
        trigger="cron",
        hour=23, minute=59,
        args=[app.bot],
        id="daily_summary",
    )

    # 23:59 every Sunday — weekly summary + full Sheets sync
    scheduler.add_job(
        send_weekly_summary_and_sync,
        trigger="cron",
        day_of_week="sun",
        hour=23, minute=59,
        args=[app.bot],
        id="weekly_summary",
    )

    scheduler.start()
    logger.info("Scheduler started — daily@23:59 | weekly(Sun)@23:59")
    logger.info("Bot is running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
