from flask import Blueprint, jsonify, request
from database import get_db

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/suppliers', methods=['GET'])
def list_suppliers():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, phone, address, notes FROM suppliers ORDER BY name ASC").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@suppliers_bp.route('/suppliers/with-debt', methods=['GET'])
def list_suppliers_with_debt():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM (
                SELECT s.id, s.name, s.phone,
                       COALESCE(SUM(d.amount_due - d.amount_paid), 0)
                           - COALESCE((SELECT SUM(sp.amount) FROM supplier_payments sp
                                       JOIN deliveries dd ON dd.id = sp.delivery_id
                                       WHERE dd.supplier_id = s.id), 0) AS remaining_debt
                FROM suppliers s
                LEFT JOIN deliveries d ON d.supplier_id = s.id
                GROUP BY s.id
            )
            WHERE remaining_debt > 0
            ORDER BY remaining_debt DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@suppliers_bp.route('/suppliers/<int:id>', methods=['GET'])
def get_supplier(id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, phone, address, notes FROM suppliers WHERE id = ?", [id]).fetchone()
        if row is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()


@suppliers_bp.route('/suppliers/search', methods=['GET'])
def search_suppliers():
    q = request.args.get('q', '')
    conn = get_db()
    try:
        rows = conn.execute("SELECT id, name, phone FROM suppliers WHERE name LIKE ? ORDER BY name ASC", [
                            f'%{q}%']).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@suppliers_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO suppliers (name, phone, address, notes) VALUES (?, ?, ?, ?)",
                     [data['name'], data.get('phone'), data.get('address'), data.get('notes')])
        conn.commit()
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@suppliers_bp.route('/suppliers/<int:id>', methods=['PUT'])
def update_supplier(id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("UPDATE suppliers SET name = ?, phone = ?, address = ?, notes = ? WHERE id = ?",
                     [data['name'], data.get('phone'), data.get('address'), data.get('notes'), id])
        conn.commit()
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@suppliers_bp.route('/suppliers/<int:id>', methods=['DELETE'])
def delete_supplier(id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM suppliers WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
