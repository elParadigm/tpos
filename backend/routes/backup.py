import os
import sqlite3
import shutil
import time
import datetime
import threading
from flask import Blueprint, jsonify, request
import database
from auth import login_required
from audit import log_action

backup_bp = Blueprint('backup', __name__)

SEARCH_PATHS = ['/media', '/mnt', '/run/media']

MAX_BACKUPS_PER_DRIVE = 5
AUTO_BACKUP_INTERVAL = 60          # seconds between drive scans
AUTO_BACKUP_MAX_AGE_HOURS = 24     # don't re-backup a drive newer than this
OVERDUE_DAYS = 7                   # badge shows when newest backup is older

_backup_lock = threading.Lock()
_last_autoback = {}                # drive path -> last auto-backup time
_autoback_started = False
_autoback_ready = False


def backup_to_drive(drive_path, created_by=None, note=None):
    """Write a full DB backup to <drive>/TPOS_Backups/, prune old ones,
    and return metadata. Uses the SQLite online backup API so the snapshot
    is consistent even in WAL mode. drive_path is a writable directory."""
    db_file = database.DB_PATH
    if not os.path.exists(db_file):
        raise FileNotFoundError("Fichier de base de données pos.db introuvable.")

    backup_dir = os.path.join(drive_path, "TPOS_Backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"tpos_backup_{timestamp}.db"
    destination = os.path.join(backup_dir, backup_filename)
    # Avoid collisions when two backups are written within the same second
    # (e.g. auto-backup across drives): bump the name until it's free.
    n = 1
    while os.path.exists(destination):
        backup_filename = f"tpos_backup_{timestamp}_{n}.db"
        destination = os.path.join(backup_dir, backup_filename)
        n += 1

    with _backup_lock:
        src = sqlite3.connect(db_file)
        dst = sqlite3.connect(destination)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

        # Keep only the newest MAX_BACKUPS_PER_DRIVE files per drive.
        # Sort by filename: it embeds a zero-padded timestamp
        # (tpos_backup_YYYY-MM-DD_HH-MM-SS.db), so lexicographic order is
        # chronological and deterministic even when mtimes tie.
        backups = sorted(
            (os.path.join(backup_dir, f) for f in os.listdir(backup_dir)
             if f.endswith('.db')),
            reverse=True,
        )
        for old in backups[MAX_BACKUPS_PER_DRIVE:]:
            try:
                os.remove(old)
            except OSError:
                pass

    log_action('SETTINGS', f"Sauvegarde de la base de données effectuée vers {destination}"
               + (f" ({note})" if note else ""),
               worker_id=created_by)
    return {
        "success": True,
        "message": f"Sauvegarde réussie dans {destination}",
        "filename": backup_filename,
        "path": destination,
    }


def _list_drive_backups(drive_path):
    """Return existing backup files (with mtime) in a drive's TPOS_Backups."""
    backup_dir = os.path.join(drive_path, "TPOS_Backups")
    if not os.path.isdir(backup_dir):
        return []
    out = []
    for f in os.listdir(backup_dir):
        if f.endswith('.db'):
            full = os.path.join(backup_dir, f)
            try:
                out.append((full, os.path.getmtime(full)))
            except OSError:
                continue
    return out


def _newest_backup_age_days(drives):
    """Most recent backup mtime across all drives -> age in days (or None)."""
    newest = None
    for d in drives:
        for full, mtime in _list_drive_backups(d['path']):
            if newest is None or mtime > newest:
                newest = mtime
    if newest is None:
        return None
    return max(0.0, (time.time() - newest) / 86400.0)


def _autobackup_scan():
    """One pass of the auto-backup logic (returns list of drives written)."""
    written = []
    for drive in find_usb_drives():
        path = drive['path']
        recent = _newest_backup_age_days([drive])
        if recent is not None and recent * 24 < AUTO_BACKUP_MAX_AGE_HOURS:
            continue  # already backed up recently on this drive
        # throttle: don't retry the same drive more than once/interval
        last = _last_autoback.get(path)
        if last and time.time() - last < AUTO_BACKUP_INTERVAL:
            continue
        try:
            backup_to_drive(path, created_by=None, note="automatique")
            _last_autoback[path] = time.time()
            written.append(path)
        except Exception as e:
            print(f"Auto-backup failed for {path}: {e}")
    return written


def _autobackup_loop():
    """Background thread: whenever a writable USB is present and no backup
    was written to it recently, write one automatically."""
    global _autoback_ready
    while True:
        try:
            _autobackup_scan()
            time.sleep(AUTO_BACKUP_INTERVAL)
        except Exception as e:
            print(f"Auto-backup loop error: {e}")
            time.sleep(AUTO_BACKUP_INTERVAL)


def ensure_autobackup_started():
    """Start the background auto-backup thread once (safe across reloaders)."""
    global _autoback_started, _autoback_ready
    if _autoback_started:
        return
    _autoback_started = True
    t = threading.Thread(target=_autobackup_loop, daemon=True, name='tpos-autobackup')
    t.start()
    _autoback_ready = True

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
@login_required
def get_drives():
    drives = find_usb_drives()
    return jsonify({"drives": drives})

@backup_bp.route('/backup/export', methods=['POST'])
@login_required
def export_backup():
    data = request.json or {}
    target_path = data.get('target_path')

    drives = find_usb_drives()
    if not target_path:
        if not drives:
            return jsonify({"error": "Aucune clé USB détectée. Veuillez insérer une clé USB et réessayer."}), 400
        target_path = drives[0]['path']

    try:
        result = backup_to_drive(target_path, created_by=(data or {}).get('created_by'))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Échec de la sauvegarde: {str(e)}"}), 500


@backup_bp.route('/backup/status', methods=['GET'])
@login_required
def backup_status():
    """How stale is the newest backup? The sidebar badge and settings page
    poll this."""
    drives = find_usb_drives()
    newest_days = _newest_backup_age_days(drives)
    return jsonify({
        "drives": drives,
        "newest_backup_days": newest_days,
        "overdue": newest_days is None or newest_days > OVERDUE_DAYS,
    })


@backup_bp.route('/backup/verify', methods=['POST'])
@login_required
def verify_backup():
    """Integrity-check a backup file without restoring it."""
    data = request.json or {}
    backup_path = data.get('backup_path')
    if not backup_path:
        return jsonify({"error": "Aucun fichier de sauvegarde spécifié."}), 400
    if not os.path.exists(backup_path):
        return jsonify({"error": "Fichier de sauvegarde introuvable."}), 404

    try:
        conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {}
            for t in ('sales', 'products', 'customers', 'settings', 'workers'):
                try:
                    tables[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                except sqlite3.OperationalError:
                    tables[t] = None
        finally:
            conn.close()

        ok = (integrity == 'ok') and all(v is not None for v in tables.values())
        return jsonify({
            "success": ok,
            "integrity": integrity,
            "tables": tables,
            "size": os.path.getsize(backup_path),
            "date": datetime.datetime.fromtimestamp(
                os.path.getmtime(backup_path)).strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Base valide" if ok else "Fichier invalide",
        })
    except Exception as e:
        return jsonify({"error": f"Échec de la vérification: {str(e)}"}), 500


@backup_bp.route('/backup/list', methods=['POST'])
@login_required
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
@login_required
def restore_backup():
    data = request.json or {}
    backup_path = data.get('backup_path')
    if not backup_path:
        return jsonify({"error": "Aucun fichier de sauvegarde spécifié."}), 400

    if not os.path.exists(backup_path):
        return jsonify({"error": "Fichier de sauvegarde introuvable."}), 404

    db_file = database.DB_PATH
    if not os.path.exists(db_file):
        return jsonify({"error": "Base de données actuelle introuvable."}), 404

    try:
        # Create a safety backup of the CURRENT DB before restoring (using
        # the online backup API so the snapshot is consistent).
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safety = f"pos_pre_restore_{timestamp}.db"
        src = sqlite3.connect(db_file)
        safe = sqlite3.connect(safety)
        src.backup(safe)
        safe.close()
        src.close()

        # Copy the backup over the live file, then delete any stale WAL/SHM
        # files. Otherwise SQLite would replay old WAL frames against the
        # restored file (data mixing / corruption). The safety copy already
        # has everything that was committed, so nothing is lost.
        shutil.copy2(backup_path, db_file)
        for suffix in ('-wal', '-shm'):
            sidecar = db_file + suffix
            if os.path.exists(sidecar):
                os.remove(sidecar)

        log_action('SETTINGS', f"Restauration de la base de données depuis {backup_path}")
        return jsonify({
            "success": True,
            "message": f"Restauration réussie depuis {os.path.basename(backup_path)}. Une sauvegarde de sécurité (avant restauration) a été créée."
        })
    except Exception as e:
        return jsonify({"error": f"Échec de la restauration: {str(e)}"}), 500
