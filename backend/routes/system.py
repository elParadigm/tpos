import subprocess
from flask import Blueprint, jsonify

system_bp = Blueprint('system', __name__)

@system_bp.route('/system/shutdown', methods=['POST'])
def system_shutdown():
    try:
        subprocess.run(['systemctl', 'poweroff'], check=True, timeout=10)
        return jsonify({'message': 'shutdown initiated'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Erreur: {e}'}), 500
    except FileNotFoundError:
        return jsonify({'error': 'Commande systemctl introuvable'}), 500

@system_bp.route('/system/reboot', methods=['POST'])
def system_reboot():
    try:
        subprocess.run(['systemctl', 'reboot'], check=True, timeout=10)
        return jsonify({'message': 'reboot initiated'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Erreur: {e}'}), 500
    except FileNotFoundError:
        return jsonify({'error': 'Commande systemctl introuvable'}), 500
