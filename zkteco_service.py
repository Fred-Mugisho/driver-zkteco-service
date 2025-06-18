import threading
import time
import schedule
import requests
import json
import logging
from pyzk_lib.zk import ZK
from datetime import datetime
from typing import Optional, List, Dict
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zkteco_sync.log'),
        logging.StreamHandler()
    ]
)

# Configuration
CONFIG = {
    'API_URL': 'ENDPOINT',
    'DEVICE_IP': '192.168.1.100',
    'DEVICE_PORT': 4370,
    'TIMEOUT': 60,
    'SYNC_INTERVAL': 5,
    'SYNC_FILE': 'sync_state.json',
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5
}

def load_last_sync() -> Optional[datetime]:
    """
    Charge la date de la dernière synchronisation depuis le fichier de sauvegarde.
    
    Returns:
        Optional[datetime]: La date de la dernière synchronisation ou None si non trouvée
    """
    try:
        with open(CONFIG['SYNC_FILE'], "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get("last_sync"))
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.warning(f"Erreur lors du chargement de la dernière synchronisation: {e}")
        return None

def save_last_sync(sync_time: datetime) -> None:
    """
    Sauvegarde la date de la dernière synchronisation dans le fichier.
    
    Args:
        sync_time (datetime): La date à sauvegarder
    """
    try:
        with open(CONFIG['SYNC_FILE'], "w") as f:
            json.dump({"last_sync": sync_time.isoformat()}, f)
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de la synchronisation: {e}")

class ZKAttendanceAgent:
    """
    Classe pour gérer la communication avec l'appareil ZKTeco.
    Implémente le pattern context manager pour une gestion automatique des ressources.
    """
    
    def __init__(self, ip: str, port: int = 4370, timeout: int = 60):
        """
        Initialise l'agent de communication avec l'appareil ZKTeco.
        
        Args:
            ip (str): Adresse IP de l'appareil
            port (int): Port de communication
            timeout (int): Délai d'attente maximum
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.zk = None
        self.conn = None

    def __enter__(self):
        """Gestion de l'entrée dans le contexte (with)"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Gestion de la sortie du contexte (with)"""
        self.disconnect()

    def connect(self) -> None:
        """
        Établit la connexion avec l'appareil ZKTeco.
        Lève une exception en cas d'échec.
        """
        try:
            self.zk = ZK(self.ip, port=self.port, timeout=self.timeout)
            self.conn = self.zk.connect()
            logging.info(f"Connecté avec succès à l'appareil {self.ip}")
        except Exception as e:
            logging.error(f"Erreur de connexion à l'appareil {self.ip}: {e}")
            raise

    def disconnect(self) -> None:
        """Ferme proprement la connexion avec l'appareil"""
        if self.conn:
            try:
                self.conn.enable_device()
                self.conn.disconnect()
                logging.info("Déconnexion réussie de l'appareil")
            except Exception as e:
                logging.error(f"Erreur lors de la déconnexion: {e}")

    def get_new_attendances(self) -> List[Dict]:
        """
        Récupère les nouvelles présences depuis l'appareil.
        
        Returns:
            List[Dict]: Liste des nouvelles présences avec matricule et timestamp
        """
        if not self.conn:
            raise ConnectionError("Non connecté à l'appareil")

        try:
            self.conn.disable_device()
            presences = []
            last_sync = load_last_sync()

            all_presences = self.conn.get_attendance()
            if all_presences:
                for presence in all_presences:
                    try:
                        convert_presence_str = str(presence).split('|')
                        if len(convert_presence_str) > 1:
                            timestamp = datetime.strptime(convert_presence_str[1], '%Y-%m-%d %H:%M:%S')
                            if last_sync is None or timestamp > last_sync:
                                presences.append({
                                    'matricule': convert_presence_str[0],
                                    'timestamp': timestamp.isoformat(),
                                })
                    except Exception as e:
                        logging.error(f"Erreur lors du traitement d'une présence: {e}")
                        continue

                presences.sort(key=lambda x: x['timestamp'])
                logging.info(f"{len(presences)} nouvelles présences trouvées")

            return presences
        finally:
            self.conn.enable_device()

def fetch_and_send_attendance() -> None:
    """
    Fonction principale qui récupère et envoie les présences.
    Gère les tentatives multiples en cas d'échec.
    """
    for attempt in range(CONFIG['MAX_RETRIES']):
        try:
            with ZKAttendanceAgent(
                CONFIG['DEVICE_IP'],
                port=CONFIG['DEVICE_PORT'],
                timeout=CONFIG['TIMEOUT']
            ) as zk:
                new_attendances = zk.get_new_attendances()
                
                if new_attendances:
                    response = requests.post(
                        CONFIG['API_URL'],
                        json=new_attendances,
                        headers={'Content-Type': 'application/json'},
                        timeout=CONFIG['TIMEOUT']
                    )

                    if response.status_code == 200:
                        last_sync_time = max(datetime.fromisoformat(att["timestamp"]) for att in new_attendances)
                        save_last_sync(last_sync_time)
                        logging.info(f"Données envoyées avec succès: {len(new_attendances)} présences")
                    else:
                        logging.error(f"Erreur API ({response.status_code}): {response.text}")
                else:
                    logging.info("Aucune nouvelle présence à synchroniser")
                return
        except Exception as e:
            logging.error(f"Tentative {attempt + 1}/{CONFIG['MAX_RETRIES']} échouée: {e}")
            if attempt < CONFIG['MAX_RETRIES'] - 1:
                time.sleep(CONFIG['RETRY_DELAY'])
            else:
                logging.error("Nombre maximum de tentatives atteint")

def run_scheduler() -> None:
    """
    Fonction qui exécute le planificateur de tâches en continu.
    Gère les erreurs qui pourraient survenir pendant l'exécution.
    """
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Erreur dans le scheduler: {e}")
            time.sleep(CONFIG['RETRY_DELAY'])

if __name__ == '__main__':
    # Point d'entrée principal du programme
    logging.info("Démarrage du service de synchronisation ZKTeco")
    
    # Configuration de la tâche planifiée
    schedule.every(CONFIG['SYNC_INTERVAL']).minutes.do(fetch_and_send_attendance)
    
    # Démarrage du scheduler dans un thread séparé
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    
    try:
        # Attente de la fin du thread
        thread.join()
    except KeyboardInterrupt:
        # Gestion de l'arrêt propre avec Ctrl+C
        logging.info("Arrêt du service demandé")
    except Exception as e:
        # Gestion des erreurs inattendues
        logging.error(f"Erreur inattendue: {e}")
    finally:
        # Message final de confirmation d'arrêt
        logging.info("Arrêt du service")
