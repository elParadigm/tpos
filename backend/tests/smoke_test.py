"""Quick smoke test for the TPOS backend.

Runs the core business flows against a throwaway SQLite DB (never the real
pos.db) using Flask's test client, and asserts the key outcomes. Exits
non-zero if anything fails.

Run:
    cd backend
    ../venv/bin/python tests/smoke_test.py

Requires: a hashed-PIN manager seeded into the throwaway DB (done here).
"""

import os
import shutil
import sys
import sqlite3
import tempfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')

import database

# Point at a throwaway DB BEFORE importing app so all routes use it.
TEST_DB = os.path.join(tempfile.gettempdir(), 'tpos_smoke.db')
for suffix in ('', '-wal', '-shm'):
    if os.path.exists(TEST_DB + suffix):
        os.remove(TEST_DB + suffix)
database.DB_PATH = TEST_DB
database.init_db()

from auth import hash_pin
conn = sqlite3.connect(TEST_DB)
conn.execute("INSERT INTO workers (name, phone, role, pin) VALUES (?,?,?,?)",
             ['SmokeMgr', '', 'manager', hash_pin('1234')])
conn.commit()
conn.close()

from app import app

client = app.test_client()
results = []


def check(name, got, want):
    passed = got == want
    results.append((name, got, want, passed))
    return passed


def login(pin='1234'):
    r = client.post('/api/workers/login', json={'pin': pin})
    return r.status_code, (r.get_json() or {}).get('token')


def auth(token):
    return {'X-Auth-Token': token}


# --- 1. Auth ----------------------------------------------------------------
s, tok = login()
check('login ok', s, 200)
check('token issued', isinstance(tok, str) and len(tok) > 10, True)
check('no-token rejected', client.get('/api/categories').status_code, 401)
check('bad pin rejected', login('9999')[0], 401)

# --- 2. Catalog + sale flow -------------------------------------------------
h = auth(tok)
check('create category', client.post('/api/categories', json={'name': 'Elec', 'description': ''}, headers=h).status_code, 201)
check('create product', client.post('/api/products', json={
    'barcode': '1', 'name': 'Cable', 'category_id': 1, 'cost_price': 1,
    'sell_price': 5, 'quantity': 50, 'min_stock': 5, 'description': ''
}, headers=h).status_code, 201)
check('create customer', client.post('/api/customers', json={'name': 'Client A', 'phone': '', 'notes': ''}, headers=h).status_code, 201)
check('list products', len(client.get('/api/products', headers=h).get_json()), 1)

# cash sale -> stock decrements
r = client.post('/api/sales', json={
    'total': 10, 'discount': 0, 'payment_method': 'cash', 'amount_paid': None,
    'created_by': 1,
    'items': [{'barcode': '1', 'quantity': 2, 'unit_price': 5, 'discount': 0}],
}, headers=h)
check('cash sale', r.status_code, 201)
stock = client.get('/api/products/1', headers=h).get_json()['quantity']
check('stock after cash sale (48)', stock, 48)

# partial credit sale -> customer debt
r = client.post('/api/sales', json={
    'total': 5, 'discount': 0, 'payment_method': 'cash', 'customer_id': 1,
    'amount_paid': 2, 'created_by': 1,
    'items': [{'barcode': '1', 'quantity': 1, 'unit_price': 5, 'discount': 0}],
}, headers=h)
check('partial sale', r.status_code, 201)
debt = client.get('/api/customers/1', headers=h).get_json()['remaining_debt']
check('customer debt (3)', debt, 3)

# delete sale restores stock + clears orphan payment
sale_id = client.get('/api/sales?limit=1', headers=h).get_json()[0]['id']
check('delete sale', client.delete(f'/api/sales/{sale_id}', headers=h).status_code, 200)
debt = client.get('/api/customers/1', headers=h).get_json()['remaining_debt']
check('debt after delete (0)', debt, 0)

# --- 3. Stock / deliveries --------------------------------------------------
check('create supplier', client.post('/api/suppliers', json={'name': 'Sup', 'phone': ''}, headers=h).status_code, 201)
r = client.post('/api/deliveries', json={
    'supplier_id': 1, 'amount_due': 20, 'amount_paid': 0, 'due_date': None,
    'notes': '', 'created_by': 1,
    'items': [{'barcode': '1', 'quantity': 4, 'cost_price': 5, 'suggested_sell_price': None}],
}, headers=h)
check('create delivery', r.status_code, 201)
stock = client.get('/api/products/1', headers=h).get_json()['quantity']
check('stock after delivery (+4)', stock, 52)

# --- 4. Backup --------------------------------------------------------------
usb = tempfile.mkdtemp(prefix='tpos_usb_')
r = client.post('/api/backup/export', json={'target_path': usb}, headers=h)
bk = (r.get_json() or {}).get('path')
check('backup export', r.status_code, 200)
r = client.post('/api/backup/verify', json={'backup_path': bk}, headers=h)
check('backup verify ok', (r.get_json() or {}).get('success'), True)
s = client.get('/api/backup/status', headers=h).get_json()
check('backup status field present', 'newest_backup_days' in s, True)
check('backup endpoints need auth', client.get('/api/backup/status').status_code, 401)

# --- 5. Settings ------------------------------------------------------------
check('get settings', client.get('/api/settings', headers=h).status_code, 200)
check('settings has printer keys', 'printer_port' in client.get('/api/settings', headers=h).get_json(), True)

# --- 6. Reports / analytics -------------------------------------------------
check('daily report', client.get('/api/reports/daily', headers=h).status_code, 200)
check('dashboard', client.get('/api/analytics/dashboard', headers=h).status_code, 200)
check('history', client.get('/api/history', headers=h).status_code, 200)

# cleanup
for suffix in ('', '-wal', '-shm'):
    if os.path.exists(TEST_DB + suffix):
        os.remove(TEST_DB + suffix)
shutil.rmtree(usb, ignore_errors=True)

failed = [n for n, _, _, ok in results if not ok]
for name, got, want, ok in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got={got} want={want}")
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
if failed:
    print("FAILED:", ', '.join(failed))
    sys.exit(1)
print("SMOKE OK")
