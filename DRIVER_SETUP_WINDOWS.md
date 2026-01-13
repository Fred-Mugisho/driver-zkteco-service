# Configuration ZKTeco Service sur Windows (Léger)

Guide optimisé pour machines Windows avec peu de ressources (4 Go RAM, HDD, 2 cœurs).

**Avantages :** Léger, pas de virtualisation, démarrage rapide, faible consommation mémoire.

---

## Resume Rapide (Copier-Coller)

```powershell
# 1. Installer Python (PowerShell Admin)
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe" -OutFile "$env:TEMP\python.exe"
Start-Process "$env:TEMP\python.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

# 2. Fermer et rouvrir PowerShell, puis :
mkdir C:\zkteco-service
cd C:\zkteco-service
# Copier les fichiers du projet ici

# 3. Creer venv et installer dependances
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Configurer
copy .env.example .env
notepad .env

# 5. Creer tache planifiee (avec venv)
$py = "C:\zkteco-service\venv\Scripts\python.exe"
$action = New-ScheduledTaskAction -Execute $py -Argument "zkteco_service.py" -WorkingDirectory "C:\zkteco-service"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Hours 0)
Register-ScheduledTask -TaskName "ZKTeco_Sync_Service" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "SYSTEM"

# 6. Demarrer
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"
```

---

## Étape 1 : Installer Python

### Option A : Installation automatique (Recommandé)

Ouvrir **PowerShell en Administrateur** :

```powershell
# Télécharger Python 3.12
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"

# Installer silencieusement
Start-Process -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait

Write-Host "Installation terminée. Fermez et rouvrez PowerShell."
```

**IMPORTANT : Fermer et rouvrir PowerShell après l'installation !**

### Option B : Installation manuelle

1. Télécharger : https://www.python.org/downloads/
2. Lancer l'installateur
3. **COCHER** : ☑ "Add Python to PATH" (très important !)
4. Cliquer "Install Now"

### Vérifier l'installation

```powershell
python --version
pip --version
```

Résultat attendu :
```
Python 3.12.0
pip 23.x.x
```

---

## Etape 2 : Installer le service ZKTeco

### 2.1 Creer le dossier

```powershell
# Creer le dossier
New-Item -ItemType Directory -Path "C:\zkteco-service" -Force

# Aller dans le dossier
cd C:\zkteco-service
```

### 2.2 Copier les fichiers

Copier tous les fichiers du projet dans `C:\zkteco-service\` :
- Via cle USB
- Via reseau partage
- Via telechargement

**Fichiers necessaires :**
```
C:\zkteco-service\
├── zkteco_service.py
├── config.py
├── notification.py
├── .env.example
├── requirements.txt
└── pyzk_lib\
```

### 2.3 Creer un environnement virtuel (Recommande)

```powershell
cd C:\zkteco-service

# Creer le venv
python -m venv venv

# Activer le venv
.\venv\Scripts\Activate.ps1

# Installer les dependances dans le venv
pip install -r requirements.txt
```

> **Note :** L'environnement virtuel isole les dependances du projet et evite les conflits avec d'autres applications Python.

### 2.3b Alternative : Installation globale (Sans venv)

```powershell
cd C:\zkteco-service
pip install -r requirements.txt
```

### 2.4 Configurer le fichier .env

```powershell
# Créer le fichier de configuration
Copy-Item .env.example .env

# Ouvrir pour modification
notepad .env
```

**Modifier ces valeurs dans .env :**

```ini
# OBLIGATOIRE - IP de votre appareil ZKTeco
DEVICE_IP=192.168.1.XXX

# OBLIGATOIRE - URL de votre API backend
API_URL=https://votre-api.com/api/attendance

# OPTIONNEL - Notifications email
API_ENDPOINT_SEND_MAIL=https://votre-api.com/send-email
RECEIVERS_EMAILS=admin@example.com
```

Sauvegarder et fermer.

---

## Etape 3 : Tester le service

### Avec venv (Recommande)
```powershell
cd C:\zkteco-service
.\venv\Scripts\Activate.ps1
python zkteco_service.py
```

### Sans venv
```powershell
cd C:\zkteco-service
python zkteco_service.py
```

**Resultat attendu :**
```
2026-01-07 10:00:00 - INFO - === Service ZKTeco ===
2026-01-07 10:00:00 - INFO - OS: Windows
2026-01-07 10:00:00 - INFO - Appareil: 192.168.1.XXX:4370
2026-01-07 10:00:00 - INFO - API: https://votre-api.com/api/attendance
2026-01-07 10:00:00 - INFO - Intervalle: 5 min
2026-01-07 10:00:00 - INFO - === Debut sync ===
```

Arreter avec `Ctrl+C` si tout fonctionne.

---

## Etape 4 : Creer la tache planifiee

### Option A : Via PowerShell - Avec venv (Recommande)

```powershell
# Utiliser Python du venv
$pythonPath = "C:\zkteco-service\venv\Scripts\python.exe"
Write-Host "Python (venv): $pythonPath"

# Creer la tache
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "zkteco_service.py" `
    -WorkingDirectory "C:\zkteco-service"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "ZKTeco_Sync_Service" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Service de synchronisation ZKTeco - Demarre au boot"

# Demarrer immediatement
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"

Write-Host "Tache creee et demarree !"
```

### Option A bis : Via PowerShell - Sans venv

```powershell
# Trouver Python global
$pythonPath = (Get-Command python).Source
Write-Host "Python: $pythonPath"

# Creer la tache
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "zkteco_service.py" `
    -WorkingDirectory "C:\zkteco-service"

$trigger = New-ScheduledTaskTrigger -AtStartup

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName "ZKTeco_Sync_Service" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Service de synchronisation ZKTeco - Demarre au boot"

# Demarrer immediatement
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"

Write-Host "Tache creee et demarree !"
```

### Option B : Via Interface Graphique

1. **Ouvrir le Planificateur de taches**
   - `Win + R` → taper `taskschd.msc` → OK

2. **Creer une tache**
   - Panneau droit → "Creer une tache..."

3. **Onglet General**
   ```
   Nom : ZKTeco_Sync_Service
   Description : Service de synchronisation ZKTeco

   ☑ Executer meme si l'utilisateur n'est pas connecte
   ☑ Executer avec les autorisations maximales
   ```

4. **Onglet Declencheurs** → Nouveau
   ```
   Commencer la tache : Au demarrage
   ☑ Active
   ```

5. **Onglet Actions** → Nouveau

   **Avec venv (Recommande) :**
   ```
   Action : Demarrer un programme

   Programme/script : C:\zkteco-service\venv\Scripts\python.exe
   Arguments : zkteco_service.py
   Demarrer dans : C:\zkteco-service
   ```

   **Sans venv :**
   ```
   Action : Demarrer un programme

   Programme/script : [chemin vers python.exe global]
   Arguments : zkteco_service.py
   Demarrer dans : C:\zkteco-service
   ```

   **Pour trouver le chemin de Python global :**
   ```powershell
   (Get-Command python).Source
   ```
   Exemple : `C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe`

6. **Onglet Conditions**
   ```
   ☐ Ne demarrer que si l'ordinateur est sur secteur (DECOCHER)
   ☐ Arreter si l'ordinateur passe sur batterie (DECOCHER)
   ```

7. **Onglet Parametres**
   ```
   ☑ Autoriser l'execution a la demande
   ☑ Si la tache echoue, redemarrer toutes les : 1 minute
      Nombre de tentatives : 3
   ☐ Arreter la tache si elle s'execute plus de : (DECOCHER ou mettre 0)
   ```

8. **Valider** avec OK (entrer le mot de passe si demande)

---

## Étape 5 : Vérifier que tout fonctionne

### Vérifier la tâche

```powershell
# Voir le statut
Get-ScheduledTask -TaskName "ZKTeco_Sync_Service"

# Voir les infos d'exécution
Get-ScheduledTask -TaskName "ZKTeco_Sync_Service" | Get-ScheduledTaskInfo
```

### Vérifier les logs

```powershell
# Voir les dernières lignes du log
Get-Content C:\zkteco-service\zkteco_sync.log -Tail 30

# Suivre les logs en temps réel
Get-Content C:\zkteco-service\zkteco_sync.log -Wait -Tail 10
```

### Tester le redémarrage

1. Redémarrer le PC
2. Après redémarrage, vérifier :
   ```powershell
   Get-ScheduledTask -TaskName "ZKTeco_Sync_Service" | Get-ScheduledTaskInfo
   Get-Content C:\zkteco-service\zkteco_sync.log -Tail 10
   ```

---

## Commandes Utiles - Aide-Mémoire

### Gestion de la tâche

```powershell
# Démarrer
Start-ScheduledTask -TaskName "ZKTeco_Sync_Service"

# Arrêter
Stop-ScheduledTask -TaskName "ZKTeco_Sync_Service"

# Statut
Get-ScheduledTask -TaskName "ZKTeco_Sync_Service" | Select-Object TaskName, State

# Supprimer
Unregister-ScheduledTask -TaskName "ZKTeco_Sync_Service" -Confirm:$false
```

### Logs

```powershell
# Voir les logs du service
Get-Content C:\zkteco-service\zkteco_sync.log -Tail 50

# Suivre en temps réel
Get-Content C:\zkteco-service\zkteco_sync.log -Wait -Tail 10

# Vider les logs (si trop gros)
Clear-Content C:\zkteco-service\zkteco_sync.log
```

### Test manuel

**Avec venv :**
```powershell
cd C:\zkteco-service
.\venv\Scripts\python.exe zkteco_service.py
```

**Sans venv :**
```powershell
cd C:\zkteco-service
python zkteco_service.py
```

---

## Dépannage

### "python" n'est pas reconnu

**Cause :** Python n'est pas dans le PATH

**Solution :**
```powershell
# Trouver Python manuellement
Get-ChildItem -Path "C:\Users" -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue | Select-Object FullName

# Ou chercher dans Program Files
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue | Select-Object FullName
```

Puis utiliser le chemin complet dans la tâche planifiée.

### La tâche ne démarre pas

**Vérifier les logs Windows :**
```powershell
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" |
    Where-Object {$_.Message -like "*ZKTeco*"} |
    Select-Object -First 5 |
    Format-List TimeCreated, Message
```

### Erreur de connexion à l'appareil ZKTeco

```powershell
# Tester la connectivité
ping 192.168.1.XXX

# Si pas de réponse, vérifier :
# - L'appareil est allumé
# - L'IP est correcte
# - Le PC et l'appareil sont sur le même réseau
```

### Le service consomme trop de mémoire

Le service est conçu pour être léger (~30 Mo de RAM). Si problème :
1. Vérifier les logs pour erreurs en boucle
2. Augmenter `SYNC_INTERVAL` dans `.env` (ex: 10 au lieu de 5)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        WINDOWS                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Planificateur de tâches Windows                      │  │
│  │  Tâche : ZKTeco_Sync_Service                          │  │
│  │  Déclencheur : Au démarrage                           │  │
│  │  Redémarrage auto si échec                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  python.exe zkteco_service.py                         │  │
│  │  • Synchronise toutes les X minutes                   │  │
│  │  • Envoie notifications si erreur                     │  │
│  │  • Logs dans zkteco_sync.log                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │ Appareil ZKTeco │         │   API Backend   │
    │ 192.168.1.XXX   │         │ /api/attendance │
    └─────────────────┘         └─────────────────┘
```

---

## Checklist d'Installation

- [ ] Python installé et accessible via `python --version`
- [ ] Fichiers copiés dans `C:\zkteco-service\`
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier `.env` configuré (DEVICE_IP, API_URL)
- [ ] Test manuel réussi (`python zkteco_service.py`)
- [ ] Tâche planifiée créée
- [ ] Tâche démarre au boot (testé après redémarrage)
- [ ] Logs générés dans `zkteco_sync.log`

---

## Configuration Recommandée pour Machine Légère

Dans `.env`, ajuster ces valeurs :

```ini
# Augmenter l'intervalle pour réduire la charge CPU
SYNC_INTERVAL=10

# Réduire les retries
MAX_RETRIES=2
RETRY_DELAY=15

# Limiter la taille des logs
LOG_MAX_BYTES=5242880
LOG_BACKUP_COUNT=2
```

---

**Document créé le :** 07/01/2026
**Optimisé pour :** Windows 10/11 avec ressources limitées (4 Go RAM, HDD)
