from flask import Blueprint, jsonify, request
from database import get_db
from audit import log_action

products_bp = Blueprint('products', __name__)


@products_bp.route('/products', methods=['GET'])
def list_products():
    category_id = request.args.get('category_id')
    conn = get_db()
    try:
        if category_id:
            rows = conn.execute("""
                SELECT p.barcode, p.name, c.name AS category, p.category_id, p.cost_price,
                       p.sell_price, p.quantity, p.min_stock, p.description, p.created_at
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1 AND p.category_id = ?
                ORDER BY p.name ASC
            """, [category_id]).fetchall()
        else:
            rows = conn.execute("""
                SELECT p.barcode, p.name, c.name AS category, p.category_id, p.cost_price,
                       p.sell_price, p.quantity, p.min_stock, p.description, p.created_at
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE p.is_active = 1
                ORDER BY p.name ASC
            """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@products_bp.route('/products/search', methods=['GET'])
def search_products():
    q = request.args.get('q', '')
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT barcode, name, sell_price, quantity
            FROM products
            WHERE is_active = 1 AND name LIKE ?
            ORDER BY name ASC LIMIT 20
        """, [f'%{q}%']).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@products_bp.route('/products/<barcode>', methods=['GET'])
def get_product(barcode):
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT p.barcode, p.name, c.name AS category, p.sell_price, p.quantity, p.is_active
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.barcode = ?
        """, [barcode]).fetchone()
        if row is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()


@products_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO products (barcode, name, category_id, cost_price, sell_price, quantity, min_stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [data['barcode'], data['name'], data.get('category_id'), data.get('cost_price', 0),
              data['sell_price'], data.get('quantity', 0), data.get('min_stock', 5), data.get('description')])
        conn.commit()
        log_action('PRODUCT', f"Création du produit {data.get('name')} ({data.get('barcode')})",
                   worker_id=data.get('created_by'))
        return jsonify({'message': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@products_bp.route('/products/<barcode>', methods=['PUT'])
def update_product(barcode):
    data = request.get_json()
    conn = get_db()
    try:
        conn.execute("""
            UPDATE products SET name = ?, category_id = ?, sell_price = ?, min_stock = ?, description = ?
            WHERE barcode = ?
        """, [data['name'], data.get('category_id'), data['sell_price'],
              data.get('min_stock', 5), data.get('description'), barcode])
        conn.commit()
        log_action('PRODUCT', f"Modification du produit {data.get('name')} ({barcode})",
                   worker_id=data.get('created_by'))
        return jsonify({'message': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()


@products_bp.route('/products/<barcode>/deactivate', methods=['PUT'])
def deactivate_product(barcode):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        conn.execute(
            "UPDATE products SET is_active = 0 WHERE barcode = ?", [barcode])
        conn.commit()
        log_action('PRODUCT', f"Désactivation du produit {barcode}",
                   worker_id=data.get('created_by'))
        return jsonify({'message': 'deactivated'})
    finally:
        conn.close()


@products_bp.route('/products/<barcode>/reactivate', methods=['PUT'])
def reactivate_product(barcode):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    try:
        conn.execute(
            "UPDATE products SET is_active = 1 WHERE barcode = ?", [barcode])
        conn.commit()
        log_action('PRODUCT', f"Réactivation du produit {barcode}",
                   worker_id=data.get('created_by'))
        return jsonify({'message': 'reactivated'})
    finally:
        conn.close()


@products_bp.route('/products/low-stock', methods=['GET'])
def low_stock():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT barcode, name, quantity, min_stock,
                   (min_stock - quantity) AS deficit
            FROM products
            WHERE is_active = 1 AND quantity <= min_stock
            ORDER BY deficit DESC, name ASC
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()
