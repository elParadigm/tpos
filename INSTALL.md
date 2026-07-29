# TPOS — Guide d'installation Kiosk

Crée une clé USB bootable qui démarre directement sur l'interface TPOS.

---

## Étape 1 : Créer une VM Debian sur Windows

1. Téléchargez **VirtualBox** : https://www.virtualbox.org/
2. Téléchargez **Debian 12 netinstall** : https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.10.0-amd64-netinst.iso
3. Créez une VM dans VirtualBox :
   - Nom : `tpos`
   - RAM : **2048 Mo**
   - Disque : **20 Go**
   - Réseau : **NAT** ou **Accès par pont**
4. Démarrez la VM avec l'ISO Debian
5. Installation :
   - Language : **English**
   - Hostname : `tpos`
   - Root password : `tpos`
   - User : `tpos`, password : `tpos`
   - Partition : **Guided - use entire disk**
   - Software selection : **décochez TOUT** (on installe nous-mêmes après)
   - Grub : **Yes**

---

## Étape 2 : Mettre TPOS sur GitHub

Depuis votre Windows, dans le dossier du projet :

```bash
cd C:\Users\votre-nom\tpos
git init
git add .
git commit -m "Initial commit"
# Créez un repo sur github.com, puis :
git remote add origin https://github.com/votre-compte/tpos.git
git branch -M main
git push -u origin main
```

> Si vous n'avez pas git : https://git-scm.com/downloads/win

---

## Étape 3 : Lancer le setup dans la VM

Dans la VM Debian, ouvrez un terminal et tapez :

```bash
apt update && apt install -y curl
curl -sL https://raw.githubusercontent.com/votre-compte/tpos/main/tools/tpos-kiosk-setup.sh | bash
```

Le script fait tout automatiquement :
- Installe Xorg, Firefox, Python, Node.js, CUPS, drivers imprimante
- Clone l'app depuis GitHub
- Configure le backend et build le frontend
- Active le démarrage automatique en kiosk (pas de login)

---

## Étape 4 : Tester dans la VM

```bash
reboot
```

La VM redémarre directement sur l'interface POS. Si besoin d'un terminal :
- **Ctrl+Alt+F2** → terminal
- **Ctrl+Alt+F1** → retour au kiosk

---

## Étape 5 : Générer l'ISO bootable

**Dans la VM**, après avoir testé que tout fonctionne :

```bash
# Installer Systemback
echo 'deb http://mirror.yandex.ru/mirrors/systemback/ stable main' > /etc/apt/sources.list.d/systemback.list
curl -fsSL https://mirror.yandex.ru/mirrors/systemback/key.asc | apt-key add -
apt update && apt install -y systemback
```

Ouvrez Systemback depuis le terminal :

```bash
systemback-sustart
```

1. Cliquez sur **"Live system"**
2. **"Create new"**
3. Donnez un nom (ex: `tpos-kiosk`)
4. **"Create"** (ça prend 5-10 minutes)
5. Le fichier `.iso` et `.sblive` sont créés dans `/home/Systemback/`

---

## Étape 6 : Copier l'ISO vers Windows

**Option A — Shared folder VirtualBox :**
- Dans VirtualBox : Périphériques → Dossiers partagés → Ajouter un dossier
- Choisissez un dossier sur Windows (ex: `C:\Users\votre-nom\Desktop\ISO`)
- Cochez **"Montage automatique"**
- Dans la VM :
  ```bash
  cp /home/Systemback/tpos-kiosk.iso /media/sf_ISO/
  ```

**Option B — Clé USB :**
- Branchez une clé USB dans Windows
- Dans VirtualBox : Périphériques → USB → sélectionnez votre clé
- Dans la VM :
  ```bash
  lsblk  # repérez votre clé (ex: /dev/sdb)
  dd if=/home/Systemback/tpos-kiosk.iso of=/dev/sdb bs=4M status=progress
  ```

---

## Étape 7 : Utiliser l'ISO sur une vraie machine

1. Copiez `tpos-kiosk.iso` sur une clé USB avec **Rufus** (https://rufus.ie/)
2. Branchez la clé dans le laptop du client
3. Démarrez et appuyez sur **F12** (ou F2, F10, Esc) pour choisir la clé USB
4. Systemback propose :
   - **"Live System"** → test sans installer
   - **"Installation"** → installer sur le disque dur

---

## Imprimante Canon LBP3010B

Le script installe les drivers génériques. Pour la Canon, il faut un pilote spécifique :

```bash
# Télécharger le driver CAPT Canon depuis un navigateur dans la VM :
# Cherchez "Canon LBP3010 Linux driver CAPT"
# Prenez la version .deb pour Ubuntu/Debian 64-bit

sudo dpkg -i cndrvcups-common_*.deb
sudo dpkg -i cndrvcups-capt_*.deb
sudo systemctl restart cups
```

Puis dans TPOS → Configuration → Format : choisissez **A4**.

---

## Notes utiles

| Action | Comment |
|--------|---------|
| Mot de passe utilisateur | `tpos` |
| Mot de passe root | `tpos` |
| Dossier de l'app | `/home/tpos/tpos/` |
| Éteindre le système | Icône ⏻ en haut à droite |
| Terminal en kiosk | **Ctrl+Alt+F2** |
| Retour au kiosk | **Ctrl+Alt+F1** |
| Mise à jour de l'app | `cd /home/tpos/tpos && git pull && cd frontend && npm run build` |
