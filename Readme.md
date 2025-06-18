# ZKTeco Attendance Sync

## Description
Ce projet permet de récupérer automatiquement les présences depuis un appareil biométrique **ZKTeco** et d'envoyer ces données à une **API Django** pour traitement.

✅ Récupération des données d'assiduité depuis un appareil ZKTeco.
✅ Envoi automatique des présences à une API REST Django.
✅ Fonctionnement en **background** sous Linux avec `systemd`.
✅ Exécution planifiée toutes les 5 minutes.

---

## Prérequis

### Matériel 📟
- Un appareil **ZKTeco** connecté au réseau.
- Un serveur Linux avec Python 3 ou plus.
---

### Configurer l'IP de l'appareil ZKTeco
Modifie `zkteco_service.py` et mets l'adresse IP correcte de ton appareil.
```python
ip = "192.168.1.201"  # Adresse IP de ton ZKTeco
API_URL = "https://ton-api.com/api/ENDPOINT"  # URL de ton API Django
```

---

## Utilisation

### Démarrer le script manuellement
```bash
python3 zkteco_service.py
```

Cela va récupérer les présences et les envoyer à l'API Django toutes les 5 minutes.

---

## Automatisation avec `systemd`
Pour exécuter le script **en arrière-plan**, crée un service `systemd`.

### Créer un fichier service
```bash
sudo nano /etc/systemd/system/zkteco_attendance.service
```

### Ajouter le contenu suivant
```ini
[Unit]
Description=Service de récupération et envoi des présences ZKTeco
After=network.target

[Service]
ExecStart=/usr/bin/python3 /chemin/vers/zkteco_service.py
Restart=always
User=root
WorkingDirectory=/chemin/vers/le/dossier
StandardOutput=append:/var/log/zkteco.log
StandardError=append:/var/log/zkteco_error.log

[Install]
WantedBy=multi-user.target
```

### Activer et démarrer le service
```bash
# Recharger les services
sudo systemctl daemon-reload

# Démarrer le service
sudo systemctl start zkteco_attendance.service

# Activer au démarrage
sudo systemctl enable zkteco_attendance.service
```

### Vérifier que tout fonctionne
```bash
sudo systemctl status zkteco_attendance.service
```

### Arreter le service
```bash
sudo systemctl stop zkteco_attendance.service
sudo service zkteco_attendance stop
```