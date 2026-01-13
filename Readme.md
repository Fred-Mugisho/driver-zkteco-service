# ZKTeco Service - Synchronisation Automatique

Service de synchronisation des présences depuis appareils ZKTeco vers API backend.

**✅ Compatible : Linux, Windows, macOS**

## Installation Rapide

```bash
# 1. Cloner/Copier le projet
cd driver-zkteco-service

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer
cp .env.example .env
nano .env
```

**Configuration minimale :**
```bash
DEVICE_IP=192.168.1.XXX              # IP de votre appareil
API_URL=https://your-api.com/api/attendance
```

## Lancer le Service

```bash
python3 zkteco_service.py
```

Le service tourne en continu et synchronise automatiquement.

## Configuration en Tâche de Fond

### Linux (systemd)
```bash
sudo ./manage.sh install
sudo ./manage.sh start
sudo ./manage.sh enable
```

### Windows (Task Scheduler)

#### Étape 1 : Installer Python

Ouvrir PowerShell en **Administrateur** et exécuter :

```powershell
# Télécharger Python 3.12 (installer silencieux)
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"

# Installer Python (ajoute au PATH automatiquement)
Start-Process -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait

# Vérifier l'installation (fermer et rouvrir PowerShell d'abord)
python --version
```

**Ou manuellement :**
1. Télécharger Python sur https://www.python.org/downloads/
2. Lancer l'installateur
3. **IMPORTANT** : Cocher ☑ "Add Python to PATH"
4. Cliquer sur "Install Now"

#### Étape 2 : Installer le service ZKTeco

```powershell
# Créer le dossier
New-Item -ItemType Directory -Path "C:\zkteco-service" -Force

# Copier les fichiers du projet dans C:\zkteco-service
# (via clé USB, réseau, ou téléchargement)

# Aller dans le dossier
cd C:\zkteco-service

# Installer les dépendances Python
pip install -r requirements.txt

# Configurer le fichier .env
Copy-Item .env.example .env
notepad .env
```

**Modifier dans .env :**
```
DEVICE_IP=192.168.1.XXX        # IP de votre ZKTeco
API_URL=https://votre-api.com/api/attendance
```

#### Étape 3 : Tester le service

```powershell
# Tester manuellement
cd C:\zkteco-service
python zkteco_service.py
```

Si tout fonctionne (logs affichés), arrêter avec `Ctrl+C`.

#### Étape 4 : Créer la tâche planifiée

**Via PowerShell (Recommandé) :**

```powershell
# Trouver le chemin exact de Python
$pythonPath = (Get-Command python).Source
Write-Host "Python trouvé: $pythonPath"

# Créer la tâche planifiée
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "C:\zkteco-service\zkteco_service.py" -WorkingDirectory "C:\zkteco-service"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "ZKTeco_Sync_Service" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Service de synchronisation ZKTeco"

# Démarrer immédiatement
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"
```

**Via Interface Graphique :**

1. **Ouvrir le Planificateur de tâches**
   - Appuyer sur `Win + R`
   - Taper `taskschd.msc` et valider

2. **Créer une nouvelle tâche**
   - Cliquer sur "Créer une tâche..." (panneau de droite)

3. **Onglet Général**
   ```
   Nom : ZKTeco_Sync_Service
   Description : Service de synchronisation des présences ZKTeco
   ☑ Exécuter même si l'utilisateur n'est pas connecté
   ☑ Exécuter avec les autorisations maximales
   ```

4. **Onglet Déclencheurs** → Nouveau...
   ```
   Commencer la tâche : Au démarrage
   ☑ Activé
   ```

5. **Onglet Actions** → Nouveau...
   ```
   Action : Démarrer un programme
   Programme/script : C:\Users\[USER]\AppData\Local\Programs\Python\Python312\python.exe
   Arguments : zkteco_service.py
   Démarrer dans : C:\zkteco-service
   ```

   **Note :** Pour trouver le chemin de Python, exécuter dans PowerShell :
   ```powershell
   (Get-Command python).Source
   ```

6. **Onglet Conditions**
   ```
   ☐ Ne démarrer que si l'ordinateur est sur secteur (décocher)
   ```

7. **Onglet Paramètres**
   ```
   ☑ Autoriser l'exécution à la demande
   ☑ Si la tâche échoue, redémarrer toutes les : 1 minute
   ☑ Nombre de tentatives de redémarrage : 3
   ```

8. **Valider** avec OK

#### Commandes utiles

```powershell
# Démarrer la tâche
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"

# Vérifier le statut
Get-ScheduledTask -TaskName "ZKTeco_Sync_Service" | Get-ScheduledTaskInfo

# Arrêter la tâche
Stop-ScheduledTask -TaskName "ZKTeco_Sync_Service"

# Voir les logs du service
Get-Content C:\zkteco-service\zkteco_sync.log -Tail 50

# Supprimer la tâche (si besoin)
Unregister-ScheduledTask -TaskName "ZKTeco_Sync_Service" -Confirm:$false
```

#### Dépannage Windows

```powershell
# Vérifier si Python est installé
python --version

# Vérifier si les dépendances sont installées
pip list | Select-String "requests|schedule|pyzk"

# Tester le service manuellement
cd C:\zkteco-service
python zkteco_service.py

# Voir les logs Windows du planificateur
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*ZKTeco*"} | Select-Object -First 10
```

### Windows avec WSL (Alternative Recommandée)

WSL permet d'exécuter Linux directement sur Windows. Plus simple et plus stable.

#### Étape 1 : Installer WSL

Ouvrir PowerShell en **Administrateur** :

```powershell
# Installer WSL avec Ubuntu
wsl --install -d Ubuntu

# Redémarrer le PC si demandé
# Après redémarrage, Ubuntu s'ouvre et demande un nom d'utilisateur/mot de passe
```

#### Étape 2 : Configurer le service dans WSL

Ouvrir le terminal Ubuntu (WSL) :

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et pip
sudo apt install python3 python3-pip python3-venv -y

# Créer le dossier du service
mkdir -p ~/zkteco-service
cd ~/zkteco-service

# Copier les fichiers du projet (depuis Windows)
# Les fichiers Windows sont accessibles via /mnt/c/
cp -r /mnt/c/Users/VOTRE_USER/Desktop/zkteco-service/* .

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer
cp .env.example .env
nano .env   # Modifier DEVICE_IP et API_URL
```

#### Étape 3 : Tester le service

```bash
cd ~/zkteco-service
source venv/bin/activate
python3 zkteco_service.py
```

#### Étape 4 : Configurer le démarrage automatique

**Option A : Via systemd (WSL2 avec systemd activé)**

```bash
# Vérifier si systemd est actif
systemctl --version

# Si actif, utiliser manage.sh
chmod +x manage.sh
sudo ./manage.sh install
sudo ./manage.sh start
sudo ./manage.sh enable
```

**Option B : Via script de démarrage Windows**

Créer un fichier `start_zkteco_wsl.bat` sur le Bureau Windows :

```batch
@echo off
wsl -d Ubuntu -u root -- bash -c "cd /home/VOTRE_USER/zkteco-service && source venv/bin/activate && python3 zkteco_service.py"
```

Puis créer une tâche planifiée Windows pour exécuter ce `.bat` au démarrage :

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\VOTRE_USER\Desktop\start_zkteco_wsl.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "ZKTeco_WSL_Service" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Service ZKTeco via WSL"
```

**Option C : Via crontab @reboot**

```bash
# Ouvrir crontab
crontab -e

# Ajouter cette ligne à la fin
@reboot cd /home/VOTRE_USER/zkteco-service && source venv/bin/activate && python3 zkteco_service.py >> /home/VOTRE_USER/zkteco-service/cron.log 2>&1
```

#### Commandes utiles WSL

```bash
# Depuis PowerShell Windows
wsl --list --verbose          # Voir les distributions installées
wsl -d Ubuntu                 # Ouvrir Ubuntu
wsl --shutdown                # Arrêter WSL

# Depuis Ubuntu (WSL)
source ~/zkteco-service/venv/bin/activate
python3 ~/zkteco-service/zkteco_service.py    # Lancer manuellement
tail -f ~/zkteco-service/zkteco_sync.log      # Voir les logs
```

#### Avantages de WSL

| WSL | Python natif Windows |
|-----|---------------------|
| ✅ Environnement Linux natif | ❌ Problèmes de compatibilité possibles |
| ✅ Python préinstallé | ❌ Installation manuelle requise |
| ✅ Utilise manage.sh et systemd | ❌ Task Scheduler uniquement |
| ✅ Plus stable pour les services | ❌ Gestion des processus complexe |
| ✅ Même comportement que serveur Linux | ❌ Comportement différent |

### macOS
```bash
# Lancer manuellement
./manage.sh run

# Ou directement
python3 zkteco_service.py
```

Pour le démarrage automatique, utilisez launchd (voir documentation macOS).

## Structure

```
driver-zkteco-service/
├── zkteco_service.py          # Service principal
├── config.py                  # Configuration
├── .env                       # Paramètres (à créer)
├── .env.example               # Template
├── requirements.txt           # Dépendances
├── manage.sh                  # Script Linux/macOS
└── zkteco_attendance.service  # Service systemd
```

## Configuration (.env)

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| `DEVICE_IP` | IP appareil ZKTeco | 192.168.1.100 |
| `DEVICE_PORT` | Port | 4370 |
| `API_URL` | URL API backend | - |
| `SYNC_INTERVAL` | Intervalle (minutes) | 5 |
| `MAX_RETRIES` | Nombre retries | 3 |
| `LOG_FILE` | Fichier log | zkteco_sync.log |
| `API_ENDPOINT_SEND_MAIL` | API envoi email (optionnel) | - |
| `RECEIVERS_EMAILS` | Destinataires emails (optionnel) | - |
| `EMAIL_HOST` | Serveur SMTP (optionnel) | - |
| `EMAIL_HOST_USER` | Utilisateur SMTP (optionnel) | - |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP (optionnel) | - |

## Notifications Email (Optionnel)

Le service peut envoyer des notifications email en cas d'erreur critique ou d'échec de synchronisation.

**Configuration :**
1. Configurer les paramètres email dans `.env`:
```bash
API_ENDPOINT_SEND_MAIL=https://your-api.com/send-email
RECEIVERS_EMAILS=admin@example.com,it@example.com
EMAIL_HOST=smtp.example.com
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your_password
```

2. Le fichier `notification.py` doit être présent dans le projet.

**Notifications envoyées :**
- Échec de synchronisation après toutes les tentatives de retry
- Erreurs critiques durant le processus

**Format des emails :**
Les emails sont automatiquement formatés en HTML avec :
- En-tête coloré selon le type d'alerte (rouge pour erreurs, vert pour succès)
- Tableau structuré avec les informations clés
- Design responsive et professionnel
- Compatible tous clients email

Si les paramètres ne sont pas configurés, le service fonctionne normalement sans envoyer de notifications.

## Logs

```bash
tail -f zkteco_sync.log
```

## Dépannage

### Erreur connexion appareil
```bash
# Vérifier IP
ping 192.168.1.XXX

# Voir logs
tail -f zkteco_sync.log
```

### Erreur API
- Vérifier `API_URL` dans `.env`
- Tester l'API manuellement
- Vérifier connexion réseau

## Format Données

POST JSON vers `API_URL` :
```json
[
  {
    "matricule": "12345",
    "timestamp": "2026-01-06T10:30:00"
  }
]
```

## Commandes (Linux/macOS)

```bash
./manage.sh install    # Installer
./manage.sh run        # Lancer
./manage.sh start      # Démarrer (systemd)
./manage.sh stop       # Arrêter (systemd)
./manage.sh status     # Statut (systemd)
./manage.sh logs       # Logs (systemd)
```
