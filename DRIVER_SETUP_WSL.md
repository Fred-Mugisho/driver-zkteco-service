# Configuration ZKTeco Service sur WSL (Windows Subsystem for Linux)

Guide complet pour installer et configurer le service ZKTeco sur WSL avec :
- Démarrage automatique au boot Windows
- Persistance en mode veille
- Redémarrage automatique après reboot

---

## Prérequis

- Windows 10 (version 2004+) ou Windows 11
- Droits administrateur
- Connexion internet pour l'installation

---

## Étape 1 : Installer WSL2 avec Ubuntu

### 1.1 Activer les fonctionnalités Windows requises

Ouvrir **PowerShell en Administrateur** (clic droit → Exécuter en tant qu'administrateur) :

```powershell
# Activer la fonctionnalité WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Activer la fonctionnalité Machine Virtuelle
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**IMPORTANT : Redémarrer le PC maintenant !**

```powershell
shutdown /r /t 0
```

### 1.2 Après le redémarrage - Installer le kernel WSL2

Ouvrir à nouveau **PowerShell en Administrateur** :

```powershell
# Télécharger et installer le kernel WSL2
Invoke-WebRequest -Uri "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi" -OutFile "$env:TEMP\wsl_update.msi"
Start-Process msiexec.exe -ArgumentList "/i `"$env:TEMP\wsl_update.msi`" /quiet" -Wait

# Définir WSL2 comme version par défaut
wsl --set-default-version 2
```

### 1.3 Installer Ubuntu

```powershell
# Installer Ubuntu
wsl --install -d Ubuntu

# Si erreur "wsl n'est pas reconnu", fermer et rouvrir PowerShell en Admin
# Puis réessayer la commande
```

**Alternative si la commande wsl ne fonctionne toujours pas :**

1. Ouvrir le **Microsoft Store** (menu Démarrer → Microsoft Store)
2. Rechercher "Ubuntu"
3. Cliquer sur "Ubuntu 22.04 LTS" (ou la version disponible)
4. Cliquer sur "Obtenir" puis "Installer"
5. Une fois installé, cliquer sur "Ouvrir"

### 1.4 Premier lancement d'Ubuntu

Après l'installation, Ubuntu s'ouvre et demande de créer un utilisateur :

```
Installing, this may take a few minutes...
Please create a default UNIX user account...
Enter new UNIX username: zkteco
New password: ********
Retype new password: ********
```

> **Note :** Retenez ce mot de passe, il sera nécessaire pour `sudo`.

### 1.5 Vérifier l'installation

```powershell
# Dans PowerShell (pas Ubuntu)
wsl --list --verbose
```

Résultat attendu :
```
  NAME      STATE           VERSION
* Ubuntu    Running         2
```

**Si VERSION = 1, convertir en WSL2 :**
```powershell
wsl --set-version Ubuntu 2
```

---

## Étape 2 : Configurer Ubuntu (WSL)

### 2.1 Ouvrir le terminal Ubuntu

Depuis le menu Démarrer, chercher "Ubuntu" et l'ouvrir.

### 2.2 Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Installer Python et les outils nécessaires

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### 2.4 Vérifier Python

```bash
python3 --version
pip3 --version
```

---

## Étape 3 : Installer le service ZKTeco

### 3.1 Créer le dossier du service

```bash
mkdir -p ~/zkteco-service
cd ~/zkteco-service
```

### 3.2 Copier les fichiers du projet

**Option A : Depuis un dossier Windows**

```bash
# Les fichiers Windows sont accessibles via /mnt/c/
# Exemple : copier depuis le Bureau
cp -r /mnt/c/Users/VOTRE_USER/Desktop/driver-zkteco-service/* ~/zkteco-service/

# Ou depuis une clé USB (généralement /mnt/d/ ou /mnt/e/)
cp -r /mnt/d/driver-zkteco-service/* ~/zkteco-service/
```

**Option B : Depuis Git**

```bash
git clone https://votre-repo/driver-zkteco-service.git ~/zkteco-service
cd ~/zkteco-service
```

### 3.3 Créer l'environnement virtuel Python

```bash
cd ~/zkteco-service
python3 -m venv venv
source venv/bin/activate
```

### 3.4 Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3.5 Configurer le fichier .env

```bash
cp .env.example .env
nano .env
```

**Modifier les valeurs suivantes :**

```bash
# Appareil ZKTeco (OBLIGATOIRE)
DEVICE_IP=192.168.1.XXX          # Remplacer par l'IP de votre appareil
DEVICE_PORT=4370

# API Backend (OBLIGATOIRE)
API_URL=https://votre-api.com/api/attendance

# Synchronisation
SYNC_INTERVAL=5                   # Intervalle en minutes

# Notifications Email (OPTIONNEL)
API_ENDPOINT_SEND_MAIL=https://votre-api.com/send-email
RECEIVERS_EMAILS=admin@example.com
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password
```

Sauvegarder : `Ctrl+O`, `Enter`, puis `Ctrl+X`

### 3.6 Tester le service

```bash
cd ~/zkteco-service
source venv/bin/activate
python3 zkteco_service.py
```

Si les logs s'affichent correctement, arrêter avec `Ctrl+C`.

---

## Étape 4 : Activer systemd dans WSL2

### 4.1 Vérifier si systemd est disponible

```bash
systemctl --version
```

Si une erreur s'affiche, activer systemd :

### 4.2 Activer systemd

```bash
sudo nano /etc/wsl.conf
```

Ajouter ou modifier :

```ini
[boot]
systemd=true

[interop]
enabled=true
appendWindowsPath=true
```

Sauvegarder : `Ctrl+O`, `Enter`, puis `Ctrl+X`

### 4.3 Redémarrer WSL

**Dans PowerShell (Windows) :**

```powershell
wsl --shutdown
wsl -d Ubuntu
```

### 4.4 Vérifier que systemd fonctionne

```bash
systemctl --version
systemctl status
```

---

## Étape 5 : Créer le service systemd

### 5.1 Créer le fichier de service

```bash
sudo nano /etc/systemd/system/zkteco.service
```

Coller le contenu suivant :

```ini
[Unit]
Description=ZKTeco Attendance Sync Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=zkteco
Group=zkteco
WorkingDirectory=/home/zkteco/zkteco-service
Environment="PATH=/home/zkteco/zkteco-service/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/zkteco/zkteco-service/venv/bin/python3 /home/zkteco/zkteco-service/zkteco_service.py
Restart=always
RestartSec=10
StandardOutput=append:/home/zkteco/zkteco-service/zkteco_sync.log
StandardError=append:/home/zkteco/zkteco-service/zkteco_sync.log

[Install]
WantedBy=multi-user.target
```

> **Important :** Remplacer `zkteco` par votre nom d'utilisateur WSL si différent.

Sauvegarder : `Ctrl+O`, `Enter`, puis `Ctrl+X`

### 5.2 Recharger systemd

```bash
sudo systemctl daemon-reload
```

### 5.3 Activer et démarrer le service

```bash
# Activer le démarrage automatique
sudo systemctl enable zkteco.service

# Démarrer le service
sudo systemctl start zkteco.service

# Vérifier le statut
sudo systemctl status zkteco.service
```

### 5.4 Commandes de gestion du service

```bash
# Démarrer
sudo systemctl start zkteco.service

# Arrêter
sudo systemctl stop zkteco.service

# Redémarrer
sudo systemctl restart zkteco.service

# Voir le statut
sudo systemctl status zkteco.service

# Voir les logs
journalctl -u zkteco.service -f

# Ou
tail -f ~/zkteco-service/zkteco_sync.log
```

---

## Étape 6 : Démarrage automatique de WSL au boot Windows

### 6.1 Créer le script de démarrage

**Dans PowerShell (Windows) :**

```powershell
# Créer le dossier pour les scripts
New-Item -ItemType Directory -Path "C:\Scripts" -Force

# Créer le script de démarrage WSL
@"
@echo off
REM Script de démarrage automatique WSL + ZKTeco Service
REM Ce script démarre WSL en arrière-plan au boot Windows

REM Démarrer WSL Ubuntu en arrière-plan
start /B wsl -d Ubuntu -u root -- bash -c "systemctl start zkteco.service && tail -f /dev/null"

REM Alternative : démarrer WSL et garder actif
REM wsl -d Ubuntu -u root -- bash -c "while true; do sleep 3600; done"
"@ | Out-File -FilePath "C:\Scripts\start_wsl_zkteco.bat" -Encoding ASCII

# Vérifier le fichier créé
Get-Content "C:\Scripts\start_wsl_zkteco.bat"
```

### 6.2 Créer la tâche planifiée Windows

```powershell
# Supprimer l'ancienne tâche si elle existe
Unregister-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart" -Confirm:$false -ErrorAction SilentlyContinue

# Créer la nouvelle tâche planifiée
$action = New-ScheduledTaskAction -Execute "C:\Scripts\start_wsl_zkteco.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask `
    -TaskName "WSL_ZKTeco_AutoStart" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Démarre automatiquement WSL et le service ZKTeco au démarrage de Windows"

# Vérifier la création
Get-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart"
```

### 6.3 Tester la tâche planifiée

```powershell
# Démarrer la tâche manuellement pour tester
Start-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart"

# Vérifier le statut
Get-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart" | Get-ScheduledTaskInfo
```

---

## Étape 7 : Empêcher la mise en veille de WSL

### 7.1 Configurer Windows pour garder WSL actif

**Dans PowerShell (Administrateur) :**

```powershell
# Désactiver la mise en veille des connexions réseau
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

# Ou créer un profil d'alimentation personnalisé
powercfg -duplicatescheme 381b4222-f694-41f0-9685-ff5bb260df2e 12345678-1234-1234-1234-123456789012
powercfg -changename 12345678-1234-1234-1234-123456789012 "ZKTeco Service" "Profil pour maintenir WSL actif"
powercfg -setactive 12345678-1234-1234-1234-123456789012
```

### 7.2 Alternative : Script de keep-alive

**Créer un script PowerShell qui maintient WSL actif :**

```powershell
# Créer le script keep-alive
@"
# Script keep-alive pour WSL
while (`$true) {
    # Vérifier si WSL est en cours d'exécution
    `$wslStatus = wsl -l -v | Select-String "Ubuntu.*Running"

    if (-not `$wslStatus) {
        Write-Host "[`$(Get-Date)] WSL arrêté, redémarrage..."
        wsl -d Ubuntu -u root -- bash -c "systemctl start zkteco.service"
    }

    # Attendre 5 minutes
    Start-Sleep -Seconds 300
}
"@ | Out-File -FilePath "C:\Scripts\wsl_keepalive.ps1" -Encoding UTF8
```

### 7.3 Créer une tâche pour le keep-alive

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Scripts\wsl_keepalive.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask `
    -TaskName "WSL_KeepAlive" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Maintient WSL actif en permanence"
```

---

## Étape 8 : Configuration finale - Résumé

### 8.1 Vérifier toutes les configurations

**Dans Ubuntu (WSL) :**

```bash
# Vérifier le service
sudo systemctl status zkteco.service

# Vérifier les logs
tail -20 ~/zkteco-service/zkteco_sync.log

# Vérifier la configuration
cat ~/zkteco-service/.env | grep -E "DEVICE_IP|API_URL"
```

**Dans PowerShell (Windows) :**

```powershell
# Vérifier WSL
wsl --list --verbose

# Vérifier les tâches planifiées
Get-ScheduledTask | Where-Object {$_.TaskName -like "*WSL*" -or $_.TaskName -like "*ZKTeco*"}

# Vérifier le statut des tâches
Get-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart" | Get-ScheduledTaskInfo
```

### 8.2 Test complet

1. **Redémarrer Windows** pour tester le démarrage automatique
2. **Vérifier après redémarrage** que le service tourne :

```powershell
# Dans PowerShell
wsl -d Ubuntu -u root -- systemctl status zkteco.service
```

3. **Mettre en veille** puis réveiller le PC
4. **Vérifier** que le service est toujours actif

---

## Commandes Utiles - Aide-Mémoire

### Gestion WSL (PowerShell Windows)

```powershell
wsl --list --verbose              # Liste des distributions
wsl -d Ubuntu                     # Ouvrir Ubuntu
wsl --shutdown                    # Arrêter toutes les distributions
wsl --terminate Ubuntu            # Arrêter Ubuntu uniquement
wsl -d Ubuntu -u root -- <cmd>    # Exécuter une commande en root
```

### Gestion du service (Ubuntu WSL)

```bash
sudo systemctl start zkteco.service     # Démarrer
sudo systemctl stop zkteco.service      # Arrêter
sudo systemctl restart zkteco.service   # Redémarrer
sudo systemctl status zkteco.service    # Statut
sudo systemctl enable zkteco.service    # Activer au boot
sudo systemctl disable zkteco.service   # Désactiver au boot
```

### Logs

```bash
# Logs du service
tail -f ~/zkteco-service/zkteco_sync.log

# Logs systemd
journalctl -u zkteco.service -f
journalctl -u zkteco.service --since "1 hour ago"
```

### Tâches planifiées Windows

```powershell
# Lister
Get-ScheduledTask | Where-Object {$_.TaskName -like "*ZKTeco*" -or $_.TaskName -like "*WSL*"}

# Démarrer manuellement
Start-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart"

# Arrêter
Stop-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart"

# Supprimer
Unregister-ScheduledTask -TaskName "WSL_ZKTeco_AutoStart" -Confirm:$false
```

---

## Dépannage

### WSL ne démarre pas automatiquement

```powershell
# Vérifier les logs de la tâche planifiée
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" |
    Where-Object {$_.Message -like "*WSL*" -or $_.Message -like "*ZKTeco*"} |
    Select-Object -First 10
```

### Le service ne démarre pas dans WSL

```bash
# Vérifier les erreurs systemd
sudo journalctl -u zkteco.service -n 50

# Vérifier les permissions
ls -la ~/zkteco-service/

# Tester manuellement
cd ~/zkteco-service
source venv/bin/activate
python3 zkteco_service.py
```

### Problème de connexion à l'appareil ZKTeco

```bash
# Tester la connectivité réseau depuis WSL
ping 192.168.1.XXX

# Si ping échoue, vérifier le pare-feu Windows
# Ou essayer d'accéder depuis Windows directement
```

### WSL perd la connexion réseau après veille

```bash
# Redémarrer le réseau dans WSL
sudo ip link set eth0 down
sudo ip link set eth0 up

# Ou redémarrer WSL complètement (depuis PowerShell)
wsl --shutdown
wsl -d Ubuntu
```

---

## Résumé de l'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINDOWS                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tâche Planifiée: WSL_ZKTeco_AutoStart                   │  │
│  │  Déclenche: Au démarrage Windows                         │  │
│  │  Action: Démarre WSL + service ZKTeco                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      WSL2 (Ubuntu)                        │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  systemd: zkteco.service                           │  │  │
│  │  │  • Restart=always                                  │  │  │
│  │  │  • Démarre automatiquement avec systemd            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                          │                                │  │
│  │                          ▼                                │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  zkteco_service.py                                 │  │  │
│  │  │  • Synchronise toutes les X minutes                │  │  │
│  │  │  • Envoie notifications email si erreur            │  │  │
│  │  │  • Logs dans zkteco_sync.log                       │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Appareil ZKTeco   │
                    │   192.168.1.XXX     │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    API Backend      │
                    │  /api/attendance    │
                    └─────────────────────┘
```

---

## Checklist d'Installation

- [ ] WSL2 installé avec Ubuntu
- [ ] Python 3 installé dans WSL
- [ ] Fichiers du projet copiés dans `~/zkteco-service/`
- [ ] Environnement virtuel créé et dépendances installées
- [ ] Fichier `.env` configuré avec les bonnes valeurs
- [ ] Test manuel du service réussi
- [ ] systemd activé dans WSL
- [ ] Service systemd créé et activé
- [ ] Script de démarrage Windows créé
- [ ] Tâche planifiée Windows créée
- [ ] Test après redémarrage Windows réussi
- [ ] Test après mise en veille réussi

---

**Document créé le :** $(date +%d/%m/%Y)
**Version :** 1.0
