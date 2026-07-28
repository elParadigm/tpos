from flask import Blueprint, jsonify, request
from database import get_db

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories', methods=['GET'])
def list_categories():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, description FROM categories ORDER BY name ASC").fetchall()
    return jsonify([dict(row) for row in rows])


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
    db = get_db()
    db.execute("UPDATE categories SET name = ?, description = ? WHERE id = ?",
               [data['name'], data.get('description'), id])
    db.commit()
    return jsonify({'message': 'updated'})


@categories_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", [id])
    db.commit()
    return jsonify({'message': 'deleted'})
