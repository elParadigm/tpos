from flask import Blueprint, jsonify, request
from database import get_db

history_bp = Blueprint('history', __name__)


@history_bp.route('/history', methods=['GET'])
def get_history():
    db = get_db()

    action_filter = request.args.get('action')

    # Use the existing 'worker_name' column
    base_query = """
        SELECT id, action_type, description, worker_name, created_at 
        FROM audit_logs
    """

    if action_filter:
        rows = db.execute(
            base_query + " WHERE action_type = ? ORDER BY created_at DESC LIMIT 200",
            (action_filter,)
        ).fetchall()
    else:
        rows = db.execute(
            base_query + " ORDER BY created_at DESC LIMIT 200"
        ).fetchall()

    return jsonify([dict(row) for row in rows])
