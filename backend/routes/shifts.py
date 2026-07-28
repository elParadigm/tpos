from flask import Blueprint, jsonify, request
from database import get_db

shifts_bp = Blueprint('shifts', __name__)


@shifts_bp.route('/shifts/open', methods=['GET'])
def get_open_shift():
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT sh.id, w.name AS worker_name, sh.started_at, sh.opening_cash
            FROM shifts sh
            JOIN workers w ON w.id = sh.worker_id
            WHERE sh.ended_at IS NULL
            LIMIT 1
        """).fetchone()
        if row is None:
            return jsonify(None)
        return jsonify(dict(row))
    finally:
        conn.close()


@shifts_bp.route('/shifts', methods=['GET'])
def list_shifts():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT sh.id, w.name AS worker_name, sh.started_at, sh.ended_at,
                   sh.opening_cash, sh.closing_cash, sh.notes
            FROM shifts sh
            JOIN workers w ON w.id = sh.worker_id
            ORDER BY sh.started_at DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@shifts_bp.route('/shifts/<int:id>', methods=['GET'])
def get_shift_summary(id):
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT sh.id, w.name AS worker_name, sh.started_at, sh.ended_at,
                   sh.opening_cash, sh.closing_cash,
                   COUNT(s.id) AS total_sales,
                   COALESCE(SUM(s.total - s.discount), 0) AS revenue,
                   COALESCE(SUM(CASE WHEN s.payment_method = 'cash' THEN s.total - s.discount ELSE 0 END), 0) AS cash_sales,
                   sh.opening_cash + COALESCE(SUM(CASE WHEN s.payment_method = 'cash' THEN s.total - s.discount ELSE 0 END), 0) AS expected_cash,
                   sh.notes
            FROM shifts sh
            JOIN workers w ON w.id = sh.worker_id
            LEFT JOIN sales s ON s.shift_id = sh.id
            WHERE sh.id = ?
            GROUP BY sh.id
        """, [id]).fetchone()
        if row is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()


@shifts_bp.route('/shifts', methods=['POST'])
def open_shift():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO shifts (worker_id, opening_cash) VALUES (?, ?)",
                     [data['worker_id'], data.get('opening_cash', 0)])
        conn.commit()
        return jsonify({'message': 'shift opened'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@shifts_bp.route('/shifts/<int:id>/close', methods=['PUT'])
def close_shift(id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            UPDATE shifts SET ended_at = CURRENT_TIMESTAMP, closing_cash = ?, notes = ?
            WHERE id = ?
        """, [data['closing_cash'], data.get('notes'), id])
        conn.commit()
        return jsonify({'message': 'shift closed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
