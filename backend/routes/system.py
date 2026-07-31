import subprocess
from flask import Blueprint, jsonify
from auth import login_required

system_bp = Blueprint('system', __name__)

# The kiosk runs the backend as an unprivileged user. systemctl poweroff /
# reboot would fail for that user without polkit. Use a sudoers rule that
# allows ONLY these two commands (see tools/tpos-kiosk-setup.sh), falling
# back to a direct systemctl call if sudo is not available (e.g. dev on a
# root shell).
def _run_systemctl(action):
    try:
        # 'sudo -n systemctl <action>' — NOPASSWD rule granted by the setup
        subprocess.run(['sudo', '-n', 'systemctl', action], check=True, timeout=10)
        return True, None
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['systemctl', action], check=True, timeout=10)
            return True, None
        except subprocess.CalledProcessError as e:
            return False, f'Erreur: {e}'
        except FileNotFoundError:
            return False, 'Commande systemctl introuvable'


@system_bp.route('/system/shutdown', methods=['POST'])
@login_required
def system_shutdown():
    ok, err = _run_systemctl('poweroff')
    if not ok:
        return jsonify({'error': err}), 500
    return jsonify({'message': 'shutdown initiated'})


@system_bp.route('/system/reboot', methods=['POST'])
@login_required
def system_reboot():
    ok, err = _run_systemctl('reboot')
    if not ok:
        return jsonify({'error': err}), 500
    return jsonify({'message': 'reboot initiated'})
