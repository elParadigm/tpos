from flask import Blueprint, jsonify, request
from database import get_db, utc_offset_sql, local_now
from datetime import date

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/daily', methods=['GET'])
def daily_report():
    report_date = request.args.get('date', local_now().date().isoformat())
    conn = get_db()
    try:
        # Sales summary (timestamps stored UTC; shift to local calendar day)
        summary = conn.execute(f"""
            SELECT
                COUNT(*) AS sales_count,
                COALESCE(SUM(total - discount), 0) AS revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total - discount ELSE 0 END), 0) AS cash_revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'check' THEN total - discount ELSE 0 END), 0) AS check_revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'credit' THEN total - discount ELSE 0 END), 0) AS credit_revenue,
                COALESCE(SUM(discount), 0) AS total_discounts,
                COUNT(CASE WHEN discount > 0 THEN 1 END) AS discounted_sales
            FROM sales WHERE DATE(sale_date, {utc_offset_sql()}) = DATE(?)
        """, [report_date]).fetchone()

        # By worker
        workers = conn.execute(f"""
            SELECT COALESCE(w.name, 'Caisse') AS worker_name,
                   COUNT(*) AS sales_count,
                   COALESCE(SUM(s.total - s.discount), 0) AS revenue
            FROM sales s
            LEFT JOIN workers w ON w.id = s.created_by
            WHERE DATE(s.sale_date, {utc_offset_sql()}) = DATE(?)
            GROUP BY s.created_by
            ORDER BY revenue DESC
        """, [report_date]).fetchall()

        # Top products today
        top_products = conn.execute(f"""
            SELECT COALESCE(p.name, si.custom_name) AS product_name,
                   SUM(si.quantity) AS units_sold
            FROM sale_items si
            LEFT JOIN products p ON p.barcode = si.barcode
            JOIN sales s ON s.id = si.sale_id
            WHERE DATE(s.sale_date, {utc_offset_sql()}) = DATE(?)
            GROUP BY si.barcode, si.custom_name
            ORDER BY units_sold DESC LIMIT 10
        """, [report_date]).fetchall()

        # Low stock alerts
        low_stock = conn.execute("""
            SELECT COUNT(*) AS count FROM products
            WHERE is_active = 1 AND quantity <= min_stock
        """).fetchone()

        return jsonify({
            'date': report_date,
            'summary': dict(summary),
            'workers': [dict(w) for w in workers],
            'top_products': [dict(p) for p in top_products],
            'low_stock_count': low_stock['count'],
        })
    finally:
        conn.close()
