import threading
import time
import schedule
import requests
import json
import logging
from pyzk_lib.zk import ZK
from datetime import datetime
from typing import Optional, List, Dict

# ----------------------
# Logging
# ----------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zkteco_sync.log'),
        logging.StreamHandler()
    ]
)

# ----------------------
# Configuration
# ----------------------
CONFIG = {
    'API_URL': 'BACKEND_URL',
    'DEVICE_IP': '192.168.1.100',
    'DEVICE_PORT': 4370,
    'TIMEOUT': 60,
    'SYNC_INTERVAL': 5,          # en minutes
    'SYNC_FILE': 'sync_state.json',
    'MAX_RETRIES': 3,            # retry pour ZK + API
    'RETRY_DELAY': 10,            # secondes entre retries simples
    'MAX_CONSECUTIVE_FAILURES': 3  # alert si échecs consécutifs
}

sync_lock = threading.Lock()
consecutive_failures = 0

# ----------------------
# Dernier sync
# ----------------------
def load_last_sync() -> Optional[datetime]:
    try:
        with open(CONFIG['SYNC_FILE'], "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get("last_sync"))
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.warning(f"Impossible de charger la dernière synchronisation: {e}")
        return None

def save_last_sync(sync_time: datetime) -> None:
    try:
        with open(CONFIG['SYNC_FILE'], "w") as f:
            json.dump({"last_sync": sync_time.isoformat()}, f)
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de la synchronisation: {e}")

# ----------------------
# Agent ZKTeco
# ----------------------
class ZKAttendanceAgent:
    def __init__(self, ip: str, port: int = 4370, timeout: int = 60):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.zk = None
        self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self) -> None:
        try:
            self.zk = ZK(self.ip, port=self.port, timeout=self.timeout)
            self.conn = self.zk.connect()
            logging.info(f"Connecté à l'appareil {self.ip}")
        except Exception as e:
            logging.error(f"Erreur de connexion à l'appareil {self.ip}: {e}")
            raise

    def disconnect(self) -> None:
        if self.conn:
            try:
                self.conn.enable_device()
                self.conn.disconnect()
                logging.info("Déconnexion réussie")
            except Exception as e:
                logging.error(f"Erreur lors de la déconnexion: {e}")

    def get_new_attendances(self) -> List[Dict]:
        if not self.conn:
            raise ConnectionError("Non connecté à l'appareil")

        presences: List[Dict] = []
        last_sync = load_last_sync()

        try:
            self.conn.disable_device()
            all_presences = self.conn.get_attendance()
            if all_presences:
                for attendance in all_presences:
                    ts = attendance.timestamp
                    if last_sync is None or ts > last_sync:
                        presences.append({
                            'matricule': attendance.user_id,
                            'timestamp': ts.isoformat()
                        })
                presences.sort(key=lambda x: x['timestamp'])
            return presences
        finally:
            self.conn.enable_device()

# ----------------------
# Synchronisation avec retry exponentiel
# ----------------------
def fetch_and_send_attendance() -> None:
    global consecutive_failures
    
    logging.info("Démarrage de la synchronisation")

    if not sync_lock.acquire(blocking=False):
        logging.info("Une synchronisation est déjà en cours, skipping...")
        return

    try:
        for attempt in range(1, CONFIG['MAX_RETRIES'] + 1):
            try:
                with ZKAttendanceAgent(CONFIG['DEVICE_IP'], CONFIG['DEVICE_PORT'], CONFIG['TIMEOUT']) as zk:
                    new_attendances = zk.get_new_attendances()
                    logging.info(f"Nouvelles présences détectées: {len(new_attendances)}")

                    if not new_attendances:
                        logging.info("Aucune nouvelle présence à synchroniser")
                        consecutive_failures = 0
                        return

                    # Retry exponentiel pour l'API
                    for api_attempt in range(1, CONFIG['MAX_RETRIES'] + 1):
                        try:
                            response = requests.post(
                                CONFIG['API_URL'],
                                json=new_attendances,
                                headers={'Content-Type': 'application/json'},
                                timeout=CONFIG['TIMEOUT']
                            )
                            if response.status_code == 200:
                                last_sync_time = max(datetime.fromisoformat(att['timestamp']) for att in new_attendances)
                                save_last_sync(last_sync_time)
                                logging.info(f"Synchronisation réussie: {len(new_attendances)} présences envoyées")
                                consecutive_failures = 0
                                return
                            else:
                                logging.warning(f"Erreur API (status {response.status_code}): {response.text}")
                                raise Exception(f"Erreur API ({response.status_code})")
                        except Exception as api_err:
                            delay = CONFIG['RETRY_DELAY'] * (2 ** (api_attempt - 1))
                            logging.warning(f"Retry API {api_attempt}/{CONFIG['MAX_RETRIES']} après {delay}s: {api_err}")
                            time.sleep(delay)
                    raise Exception("Échec de l'envoi vers l'API après retries")
            except Exception as zk_err:
                logging.error(f"Tentative {attempt}/{CONFIG['MAX_RETRIES']} échouée: {zk_err}")
                if attempt < CONFIG['MAX_RETRIES']:
                    time.sleep(CONFIG['RETRY_DELAY'])
                else:
                    logging.critical("Échec complet de la synchronisation")
                    consecutive_failures += 1

        # Alertes si trop d'échecs consécutifs
        if consecutive_failures >= CONFIG['MAX_CONSECUTIVE_FAILURES']:
            logging.critical(f"{consecutive_failures} échecs consécutifs détectés ! Vérifiez le système et la connexion.")
    finally:
        sync_lock.release()

# ----------------------
# Scheduler
# ----------------------
def run_scheduler() -> None:
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Erreur dans le scheduler: {e}")
            time.sleep(CONFIG['RETRY_DELAY'])

# ----------------------
# Main
# ----------------------
if __name__ == '__main__':
    logging.info("Démarrage du service ZKTeco avec retry exponentiel et alertes")
    # schedule.every(CONFIG['SYNC_INTERVAL']).minutes.do(fetch_and_send_attendance)
    fetch_and_send_attendance()
    
    # Bloquant, systemd garde le service actif
    # run_scheduler()

    # thread = threading.Thread(target=run_scheduler, daemon=True)
    # thread.start()

    # try:
    #     thread.join()
    # except KeyboardInterrupt:
    #     logging.info("Arrêt du service demandé")
    # except Exception as e:
    #     logging.error(f"Erreur inattendue: {e}")
    # finally:
    #     logging.info("Service arrêté proprement")
