from flask import Blueprint, request, jsonify
from database import get_db
from audit import log_action

settings_bp = Blueprint('settings', __name__)

DEFAULT_SETTINGS = {
    'store_name': 'Mon Commerce',
    'tax_id': '',
    'phone': '',
    'address': '',
    'receipt_header': 'Bienvenue chez nous !',
    'receipt_footer': 'Merci pour votre visite. Les articles ne sont ni repris ni échangés.',
    'printer_format': '80mm',
    'currency': 'DT',
    'printer_port': '/dev/usb/lp0',
    'printer_enabled': '0'
}

@settings_bp.route('/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()

        settings = dict(DEFAULT_SETTINGS)
        for row in rows:
            settings[row['key']] = row['value']

        return jsonify(settings)
    finally:
        conn.close()

@settings_bp.route('/settings', methods=['POST', 'PUT'])
def update_settings():
    data = request.json or {}
    conn = get_db()
    try:
        for key, value in data.items():
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(key), str(value))
            )

        conn.commit()
        log_action('SETTINGS', 'Mise à jour de la configuration du magasin et des paramètres d\'impression',
                worker_id=data.get('created_by'))
        return jsonify({"success": True, "message": "Paramètres enregistrés avec succès"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()
