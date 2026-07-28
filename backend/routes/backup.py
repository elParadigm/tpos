import os
import shutil
import datetime
from flask import Blueprint, jsonify, request
from audit import log_action

backup_bp = Blueprint('backup', __name__)

SEARCH_PATHS = ['/media', '/mnt', '/run/media']

def find_usb_drives():
    drives = []
    username = os.getenv('USER') or os.getenv('LOGNAME') or 'el_paradigm'
    
    candidate_paths = [
        '/media',
        '/mnt',
        f'/media/{username}',
        f'/run/media/{username}'
    ]
    
    for base in candidate_paths:
        if os.path.exists(base) and os.path.isdir(base):
            try:
                for entry in os.listdir(base):
                    full_path = os.path.join(base, entry)
                    if os.path.isdir(full_path) and os.access(full_path, os.W_OK):
                        # Avoid root mounts or system dirs
                        if entry not in ['cdrom', 'floppy', 'ubuntu', 'boot']:
                            drives.append({
                                'name': entry,
                                'path': full_path
                            })
            except Exception as e:
                print(f"Error checking path {base}: {e}")
                
    return drives

@backup_bp.route('/backup/drives', methods=['GET'])
def get_drives():
    drives = find_usb_drives()
    return jsonify({"drives": drives})

@backup_bp.route('/backup/export', methods=['POST'])
def export_backup():
    data = request.json or {}
    target_path = data.get('target_path')
    
    drives = find_usb_drives()
    if not target_path:
        if not drives:
            return jsonify({"error": "Aucune clé USB détectée. Veuillez insérer une clé USB et réessayer."}), 400
        target_path = drives[0]['path']
        
    db_file = "pos.db"
    if not os.path.exists(db_file):
        return jsonify({"error": "Fichier de base de données pos.db introuvable."}), 404
        
    backup_dir = os.path.join(target_path, "TPOS_Backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"tpos_backup_{timestamp}.db"
    destination = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_file, destination)
        log_action('SETTINGS', f"Sauvegarde de la base de données effectuée vers {destination}")
        return jsonify({
            "success": True,
            "message": f"Sauvegarde réussie dans {destination}",
            "filename": backup_filename,
            "path": destination
        })
    except Exception as e:
        return jsonify({"error": f"Échec de la sauvegarde: {str(e)}"}), 500
