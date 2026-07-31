import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = "pos.db"

# App timezone offset (hours). Tunisia is UTC+1. This keeps daily/monthly
# report boundaries aligned with the store's local calendar even though
# timestamps are stored in UTC (SQLite CURRENT_TIMESTAMP).
LOCAL_TZ = timedelta(hours=int(__import__('os').environ.get('TPOS_TZ', '1')))


def local_now():
    return datetime.now(timezone.utc) + LOCAL_TZ


def utc_offset_sql():
    """SQLite string literal like '+01:00' to shift stored UTC times."""
    total_minutes = int(LOCAL_TZ.total_seconds() // 60)
    sign = '+' if total_minutes >= 0 else '-'
    h, m = divmod(abs(total_minutes), 60)
    return f"'{sign}{h:02d}:{m:02d}'"


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with open("sql/schema/000_schema.sql") as f:
        schema = f.read()
    conn = get_db()
    conn.executescript(schema)  # executescript handles multiple statements

    # Migration: link immediate customer payments to their sale so that
    # deleting a sale also removes its payment. SQLite can't add a column
    # IF NOT EXISTS, so check PRAGMA first.
    cols = [r[1] for r in conn.execute("PRAGMA table_info(customer_payments)").fetchall()]
    if "sale_id" not in cols:
        conn.execute("ALTER TABLE customer_payments ADD COLUMN sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE")

    conn.commit()
    conn.close()
