#!/bin/bash
# TPOS Kiosk Setup Script
# Run on a fresh Debian 12 minimal install as root
# Usage: curl -sL https://your-server/tpos-kiosk-setup.sh | sudo bash
# Or: scp this file to the VM, then: sudo bash tpos-kiosk-setup.sh

set -e

TPOS_USER="tpos"
TPOS_DIR="/home/${TPOS_USER}/tpos"
APP_PORT=5000
KIOSK_URL="http://localhost:${APP_PORT}"

echo "============================================"
echo "  TPOS Kiosk Setup - Debian 12"
echo "============================================"

# ---- System packages ----
echo "[1/8] Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
  git \
  xorg openbox \
  firefox-esr \
  python3 python3-pip python3-venv \
  sqlite3 \
  cups printer-driver-gutenprint printer-driver-hpcups \
  printer-driver-brlaser printer-driver-cups-pdf \
  hplip \
  curl \
  alsa-utils pulseaudio \
  network-manager \
  lightdm 2>/dev/null || true

# Node 22 LTS (Vite 8 requires Node >= 20.19 / >= 22.12; Debian 12's apt nodejs is Node 18)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - 2>/dev/null
apt-get install -y -qq nodejs

# ---- Create user ----
echo "[2/8] Creating kiosk user..."
if ! id "$TPOS_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$TPOS_USER"
fi

# Restricted sudo: allow the kiosk user to power off / reboot ONLY.
# 'TPOS_ALLOW_SUDO=1' opts into a full sudo NOPASSWD for this user.
if [ "$TPOS_ALLOW_SUDO" = "1" ]; then
  echo "${TPOS_USER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/tpos
else
  echo "${TPOS_USER} ALL=(ALL) NOPASSWD: /usr/bin/systemctl poweroff, /usr/bin/systemctl reboot" > /etc/sudoers.d/tpos
fi
chmod 440 /etc/sudoers.d/tpos

# ---- Deploy app files ----
echo "[3/8] Deploying TPOS application..."
mkdir -p "$TPOS_DIR"

# Try git clone first, fall back to local copy
REPO_URL="${REPO_URL:-https://github.com/el-paradigm/tpos.git}"

if command -v git &>/dev/null && [ -n "$REPO_URL" ]; then
  echo "Cloning from $REPO_URL ..."
  git clone --depth 1 "$REPO_URL" /tmp/tpos-repo
  cp -r /tmp/tpos-repo/* "$TPOS_DIR/"
  rm -rf /tmp/tpos-repo
elif [ -d "/root/tpos" ]; then
  cp -r /root/tpos/* "$TPOS_DIR/"
elif [ -d "$(dirname "$0")/../backend" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  cp -r "$SCRIPT_DIR"/* "$TPOS_DIR/"
else
  echo "ERROR: TPOS source files not found!"
  echo "Set REPO_URL or copy files to /root/tpos/ and re-run."
  exit 1
fi
chown -R "${TPOS_USER}:${TPOS_USER}" "$TPOS_DIR"

# ---- Python backend setup ----
echo "[4/8] Installing Python dependencies..."
su - "$TPOS_USER" -c "
  cd '$TPOS_DIR/backend'
  python3 -m venv venv
  source venv/bin/activate
  pip install flask==3.1.3 flask-cors==6.0.5 -q
"

# ---- Frontend build ----
echo "[5/8] Building frontend..."
cd "$TPOS_DIR/frontend"
su - "$TPOS_USER" -c "
  cd '$TPOS_DIR/frontend'
  npm install -q 2>/dev/null
  npm run build -q 2>/dev/null
" || echo "Frontend build done (warnings ignored)"

# Serve the built SPA from Flask's /backend/static/
echo "      Deploying SPA to backend/static/ ..."
rm -rf "$TPOS_DIR/backend/static"
mkdir -p "$TPOS_DIR/backend/static"
cp -r "$TPOS_DIR/frontend/build/"* "$TPOS_DIR/backend/static/" 2>/dev/null || true
chown -R "${TPOS_USER}:${TPOS_USER}" "$TPOS_DIR/backend/static"

# ---- Kiosk auto-start configuration ----
echo "[6/8] Configuring kiosk auto-start..."

# Auto-login on tty1
mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${TPOS_USER} --noclear %I 38400 linux
EOF

# .bash_profile -> startx -> openbox -> autostart
cat > "/home/${TPOS_USER}/.bash_profile" << 'BASHPROF'
if [ -z "${DISPLAY}" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx
fi
BASHPROF
chown "${TPOS_USER}:${TPOS_USER}" "/home/${TPOS_USER}/.bash_profile"

# Openbox autostart
mkdir -p "/home/${TPOS_USER}/.config/openbox"
cat > "/home/${TPOS_USER}/.config/openbox/autostart" << OPENBOX
#!/bin/bash
# Start TPOS backend
cd ${TPOS_DIR}/backend
${TPOS_DIR}/backend/venv/bin/python app.py &
sleep 3

# Start Firefox kiosk
firefox --kiosk "${KIOSK_URL}" &
OPENBOX
chmod +x "/home/${TPOS_USER}/.config/openbox/autostart"
chown -R "${TPOS_USER}:${TPOS_USER}" "/home/${TPOS_USER}/.config"

# Openbox RC - no window decorations, no right-click menu
mkdir -p "/home/${TPOS_USER}/.config/openbox"
cat > "/home/${TPOS_USER}/.config/openbox/rc.xml" << 'OPENBOXRC'
<?xml version="1.0"?>
<openbox_config>
  <desktops>
    <number>1</number>
  </desktops>
  <resistance>
    <strength>10</strength>
  </resistance>
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
  </focus>
  <placement>
    <policy>UnderMouse</policy>
  </placement>
  <theme>
    <name>Clearlooks</name>
    <cornerRadius>0</cornerRadius>
  </theme>
  <applications>
    <application class="*">
      <decor>no</decor>
      <maximized>yes</maximized>
      <desktop>all</desktop>
    </application>
  </applications>
</openbox_config>
OPENBOXRC
chown -R "${TPOS_USER}:${TPOS_USER}" "/home/${TPOS_USER}/.config"

# ---- Disable screen blanking ----
echo "[7/8] Disabling screen blanking and sleep..."
cat > "/home/${TPOS_USER}/.xinitrc" << XINIT
xset s off
xset -dpms
xset s noblank
exec openbox-session
XINIT
chown "${TPOS_USER}:${TPOS_USER}" "/home/${TPOS_USER}/.xinitrc"

# ---- Printer drivers ----
echo "[8/8] Enabling CUPS for local printing..."
systemctl enable cups --now 2>/dev/null || true
usermod -a -G lpadmin "${TPOS_USER}"

# Clean up apt cache
apt-get clean

echo ""
echo "============================================"
echo "  TPOS Kiosk Setup Complete!"
echo "============================================"
echo ""
echo "Reboot the VM. It will boot directly into"
echo "the POS interface. No login required."
echo ""
echo "To generate a bootable live USB from this VM:"
echo "  1. Install Systemback:"
echo "     echo 'deb http://mirror.yandex.ru/mirrors/systemback/ stable main' > /etc/apt/sources.list.d/systemback.list"
echo "     apt-get update && apt-get install systemback"
echo "  2. Open Systemback GUI, create Live system"
echo "  3. It will generate a bootable .iso in /home/Systemback/"
echo ""
echo "Copy that ISO to a USB:"
echo "  sudo dd if=systemback.iso of=/dev/sdX bs=4M status=progress"
echo ""
