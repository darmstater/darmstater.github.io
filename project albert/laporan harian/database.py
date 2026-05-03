import sqlite3
from datetime import datetime, timedelta
import pytz

from config import TIMEZONE, DAY_NAMES_ID, TELEGRAM_CHAT_ID, SPREADSHEET_ID

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
        CREATE TABLE IF NOT EXISTS users (
            telegram_user_id TEXT PRIMARY KEY,
            spreadsheet_id   TEXT NOT NULL,
            name             TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL DEFAULT '',
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
    # Migration: add user_id column for existing installs
    try:
        c.execute("ALTER TABLE transactions ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass
    conn.commit()
    conn.close()

    # Auto-register owner from env vars
    if TELEGRAM_CHAT_ID and SPREADSHEET_ID:
        register_user(str(TELEGRAM_CHAT_ID), SPREADSHEET_ID, "Owner")
        # Migrate existing transactions that have no user_id
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE transactions SET user_id = ? WHERE user_id = ''",
                  (str(TELEGRAM_CHAT_ID),))
        conn.commit()
        conn.close()


def register_user(user_id: str, spreadsheet_id: str, name: str = None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (telegram_user_id, spreadsheet_id, name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET spreadsheet_id = excluded.spreadsheet_id
    """, (str(user_id), spreadsheet_id, name))
    conn.commit()
    conn.close()


def get_user(user_id: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_user_id = ?", (str(user_id),))
    row = c.fetchone()
    conn.close()
    return row


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return rows


def add_transaction(user_id: str, type_, category, quantity, unit_price, description,
                    date_str=None, day_name=None):
    now = datetime.now(TZ)
    if date_str is None:
        date_str = now.strftime("%Y-%m-%d")
    if day_name is None:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = DAY_NAMES_ID.get(d.strftime("%A"), d.strftime("%A").upper())
    total_price = quantity * unit_price
    created_at = now.isoformat()

    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions
            (user_id, date, day_name, type, category, quantity, unit_price,
             total_price, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(user_id), date_str, day_name, type_, category,
          quantity, unit_price, total_price, description, created_at))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def delete_transaction(trans_id, user_id: str = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?",
                  (trans_id, str(user_id)))
    else:
        c.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def get_transaction_by_id(trans_id, user_id: str = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?",
                  (trans_id, str(user_id)))
    else:
        c.execute("SELECT * FROM transactions WHERE id = ?", (trans_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_today_transactions(user_id: str = None):
    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")
    return get_date_transactions(date_str, user_id=user_id)


def get_date_transactions(date_str: str, user_id: str = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date = ? ORDER BY created_at",
            (str(user_id), date_str)
        )
    else:
        c.execute("SELECT * FROM transactions WHERE date = ? ORDER BY created_at", (date_str,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_week_transactions(user_id: str = None):
    now = datetime.now(TZ)
    monday = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date >= ? AND date <= ? "
            "ORDER BY date, created_at",
            (str(user_id), monday, today)
        )
    else:
        c.execute(
            "SELECT * FROM transactions WHERE date >= ? AND date <= ? "
            "ORDER BY date, created_at",
            (monday, today)
        )
    rows = c.fetchall()
    conn.close()
    return rows


def get_month_transactions(year, month, user_id: str = None):
    prefix = f"{year}-{month:02d}"
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date LIKE ? "
            "ORDER BY date, created_at",
            (str(user_id), f"{prefix}%")
        )
    else:
        c.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date, created_at",
            (f"{prefix}%",)
        )
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_transactions(user_id: str = None):
    conn = get_conn()
    c = conn.cursor()
    if user_id:
        c.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY date, created_at",
            (str(user_id),)
        )
    else:
        c.execute("SELECT * FROM transactions ORDER BY date, created_at")
    rows = c.fetchall()
    conn.close()
    return rows
