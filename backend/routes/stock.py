from flask import Blueprint, jsonify, request
from database import get_db

stock_bp = Blueprint('stock', __name__)


# ------------------------------------------------------------
# AUDIT LOG HELPER
# ------------------------------------------------------------

def log_audit(conn, action_type, description, worker_name=None):
    conn.execute("""
        INSERT INTO audit_logs (
            action_type,
            description,
            worker_name
        )
        VALUES (?, ?, ?)
    """, [
        action_type,
        description,
        str(worker_name) if worker_name else "Système"
    ])


# ------------------------------------------------------------
# DELIVERIES
# ------------------------------------------------------------


@stock_bp.route('/deliveries', methods=['GET'])
def list_deliveries():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT d.id,
                   s.name AS supplier_name,
                   d.delivery_date,
                   d.amount_due,
                   d.amount_paid,
                   d.amount_due - d.amount_paid
                       - COALESCE(sp.total_paid, 0) AS remaining,
                   d.due_date,
                   d.notes
            FROM deliveries d
            LEFT JOIN suppliers s ON s.id = d.supplier_id
            LEFT JOIN (
                SELECT delivery_id, SUM(amount) AS total_paid
                FROM supplier_payments
                GROUP BY delivery_id
            ) sp ON sp.delivery_id = d.id
            ORDER BY d.delivery_date DESC
        """).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        conn.close()


@stock_bp.route('/deliveries/unpaid', methods=['GET'])
def list_unpaid_deliveries():
    conn = get_db()

    try:
        rows = conn.execute("""
            SELECT d.id,
                   s.name AS supplier_name,
                   d.delivery_date,
                   d.amount_due,
                   d.amount_paid,
                   d.amount_due - d.amount_paid
                       - COALESCE(sp.total_paid, 0) AS remaining,
                   d.due_date,
                   d.notes
            FROM deliveries d
            LEFT JOIN suppliers s ON s.id = d.supplier_id
            LEFT JOIN (
                SELECT delivery_id, SUM(amount) AS total_paid
                FROM supplier_payments
                GROUP BY delivery_id
            ) sp ON sp.delivery_id = d.id
            WHERE (
                d.amount_due -
                d.amount_paid -
                COALESCE(sp.total_paid,0)
            ) > 0
            ORDER BY d.due_date ASC
        """).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        conn.close()


@stock_bp.route('/deliveries/<int:id>', methods=['GET'])
def get_delivery(id):

    conn = get_db()

    try:
        delivery = conn.execute("""
            SELECT d.id,
                   s.name AS supplier_name,
                   d.supplier_id,
                   d.delivery_date,
                   d.amount_due,
                   d.amount_paid,
                   d.amount_due - d.amount_paid
                       - COALESCE(sp.total_paid,0) AS remaining,
                   d.due_date,
                   d.notes
            FROM deliveries d
            LEFT JOIN suppliers s
                ON s.id = d.supplier_id
            LEFT JOIN (
                SELECT delivery_id, SUM(amount) AS total_paid
                FROM supplier_payments
                GROUP BY delivery_id
            ) sp
                ON sp.delivery_id=d.id
            WHERE d.id=?
        """, [id]).fetchone()

        if not delivery:
            return jsonify({"error": "not found"}), 404

        items = conn.execute("""
            SELECT di.id,
                   di.barcode,
                   p.name AS product_name,
                   di.quantity,
                   di.cost_price,
                   di.suggested_sell_price
            FROM delivery_items di
            JOIN products p
                ON p.barcode=di.barcode
            WHERE di.delivery_id=?
        """, [id]).fetchall()

        payments = conn.execute("""
            SELECT id,
                   amount,
                   paid_at,
                   notes
            FROM supplier_payments
            WHERE delivery_id=?
            ORDER BY paid_at ASC
        """, [id]).fetchall()

        result = dict(delivery)
        result["items"] = [dict(x) for x in items]
        result["payments"] = [dict(x) for x in payments]

        return jsonify(result)

    finally:
        conn.close()


@stock_bp.route('/deliveries', methods=['POST'])
def create_delivery():

    data = request.get_json()
    conn = get_db()

    try:

        cursor = conn.execute("""
            INSERT INTO deliveries
            (
                supplier_id,
                amount_due,
                amount_paid,
                due_date,
                notes,
                created_by
            )
            VALUES (?,?,?,?,?,?)
        """, [
            data.get("supplier_id"),
            data.get("amount_due", 0),
            data.get("amount_paid", 0),
            data.get("due_date"),
            data.get("notes"),
            data.get("created_by")
        ])

        delivery_id = cursor.lastrowid

        for item in data.get("items", []):

            conn.execute("""
                INSERT INTO delivery_items
                (
                    delivery_id,
                    barcode,
                    quantity,
                    cost_price,
                    suggested_sell_price
                )
                VALUES (?,?,?,?,?)
            """, [
                delivery_id,
                item["barcode"],
                item["quantity"],
                item["cost_price"],
                item.get("suggested_sell_price")
            ])

            product = conn.execute("""
                SELECT name
                FROM products
                WHERE barcode=?
            """, [item["barcode"]]).fetchone()

            conn.execute("""
                UPDATE products
                SET quantity = quantity + ?,
                    cost_price = ?
                WHERE barcode=?
            """, [
                item["quantity"],
                item["cost_price"],
                item["barcode"]
            ])

            log_audit(
                conn,
                "STOCK",
                f"Réception de {item['quantity']} unités de {
                    product['name'] if product else item['barcode']}",
                data.get("created_by")
            )

        conn.commit()

        return jsonify({
            "message": "created",
            "id": delivery_id
        }), 201

    except Exception as e:

        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        conn.close()


# ------------------------------------------------------------
# PAYMENTS
# ------------------------------------------------------------


@stock_bp.route('/deliveries/<int:id>/payments', methods=['POST'])
def add_delivery_payment(id):

    data = request.get_json()
    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO supplier_payments
            (
                delivery_id,
                amount,
                notes,
                created_by
            )
            VALUES (?,?,?,?)
        """, [
            id,
            data["amount"],
            data.get("notes"),
            data.get("created_by")
        ])

        log_audit(
            conn,
            "STOCK",
            f"Paiement fournisseur enregistré: {data['amount']}",
            data.get("created_by")
        )

        conn.commit()

        return jsonify({
            "message": "payment recorded"
        }), 201

    except Exception as e:

        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        conn.close()
