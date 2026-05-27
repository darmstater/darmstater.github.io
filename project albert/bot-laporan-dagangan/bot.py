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

from config import TELEGRAM_TOKEN, TIMEZONE, PRODUCTS, EXPENSE_OTHERS, MONTH_NAMES_ID, DAY_NAMES_ID
from database import (
    init_db, add_transaction, delete_transaction, update_transaction,
    get_date_transactions, get_transaction_by_id,
    get_stock_summary, get_cash_summary, get_date_cash_summary,
    register_group, get_group_config,
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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


def _cid(update: Update) -> str:
    return str(update.effective_chat.id)


def _format_stok(chat_id: str) -> str:
    stok = get_stock_summary(chat_id)
    tin, tout, bal = get_cash_summary(chat_id)
    lines = ["📦 *Stok Sekarang:*"]
    for p in ["Gas LPG 3kg", "Sunlight"]:
        s = stok.get(p, {"restock": 0, "sold": 0, "stok": 0})
        lines.append(
            f"  • {p}: *{int(s['stok'])} unit*"
            f"  _(masuk {int(s['restock'])}, terjual {int(s['sold'])})_"
        )
    sign = "+" if bal >= 0 else ""
    lines.append(f"\n💵 *Saldo Kas:*")
    lines.append(f"  Masuk   : +{fmt_rp(tin)}")
    lines.append(f"  Keluar  : -{fmt_rp(tout)}")
    lines.append(f"  *Saldo  : {sign}{fmt_rp(bal)}*")
    return "\n".join(lines)


def _get_spreadsheet_id(chat_id: str) -> str | None:
    cfg = get_group_config(chat_id)
    return cfg["spreadsheet_id"] if cfg else None


async def _require_setup(update: Update) -> str | None:
    cid = _cid(update)
    sid = _get_spreadsheet_id(cid)
    if not sid:
        await update.message.reply_text(
            "⚠️ *Bot belum di-setup!*\n\n"
            "Admin grup, jalankan dulu:\n"
            "`/setup <spreadsheet_id>`\n\n"
            "Spreadsheet ID ada di URL Google Sheets:\n"
            "`https://docs.google.com/spreadsheets/d/`*ID_INI*`/edit`\n\n"
            "Share spreadsheet ke service account dengan akses *Editor*.",
            parse_mode="Markdown"
        )
        return None
    return sid


def parse_date_prefix(args: list) -> tuple:
    """Returns (date_str, day_name, remaining_args)."""
    if not args:
        return None, None, args

    first  = args[0].lower()
    now    = datetime.now(TZ)
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
        p = first.split('/')
        try:
            target = TZ.localize(datetime(now.year, int(p[1]), int(p[0])))
        except (ValueError, OverflowError):
            return None, None, args
    elif re.match(r'^\d{1,2}$', first):
        try:
            target = TZ.localize(datetime(now.year, now.month, int(first)))
        except (ValueError, OverflowError):
            return None, None, args

    if target is not None:
        date_str = target.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(target.strftime("%A"), target.strftime("%A").upper())
        return date_str, day_name, args[1:]

    return None, None, args


def _format_date_label(date_str: str) -> str:
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
    if pending["type"] == "IN":
        qty     = int(pending["qty"]) if float(pending["qty"]).is_integer() else pending["qty"]
        dlabel  = _format_date_label(pending["date_str"])
        return (
            f"🛒 *Penjualan — {pending['day_name']}, {dlabel}*\n\n"
            f"Produk    : {pending['product']}\n"
            f"Pelanggan : {pending['customer']}\n"
            f"Jumlah    : {qty} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}\n\n"
            f"Catat penjualan ini?"
        )
    else:
        qty    = int(pending["qty"]) if float(pending["qty"]).is_integer() else pending["qty"]
        dlabel = _format_date_label(pending["date_str"])
        cat    = pending["category"]
        prod   = f" ({pending['product']})" if pending["product"] else ""
        return (
            f"📦 *{cat}{prod} — {pending['day_name']}, {dlabel}*\n\n"
            f"Kategori  : {cat}\n"
            f"Jumlah    : {qty} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}\n\n"
            f"Catat ini?"
        )


# ─── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid  = _cid(update)
    cfg  = get_group_config(cid)
    note = (
        "\n\n⚠️ *Belum di-setup!* Admin jalankan:\n"
        "`/setup <spreadsheet_id>`"
    ) if not cfg else ""

    text = (
        "🛒 *Bot Dagangan Eny* siap!\n\n"
        "*Catat penjualan:*\n"
        "`/in [tanggal] [pelanggan] [produk] [qty] [harga] [note]`\n\n"
        "*Catat restock/pengeluaran:*\n"
        "`/out [tanggal] [produk/kategori] [qty] [harga] [note]`\n\n"
        "*Tanggal (opsional, default hari ini):*\n"
        "`kemarin`  `besok`  `2hari`  `15`  `01/05`\n\n"
        "*Contoh Penjualan:*\n"
        "`/in Budi gas 1 20000`\n"
        "`/in SariBu sunlight 2 5000 bayar besok`\n"
        "`/in kemarin Pak RT gas 3 19000`\n\n"
        "*Contoh Restock:*\n"
        "`/out gas 25 16000 kulakan pagi`\n"
        "`/out sunlight 12 7000`\n"
        "`/out lain 1 50000 bensin motor`\n\n"
        "*Info & Ringkasan:*\n"
        "`/stok` — lihat stok + saldo kas\n"
        "`/today` — ringkasan hari ini\n"
        "`/week` — ringkasan minggu ini\n"
        "`/list` — daftar transaksi hari ini\n\n"
        "*Lainnya:*\n"
        "`/hapus [id]` — hapus transaksi\n"
        "`/edit [id] [field] [nilai]` — edit transaksi\n"
        "`/sync` — sinkronkan ke Google Sheets\n"
        "`/produk` — daftar produk & kategori\n"
        "`/setup <id>` — setup spreadsheet (admin)"
        + note
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /setup ───────────────────────────────────────────────────────────────────

async def cmd_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Format: `/setup <spreadsheet_id>`\n\n"
            "Spreadsheet ID ada di URL Google Sheets:\n"
            "`https://docs.google.com/spreadsheets/d/`*ID_INI*`/edit`\n\n"
            "Pastikan sudah share ke service account dengan akses *Editor*.",
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
            "❌ Tidak bisa mengakses spreadsheet.\n\n"
            "Pastikan:\n"
            "1. Spreadsheet ID benar\n"
            "2. Sudah di-share ke service account dengan akses *Editor*",
            parse_mode="Markdown"
        )
        return

    cid  = _cid(update)
    name = update.effective_chat.title or update.effective_user.first_name or "Grup"
    register_group(cid, spreadsheet_id, name)
    await update.message.reply_text(
        f"✅ *Setup berhasil!*\n\n"
        f"Grup    : {name}\n"
        f"Sheet ID: `{spreadsheet_id}`\n\n"
        f"Ketik /start untuk panduan lengkap.",
        parse_mode="Markdown"
    )


# ─── /in (penjualan) ──────────────────────────────────────────────────────────

async def cmd_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    args = list(context.args)
    if len(args) < 4:
        await update.message.reply_text(
            "⚠️ Format: `/in [tanggal] [pelanggan] [produk] [qty] [harga] [note]`\n\n"
            "Contoh:\n"
            "`/in Budi gas 1 20000`\n"
            "`/in SariBu sunlight 2 5000 bayar besok`\n"
            "`/in kemarin PakRT gas 3 19000`\n\n"
            "*Produk:* `gas` `lpg` `elpiji` `sunlight` `sl` `sabun`\n"
            "*Tanggal opsional:* `kemarin` `besok` `2hari` `15` `01/05`",
            parse_mode="Markdown"
        )
        return

    date_str, day_name, args = parse_date_prefix(args)
    if date_str is None:
        now      = datetime.now(TZ)
        date_str = now.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(now.strftime("%A"), now.strftime("%A").upper())

    if len(args) < 4:
        await update.message.reply_text(
            "⚠️ Format: `/in [tanggal] [pelanggan] [produk] [qty] [harga] [note]`",
            parse_mode="Markdown"
        )
        return

    customer    = args[0]
    product_raw = args[1].lower()
    product     = PRODUCTS.get(product_raw)

    if not product:
        await update.message.reply_text(
            f"❌ Produk `{product_raw}` tidak dikenal.\n\n"
            "Produk yang tersedia:\n"
            "`gas` `lpg` `elpiji` `tabung` → Gas LPG 3kg\n"
            "`sunlight` `sl` `sabun` `cuci` → Sunlight",
            parse_mode="Markdown"
        )
        return

    try:
        qty        = float(args[2])
        unit_price = float(args[3])
    except ValueError:
        await update.message.reply_text(
            "❌ Qty dan harga harus angka!\n"
            "Contoh: `/in Budi gas 1 20000`",
            parse_mode="Markdown"
        )
        return

    if qty <= 0 or unit_price <= 0:
        await update.message.reply_text("❌ Qty dan harga harus lebih dari 0.")
        return

    description = " ".join(args[4:]) if len(args) > 4 else "-"

    context.user_data["pending_txn"] = {
        "type":        "IN",
        "chat_id":     _cid(update),
        "spreadsheet": sid,
        "product":     product,
        "category":    f"Penjualan {product}",
        "customer":    customer,
        "qty":         qty,
        "unit_price":  unit_price,
        "total":       qty * unit_price,
        "description": description,
        "date_str":    date_str,
        "day_name":    day_name,
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


# ─── /out (restock / pengeluaran) ─────────────────────────────────────────────

async def cmd_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    args = list(context.args)
    if len(args) < 3:
        await update.message.reply_text(
            "⚠️ Format: `/out [tanggal] [produk/kategori] [qty] [harga] [note]`\n\n"
            "Contoh Restock:\n"
            "`/out gas 25 16000 kulakan pagi`\n"
            "`/out sunlight 12 7000`\n"
            "`/out kemarin gas 25 16000`\n\n"
            "Contoh Pengeluaran lain:\n"
            "`/out lain 1 50000 bensin motor`\n"
            "`/out operasional 1 20000 ongkir`\n\n"
            "*Tanggal opsional:* `kemarin` `besok` `2hari` `15` `01/05`",
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
            "⚠️ Format: `/out [tanggal] [produk/kategori] [qty] [harga] [note]`",
            parse_mode="Markdown"
        )
        return

    cat_raw = args[0].lower()
    try:
        qty        = float(args[1])
        unit_price = float(args[2])
    except ValueError:
        await update.message.reply_text(
            "❌ Qty dan harga harus angka!\n"
            "Contoh: `/out gas 25 16000`",
            parse_mode="Markdown"
        )
        return

    if qty <= 0 or unit_price <= 0:
        await update.message.reply_text("❌ Qty dan harga harus lebih dari 0.")
        return

    description = " ".join(args[3:]) if len(args) > 3 else "-"

    # Determine if it's a product restock or other expense
    product  = PRODUCTS.get(cat_raw)
    if product:
        category = f"Restock {product}"
    else:
        category = EXPENSE_OTHERS.get(cat_raw, "Lain-lain")
        product  = None

    context.user_data["pending_txn"] = {
        "type":        "OUT",
        "chat_id":     _cid(update),
        "spreadsheet": sid,
        "product":     product,
        "category":    category,
        "customer":    None,
        "qty":         qty,
        "unit_price":  unit_price,
        "total":       qty * unit_price,
        "description": description,
        "date_str":    date_str,
        "day_name":    day_name,
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
        pending["chat_id"],
        pending["type"],
        pending["product"],
        pending["category"],
        pending["customer"],
        pending["qty"],
        pending["unit_price"],
        pending["description"],
        pending["date_str"],
        pending["day_name"],
    )

    # Async append to Sheets
    loop = asyncio.get_event_loop()
    d    = datetime.strptime(pending["date_str"], "%Y-%m-%d")
    loop.run_in_executor(
        None,
        lambda: append_transaction_row(
            trans_id, pending["date_str"], pending["day_name"],
            pending["type"], pending["product"], pending["category"],
            pending["customer"], pending["qty"], pending["unit_price"], pending["total"],
            pending["description"], d.year, d.month,
            spreadsheet_id=pending["spreadsheet"],
        )
    )

    dlabel = _format_date_label(pending["date_str"])
    qty    = int(pending["qty"]) if float(pending["qty"]).is_integer() else pending["qty"]

    if pending["type"] == "IN":
        text = (
            f"✅ *Penjualan dicatat!*\n"
            f"ID        : `#{trans_id}`\n"
            f"Tanggal   : {pending['day_name']}, {dlabel}\n"
            f"Produk    : {pending['product']}\n"
            f"Pelanggan : {pending['customer']}\n"
            f"Jumlah    : {qty} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}\n\n"
            + _format_stok(pending["chat_id"])
        )
    else:
        prod_note = f" ({pending['product']})" if pending["product"] else ""
        text = (
            f"✅ *{pending['category']}{prod_note} dicatat!*\n"
            f"ID        : `#{trans_id}`\n"
            f"Tanggal   : {pending['day_name']}, {dlabel}\n"
            f"Jumlah    : {qty} × {fmt_rp(pending['unit_price'])} = *{fmt_rp(pending['total'])}*\n"
            f"Keterangan: {pending['description']}\n\n"
            + _format_stok(pending["chat_id"])
        )

    await query.edit_message_text(text, parse_mode="Markdown")


# ─── /stok ────────────────────────────────────────────────────────────────────

async def cmd_stok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return
    await update.message.reply_text(_format_stok(_cid(update)), parse_mode="Markdown")


# ─── /today ───────────────────────────────────────────────────────────────────

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return
    text = format_daily_summary(_cid(update))
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /week ────────────────────────────────────────────────────────────────────

async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return
    text = format_weekly_summary(_cid(update))
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /list ────────────────────────────────────────────────────────────────────

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    cid  = _cid(update)
    args = list(context.args)

    date_str, day_name, _ = parse_date_prefix(args)
    if date_str is None:
        now      = datetime.now(TZ)
        date_str = now.strftime("%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(now.strftime("%A"), now.strftime("%A").upper())

    txns   = get_date_transactions(date_str, cid)
    dlabel = _format_date_label(date_str)

    if not txns:
        await update.message.reply_text(f"Belum ada transaksi {dlabel}.")
        return

    lines = [f"📋 *Transaksi {day_name}, {dlabel}:*\n"]
    for t in txns:
        qty  = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
        icon = "🛒" if t["type"] == "IN" else "📦"
        lbl  = t["customer"] if t["customer"] and t["customer"] != "-" else t["description"] or "-"
        lines.append(
            f"{icon} `#{t['id']}` {t['product'] or t['category']}\n"
            f"    {qty} × {fmt_rp(t['unit_price'])} = *{fmt_rp(t['total_price'])}*"
            f"  _({lbl})_\n"
        )

    tin, tout, net = get_date_cash_summary(date_str, cid)
    sign = "+" if net >= 0 else ""
    lines.append(
        f"─────────────────\n"
        f"Masuk: +{fmt_rp(tin)} | Keluar: -{fmt_rp(tout)}\n"
        f"*NET: {sign}{fmt_rp(net)}*"
    )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── /hapus ───────────────────────────────────────────────────────────────────

async def cmd_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Format: `/hapus [id] [id] ...`\n\n"
            "Contoh:\n"
            "`/hapus 5` — hapus satu\n"
            "`/hapus 5 6 7` — hapus beberapa\n\n"
            "Gunakan /list untuk melihat ID transaksi.",
            parse_mode="Markdown"
        )
        return

    raw = " ".join(args).replace(",", " ").split()
    ids = []
    for token in raw:
        try:
            ids.append(int(token.lstrip("#")))
        except ValueError:
            await update.message.reply_text(
                f"❌ `{token}` bukan ID yang valid.", parse_mode="Markdown"
            )
            return

    cid   = _cid(update)
    found = []
    not_found = []
    for tid in ids:
        t = get_transaction_by_id(tid, cid)
        if t:
            found.append(t)
        else:
            not_found.append(tid)

    if not found:
        await update.message.reply_text("❌ Tidak ada transaksi yang ditemukan.")
        return

    context.user_data["pending_hapus"] = [t["id"] for t in found]

    lines = [f"Hapus {len(found)} transaksi berikut?\n"]
    for t in found:
        qty  = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
        icon = "🛒" if t["type"] == "IN" else "📦"
        lines.append(
            f"{icon} `#{t['id']}` {t['product'] or t['category']} — "
            f"{qty} × {fmt_rp(t['unit_price'])} = *{fmt_rp(t['total_price'])}*"
        )

    if not_found:
        lines.append(f"\n_ID tidak ditemukan: {', '.join(f'#{i}' for i in not_found)}_")

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ya, hapus", callback_data="del_confirm"),
        InlineKeyboardButton("❌ Batal",     callback_data="del_cancel"),
    ]])
    await update.message.reply_text(
        "\n".join(lines), reply_markup=keyboard, parse_mode="Markdown"
    )


async def hapus_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "del_cancel":
        context.user_data.pop("pending_hapus", None)
        await query.edit_message_text("Dibatalkan.")
        return

    ids = context.user_data.pop("pending_hapus", None)
    if not ids:
        await query.edit_message_text("❌ Sesi kadaluarsa.")
        return

    cid     = str(query.message.chat_id)
    deleted = [tid for tid in ids if delete_transaction(tid, cid)]

    if len(deleted) == 1:
        await query.edit_message_text(
            f"✅ Transaksi `#{deleted[0]}` dihapus.", parse_mode="Markdown"
        )
    else:
        id_list = ", ".join(f"`#{i}`" for i in deleted)
        await query.edit_message_text(
            f"✅ {len(deleted)} transaksi dihapus: {id_list}", parse_mode="Markdown"
        )


# ─── /edit ────────────────────────────────────────────────────────────────────

_EDIT_FIELD_MAP = {
    "harga":      "unit_price",
    "jumlah":     "unit_price",
    "nominal":    "unit_price",
    "qty":        "quantity",
    "kuantitas":  "quantity",
    "pelanggan":  "customer",
    "keterangan": "description",
    "deskripsi":  "description",
    "tanggal":    "date",
}


async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    args = list(context.args)
    if len(args) < 3:
        await update.message.reply_text(
            "Format: `/edit <id> <field> <nilai baru>`\n\n"
            "Field yang bisa diubah:\n"
            "`harga` — harga satuan\n"
            "`qty` — kuantitas\n"
            "`pelanggan` — nama pelanggan\n"
            "`keterangan` — catatan\n"
            "`tanggal` — tanggal (`kemarin` `2hari` `15` `01/05`)\n\n"
            "Contoh:\n"
            "`/edit 5 harga 21000`\n"
            "`/edit 5 pelanggan BuTini`\n\n"
            "Gunakan /list untuk melihat ID.",
            parse_mode="Markdown"
        )
        return

    try:
        trans_id = int(args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("❌ ID harus angka.", parse_mode="Markdown")
        return

    cid = _cid(update)
    txn = get_transaction_by_id(trans_id, cid)
    if not txn:
        await update.message.reply_text(
            f"❌ Transaksi `#{trans_id}` tidak ditemukan.", parse_mode="Markdown"
        )
        return

    field_raw     = args[1].lower()
    new_value_raw = " ".join(args[2:])
    db_field      = _EDIT_FIELD_MAP.get(field_raw)

    if not db_field:
        await update.message.reply_text(
            "❌ Field tidak dikenal.\n\n"
            "Field valid: `harga` `qty` `pelanggan` `keterangan` `tanggal`",
            parse_mode="Markdown"
        )
        return

    updates      = {}
    display_old  = ""
    display_new  = ""
    new_date_str = txn["date"]

    if db_field == "unit_price":
        try:
            new_price = float(new_value_raw)
        except ValueError:
            await update.message.reply_text("❌ Harga harus angka.", parse_mode="Markdown")
            return
        if new_price <= 0:
            await update.message.reply_text("❌ Harga harus lebih dari 0.", parse_mode="Markdown")
            return
        updates    = {"unit_price": new_price, "total_price": txn["quantity"] * new_price}
        display_old = fmt_rp(txn["unit_price"])
        display_new = fmt_rp(new_price)

    elif db_field == "quantity":
        try:
            new_qty = float(new_value_raw)
        except ValueError:
            await update.message.reply_text("❌ Qty harus angka.", parse_mode="Markdown")
            return
        if new_qty <= 0:
            await update.message.reply_text("❌ Qty harus lebih dari 0.", parse_mode="Markdown")
            return
        old_q = int(txn["quantity"]) if float(txn["quantity"]).is_integer() else float(txn["quantity"])
        new_q = int(new_qty) if new_qty.is_integer() else new_qty
        updates    = {"quantity": new_qty, "total_price": new_qty * txn["unit_price"]}
        display_old = str(old_q)
        display_new = str(new_q)

    elif db_field == "customer":
        if not new_value_raw.strip():
            await update.message.reply_text("❌ Nama pelanggan tidak boleh kosong.", parse_mode="Markdown")
            return
        updates    = {"customer": new_value_raw.strip()}
        display_old = txn["customer"] or "-"
        display_new = new_value_raw.strip()

    elif db_field == "description":
        if not new_value_raw.strip():
            await update.message.reply_text("❌ Keterangan tidak boleh kosong.", parse_mode="Markdown")
            return
        updates    = {"description": new_value_raw.strip()}
        display_old = txn["description"] or "-"
        display_new = new_value_raw.strip()

    elif db_field == "date":
        new_date_str, new_day_name, _ = parse_date_prefix([new_value_raw])
        if new_date_str is None:
            await update.message.reply_text(
                "❌ Format tanggal tidak valid.\n"
                "Gunakan: `kemarin` `besok` `2hari` `15` `01/05`",
                parse_mode="Markdown"
            )
            return
        updates    = {"date": new_date_str, "day_name": new_day_name}
        display_old = _format_date_label(txn["date"])
        display_new = _format_date_label(new_date_str)

    context.user_data["pending_edit"] = {
        "trans_id":    trans_id,
        "chat_id":     cid,
        "spreadsheet": sid,
        "updates":     updates,
        "field_label": field_raw,
        "display_old": display_old,
        "display_new": display_new,
        "orig_date":   txn["date"],
        "new_date":    new_date_str,
    }

    icon  = "🛒" if txn["type"] == "IN" else "📦"
    ttype = "Penjualan" if txn["type"] == "IN" else "Pengeluaran"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ya, ubah", callback_data="edit_confirm"),
        InlineKeyboardButton("❌ Batal",    callback_data="edit_cancel"),
    ]])
    await update.message.reply_text(
        f"{icon} *Edit Transaksi `#{trans_id}`* ({ttype})\n\n"
        f"Field   : *{field_raw}*\n"
        f"Sebelum : {display_old}\n"
        f"Sesudah : {display_new}\n\n"
        f"Konfirmasi perubahan?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_cancel":
        context.user_data.pop("pending_edit", None)
        await query.edit_message_text("Dibatalkan.")
        return

    pending = context.user_data.pop("pending_edit", None)
    if not pending:
        await query.edit_message_text("❌ Sesi kadaluarsa.")
        return

    ok = update_transaction(pending["trans_id"], pending["chat_id"], **pending["updates"])
    if not ok:
        await query.edit_message_text("❌ Gagal mengubah transaksi.")
        return

    loop = asyncio.get_event_loop()
    cid  = pending["chat_id"]
    sid  = pending["spreadsheet"]

    def _rebuild():
        months = set()
        for ds in {pending["orig_date"], pending["new_date"]}:
            d = datetime.strptime(ds, "%Y-%m-%d")
            months.add((d.year, d.month))
        for year, month in months:
            rebuild_month_sheet(year, month, cid, sid)
        update_summary_sheet(cid, sid)

    loop.run_in_executor(None, _rebuild)

    await query.edit_message_text(
        f"✅ Transaksi `#{pending['trans_id']}` berhasil diubah.\n"
        f"*{pending['field_label']}*: {pending['display_old']} → {pending['display_new']}",
        parse_mode="Markdown"
    )


# ─── /produk ──────────────────────────────────────────────────────────────────

async def cmd_produk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Produk untuk /in (penjualan) dan /out (restock):*\n"
        "`gas` `lpg` `elpiji` `tabung` → Gas LPG 3kg\n"
        "`sunlight` `sl` `sabun` `cuci` → Sunlight\n\n"
        "*Kategori untuk /out lain-lain:*\n"
        "`lain` `other` `dll` → Lain-lain\n"
        "`operasional` `ops` `transport` `bensin` `ongkir` `parkir` → Operasional"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /sync ────────────────────────────────────────────────────────────────────

async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = await _require_setup(update)
    if not sid:
        return

    cid = _cid(update)
    await update.message.reply_text("🔄 Menyinkronkan ke Google Sheets, harap tunggu...")

    now  = datetime.now(TZ)
    loop = asyncio.get_event_loop()

    ok1 = await loop.run_in_executor(
        None, lambda: rebuild_month_sheet(now.year, now.month, cid, sid)
    )
    ok2 = await loop.run_in_executor(
        None, lambda: update_summary_sheet(cid, sid)
    )

    if ok1 and ok2:
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
        "❓ Perintah tidak dikenal. Ketik /start untuk panduan lengkap."
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    init_db()
    logger.info("Database initialized")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("setup",   cmd_setup))
    app.add_handler(CommandHandler("in",      cmd_in))
    app.add_handler(CommandHandler("out",     cmd_out))
    app.add_handler(CommandHandler("stok",    cmd_stok))
    app.add_handler(CommandHandler("today",   cmd_today))
    app.add_handler(CommandHandler("week",    cmd_week))
    app.add_handler(CommandHandler("list",    cmd_list))
    app.add_handler(CommandHandler("hapus",   cmd_hapus))
    app.add_handler(CommandHandler("edit",    cmd_edit))
    app.add_handler(CommandHandler("produk",  cmd_produk))
    app.add_handler(CommandHandler("sync",    cmd_sync))
    app.add_handler(CallbackQueryHandler(confirm_txn_callback, pattern=r"^txn_"))
    app.add_handler(CallbackQueryHandler(hapus_callback,       pattern=r"^del_"))
    app.add_handler(CallbackQueryHandler(edit_callback,        pattern=r"^edit_"))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(
        send_daily_summary, trigger="cron", hour=23, minute=59,
        args=[app.bot], id="daily_summary",
    )
    scheduler.add_job(
        send_weekly_summary_and_sync, trigger="cron",
        day_of_week="sun", hour=23, minute=59,
        args=[app.bot], id="weekly_summary",
    )
    scheduler.start()
    logger.info("Scheduler started — daily@23:59 | weekly(Sun)@23:59")
    logger.info("Bot DaganganEny is running...")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
