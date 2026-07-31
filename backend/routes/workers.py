from flask import Blueprint, jsonify, request
from database import get_db
from audit import log_action
from auth import (hash_pin, verify_pin, issue_token, login_required,
                  manager_required, _login_allowed,
                  _record_login_failure, _reset_login_failures)

workers_bp = Blueprint('workers', __name__)


@workers_bp.route('/workers', methods=['GET'])
@manager_required
def list_workers():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, name, phone, role, is_active, created_at
            FROM workers ORDER BY name ASC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@workers_bp.route('/workers/active', methods=['GET'])
@login_required
def list_active_workers():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, name, phone, role FROM workers
            WHERE is_active = 1 ORDER BY name ASC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>', methods=['GET'])
def get_worker(id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, phone, role, is_active FROM workers WHERE id = ?", [id]).fetchone()
        if row is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()


@workers_bp.route('/workers', methods=['POST'])
@manager_required
def create_worker():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO workers (name, phone, role, pin) VALUES (?, ?, ?, ?)",
                     [data['name'], data.get('phone'), data.get('role'), hash_pin(data['pin'])])
        conn.commit()
        log_action('PRODUCT', f"Création du compte {data['name']} ({data.get('role')})",
                   worker_id=request.worker['id'])
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>', methods=['PUT'])
@manager_required
def update_worker(id):
    data = request.get_json()
    conn = get_db()
    try:
        # If a new PIN is provided, hash and store it; otherwise keep the old.
        if data.get('pin'):
            conn.execute("""
                UPDATE workers
                SET name = ?, phone = ?, role = ?, pin = ?
                WHERE id = ?
            """, [data['name'], data.get('phone'), data.get('role'),
                  hash_pin(data['pin']), id])
        else:
            conn.execute("""
                UPDATE workers
                SET name = ?, phone = ?, role = ?
                WHERE id = ?
            """, [data['name'], data.get('phone'), data.get('role'), id])

        conn.commit()
        log_action('PRODUCT', f"Modification du compte {data['name']}",
                   worker_id=request.worker['id'])
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>/deactivate', methods=['PUT'])
@manager_required
def deactivate_worker(id):
    conn = get_db()
    try:
        conn.execute("UPDATE workers SET is_active = 0 WHERE id = ?", [id])
        conn.commit()
        log_action('PRODUCT', f"Désactivation du compte #{id}",
                   worker_id=request.worker['id'])
        return jsonify({'message': 'deactivated'})
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>/reactivate', methods=['PUT'])
@manager_required
def reactivate_worker(id):
    conn = get_db()
    try:
        conn.execute("UPDATE workers SET is_active = 1 WHERE id = ?", [id])
        conn.commit()
        log_action('PRODUCT', f"Réactivation du compte #{id}",
                   worker_id=request.worker['id'])
        return jsonify({'message': 'reactivated'})
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>', methods=['DELETE'])
@manager_required
def delete_worker(id):
    conn = get_db()
    try:
        # Refuse to delete a worker with activity — they are referenced
        # by sales, deliveries and payments.
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM sales WHERE created_by = ?) +
                (SELECT COUNT(*) FROM deliveries WHERE created_by = ?) +
                (SELECT COUNT(*) FROM supplier_payments WHERE created_by = ?) +
                (SELECT COUNT(*) FROM customer_payments WHERE created_by = ?)
            AS activity_count
        """, [id, id, id, id]).fetchone()
        if row['activity_count'] > 0:
            return jsonify({'error': "Cet employé a des opérations enregistrées, il ne peut pas être supprimé. Désactivez-le à la place."}), 400

        conn.execute("DELETE FROM workers WHERE id = ?", [id])
        conn.commit()
        log_action('PRODUCT', f"Suppression du compte #{id}",
                   worker_id=request.worker['id'])
        return jsonify({'message': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@workers_bp.route('/workers/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    pin = str(data.get('pin', ''))
    conn = get_db()
    try:
        # Throttle by PIN: check the lockout before verifying, and record
        # failures so repeated guesses at a PIN are blocked.
        if not _login_allowed(pin):
            return jsonify({'error': 'Trop de tentatives. Réessayez dans quelques minutes.'}), 429

        row = conn.execute(
            "SELECT id, name, role, pin FROM workers WHERE is_active = 1"
        ).fetchall()
        target = next((r for r in row if verify_pin(pin, r['pin'])), None)

        if not target:
            _record_login_failure(pin)
            return jsonify({'error': 'Code PIN incorrect'}), 401

        _reset_login_failures(pin)
        token = issue_token(target['id'])
        return jsonify({'id': target['id'], 'name': target['name'],
                        'role': target['role'], 'token': token})
    finally:
        conn.close()
