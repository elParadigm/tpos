from flask import Blueprint, jsonify, request
from database import get_db
from audit import log_action

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/sales', methods=['GET'])
def list_sales():
    conn = get_db()
    try:
        limit = request.args.get('limit', 50)
        offset = request.args.get('offset', 0)
        rows = conn.execute("""
            SELECT s.id, s.sale_date, s.total, s.discount,
                   s.total - s.discount AS net_total,
                   s.payment_method, c.name AS customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            ORDER BY s.sale_date DESC
            LIMIT ? OFFSET ?
        """, [limit, offset]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@sales_bp.route('/sales/<int:id>', methods=['GET'])
def get_sale(id):
    conn = get_db()
    try:
        sale = conn.execute("""
            SELECT s.id, s.sale_date, s.total, s.discount, s.payment_method,
                   s.notes, c.name AS customer_name, w.name AS worker_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            LEFT JOIN workers w ON w.id = s.created_by
            WHERE s.id = ?
        """, [id]).fetchone()
        if sale is None:
            return jsonify({'error': 'not found'}), 404
        items = conn.execute("""
            SELECT si.id, si.barcode, COALESCE(p.name, si.custom_name) AS product_name,
                   si.quantity, si.unit_price, si.discount,
                   (si.unit_price - si.discount) * si.quantity AS line_total
            FROM sale_items si
            LEFT JOIN products p ON p.barcode = si.barcode
            WHERE si.sale_id = ?
        """, [id]).fetchall()
        result = dict(sale)
        result['items'] = [dict(i) for i in items]
        return jsonify(result)
    finally:
        conn.close()


@sales_bp.route('/sales/by-date/<date>', methods=['GET'])
def sales_by_date(date):
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT s.id, s.sale_date, s.total - s.discount AS net_total,
                   s.payment_method, c.name AS customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE DATE(s.sale_date) = DATE(?)
            ORDER BY s.sale_date DESC
        """, [date]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    data = request.get_json()
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO sales (total, discount, payment_method, customer_id, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [data['total'], data.get('discount', 0), data.get('payment_method', 'cash'),
              data.get('customer_id'), data.get('notes'), data.get('created_by')])
        sale_id = cursor.lastrowid
        for item in data.get('items', []):
            if item.get('barcode'):
                conn.execute("""
                    INSERT INTO sale_items (sale_id, barcode, quantity, unit_price, discount)
                    VALUES (?, ?, ?, ?, ?)
                """, [sale_id, item['barcode'], item['quantity'],
                      item['unit_price'], item.get('discount', 0)])
                conn.execute("UPDATE products SET quantity = quantity - ? WHERE barcode = ?",
                             [item['quantity'], item['barcode']])
            else:
                conn.execute("""
                    INSERT INTO sale_items (sale_id, custom_name, custom_cost, quantity, unit_price, discount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [sale_id, item['custom_name'], item.get('custom_cost'),
                      item['quantity'], item['unit_price'], item.get('discount', 0)])
        conn.commit()
        log_action('SALE', f"Vente #{sale_id} effectuée pour un montant total de {data['total']} DT (Méthode: {data.get('payment_method', 'cash')})",
                    worker_id=data.get('created_by'))
        return jsonify({'message': 'created', 'id': sale_id, 'sale_id': sale_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@sales_bp.route('/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    conn = get_db()
    try:
        # Restore product stock before deleting
        items = conn.execute(
            "SELECT barcode, quantity FROM sale_items WHERE sale_id = ? AND barcode IS NOT NULL",
            [id]
        ).fetchall()
        for item in items:
            conn.execute(
                "UPDATE products SET quantity = quantity + ? WHERE barcode = ?",
                [item['quantity'], item['barcode']]
            )

        conn.execute("DELETE FROM sales WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
