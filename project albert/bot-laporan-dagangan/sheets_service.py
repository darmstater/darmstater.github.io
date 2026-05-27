import json
import logging
import calendar as _cal
from datetime import datetime, timedelta, date as date_type
from collections import defaultdict, OrderedDict

import gspread
import pytz

from config import GOOGLE_CREDENTIALS_JSON, TIMEZONE, MONTH_NAMES_ID, DAY_NAMES_ID
from database import get_month_transactions, get_all_transactions

logger = logging.getLogger(__name__)
TZ     = pytz.timezone(TIMEZONE)

# ─── Colors ───────────────────────────────────────────────────────────────────
C_TITLE_BG      = {"red": 0.102, "green": 0.137, "blue": 0.494}   # dark navy
C_WHITE         = {"red": 1.0,   "green": 1.0,   "blue": 1.0}
C_COL_HEADER_BG = {"red": 0.176, "green": 0.490, "blue": 0.259}   # dark green
C_IN_ROW        = {"red": 0.878, "green": 0.961, "blue": 0.894}   # light green
C_OUT_ROW       = {"red": 1.0,   "green": 0.922, "blue": 0.925}   # light pink
C_NET_POS       = {"red": 0.831, "green": 0.953, "blue": 0.831}
C_NET_NEG       = {"red": 1.0,   "green": 0.831, "blue": 0.831}
C_WEEK_BG       = {"red": 0.824, "green": 0.898, "blue": 0.980}
C_WEEK_CAT_BG  = {"red": 0.906, "green": 0.937, "blue": 0.992}
C_SUMMARY_TOTAL = {"red": 1.0,   "green": 0.867, "blue": 0.557}
C_STOK_HEADER   = {"red": 0.255, "green": 0.412, "blue": 0.882}   # royal blue
C_STOK_GAS      = {"red": 0.929, "green": 0.961, "blue": 1.0}
C_STOK_SL       = {"red": 1.0,   "green": 0.973, "blue": 0.882}

HEADERS = [
    "NO", "HARI", "TANGGAL", "TIPE", "PRODUK",
    "PELANGGAN / KETERANGAN", "QTY", "HARGA SATUAN", "TOTAL", "SALDO HARIAN"
]

def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


def _border(w=1, color=None):
    c = color or {"red": 0.75, "green": 0.75, "blue": 0.75}
    b = {"style": "SOLID", "width": w, "color": c}
    return {"top": b, "bottom": b, "left": b, "right": b}


def _thick_border():
    return _border(2, {"red": 0.3, "green": 0.3, "blue": 0.3})


def _cell_fmt(bg=None, bold=False, italic=False, font_size=10,
              fg=None, h_align="LEFT", v_align="MIDDLE", wrap=False, borders=None):
    fmt = {
        "textFormat": {"bold": bold, "italic": italic, "fontSize": font_size},
        "horizontalAlignment": h_align,
        "verticalAlignment": v_align,
        "wrapStrategy": "WRAP" if wrap else "OVERFLOW_CELL",
    }
    if bg:
        fmt["backgroundColor"] = bg
    if fg:
        fmt["textFormat"]["foregroundColor"] = fg
    if borders:
        fmt["borders"] = borders
    return fmt


_FF = "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)"


def _rc(sid, r0, r1, c0, c1, fmt):
    return {"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "cell": {"userEnteredFormat": fmt},
        "fields": _FF,
    }}


def _merge(sid, r0, r1, c0, c1):
    return {"mergeCells": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "mergeType": "MERGE_ALL",
    }}


def _col_w(sid, c0, c1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}


def _row_h(sid, r0, r1, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _get_ss(spreadsheet_id):
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("GOOGLE_CREDENTIALS_JSON not set")
    if not spreadsheet_id:
        raise ValueError("No spreadsheet_id")
    creds = json.loads(GOOGLE_CREDENTIALS_JSON)
    gc    = gspread.service_account_from_dict(creds)
    return gc.open_by_key(spreadsheet_id)


def _get_or_create_ws(ss, name, rows=600, cols=12):
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        return ss.add_worksheet(title=name, rows=rows, cols=cols)


def verify_spreadsheet_access(spreadsheet_id: str) -> bool:
    try:
        _get_ss(spreadsheet_id)
        return True
    except Exception:
        return False


# ─── Month sheet ──────────────────────────────────────────────────────────────

def rebuild_month_sheet(year, month, chat_id, spreadsheet_id) -> bool:
    try:
        ss = _get_ss(spreadsheet_id)
    except Exception as e:
        logger.error(f"Sheets auth failed: {e}")
        return False

    month_name  = MONTH_NAMES_ID[month]
    sheet_title = f"{month_name} {year}"
    ws  = _get_or_create_ws(ss, sheet_title)
    sid = ws.id

    ws.clear()
    try:
        ss.batch_update({"requests": [{"unmergeCells": {"range": {
            "sheetId": sid, "startRowIndex": 0, "endRowIndex": 1000,
            "startColumnIndex": 0, "endColumnIndex": 12,
        }}}]})
    except Exception:
        pass

    transactions = get_month_transactions(year, month, chat_id)
    by_date: OrderedDict = OrderedDict()
    for t in sorted(transactions, key=lambda x: (x["date"], x["created_at"])):
        by_date.setdefault(t["date"], []).append(t)

    DATA_START = 3
    all_rows: list = []
    reqs:     list = []

    # Reset all formatting
    reqs.append({"repeatCell": {
        "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1000,
                  "startColumnIndex": 0, "endColumnIndex": 12},
        "cell": {"userEnteredFormat": {}},
        "fields": "userEnteredFormat",
    }})

    _DATA_ALIGNS = [
        (0, 3, "CENTER"),   # NO, HARI, TANGGAL
        (3, 4, "CENTER"),   # TIPE
        (4, 5, "LEFT"),     # PRODUK
        (5, 6, "LEFT"),     # PELANGGAN/KET
        (6, 7, "CENTER"),   # QTY
        (7, 9, "RIGHT"),    # HARGA SATUAN, TOTAL
    ]

    def _data_row(row_0i, bg):
        reqs_ = []
        for c0, c1, align in _DATA_ALIGNS:
            reqs_.append(_rc(sid, row_0i, row_0i+1, c0, c1,
                _cell_fmt(bg=bg, h_align=align, v_align="MIDDLE", borders=_border())))
        return reqs_

    trans_no = 1
    cur_row  = DATA_START

    # Group by ISO-week
    week_groups: OrderedDict = OrderedDict()
    for date_str in by_date:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        mon = d - timedelta(days=d.weekday())
        sun = mon + timedelta(days=6)
        key = mon.isoformat()
        if key not in week_groups:
            week_groups[key] = {"monday": mon, "sunday": sun, "dates": []}
        week_groups[key]["dates"].append(date_str)

    now      = datetime.now(TZ)
    today    = now.date()
    week_num = 1

    for week_key, wi in week_groups.items():
        monday: date_type = wi["monday"]
        sunday: date_type = wi["sunday"]
        week_trans = []

        for date_str in sorted(wi["dates"]):
            day_trans = by_date[date_str]
            d         = datetime.strptime(date_str, "%Y-%m-%d").date()
            day_lbl   = DAY_NAMES_ID.get(d.strftime("%A"), d.strftime("%A").upper())
            date_lbl  = f"{d.day} {MONTH_NAMES_ID[d.month]}"

            day_in  = sum(t["total_price"] for t in day_trans if t["type"] == "IN")
            day_out = sum(t["total_price"] for t in day_trans if t["type"] == "OUT")
            day_net = day_in - day_out
            sign    = "+" if day_net >= 0 else ""
            saldo_text = (
                f"MASUK  : +{fmt_rp(day_in)}\n"
                f"KELUAR : -{fmt_rp(day_out)}\n"
                f"NET      : {sign}{fmt_rp(day_net)}"
            )

            day_start_row = cur_row

            for i, t in enumerate(day_trans):
                qty      = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
                tipe_lbl = "JUAL" if t["type"] == "IN" else "BELI"
                label    = t["customer"] if t["customer"] and t["customer"] != "-" else t["description"] or "-"
                row = [
                    trans_no, day_lbl, date_lbl,
                    tipe_lbl, t["product"] or "-",
                    label, qty,
                    fmt_rp(t["unit_price"]), fmt_rp(t["total_price"]),
                    saldo_text if i == 0 else "",
                ]
                all_rows.append(row)
                bg = C_IN_ROW if t["type"] == "IN" else C_OUT_ROW
                reqs.extend(_data_row(cur_row - 1, bg))
                trans_no += 1
                cur_row  += 1
                week_trans.append(t)

            day_end_row = cur_row
            r0 = day_start_row - 1
            r1 = day_end_row   - 1
            if r1 - r0 >= 1:
                reqs.append(_merge(sid, r0, r1, 9, 10))
            net_bg = C_NET_POS if day_net >= 0 else C_NET_NEG
            reqs.append(_rc(sid, r0, r1, 9, 10,
                _cell_fmt(bg=net_bg, bold=True, font_size=9,
                          h_align="CENTER", v_align="MIDDLE", wrap=True, borders=_thick_border())))

        is_last = week_key == list(week_groups.keys())[-1]
        if sunday <= today or is_last:
            w_in  = sum(t["total_price"] for t in week_trans if t["type"] == "IN")
            w_out = sum(t["total_price"] for t in week_trans if t["type"] == "OUT")
            w_net = w_in - w_out
            sign  = "+" if w_net >= 0 else ""

            mon_day = monday.day if monday.month == month else 1
            sun_day = sunday.day if sunday.month == month else _cal.monthrange(year, month)[1]
            week_label = f"TOTAL MINGGU {week_num}   ({mon_day} – {sun_day} {MONTH_NAMES_ID[month]})"

            # stok minggu ini
            stok_gas = sum(
                t["quantity"] * (1 if t["type"] == "OUT" else -1)
                for t in week_trans if t["product"] == "Gas LPG 3kg"
            )
            stok_sl = sum(
                t["quantity"] * (1 if t["type"] == "OUT" else -1)
                for t in week_trans if t["product"] == "Sunlight"
            )
            stok_note = f"Gas beli={int(sum(t['quantity'] for t in week_trans if t['type']=='OUT' and t['product']=='Gas LPG 3kg'))} jual={int(sum(t['quantity'] for t in week_trans if t['type']=='IN' and t['product']=='Gas LPG 3kg'))}"

            saldo_week = (
                f"MASUK  : +{fmt_rp(w_in)}\n"
                f"KELUAR : -{fmt_rp(w_out)}\n"
                f"NET      : {sign}{fmt_rp(abs(w_net))}"
            )
            summary_row = [
                week_label, "", "", "", "", stok_note, "", "", "", saldo_week
            ]
            all_rows.append(summary_row)
            sr0 = cur_row - 1
            reqs.append(_merge(sid, sr0, sr0+1, 0, 5))
            net_bg = C_NET_POS if w_net >= 0 else C_NET_NEG
            reqs.append(_rc(sid, sr0, sr0+1, 0, 10,
                _cell_fmt(bg=C_WEEK_BG, bold=True, h_align="CENTER",
                          v_align="MIDDLE", borders=_thick_border())))
            reqs.append(_rc(sid, sr0, sr0+1, 9, 10,
                _cell_fmt(bg=net_bg, bold=True, font_size=9,
                          h_align="CENTER", v_align="MIDDLE", wrap=True, borders=_thick_border())))
            cur_row  += 1
            week_num += 1

    title_text = f"DAGANGAN ENY  ·  {month_name.upper()} {year}"
    ws.update("A1", [[title_text]])
    ws.update("A2", [HEADERS])
    if all_rows:
        ws.update(f"A{DATA_START}", all_rows, value_input_option="USER_ENTERED")

    static = [
        _merge(sid, 0, 1, 0, 10),
        _rc(sid, 0, 1, 0, 10, _cell_fmt(bg=C_TITLE_BG, bold=True, font_size=14,
                                         fg=C_WHITE, h_align="CENTER", v_align="MIDDLE")),
        _rc(sid, 1, 2, 0, 10, _cell_fmt(bg=C_COL_HEADER_BG, bold=True,
                                         fg=C_WHITE, h_align="CENTER", v_align="MIDDLE", borders=_border())),
        _col_w(sid, 0, 1, 45),    # NO
        _col_w(sid, 1, 2, 80),    # HARI
        _col_w(sid, 2, 3, 100),   # TANGGAL
        _col_w(sid, 3, 4, 60),    # TIPE
        _col_w(sid, 4, 5, 120),   # PRODUK
        _col_w(sid, 5, 6, 200),   # PELANGGAN/KET
        _col_w(sid, 6, 7, 55),    # QTY
        _col_w(sid, 7, 8, 125),   # HARGA SATUAN
        _col_w(sid, 8, 9, 125),   # TOTAL
        _col_w(sid, 9, 10, 165),  # SALDO HARIAN
        _row_h(sid, 0, 1, 45),
        {"updateSheetProperties": {
            "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 2}},
            "fields": "gridProperties.frozenRowCount",
        }},
    ]
    ss.batch_update({"requests": static + reqs})
    logger.info(f"Sheet '{sheet_title}' rebuilt — {len(transactions)} transactions")
    return True


# ─── STOK + SUMMARY sheet ─────────────────────────────────────────────────────

def update_summary_sheet(chat_id, spreadsheet_id) -> bool:
    try:
        ss = _get_ss(spreadsheet_id)
    except Exception as e:
        logger.error(f"Sheets auth failed: {e}")
        return False

    ws  = _get_or_create_ws(ss, "SUMMARY & STOK", rows=500, cols=9)
    sid = ws.id
    ws.clear()
    try:
        ss.batch_update({"requests": [{"unmergeCells": {"range": {
            "sheetId": sid, "startRowIndex": 0, "endRowIndex": 500,
            "startColumnIndex": 0, "endColumnIndex": 9,
        }}}]})
    except Exception:
        pass

    all_txns = get_all_transactions(chat_id)

    # ── Current stock block ─────────────────────────────────────────────────
    from database import get_stock_summary, get_cash_summary
    stok  = get_stock_summary(chat_id)
    tin, tout, bal = get_cash_summary(chat_id)

    stok_rows = [
        ["📦 STOK BARANG SAAT INI", "", "", "", "", "", "", "", ""],
        ["Produk", "Total Restock", "Total Terjual", "Stok Tersisa", "", "", "", "", ""],
    ]
    for prod in ["Gas LPG 3kg", "Sunlight"]:
        s = stok.get(prod, {"restock": 0, "sold": 0, "stok": 0})
        stok_rows.append([
            prod,
            int(s["restock"]),
            int(s["sold"]),
            int(s["stok"]),
            "", "", "", "", ""
        ])

    stok_rows += [
        ["", "", "", "", "", "", "", "", ""],
        ["💵 SALDO KAS KESELURUHAN", "", "", "", "", "", "", "", ""],
        ["Total Pemasukan",   fmt_rp(tin),  "", "", "", "", "", "", ""],
        ["Total Pengeluaran", fmt_rp(tout), "", "", "", "", "", "", ""],
        ["Saldo Bersih",      fmt_rp(bal),  "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
    ]

    # ── Monthly summary ─────────────────────────────────────────────────────
    by_ym: dict = defaultdict(list)
    for t in all_txns:
        d = datetime.strptime(t["date"], "%Y-%m-%d").date()
        by_ym[(d.year, d.month)].append(t)

    S_HEADERS = [
        "PERIODE", "OMZET PENJUALAN",
        "MODAL RESTOCK", "BIAYA LAIN", "TOTAL KELUAR", "MARGIN",
        "TERJUAL GAS", "TERJUAL SUNLIGHT", "STOK AKHIR (est.)"
    ]
    monthly_rows: list = []

    for (year, month) in sorted(by_ym.keys()):
        mts = by_ym[(year, month)]
        mn  = MONTH_NAMES_ID[month]

        omzet     = sum(t["total_price"] for t in mts if t["type"] == "IN")
        restock   = sum(t["total_price"] for t in mts if t["type"] == "OUT" and t["product"])
        biaya     = sum(t["total_price"] for t in mts if t["type"] == "OUT" and not t["product"])
        total_out = restock + biaya
        margin    = omzet - total_out

        sold_gas = sum(t["quantity"] for t in mts if t["type"] == "IN" and t["product"] == "Gas LPG 3kg")
        sold_sl  = sum(t["quantity"] for t in mts if t["type"] == "IN" and t["product"] == "Sunlight")

        beli_gas = sum(t["quantity"] for t in mts if t["type"] == "OUT" and t["product"] == "Gas LPG 3kg")
        beli_sl  = sum(t["quantity"] for t in mts if t["type"] == "OUT" and t["product"] == "Sunlight")

        monthly_rows.append([
            f"{mn} {year}",
            fmt_rp(omzet),
            fmt_rp(restock),
            fmt_rp(biaya),
            fmt_rp(total_out),
            fmt_rp(margin),
            int(sold_gas),
            int(sold_sl),
            f"Gas +{int(beli_gas)}-{int(sold_gas)} | SL +{int(beli_sl)}-{int(sold_sl)}",
        ])

    # Write all data
    start_summary = len(stok_rows) + 3
    ws.update("A1", stok_rows, value_input_option="USER_ENTERED")
    ws.update(f"A{len(stok_rows)+2}", [S_HEADERS])
    if monthly_rows:
        ws.update(f"A{start_summary}", monthly_rows, value_input_option="USER_ENTERED")

    # Formatting requests
    reqs = [
        {"repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 500,
                      "startColumnIndex": 0, "endColumnIndex": 9},
            "cell": {"userEnteredFormat": {}}, "fields": "userEnteredFormat",
        }},
        # Stok header
        _merge(sid, 0, 1, 0, 9),
        _rc(sid, 0, 1, 0, 9, _cell_fmt(bg=C_STOK_HEADER, bold=True, fg=C_WHITE,
                                        font_size=13, h_align="CENTER", v_align="MIDDLE")),
        # Stok column headers
        _rc(sid, 1, 2, 0, 4, _cell_fmt(bg=C_COL_HEADER_BG, bold=True, fg=C_WHITE,
                                        h_align="CENTER", v_align="MIDDLE", borders=_border())),
        # Gas row
        _rc(sid, 2, 3, 0, 4, _cell_fmt(bg=C_STOK_GAS, h_align="CENTER", borders=_border())),
        # Sunlight row
        _rc(sid, 3, 4, 0, 4, _cell_fmt(bg=C_STOK_SL, h_align="CENTER", borders=_border())),
        # Column widths
        _col_w(sid, 0, 1, 180),
        _col_w(sid, 1, 2, 140),
        _col_w(sid, 2, 3, 140),
        _col_w(sid, 3, 4, 120),
        _col_w(sid, 4, 5, 120),
        _col_w(sid, 5, 6, 120),
        _col_w(sid, 6, 7, 100),
        _col_w(sid, 7, 8, 130),
        _col_w(sid, 8, 9, 200),
        _row_h(sid, 0, 1, 42),
    ]

    # Monthly summary header row
    hdr_row0i = len(stok_rows) + 1
    reqs += [
        _merge(sid, hdr_row0i - 1, hdr_row0i, 0, 9),
        _rc(sid, hdr_row0i - 1, hdr_row0i, 0, 9,
            _cell_fmt(bg=C_TITLE_BG, bold=True, fg=C_WHITE, font_size=12, h_align="CENTER")),
        _rc(sid, hdr_row0i, hdr_row0i + 1, 0, 9,
            _cell_fmt(bg=C_COL_HEADER_BG, bold=True, fg=C_WHITE, h_align="CENTER", borders=_border())),
    ]
    for i, mr in enumerate(monthly_rows):
        r0i = hdr_row0i + 1 + i
        margin_val = mr[5].replace("Rp ", "").replace(".", "").replace(",", "")
        try:
            is_pos = int(margin_val) >= 0
        except ValueError:
            is_pos = True
        bg = C_NET_POS if is_pos else C_NET_NEG
        reqs.append(_rc(sid, r0i, r0i+1, 0, 9,
                        _cell_fmt(bg=bg, h_align="CENTER", borders=_border())))

    ss.batch_update({"requests": reqs})
    logger.info("SUMMARY & STOK sheet updated")
    return True


# ─── Quick append ─────────────────────────────────────────────────────────────

def append_transaction_row(trans_id, date_str, day_name, type_, product,
                           category, customer, qty, unit_price, total_price,
                           description, year, month, spreadsheet_id):
    try:
        ss = _get_ss(spreadsheet_id)
        mn  = MONTH_NAMES_ID[month]
        ws  = _get_or_create_ws(ss, f"{mn} {year}")
        d   = datetime.strptime(date_str, "%Y-%m-%d").date()
        q   = int(qty) if float(qty).is_integer() else float(qty)
        lbl = customer if customer and customer != "-" else description or "-"
        row = [
            trans_id, day_name, f"{d.day} {MONTH_NAMES_ID[d.month]}",
            "JUAL" if type_ == "IN" else "BELI",
            product or "-", lbl, q,
            fmt_rp(unit_price), fmt_rp(total_price), "",
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.warning(f"append_transaction_row failed: {e}")
