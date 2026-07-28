from flask import Blueprint, jsonify, request
from database import get_db

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) AS sales_count,
                COALESCE(SUM(total - discount), 0) AS revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total - discount ELSE 0 END), 0) AS cash_revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'credit' THEN total - discount ELSE 0 END), 0) AS credit_revenue
            FROM sales WHERE DATE(sale_date) = DATE('now')
        """).fetchone()
        return jsonify(dict(row))
    finally:
        conn.close()


@analytics_bp.route('/analytics/revenue/daily', methods=['GET'])
def daily_revenue():
    since = request.args.get('since')
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT DATE(sale_date) AS day, COUNT(*) AS sales_count,
                   COALESCE(SUM(total - discount), 0) AS revenue
            FROM sales WHERE sale_date >= ?
            GROUP BY DATE(sale_date) ORDER BY day ASC
        """, [since]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@analytics_bp.route('/analytics/revenue/monthly', methods=['GET'])
def monthly_revenue():
    since = request.args.get('since')
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT strftime('%Y-%m', sale_date) AS month, COUNT(*) AS sales_count,
                   COALESCE(SUM(total - discount), 0) AS revenue
            FROM sales WHERE sale_date >= ?
            GROUP BY month ORDER BY month ASC
        """, [since]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@analytics_bp.route('/analytics/products/top', methods=['GET'])
def top_products():
    since = request.args.get('since')
    sort = request.args.get('sort', 'quantity')
    order_col = 'units_sold' if sort == 'quantity' else 'revenue'
    conn = get_db()
    try:
        rows = conn.execute(f"""
            SELECT COALESCE(p.name, si.custom_name) AS product_name, si.barcode,
                   SUM(si.quantity) AS units_sold,
                   SUM((si.unit_price - si.discount) * si.quantity) AS revenue
            FROM sale_items si
            LEFT JOIN products p ON p.barcode = si.barcode
            JOIN sales s ON s.id = si.sale_id
            WHERE s.sale_date >= ?
            GROUP BY si.barcode, si.custom_name
            ORDER BY {order_col} DESC LIMIT 10
        """, [since]).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@analytics_bp.route('/analytics/products/margins', methods=['GET'])
def product_margins():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT barcode, name, cost_price, sell_price,
                   sell_price - cost_price AS margin,
                   ROUND((sell_price - cost_price) / NULLIF(sell_price, 0) * 100, 2) AS margin_percent
            FROM products WHERE is_active = 1
            ORDER BY margin_percent DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@analytics_bp.route('/analytics/shifts', methods=['GET'])
def shift_summaries():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT COALESCE(w.name, '—') AS worker_name,
                   DATE(s.sale_date) AS day,
                   COUNT(*) AS sales_count,
                   COALESCE(SUM(s.total - s.discount), 0) AS revenue,
                   COALESCE(SUM(CASE WHEN s.payment_method = 'cash' THEN s.total - s.discount ELSE 0 END), 0) AS cash_revenue
            FROM sales s
            LEFT JOIN workers w ON w.id = s.created_by
            GROUP BY DATE(s.sale_date), s.created_by
            ORDER BY day DESC
            LIMIT 20
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()
