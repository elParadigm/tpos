import sqlite3

DB_PATH = "pos.db"


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
    conn.close()
