from flask import Blueprint, jsonify, request
from database import get_db

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories', methods=['GET'])
def list_categories():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, description FROM categories ORDER BY name ASC").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@categories_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name, description) VALUES (?, ?)",
                     [data['name'], data.get('description')])
        conn.commit()
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@categories_bp.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("UPDATE categories SET name = ?, description = ? WHERE id = ?",
                     [data['name'], data.get('description'), id])
        conn.commit()
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@categories_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM categories WHERE id = ?", [id])
        conn.commit()
        return jsonify({'message': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
