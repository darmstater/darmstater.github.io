import json
import logging
from datetime import datetime, timedelta, date as date_type
from collections import defaultdict, OrderedDict

import gspread
import pytz

from config import SPREADSHEET_ID, GOOGLE_CREDENTIALS_JSON, TIMEZONE, MONTH_NAMES_ID, DAY_NAMES_ID
from database import get_month_transactions, get_all_transactions

logger = logging.getLogger(__name__)
TZ = pytz.timezone(TIMEZONE)

# ─── Colors ───────────────────────────────────────────────────────────────────
C_TITLE_BG       = {"red": 0.102, "green": 0.137, "blue": 0.494}   # dark navy
C_WHITE          = {"red": 1.0,   "green": 1.0,   "blue": 1.0}
C_COL_HEADER_BG  = {"red": 0.176, "green": 0.490, "blue": 0.259}   # dark green
C_IN_ROW         = {"red": 0.878, "green": 0.961, "blue": 0.894}   # light green
C_OUT_ROW        = {"red": 1.0,   "green": 0.922, "blue": 0.925}   # light pink
C_TOTAL_NET_POS  = {"red": 0.831, "green": 0.953, "blue": 0.831}   # green-ish
C_TOTAL_NET_NEG  = {"red": 1.0,   "green": 0.831, "blue": 0.831}   # red-ish
C_WEEK_BG        = {"red": 0.824, "green": 0.898, "blue": 0.980}   # light blue
C_WEEK_CAT_BG    = {"red": 0.906, "green": 0.937, "blue": 0.992}   # lighter blue
C_SUMMARY_TOTAL  = {"red": 1.0,   "green": 0.867, "blue": 0.557}   # light orange
C_GRAY_TEXT      = {"red": 0.4,   "green": 0.4,   "blue": 0.4}

HEADERS = ["NO", "HARI", "TANGGAL", "KATEGORI", "JUMLAH", "HARGA SATUAN", "HARGA TOTAL", "KETERANGAN", "TOTAL HARIAN"]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def fmt_rp(amount: float) -> str:
    return f"Rp {int(amount):,}".replace(",", ".")


def _border(width=1, color=None):
    color = color or {"red": 0.75, "green": 0.75, "blue": 0.75}
    b = {"style": "SOLID", "width": width, "color": color}
    return {"top": b, "bottom": b, "left": b, "right": b}


def _thick_border():
    return _border(2, {"red": 0.3, "green": 0.3, "blue": 0.3})


def _cell_fmt(bg=None, bold=False, italic=False, font_size=10,
              fg=None, h_align="LEFT", v_align="MIDDLE",
              wrap=False, borders=None):
    fmt = {
        "textFormat": {
            "bold": bold,
            "italic": italic,
            "fontSize": font_size,
        },
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


def _repeat_cell(sheet_id, start_row, end_row, start_col, end_col, cell_fmt, fields=None):
    if fields is None:
        fields = "userEnteredFormat"
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row,
                "endRowIndex": end_row,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            },
            "cell": {"userEnteredFormat": cell_fmt},
            "fields": fields,
        }
    }


def _merge(sheet_id, r0, r1, c0, c1):
    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r0,
                "endRowIndex": r1,
                "startColumnIndex": c0,
                "endColumnIndex": c1,
            },
            "mergeType": "MERGE_ALL",
        }
    }


def _col_width(sheet_id, c0, c1, px):
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": c0, "endIndex": c1},
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    }


def _row_height(sheet_id, r0, r1, px):
    return {
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": r0, "endIndex": r1},
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    }


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _get_spreadsheet(spreadsheet_id=None):
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("GOOGLE_CREDENTIALS_JSON is not set")
    sid = spreadsheet_id or SPREADSHEET_ID
    if not sid:
        raise ValueError("No spreadsheet_id provided")
    creds = json.loads(GOOGLE_CREDENTIALS_JSON)
    gc = gspread.service_account_from_dict(creds)
    return gc.open_by_key(sid)


def _get_or_create_ws(spreadsheet, name, rows=600, cols=10):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)


def verify_spreadsheet_access(spreadsheet_id: str) -> bool:
    try:
        _get_spreadsheet(spreadsheet_id)
        return True
    except Exception:
        return False


# ─── Week utils ───────────────────────────────────────────────────────────────

def _week_bounds(d: date_type):
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ─── Data row formatting helpers ──────────────────────────────────────────────

_FULL_FIELDS = "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)"

# Column groups with their alignment: (start_col, end_col, h_align)
_DATA_COL_ALIGNS = [
    (0, 3, "CENTER"),   # NO, HARI, TANGGAL
    (3, 4, "LEFT"),     # KATEGORI
    (4, 5, "CENTER"),   # JUMLAH
    (5, 7, "RIGHT"),    # HARGA SATUAN, HARGA TOTAL
    (7, 8, "LEFT"),     # KETERANGAN
]


def _data_row_reqs(sid, row_0i, bg):
    """Returns format requests for one transaction data row (0-indexed row_0i)."""
    reqs = []
    for c0, c1, align in _DATA_COL_ALIGNS:
        reqs.append(_repeat_cell(
            sid, row_0i, row_0i + 1, c0, c1,
            _cell_fmt(bg=bg, bold=False, italic=False, font_size=10,
                      h_align=align, v_align="MIDDLE", borders=_border()),
            fields=_FULL_FIELDS
        ))
    return reqs


# ─── Main rebuild ─────────────────────────────────────────────────────────────

def rebuild_month_sheet(year=None, month=None, user_id=None, spreadsheet_id=None) -> bool:
    now = datetime.now(TZ)
    year  = year  or now.year
    month = month or now.month
    today = now.date()

    try:
        ss = _get_spreadsheet(spreadsheet_id)
    except Exception as e:
        logger.error(f"Sheets auth failed: {e}")
        return False

    month_name  = MONTH_NAMES_ID[month]
    sheet_title = f"{month_name} {year}"
    ws = _get_or_create_ws(ss, sheet_title)
    sid = ws.id

    # Clear values and unmerge
    ws.clear()
    try:
        ss.batch_update({"requests": [{
            "unmergeCells": {"range": {
                "sheetId": sid,
                "startRowIndex": 0, "endRowIndex": 1000,
                "startColumnIndex": 0, "endColumnIndex": 10,
            }}
        }]})
    except Exception:
        pass

    # Load & group transactions
    transactions = get_month_transactions(year, month, user_id=user_id)
    by_date: OrderedDict = OrderedDict()
    for t in sorted(transactions, key=lambda x: (x["date"], x["created_at"])):
        by_date.setdefault(t["date"], []).append(t)

    DATA_START = 3   # 1-indexed (row 1 = title, row 2 = headers)
    all_rows   = []
    reqs       = []

    # Reset all existing cell formatting before applying new styles
    reqs.append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 0, "endRowIndex": 1000,
                "startColumnIndex": 0, "endColumnIndex": 10,
            },
            "cell": {"userEnteredFormat": {}},
            "fields": "userEnteredFormat",
        }
    })

    trans_no   = 1
    cur_row    = DATA_START   # 1-indexed

    # Group dates by ISO-week
    week_groups: OrderedDict = OrderedDict()
    for date_str in by_date:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        mon, sun = _week_bounds(d)
        key = mon.isoformat()
        if key not in week_groups:
            week_groups[key] = {"monday": mon, "sunday": sun, "dates": []}
        week_groups[key]["dates"].append(date_str)

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

            total_harian = (
                f"MASUK  : +{fmt_rp(day_in)}\n"
                f"KELUAR : -{fmt_rp(day_out)}\n"
                f"NET      : {sign}{fmt_rp(day_net)}"
            )

            day_start_row = cur_row  # 1-indexed

            for i, t in enumerate(day_trans):
                qty = int(t["quantity"]) if float(t["quantity"]).is_integer() else float(t["quantity"])
                row = [
                    trans_no,
                    day_lbl,
                    date_lbl,
                    t["category"],
                    qty,
                    fmt_rp(t["unit_price"]),
                    fmt_rp(t["total_price"]),
                    t["description"] or "-",
                    total_harian if i == 0 else "",
                ]
                all_rows.append(row)

                bg = C_IN_ROW if t["type"] == "IN" else C_OUT_ROW
                reqs.extend(_data_row_reqs(sid, cur_row - 1, bg))

                trans_no += 1
                cur_row  += 1
                week_trans.append(t)

            day_end_row = cur_row  # exclusive

            # Merge & format TOTAL HARIAN for this day
            r0 = day_start_row - 1
            r1 = day_end_row - 1
            if r1 - r0 >= 1:
                reqs.append(_merge(sid, r0, r1, 8, 9))
            net_bg = C_TOTAL_NET_POS if day_net >= 0 else C_TOTAL_NET_NEG
            reqs.append(_repeat_cell(sid, r0, r1, 8, 9,
                _cell_fmt(bg=net_bg, bold=True, font_size=9,
                          h_align="CENTER", v_align="MIDDLE",
                          wrap=True, borders=_thick_border()),
                fields=_FULL_FIELDS
            ))

        # ── Weekly summary ────────────────────────────────────────────────────
        is_last_week = week_key == list(week_groups.keys())[-1]
        if sunday <= today or is_last_week:
            week_in  = sum(t["total_price"] for t in week_trans if t["type"] == "IN")
            week_out = sum(t["total_price"] for t in week_trans if t["type"] == "OUT")
            week_net = week_in - week_out
            sign     = "+" if week_net >= 0 else ""

            day_spend: dict = defaultdict(float)
            for t in week_trans:
                if t["type"] == "OUT":
                    day_spend[t["date"]] += t["total_price"]

            if day_spend:
                terboros_date = max(day_spend, key=day_spend.get)
                terboros_d    = datetime.strptime(terboros_date, "%Y-%m-%d").date()
                terboros_day  = DAY_NAMES_ID.get(terboros_d.strftime("%A"), "")
                terboros_str  = f"{terboros_day} ({fmt_rp(day_spend[terboros_date])})"
            else:
                terboros_str = "-"

            cat_spend: dict = defaultdict(float)
            for t in week_trans:
                if t["type"] == "OUT":
                    cat_spend[t["category"]] += t["total_price"]
            cat_parts = [
                f"{cat}: {fmt_rp(amt)}"
                for cat, amt in sorted(cat_spend.items(), key=lambda x: -x[1])
            ]
            cat_text = "  |  ".join(cat_parts) if cat_parts else "-"

            mon_day = monday.day if monday.month == month else 1
            import calendar as _cal
            sun_day = sunday.day if sunday.month == month else _cal.monthrange(year, month)[1]
            week_label = (
                f"TOTAL MINGGU {week_num}"
                f"   ({mon_day} – {sun_day} {MONTH_NAMES_ID[month]})"
            )
            total_harian_week = (
                f"MASUK  : +{fmt_rp(week_in)}\n"
                f"KELUAR : -{fmt_rp(week_out)}\n"
                f"NET      : {sign}{fmt_rp(abs(week_net))}"
            )

            summary_row = [
                week_label, "", "", "", "", "", "",
                f"Terboros: {terboros_str}",
                total_harian_week
            ]
            cat_row = ["", "", "", "Breakdown:", "", "", cat_text, "", ""]

            all_rows.append(summary_row)
            all_rows.append(cat_row)

            sr0 = cur_row - 1
            cr0 = cur_row

            reqs.append(_merge(sid, sr0, sr0 + 1, 0, 7))
            reqs.append(_merge(sid, cr0, cr0 + 1, 6, 9))

            reqs.append(_repeat_cell(sid, sr0, sr0 + 1, 0, 9,
                _cell_fmt(bg=C_WEEK_BG, bold=True, h_align="CENTER",
                          v_align="MIDDLE", borders=_thick_border()),
                fields=_FULL_FIELDS
            ))
            net_bg = C_TOTAL_NET_POS if week_net >= 0 else C_TOTAL_NET_NEG
            reqs.append(_repeat_cell(sid, sr0, sr0 + 1, 8, 9,
                _cell_fmt(bg=net_bg, bold=True, font_size=9,
                          h_align="CENTER", v_align="MIDDLE", wrap=True,
                          borders=_thick_border()),
                fields=_FULL_FIELDS
            ))
            reqs.append(_repeat_cell(sid, cr0, cr0 + 1, 0, 9,
                _cell_fmt(bg=C_WEEK_CAT_BG, italic=True, font_size=9,
                          h_align="LEFT", v_align="MIDDLE"),
                fields=_FULL_FIELDS
            ))

            cur_row  += 2
            week_num += 1

    # ── Write data ──────────────────────────────────────────────────────────
    title_text = f"LAPORAN KEUANGAN  ·  {month_name.upper()} {year}"
    ws.update("A1", [[title_text]])
    ws.update("A2", [HEADERS])
    if all_rows:
        ws.update(f"A{DATA_START}", all_rows, value_input_option="USER_ENTERED")

    # ── Static formatting + column widths ────────────────────────────────────
    static_reqs = [
        _merge(sid, 0, 1, 0, 9),
        _repeat_cell(sid, 0, 1, 0, 9,
            _cell_fmt(bg=C_TITLE_BG, bold=True, font_size=14,
                      fg=C_WHITE, h_align="CENTER", v_align="MIDDLE"),
            fields=_FULL_FIELDS
        ),
        _repeat_cell(sid, 1, 2, 0, 9,
            _cell_fmt(bg=C_COL_HEADER_BG, bold=True, fg=C_WHITE,
                      h_align="CENTER", v_align="MIDDLE", borders=_border()),
            fields=_FULL_FIELDS
        ),
        _col_width(sid, 0, 1, 50),   # NO
        _col_width(sid, 1, 2, 85),   # HARI
        _col_width(sid, 2, 3, 105),  # TANGGAL
        _col_width(sid, 3, 4, 145),  # KATEGORI
        _col_width(sid, 4, 5, 75),   # JUMLAH
        _col_width(sid, 5, 6, 130),  # HARGA SATUAN
        _col_width(sid, 6, 7, 130),  # HARGA TOTAL
        _col_width(sid, 7, 8, 210),  # KETERANGAN
        _col_width(sid, 8, 9, 165),  # TOTAL HARIAN
        _row_height(sid, 0, 1, 45),
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sid,
                    "gridProperties": {"frozenRowCount": 2}
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]

    ss.batch_update({"requests": static_reqs + reqs})
    logger.info(f"Sheet '{sheet_title}' rebuilt — {len(transactions)} transactions")
    return True


# ─── SUMMARY sheet ────────────────────────────────────────────────────────────

def update_summary_sheet(user_id=None, spreadsheet_id=None) -> bool:
    try:
        ss = _get_spreadsheet(spreadsheet_id)
    except Exception as e:
        logger.error(f"Sheets auth failed: {e}")
        return False

    ws = _get_or_create_ws(ss, "SUMMARY", rows=500, cols=7)
    sid = ws.id
    ws.clear()
    try:
        ss.batch_update({"requests": [{
            "unmergeCells": {"range": {
                "sheetId": sid,
                "startRowIndex": 0, "endRowIndex": 500,
                "startColumnIndex": 0, "endColumnIndex": 7,
            }}
        }]})
    except Exception:
        pass

    all_transactions = get_all_transactions(user_id=user_id)

    # Group by year-month
    by_ym: dict = defaultdict(list)
    for t in all_transactions:
        d = datetime.strptime(t["date"], "%Y-%m-%d").date()
        by_ym[(d.year, d.month)].append(t)

    S_HEADERS = ["PERIODE", "TOTAL MASUK", "TOTAL KELUAR", "NET", "HARI TERBOROS", "KATEGORI TERBESAR", "PENGELUARAN TERBESAR"]
    all_rows: list = []
    reqs:     list = []
    cur_row   = 3  # 1-indexed (row 1 title, row 2 headers)

    # Reset formatting
    reqs.append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 0, "endRowIndex": 500,
                "startColumnIndex": 0, "endColumnIndex": 7,
            },
            "cell": {"userEnteredFormat": {}},
            "fields": "userEnteredFormat",
        }
    })

    # Column alignment for summary data rows: (c0, c1, align)
    _SUM_COL_ALIGNS = [
        (0, 1, "LEFT"),    # PERIODE
        (1, 4, "RIGHT"),   # MASUK, KELUAR, NET
        (4, 7, "LEFT"),    # HARI TERBOROS, KATEGORI, PENGELUARAN
    ]
    _SUM_FIELDS = "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)"

    for (year, month) in sorted(by_ym.keys()):
        month_trans = sorted(by_ym[(year, month)], key=lambda x: x["date"])
        month_name  = MONTH_NAMES_ID[month]

        # Month section header
        all_rows.append([f"── {month_name.upper()} {year} ──", "", "", "", "", "", ""])
        sec_row = cur_row - 1
        reqs.append(_merge(sid, sec_row, sec_row + 1, 0, 7))
        reqs.append(_repeat_cell(sid, sec_row, sec_row + 1, 0, 7,
            _cell_fmt(bg=C_TITLE_BG, bold=True, fg=C_WHITE, h_align="CENTER"),
            fields=_SUM_FIELDS
        ))
        cur_row += 1

        # Group by week
        week_groups: OrderedDict = OrderedDict()
        for t in month_trans:
            d   = datetime.strptime(t["date"], "%Y-%m-%d").date()
            mon, sun = _week_bounds(d)
            key = mon.isoformat()
            if key not in week_groups:
                week_groups[key] = {"monday": mon, "sunday": sun, "trans": []}
            week_groups[key]["trans"].append(t)

        month_in = month_out = 0.0
        week_num = 1

        for wk, wi in week_groups.items():
            monday: date_type = wi["monday"]
            sunday: date_type = wi["sunday"]
            wt = wi["trans"]

            w_in  = sum(t["total_price"] for t in wt if t["type"] == "IN")
            w_out = sum(t["total_price"] for t in wt if t["type"] == "OUT")
            w_net = w_in - w_out
            sign  = "+" if w_net >= 0 else ""

            day_spend: dict = defaultdict(float)
            for t in wt:
                if t["type"] == "OUT":
                    day_spend[t["date"]] += t["total_price"]

            if day_spend:
                tb_date  = max(day_spend, key=day_spend.get)
                tb_d     = datetime.strptime(tb_date, "%Y-%m-%d").date()
                terboros = f"{DAY_NAMES_ID.get(tb_d.strftime('%A'), '')} ({fmt_rp(day_spend[tb_date])})"
            else:
                terboros = "-"

            cat_spend: dict = defaultdict(float)
            for t in wt:
                if t["type"] == "OUT":
                    cat_spend[t["category"]] += t["total_price"]
            if cat_spend:
                top_cat     = max(cat_spend, key=cat_spend.get)
                top_cat_str = f"{top_cat} ({fmt_rp(cat_spend[top_cat])})"
            else:
                top_cat_str = "-"

            out_items = [t for t in wt if t["type"] == "OUT"]
            if out_items:
                biggest     = max(out_items, key=lambda x: x["total_price"])
                biggest_str = f"{biggest['description']} — {fmt_rp(biggest['total_price'])}"
            else:
                biggest_str = "-"

            import calendar as _cal
            mon_day  = monday.day if monday.month == month else 1
            sun_day  = sunday.day if sunday.month == month else _cal.monthrange(year, month)[1]
            periode  = f"Minggu {week_num}  ({mon_day}–{sun_day} {month_name})"

            all_rows.append([
                periode,
                fmt_rp(w_in),
                fmt_rp(w_out),
                f"{sign}{fmt_rp(abs(w_net))}",
                terboros,
                top_cat_str,
                biggest_str,
            ])

            row0 = cur_row - 1
            bg   = C_IN_ROW if w_net >= 0 else C_OUT_ROW
            for c0, c1, align in _SUM_COL_ALIGNS:
                reqs.append(_repeat_cell(sid, row0, row0 + 1, c0, c1,
                    _cell_fmt(bg=bg, h_align=align, v_align="MIDDLE", borders=_border()),
                    fields=_SUM_FIELDS
                ))

            month_in  += w_in
            month_out += w_out
            cur_row   += 1
            week_num  += 1

        # Monthly total row
        m_net  = month_in - month_out
        m_sign = "+" if m_net >= 0 else ""
        all_rows.append([
            f"TOTAL {month_name.upper()} {year}",
            fmt_rp(month_in),
            fmt_rp(month_out),
            f"{m_sign}{fmt_rp(abs(m_net))}",
            "", "", "",
        ])
        tot_row = cur_row - 1
        for c0, c1, align in _SUM_COL_ALIGNS:
            reqs.append(_repeat_cell(sid, tot_row, tot_row + 1, c0, c1,
                _cell_fmt(bg=C_SUMMARY_TOTAL, bold=True, h_align=align,
                          v_align="MIDDLE", borders=_thick_border()),
                fields=_SUM_FIELDS
            ))
        cur_row += 2
        all_rows.append(["", "", "", "", "", "", ""])

    # Write
    ws.update("A1", [["SUMMARY KEUANGAN"]])
    ws.update("A2", [S_HEADERS])
    if all_rows:
        ws.update("A3", all_rows, value_input_option="USER_ENTERED")

    static = [
        _merge(sid, 0, 1, 0, 7),
        _repeat_cell(sid, 0, 1, 0, 7,
            _cell_fmt(bg=C_TITLE_BG, bold=True, fg=C_WHITE, font_size=14, h_align="CENTER"),
            fields=_SUM_FIELDS
        ),
        _repeat_cell(sid, 1, 2, 0, 7,
            _cell_fmt(bg=C_COL_HEADER_BG, bold=True, fg=C_WHITE, h_align="CENTER"),
            fields=_SUM_FIELDS
        ),
        _col_width(sid, 0, 1, 200),
        _col_width(sid, 1, 2, 140),
        _col_width(sid, 2, 3, 140),
        _col_width(sid, 3, 4, 140),
        _col_width(sid, 4, 5, 180),
        _col_width(sid, 5, 6, 180),
        _col_width(sid, 6, 7, 240),
        _row_height(sid, 0, 1, 45),
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 2}},
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    ss.batch_update({"requests": static + reqs})
    logger.info("SUMMARY sheet updated")
    return True


# ─── Quick append (called immediately on each transaction) ────────────────────

def append_transaction_row(trans_id, date_str, day_name, type_, category,
                           quantity, unit_price, total_price, description,
                           year, month, spreadsheet_id=None):
    """Append a single raw row to the monthly sheet (no fancy formatting)."""
    try:
        ss = _get_spreadsheet(spreadsheet_id)
        month_name  = MONTH_NAMES_ID[month]
        sheet_title = f"{month_name} {year}"
        ws = _get_or_create_ws(ss, sheet_title)
        d    = datetime.strptime(date_str, "%Y-%m-%d").date()
        qty  = int(quantity) if float(quantity).is_integer() else float(quantity)
        row  = [
            trans_id, day_name,
            f"{d.day} {MONTH_NAMES_ID[d.month]}",
            category, qty,
            fmt_rp(unit_price), fmt_rp(total_price),
            description or "-", ""
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.warning(f"append_transaction_row failed (non-critical): {e}")
