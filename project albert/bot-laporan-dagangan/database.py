import sqlite3
import os
import pytz
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "dagangan.db")
_TZ = pytz.timezone("Asia/Jakarta")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id     TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                product     TEXT,
                category    TEXT    NOT NULL,
                customer    TEXT,
                quantity    REAL    NOT NULL,
                unit_price  REAL    NOT NULL,
                total_price REAL    NOT NULL,
                description TEXT    DEFAULT '-',
                date        TEXT    NOT NULL,
                day_name    TEXT    NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_txn_chat_date ON transactions(chat_id, date);

            CREATE TABLE IF NOT EXISTS group_config (
                chat_id        TEXT PRIMARY KEY,
                spreadsheet_id TEXT,
                group_name     TEXT,
                registered_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def add_transaction(chat_id, type_, product, category, customer, qty,
                    unit_price, description, date_str, day_name):
    total = round(qty * unit_price, 2)
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO transactions
               (chat_id, type, product, category, customer, quantity,
                unit_price, total_price, description, date, day_name)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (chat_id, type_, product, category, customer, qty,
             unit_price, total, description or "-", date_str, day_name)
        )
        return cur.lastrowid


def delete_transaction(trans_id, chat_id):
    with _conn() as c:
        return c.execute(
            "DELETE FROM transactions WHERE id=? AND chat_id=?", (trans_id, chat_id)
        ).rowcount > 0


def update_transaction(trans_id, chat_id, **updates):
    if not updates:
        return False
    cols = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [trans_id, chat_id]
    with _conn() as c:
        return c.execute(
            f"UPDATE transactions SET {cols} WHERE id=? AND chat_id=?", vals
        ).rowcount > 0


def get_transaction_by_id(trans_id, chat_id):
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM transactions WHERE id=? AND chat_id=?", (trans_id, chat_id)
        ).fetchone()
        return dict(row) if row else None


def get_date_transactions(date_str, chat_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE date=? AND chat_id=? ORDER BY id",
            (date_str, chat_id)
        ).fetchall()
        return [dict(r) for r in rows]


def get_today_transactions(chat_id):
    today = datetime.now(_TZ).strftime("%Y-%m-%d")
    return get_date_transactions(today, chat_id)


def get_week_transactions(chat_id):
    from datetime import timedelta
    now = datetime.now(_TZ)
    monday = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    today  = now.strftime("%Y-%m-%d")
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE chat_id=? AND date BETWEEN ? AND ? ORDER BY date, id",
            (chat_id, monday, today)
        ).fetchall()
        return [dict(r) for r in rows]


def get_month_transactions(year, month, chat_id):
    prefix = f"{year}-{month:02d}"
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE chat_id=? AND date LIKE ? ORDER BY date, id",
            (chat_id, f"{prefix}-%")
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_transactions(chat_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM transactions WHERE chat_id=? ORDER BY date, id",
            (chat_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_stock_summary(chat_id):
    """Returns {product_name: {'restock': qty, 'sold': qty, 'stok': qty}}"""
    with _conn() as c:
        rows = c.execute(
            """SELECT product, type, SUM(quantity) as total_qty
               FROM transactions
               WHERE chat_id=? AND product IS NOT NULL
               GROUP BY product, type""",
            (chat_id,)
        ).fetchall()

    result = {}
    for row in rows:
        p = row["product"]
        if p not in result:
            result[p] = {"restock": 0.0, "sold": 0.0}
        if row["type"] == "OUT":
            result[p]["restock"] += row["total_qty"]
        else:
            result[p]["sold"] += row["total_qty"]

    for p in result:
        result[p]["stok"] = result[p]["restock"] - result[p]["sold"]

    return result


def get_cash_summary(chat_id):
    """Returns (total_in, total_out, balance) all-time."""
    with _conn() as c:
        row = c.execute(
            """SELECT
               COALESCE(SUM(CASE WHEN type='IN' THEN total_price ELSE 0 END), 0) as tin,
               COALESCE(SUM(CASE WHEN type='OUT' THEN total_price ELSE 0 END), 0) as tout
               FROM transactions WHERE chat_id=?""",
            (chat_id,)
        ).fetchone()
    tin  = row["tin"]
    tout = row["tout"]
    return tin, tout, tin - tout


def get_date_cash_summary(date_str, chat_id):
    """Returns (total_in, total_out, balance) for a specific date."""
    with _conn() as c:
        row = c.execute(
            """SELECT
               COALESCE(SUM(CASE WHEN type='IN' THEN total_price ELSE 0 END), 0) as tin,
               COALESCE(SUM(CASE WHEN type='OUT' THEN total_price ELSE 0 END), 0) as tout
               FROM transactions WHERE chat_id=? AND date=?""",
            (chat_id, date_str)
        ).fetchone()
    tin  = row["tin"]
    tout = row["tout"]
    return tin, tout, tin - tout


def register_group(chat_id, spreadsheet_id, group_name=""):
    with _conn() as c:
        c.execute(
            """INSERT INTO group_config (chat_id, spreadsheet_id, group_name)
               VALUES (?,?,?)
               ON CONFLICT(chat_id) DO UPDATE SET
               spreadsheet_id=excluded.spreadsheet_id,
               group_name=excluded.group_name""",
            (chat_id, spreadsheet_id, group_name)
        )


def get_group_config(chat_id):
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM group_config WHERE chat_id=?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_groups():
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM group_config WHERE spreadsheet_id IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]
