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
        log_action('SETTINGS', f"Sauvegarde de la base de données effectuée vers {destination}",
                    worker_id=data.get('created_by') if data else None)
        return jsonify({
            "success": True,
            "message": f"Sauvegarde réussie dans {destination}",
            "filename": backup_filename,
            "path": destination
        })
    except Exception as e:
        return jsonify({"error": f"Échec de la sauvegarde: {str(e)}"}), 500


@backup_bp.route('/backup/list', methods=['POST'])
def list_backups():
    data = request.json or {}
    target_path = data.get('target_path')

    drives = find_usb_drives()
    if not target_path:
        if not drives:
            return jsonify({"error": "Aucune clé USB détectée."}), 400
        target_path = drives[0]['path']

    backup_dir = os.path.join(target_path, "TPOS_Backups")
    if not os.path.exists(backup_dir):
        return jsonify({"backups": []})

    try:
        backups = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.db'):
                full = os.path.join(backup_dir, f)
                size = os.path.getsize(full)
                mtime = os.path.getmtime(full)
                backups.append({
                    "filename": f,
                    "path": full,
                    "size": size,
                    "date": datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        return jsonify({"backups": backups})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@backup_bp.route('/backup/restore', methods=['POST'])
def restore_backup():
    data = request.json or {}
    backup_path = data.get('backup_path')
    if not backup_path:
        return jsonify({"error": "Aucun fichier de sauvegarde spécifié."}), 400

    if not os.path.exists(backup_path):
        return jsonify({"error": "Fichier de sauvegarde introuvable."}), 404

    db_file = "pos.db"
    if not os.path.exists(db_file):
        return jsonify({"error": "Base de données actuelle introuvable."}), 404

    try:
        # Create a safety backup of current DB before restoring
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safety = f"pos_pre_restore_{timestamp}.db"
        shutil.copy2(db_file, safety)

        # Restore the backup
        shutil.copy2(backup_path, db_file)

        log_action('SETTINGS', f"Restauration de la base de données depuis {backup_path}")
        return jsonify({
            "success": True,
            "message": f"Restauration réussie depuis {os.path.basename(backup_path)}. Une sauvegarde de sécurité (avant restauration) a été créée."
        })
    except Exception as e:
        return jsonify({"error": f"Échec de la restauration: {str(e)}"}), 500
