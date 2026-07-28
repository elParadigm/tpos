from flask import Blueprint, jsonify, request
from database import get_db

workers_bp = Blueprint('workers', __name__)


@workers_bp.route('/workers', methods=['GET'])
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
def create_worker():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO workers (name, phone, role, pin) VALUES (?, ?, ?, ?)",
                     [data['name'], data.get('phone'), data.get('role'), data['pin']])
        conn.commit()
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>', methods=['PUT'])
def update_worker(id):
    data = request.get_json()
    conn = get_db()
    try:
        # If a new PIN is provided, update it along with other fields
        if 'pin' in data and data['pin']:
            conn.execute("""
                UPDATE workers 
                SET name = ?, phone = ?, role = ?, pin = ? 
                WHERE id = ?
            """, [data['name'], data.get('phone'), data.get('role'), data['pin'], id])
        else:
            # Otherwise, keep the existing PIN and only update the other fields
            conn.execute("""
                UPDATE workers 
                SET name = ?, phone = ?, role = ? 
                WHERE id = ?
            """, [data['name'], data.get('phone'), data.get('role'), id])

        conn.commit()
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>/deactivate', methods=['PUT'])
def deactivate_worker(id):
    conn = get_db()
    try:
        conn.execute("UPDATE workers SET is_active = 0 WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'deactivated'})
    finally:
        conn.close()


@workers_bp.route('/workers/<int:id>/reactivate', methods=['PUT'])
def reactivate_worker(id):
    conn = get_db()
    try:
        conn.execute("UPDATE workers SET is_active = 1 WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'reactivated'})
    finally:
        conn.close()


@workers_bp.route('/workers/login', methods=['POST'])
def login():
    data = request.get_json()
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT id, name, role FROM workers
            WHERE pin = ? AND is_active = 1
        """, [data['pin']]).fetchone()
        if row is None:
            return jsonify({'error': 'Invalid PIN'}), 401
        return jsonify(dict(row))
    finally:
        conn.close()
