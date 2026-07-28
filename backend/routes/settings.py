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
    'currency': 'DT'
}

@settings_bp.route('/settings', methods=['GET'])
def get_settings():
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    
    settings = dict(DEFAULT_SETTINGS)
    for row in rows:
        settings[row['key']] = row['value']
        
    return jsonify(settings)

@settings_bp.route('/settings', methods=['POST', 'PUT'])
def update_settings():
    data = request.json or {}
    db = get_db()
    
    for key, value in data.items():
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(key), str(value))
        )
    
    db.commit()
    log_action('SETTINGS', 'Mise à jour de la configuration du magasin et des paramètres d\'impression')
    return jsonify({"success": True, "message": "Paramètres enregistrés avec succès"})
