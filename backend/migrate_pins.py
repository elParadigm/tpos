"""One-time migration: hash any plaintext worker PINs in pos.db.

The schema previously stored PINs in plaintext; login now verifies scrypt
hashes. Existing rows are re-hashed in place. Idempotent — rows already in
the 'scrypt$...' format are left untouched.

Run:  venv/bin/python migrate_pins.py
"""

import sqlite3

from auth import hash_pin

DB = 'pos.db'


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, pin FROM workers").fetchall()
    migrated = 0
    for row in rows:
        pin = row['pin']
        if pin and not pin.startswith('scrypt$'):
            conn.execute("UPDATE workers SET pin = ? WHERE id = ?",
                         [hash_pin(pin), row['id']])
            migrated += 1
    conn.commit()
    conn.close()
    print(f"OK: {migrated} worker PIN(s) hashed. {len(rows) - migrated} already hashed.")


if __name__ == '__main__':
    main()
