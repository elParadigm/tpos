from flask import Blueprint, jsonify, request
from database import get_db, utc_offset_sql
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
        rows = conn.execute(f"""
            SELECT s.id, s.sale_date, s.total - s.discount AS net_total,
                   s.payment_method, c.name AS customer_name
            FROM sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            WHERE DATE(s.sale_date, {utc_offset_sql()}) = DATE(?)
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
        # Check stock levels before processing
        out_of_stock = []
        for item in data.get('items', []):
            if not item.get('barcode'):
                continue  # custom items have no barcode, skip stock check
            row = conn.execute(
                "SELECT name, quantity FROM products WHERE barcode = ?",
                [item['barcode']]
            ).fetchone()
            if not row:
                out_of_stock.append(f"{item.get('custom_name') or item.get('barcode')}: produit introuvable")
            elif row['quantity'] < item['quantity']:
                out_of_stock.append(f"{row['name']}: stock {row['quantity']}, demandé {item['quantity']}")

        if out_of_stock:
            return jsonify({'error': 'Stock insuffisant', 'details': out_of_stock}), 409

        # --- Payment resolution (full / partial / credit) ---
        # amount_paid: omitted or empty => full payment; 0 => nothing paid
        # (credit); otherwise the amount actually collected.
        total = float(data['total'])
        discount = float(data.get('discount', 0))
        net_total = total - discount
        customer_id = data.get('customer_id')

        amount_paid = data.get('amount_paid')
        if amount_paid is None or amount_paid == '':
            amount_paid = net_total
        else:
            amount_paid = float(amount_paid)

        remaining = net_total - amount_paid
        if remaining > 1e-9:
            # Partial or no payment: the remainder becomes customer debt
            if not customer_id:
                return jsonify({'error': 'Veuillez sélectionner un client : ce paiement laisse un reste à payer.'}), 400
            payment_method = 'credit'
        else:
            # Fully paid: a 'credit' method makes no sense here (nothing
            # is owed), so fall back to cash.
            payment_method = data.get('payment_method', 'cash')
            if payment_method == 'credit':
                payment_method = 'cash'
            amount_paid = net_total
            remaining = 0

        cursor = conn.execute("""
            INSERT INTO sales (total, discount, payment_method, customer_id, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [data['total'], data.get('discount', 0), payment_method,
              customer_id, data.get('notes'), data.get('created_by')])
        sale_id = cursor.lastrowid

        # On a credit/partial sale, record what was actually collected now.
        # The payment is linked to the sale so that deleting the sale also
        # removes the payment (no orphaned balances).
        if payment_method == 'credit' and amount_paid > 0 and customer_id:
            conn.execute("""
                INSERT INTO customer_payments (customer_id, amount, notes, created_by, sale_id)
                VALUES (?, ?, ?, ?, ?)
            """, [customer_id, amount_paid, 'Paiement immédiat à la vente',
                  data.get('created_by'), sale_id])

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
        log_action('SALE', f"Vente #{sale_id} effectuée pour un montant total de {data['total']} DT (Méthode: {payment_method}, Payé: {amount_paid})",
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

        # The sale's immediate customer_payments (sale_id FK) are removed
        # by ON DELETE CASCADE, so customer balances stay consistent.
        conn.execute("DELETE FROM sales WHERE id = ?", [id])
        conn.commit()
        body = request.get_json(silent=True) or {}
        log_action('SALE', f"Vente #{id} annulée / supprimée (stock restitué)",
                   worker_id=body.get('created_by'))
        return jsonify({'message': 'deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
