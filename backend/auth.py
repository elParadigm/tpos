"""Lightweight server-side authentication for the TPOS API.

The kiosk serves the app and API from the same origin, so after login the
frontend keeps a signed token in localStorage and sends it as the
X-Auth-Token header. Every /api request is checked by a before_request hook
in app.py. Login is rate-limited per worker to slow brute-force attempts.

This is single-storeware auth (one token secret per install) — adequate for
a locked-down kiosk appliance, not for a multi-tenant SaaS.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import threading
from functools import wraps

from flask import jsonify, request
from database import get_db

_TOKEN_SECRET_ENV = 'TPOS_AUTH_SECRET'


def _secret():
    s = os.environ.get(_TOKEN_SECRET_ENV)
    if s:
        return s.encode()
    # Fall back to a persistent per-install secret stored in the DB, so the
    # secret survives restarts without needing an env var in the kiosk.
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key='auth_secret'").fetchone()
        if row:
            return row['value'].encode()
        s = secrets.token_hex(32)
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('auth_secret', ?)", [s])
        conn.commit()
        return s.encode()
    finally:
        conn.close()


def hash_pin(pin):
    """Return 'scheme$salt$hash' for a PIN (hex salt, scrypt digest)."""
    salt = secrets.token_hex(8)
    digest = hashlib.scrypt(pin.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_pin(pin, stored):
    if not stored or not stored.startswith('scrypt$'):
        return False
    try:
        _, salt, expected = stored.split('$')
    except ValueError:
        return False
    digest = hashlib.scrypt(pin.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()
    return hmac.compare_digest(digest, expected)


def issue_token(worker_id):
    """Signed token: worker_id.issued_timestamp.signature."""
    payload = f"{worker_id}.{int(time.time())}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_token(token):
    """Return worker_id dict or None. Rejects expired (>7 days) tokens."""
    try:
        worker_id_s, issued_s, sig = token.split('.')
        payload = f"{worker_id_s}.{issued_s}"
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(time.time()) - int(issued_s) > 7 * 24 * 3600:
            return None
        return int(worker_id_s)
    except (ValueError, AttributeError):
        return None


# --- brute-force throttling -------------------------------------------------
# Lockout is keyed by PIN: an attacker guesses a PIN, not a worker id, and
# we have to find the account by PIN anyway. Counting per PIN throttles
# repeated guesses at that PIN regardless of which account it targets.

_login_attempts = {}
_lock = threading.Lock()
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300


def _login_allowed(pin):
    with _lock:
        info = _login_attempts.get(pin)
        if not info:
            return True
        if info['count'] >= _MAX_ATTEMPTS:
            if time.time() - info['first'] < _LOCKOUT_SECONDS:
                return False
            del _login_attempts[pin]
            return True
        return True


def _record_login_failure(pin):
    with _lock:
        info = _login_attempts.setdefault(pin, {'count': 0, 'first': time.time()})
        info['count'] += 1


def _reset_login_failures(pin):
    with _lock:
        _login_attempts.pop(pin, None)


# --- decorators -------------------------------------------------------------

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get('X-Auth-Token', '')
        worker_id = verify_token(token)
        if not worker_id:
            return jsonify({'error': 'Non autorisé. Veuillez vous reconnecter.'}), 401
        conn = get_db()
        try:
            row = conn.execute("SELECT id, name, role, is_active FROM workers WHERE id = ?", [worker_id]).fetchone()
        finally:
            conn.close()
        if not row or not row['is_active']:
            return jsonify({'error': 'Compte inactif ou supprimé.'}), 401
        request.worker = dict(row)
        return fn(*args, **kwargs)
    return wrapper


def manager_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get('X-Auth-Token', '')
        worker_id = verify_token(token)
        if not worker_id:
            return jsonify({'error': 'Non autorisé. Veuillez vous reconnecter.'}), 401
        conn = get_db()
        try:
            row = conn.execute("SELECT id, name, role, is_active FROM workers WHERE id = ?", [worker_id]).fetchone()
        finally:
            conn.close()
        if not row or not row['is_active']:
            return jsonify({'error': 'Compte inactif ou supprimé.'}), 401
        if row['role'] != 'manager':
            return jsonify({'error': 'Accès réservé au gérant.'}), 403
        request.worker = dict(row)
        return fn(*args, **kwargs)
    return wrapper


def current_worker_id():
    token = request.headers.get('X-Auth-Token', '')
    wid = verify_token(token)
    if wid is None:
        return None
    return wid
