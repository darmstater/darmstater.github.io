import asyncio
import logging
import re
import pytz
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    TELEGRAM_TOKEN, TIMEZONE,
    CATEGORIES_OUT, CATEGORIES_IN,
    MONTH_NAMES_ID, DAY_NAMES_ID,
)
from database import (
    init_db, add_transaction, delete_transaction,
    get_today_transactions, get_transaction_by_id,
    get_user, register_user,
)
from sheets_service import (
    rebuild_month_sheet, update_summary_sheet, append_transaction_row,
    verify_spreadsheet_access,
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


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


async def _require_registered(update: Update):
    """Returns user Row if registered, None + sends error message if not."""
    user = get_user(_uid(update))
    if not user:
        await update.message.reply_text(
            "⚠️ *Belum terdaftar!*\n\n"
            "Daftar dulu dengan perintah:\n"
            "`/register <spreadsheet_id>`\n\n"
            "Spreadsheet ID ada di URL Google Sheets:\n"
            "`https://docs.google.com/spreadsheets/d/`*ID_INI*`/edit`\n\n"
            "Sebelum daftar, share spreadsheet ke:\n"
            "`bot-laporan@laporan-harian-495106.iam.gserviceaccount.com`\n"
            "dengan akses *Editor*.",
            parse_mode="Markdown"
        )
        return None
    return user


def parse_date_prefix(args: list) -> tuple:
    """
    Returns (date_str, day_name, remaining_args).
    Parses optional date prefix from the start of args.
    Formats: 'kemarin', 'besok', 'Nhari' (e.g. '3hari'), 'dd', 'dd/mm'
    """
    if not args:
        return None, None, args

    first = args[0].lower()
    now   = datetime.now(TZ)
    target = None

    if first == "kemarin":
        target = now - timedelta(days=1)
    elif first == "besok":
        target = now + timedelta(days=1)
    elif re.match(r'^\d+hari$', first):
        n = int(first[:-4])
        if 1 <= n <= 60:
            target = now - timedelta(days=n)
    elif re.match(r'^\d{1,2}/\d{1,2}$', first):
        parts = first.split('/')
        try:
            d, m = int(parts[0]), int(parts[1])
            target = TZ.localize(datetime(now.year, m, d))
        except (ValueError, OverflowError):
            return None, None, args
    elif re.match(r'^\d{1,2}$', first):
        try:
            d      = int(first)
            target = TZ.localize(datetime(now.year, now.month, d))
        except (ValueError, OverflowError):
            return None, None, args

    if target is not None:
        date_str = target.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(target.strftime("%A"), target.strftime("%A").upper())
        return date_str, day_name, args[1:]

    return None, None, args


def _format_date_label(date_str: str) -> str:
    """Returns human-friendly date label relative to today."""
    now       = datetime.now(TZ)
    target    = datetime.strptime(date_str, "%Y-%m-%d").date()
    today     = now.date()
    yesterday = (now - timedelta(days=1)).date()
    tomorrow  = (now + timedelta(days=1)).date()

    if target == today:
        return "hari ini"
    if target == yesterday:
        return "kemarin"
    if target == tomorrow:
        return "besok"
    return f"{target.day} {MONTH_NAMES_ID[target.month]} {target.year}"


def _make_confirm_msg(pending: dict) -> str:
    icon   = "💸" if pending["type"] == "OUT" else "💰"
    ttype  = "Pengeluaran" if pending["type"] == "OUT" else "Pemasukan"
    dlabel = _format_date_label(pending["date_str"])

    if pending["type"] == "OUT":
        qty        = int(pending["qty"]) if float(pending["qty"]).is_integer() else pending["qty"]
        amount_str = f"{qty} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*"
    else:
        amount_str = f"*{fmt_rp(pending['total'])}*"

    return (
        f"{icon} *{ttype} — {pending['day_name']}, {dlabel}*\n\n"
        f"Kategori  : {pending['category']}\n"
        f"Jumlah    : {amount_str}\n"
        f"Keterangan: {pending['description']}\n\n"
        f"Catat transaksi ini?"
    )


# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(_uid(update))
    reg_note = (
        "\n\n⚠️ *Belum terdaftar!* Daftar dulu:\n"
        "`/register <spreadsheet_id>`"
    ) if not user else ""

    text = (
        "👋 *Bot Laporan Harian* siap!\n\n"
        "*Catat transaksi:*\n"
        "`/out [tanggal] [kategori] [qty] [harga] [keterangan]`\n"
        "`/in [tanggal] [kategori] [nominal] [keterangan]`\n\n"
        "*Tanggal (opsional, default hari ini):*\n"
        "`kemarin`  `besok`  `2hari`  `15`  `01/05`\n\n"
        "*Contoh:*\n"
        "`/out makan 2 25000 makan siang`\n"
        "`/out kemarin transport 1 35000 grab ke kantor`\n"
        "`/out 01/05 makan 1 50000 makan malam kemarin`\n"
        "`/in freelance 500000 transfer klien`\n\n"
        "*Summary:*\n"
        "`/today` — ringkasan hari ini\n"
        "`/week` — ringkasan minggu ini\n\n"
        "*Lainnya:*\n"
        "`/hapus [id]` — hapus transaksi\n"
        "`/list` — daftar transaksi hari ini\n"
        "`/sync` — sinkronkan ke Google Sheets\n"
        "`/kategori` — lihat daftar kategori\n"
        "`/register <id>` — daftarkan spreadsheet"
        + reg_note
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /register ────────────────────────────────────────────────────────────────

async def cmd_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Format: `/register <spreadsheet_id>`\n\n"
            "Spreadsheet ID ada di URL Google Sheets:\n"
            "`https://docs.google.com/spreadsheets/d/`*ID_INI*`/edit`\n\n"
            "Pastikan sudah share ke:\n"
            "`bot-laporan@laporan-harian-495106.iam.gserviceaccount.com` (Editor)",
            parse_mode="Markdown"
        )
        return

    spreadsheet_id = args[0].strip()
    await update.message.reply_text("🔍 Memeriksa akses ke spreadsheet...")

    loop = asyncio.get_event_loop()
    ok   = await loop.run_in_executor(
        None, lambda sid=spreadsheet_id: verify_spreadsheet_access(sid)
    )

    if not ok:
        await update.message.reply_text(
            "❌ Tidak bisa mengakses spreadsheet tersebut.\n\n"
            "Pastikan:\n"
            "1. Spreadsheet ID benar\n"
            "2. Sudah di-share ke:\n"
            "`bot-laporan@laporan-harian-495106.iam.gserviceaccount.com`\n"
            "dengan akses *Editor*",
            parse_mode="Markdown"
        )
        return

    uid  = _uid(update)
    name = update.effective_user.first_name or "User"
    register_user(uid, spreadsheet_id, name)

    await update.message.reply_text(
        f"✅ *Berhasil terdaftar!*\n\n"
        f"Nama     : {name}\n"
        f"Sheet ID : `{spreadsheet_id}`\n\n"
        f"Ketik /start untuk panduan lengkap.",
        parse_mode="Markdown"
    )


# ─── /out ─────────────────────────────────────────────────────────────────────

async def cmd_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _require_registered(update)
    if not user:
        return

    args = list(context.args)
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/out [tanggal] [kategori] [qty] [harga\\_satuan] [keterangan]`\n\n"
            "Contoh:\n"
            "`/out makan 2 25000 makan siang`\n"
            "`/out kemarin transport 1 35000 grab ke kantor`\n"
            "`/out 01/05 makan 1 50000 makan malam`\n\n"
            "*Tanggal opsional:* `kemarin` `besok` `2hari` `15` `01/05`\n"
            "Ketik /kategori untuk daftar kategori.",
            parse_mode="Markdown"
        )
        return

    date_str, day_name, args = parse_date_prefix(args)
    if date_str is None:
        now      = datetime.now(TZ)
        date_str = now.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(now.strftime("%A"), now.strftime("%A").upper())

    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/out [tanggal] [kategori] [qty] [harga\\_satuan] [keterangan]`",
            parse_mode="Markdown"
        )
        return

    category_raw = args[0].lower()
    try:
        qty        = float(args[1])
        unit_price = float(args[2])
    except ValueError:
        await update.message.reply_text(
            "❌ Qty dan harga satuan harus angka!\n"
            "Contoh: `/out makan 2 25000 makan siang`",
            parse_mode="Markdown"
        )
        return

    if qty <= 0 or unit_price <= 0:
        await update.message.reply_text("❌ Qty dan harga satuan harus lebih dari 0.")
        return

    description = " ".join(args[3:]) if len(args) > 3 else "-"
    category    = CATEGORIES_OUT.get(category_raw, "Lain-lain")

    context.user_data["pending_txn"] = {
        "type":           "OUT",
        "user_id":        _uid(update),
        "spreadsheet_id": user["spreadsheet_id"],
        "category":       category,
        "qty":            qty,
        "unit_price":     unit_price,
        "total":          qty * unit_price,
        "description":    description,
        "date_str":       date_str,
        "day_name":       day_name,
    }

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ya, catat", callback_data="txn_yes"),
        InlineKeyboardButton("❌ Batal",     callback_data="txn_no"),
    ]])
    await update.message.reply_text(
        _make_confirm_msg(context.user_data["pending_txn"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ─── /in ──────────────────────────────────────────────────────────────────────

async def cmd_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _require_registered(update)
    if not user:
        return

    args = list(context.args)
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Format: `/in [tanggal] [kategori] [nominal] [keterangan]`\n\n"
            "Contoh:\n"
            "`/in freelance 500000 transfer klien`\n"
            "`/in kemarin gaji 5000000 gaji bulan ini`\n\n"
            "*Tanggal opsional:* `kemarin` `besok` `2hari` `15` `01/05`",
            parse_mode="Markdown"
        )
        return

    date_str, day_name, args = parse_date_prefix(args)
    if date_str is None:
        now      = datetime.now(TZ)
        date_str = now.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(now.strftime("%A"), now.strftime("%A").upper())

    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Format: `/in [tanggal] [kategori] [nominal] [keterangan]`",
            parse_mode="Markdown"
        )
        return

    category_raw = args[0].lower()
    try:
        nominal = float(args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ Nominal harus angka!\n"
            "Contoh: `/in freelance 500000 transfer klien`",
            parse_mode="Markdown"
        )
        return

    if nominal <= 0:
        await update.message.reply_text("❌ Nominal harus lebih dari 0.")
        return

    description = " ".join(args[2:]) if len(args) > 2 else "-"
    category    = CATEGORIES_IN.get(category_raw, "Lain-lain")

    context.user_data["pending_txn"] = {
        "type":           "IN",
        "user_id":        _uid(update),
        "spreadsheet_id": user["spreadsheet_id"],
        "category":       category,
        "qty":            1,
        "unit_price":     nominal,
        "total":          nominal,
        "description":    description,
        "date_str":       date_str,
        "day_name":       day_name,
    }

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ya, catat", callback_data="txn_yes"),
        InlineKeyboardButton("❌ Batal",     callback_data="txn_no"),
    ]])
    await update.message.reply_text(
        _make_confirm_msg(context.user_data["pending_txn"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ─── Transaction confirmation callback ────────────────────────────────────────

async def confirm_txn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "txn_no":
        context.user_data.pop("pending_txn", None)
        await query.edit_message_text("Dibatalkan.")
        return

    pending = context.user_data.pop("pending_txn", None)
    if not pending:
        await query.edit_message_text("❌ Sesi kadaluarsa, silakan input ulang.")
        return

    trans_id = add_transaction(
        pending["user_id"],
        pending["type"],
        pending["category"],
        pending["qty"],
        pending["unit_price"],
        pending["description"],
        date_str=pending["date_str"],
        day_name=pending["day_name"],
    )

    # Async append to Sheets (non-blocking)
    loop = asyncio.get_event_loop()
    d    = datetime.strptime(pending["date_str"], "%Y-%m-%d")
    loop.run_in_executor(
        None,
        lambda sid=pending["spreadsheet_id"]: append_transaction_row(
            trans_id, pending["date_str"], pending["day_name"],
            pending["type"], pending["category"],
            pending["qty"], pending["unit_price"], pending["total"],
            pending["description"], d.year, d.month,
            spreadsheet_id=sid,
        )
    )

    dlabel = _format_date_label(pending["date_str"])

    if pending["type"] == "OUT":
        qty_str = int(pending["qty"]) if float(pending["qty"]).is_integer() else pending["qty"]
        text = (
            f"✅ *Pengeluaran dicatat!*\n"
            f"ID        : `#{trans_id}`\n"
            f"Tanggal   : {pending['day_name']}, {dlabel}\n"
            f"Kategori  : {pending['category']}\n"
            f"Jumlah    : {qty_str} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}"
        )
    else:
        text = (
            f"✅ *Pemasukan dicatat!*\n"
            f"ID        : `#{trans_id}`\n"
            f"Tanggal   : {pending['day_name']}, {dlabel}\n"
            f"Kategori  : {pending['category']}\n"
            f"Nominal   : *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}"
        )

    await query.edit_message_text(text, parse_mode="Markdown")


# ─── /today ───────────────────────────────────────────────────────────────────

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _require_registered(update)
    if not user:
        return
    text = format_daily_summary(user_id=_uid(update))
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /week ────────────────────────────────────────────────────────────────────

async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _require_registered(update)
    if not user:
        return
    text = format_weekly_summary(user_id=_uid(update))
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /list ────────────────────────────────────────────────────────────────────

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await _require_registered(update)
    if not user:
        return

    uid  = _uid(update)
    txns = get_today_transactions(user_id=uid)
    if not txns:
        await update.message.reply_text("Belum ada transaksi hari ini.")
        return

    now   = datetime.now(TZ)
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
    user = await _require_registered(update)
    if not user:
        return

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

    uid = _uid(update)
    t   = get_transaction_by_id(trans_id, user_id=uid)
    if not t:
        await update.message.reply_text(f"❌ Transaksi `#{trans_id}` tidak ditemukan.", parse_mode="Markdown")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ya, hapus", callback_data=f"del_confirm_{trans_id}"),
        InlineKeyboardButton("❌ Batal",     callback_data="del_cancel"),
    ]])
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
    uid      = str(query.from_user.id)
    success  = delete_transaction(trans_id, user_id=uid)
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
    user = await _require_registered(update)
    if not user:
        return

    uid            = _uid(update)
    spreadsheet_id = user["spreadsheet_id"]

    await update.message.reply_text("🔄 Menyinkronkan ke Google Sheets, harap tunggu...")
    now  = datetime.now(TZ)
    loop = asyncio.get_event_loop()

    ok_month = await loop.run_in_executor(
        None,
        lambda u=uid, s=spreadsheet_id: rebuild_month_sheet(
            now.year, now.month, user_id=u, spreadsheet_id=s
        )
    )
    ok_summary = await loop.run_in_executor(
        None,
        lambda u=uid, s=spreadsheet_id: update_summary_sheet(user_id=u, spreadsheet_id=s)
    )

    if ok_month and ok_summary:
        await update.message.reply_text("✅ Sinkronisasi berhasil!")
    else:
        await update.message.reply_text(
            "⚠️ Sinkronisasi gagal sebagian. Pastikan:\n"
            "1. Spreadsheet masih bisa diakses\n"
            "2. Service account masih punya akses Editor"
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
    app.add_handler(CommandHandler("register", cmd_register))
    app.add_handler(CommandHandler("out",      cmd_out))
    app.add_handler(CommandHandler("in",       cmd_in))
    app.add_handler(CommandHandler("today",    cmd_today))
    app.add_handler(CommandHandler("week",     cmd_week))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("hapus",    cmd_hapus))
    app.add_handler(CommandHandler("kategori", cmd_kategori))
    app.add_handler(CommandHandler("sync",     cmd_sync))
    app.add_handler(CallbackQueryHandler(confirm_txn_callback, pattern=r"^txn_"))
    app.add_handler(CallbackQueryHandler(hapus_callback,       pattern=r"^del_"))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(
        send_daily_summary,
        trigger="cron",
        hour=23, minute=59,
        args=[app.bot],
        id="daily_summary",
    )
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
