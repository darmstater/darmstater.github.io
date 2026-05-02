import sqlite3
from datetime import datetime, timedelta
import pytz

from config import TIMEZONE, DAY_NAMES_ID

TZ = pytz.timezone(TIMEZONE)
DB_PATH = "laporan.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            day_name    TEXT NOT NULL,
            type        TEXT NOT NULL,
            category    TEXT NOT NULL,
            quantity    REAL NOT NULL DEFAULT 1,
            unit_price  REAL NOT NULL,
            total_price REAL NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_transaction(type_, category, quantity, unit_price, description):
    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")
    day_name = DAY_NAMES_ID.get(now.strftime("%A"), now.strftime("%A").upper())
    total_price = quantity * unit_price
    created_at = now.isoformat()

    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions
            (date, day_name, type, category, quantity, unit_price, total_price, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, day_name, type_, category, quantity, unit_price, total_price, description, created_at))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def delete_transaction(trans_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def get_transaction_by_id(trans_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE id = ?", (trans_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_today_transactions():
    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE date = ? ORDER BY created_at", (date_str,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_week_transactions():
    now = datetime.now(TZ)
    monday = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM transactions WHERE date >= ? AND date <= ? ORDER BY date, created_at",
        (monday, today)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_month_transactions(year, month):
    prefix = f"{year}-{month:02d}"
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date, created_at",
        (f"{prefix}%",)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_transactions():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY date, created_at")
    rows = c.fetchall()
    conn.close()
    return rows
