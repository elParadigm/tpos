from flask import Blueprint, jsonify, request
from database import get_db

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('/customers', methods=['GET'])
def list_customers():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, phone, notes, created_at FROM customers ORDER BY name ASC").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@customers_bp.route('/customers/with-debt', methods=['GET'])
def list_customers_with_debt():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT c.id, c.name, c.phone,
                   COALESCE(SUM(s.total - s.discount), 0)
                       - COALESCE(SUM(cp.amount), 0) AS remaining_debt
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id AND s.payment_method = 'credit'
            LEFT JOIN customer_payments cp ON cp.customer_id = c.id
            GROUP BY c.id
            HAVING remaining_debt > 0
            ORDER BY remaining_debt DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>', methods=['GET'])
def get_customer(id):
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT c.id, c.name, c.phone,
                   COALESCE(SUM(s.total - s.discount), 0) AS total_credit_sales,
                   COALESCE(SUM(cp.amount), 0) AS total_repaid,
                   COALESCE(SUM(s.total - s.discount), 0)
                       - COALESCE(SUM(cp.amount), 0) AS remaining_debt
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id AND s.payment_method = 'credit'
            LEFT JOIN customer_payments cp ON cp.customer_id = c.id
            WHERE c.id = ?
            GROUP BY c.id
        """, [id]).fetchone()
        if row is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()


@customers_bp.route('/customers/search', methods=['GET'])
def search_customers():
    q = request.args.get('q', '')
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, name, phone FROM customers
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY name ASC
        """, [f'%{q}%', f'%{q}%']).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>/sales', methods=['GET'])
def customer_credit_sales(id):
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, sale_date, total, discount, total - discount AS net_total, notes
            FROM sales
            WHERE customer_id = ? AND payment_method = 'credit'
            ORDER BY sale_date DESC
        """, [id]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@customers_bp.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO customers (name, phone, notes) VALUES (?, ?, ?)",
                     [data['name'], data.get('phone'), data.get('notes')])
        conn.commit()
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("UPDATE customers SET name = ?, phone = ?, notes = ? WHERE id = ?",
                     [data['name'], data.get('phone'), data.get('notes'), id])
        conn.commit()
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>/payments', methods=['POST'])
def add_customer_payment(id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO customer_payments (customer_id, amount, notes) VALUES (?, ?, ?)",
                     [id, data['amount'], data.get('notes')])
        conn.commit()
        return jsonify({'message': 'payment recorded'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>/payments', methods=['GET'])
def list_customer_payments(id):
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, amount, paid_at, notes FROM customer_payments
            WHERE customer_id = ? ORDER BY paid_at DESC
        """, [id]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@customers_bp.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM customers WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
