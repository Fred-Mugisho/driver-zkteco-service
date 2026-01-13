#!/usr/bin/env python3
"""
Service de synchronisation ZKTeco - Compatible tous OS
Fonctionne en tâche de fond sur Linux, Windows et macOS
"""
import threading
import time
import schedule
import requests
import json
import logging
from logging.handlers import RotatingFileHandler
from pyzk_lib.zk import ZK
from datetime import datetime
from typing import Optional, List, Dict
import signal
import sys
import os
import platform

from config import config

# Import conditionnel de la notification
try:
    from notification import send_email_notification
    NOTIFICATIONS_ENABLED = True
except ImportError as e:
    NOTIFICATIONS_ENABLED = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"Module de notification non disponible: {e}")

# Configuration du logging
def setup_logging():
    """Configure le systeme de logging"""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)

    # Configuration console avec support UTF-8 sur Windows
    if platform.system() == 'Windows':
        import io
        console_handler = logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        )
    else:
        console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# Variables globales
sync_lock = threading.Lock()
shutdown_flag = threading.Event()


def load_last_sync() -> Optional[datetime]:
    """Charge la dernière synchronisation"""
    try:
        with open(config.SYNC_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get("last_sync"))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None


def save_last_sync(sync_time: datetime) -> None:
    """Sauvegarde la dernière synchronisation"""
    try:
        with open(config.SYNC_FILE, "w") as f:
            json.dump({"last_sync": sync_time.isoformat()}, f)
    except Exception as e:
        logger.error(f"Erreur sauvegarde: {e}")


class ZKAttendanceAgent:
    """Agent de connexion à l'appareil ZKTeco"""

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
        """Connexion à l'appareil"""
        try:
            self.zk = ZK(self.ip, port=self.port, timeout=self.timeout)
            self.conn = self.zk.connect()
            logger.info(f"Connecté à {self.ip}")
        except Exception as e:
            logger.error(f"Erreur connexion: {e}")
            # raise
            

    def disconnect(self) -> None:
        """Déconnexion de l'appareil"""
        if self.conn:
            try:
                self.conn.enable_device()
                self.conn.disconnect()
            except Exception as e:
                logger.error(f"Erreur déconnexion: {e}")

    def get_new_attendances(self) -> List[Dict]:
        """Récupère les nouvelles présences"""
        
        if not self.conn:
            raise ConnectionError("Non connecté")

        presences = []
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


def fetch_and_send_attendance() -> None:
    """Synchronisation principale"""
    logger.info("=== Début sync ===")

    if not sync_lock.acquire(blocking=False):
        logger.info("Sync en cours, skip")
        return

    last_error = None
    try:
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                with ZKAttendanceAgent(config.DEVICE_IP, config.DEVICE_PORT, config.DEVICE_TIMEOUT) as zk:
                    new_attendances = zk.get_new_attendances()
                    logger.info(f"{len(new_attendances)} présences détectées")

                    if not new_attendances:
                        logger.info("Aucune nouvelle présence")
                        return

                    # Envoi à l'API
                    response = requests.post(
                        config.API_URL,
                        json=new_attendances,
                        headers={'Content-Type': 'application/json'},
                        timeout=config.API_TIMEOUT
                    )

                    if response.status_code == 200:
                        last_sync_time = max(
                            datetime.fromisoformat(att['timestamp'])
                            for att in new_attendances
                        )
                        save_last_sync(last_sync_time)
                        logger.info(f"✓ Sync réussie: {len(new_attendances)} présences")
                        return
                    else:
                        logger.warning(f"Erreur API {response.status_code} : {response.text}")
                        raise Exception(f"API {response.status_code} : {response.text}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Tentative {attempt}/{config.MAX_RETRIES}: {e}")
                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_DELAY)

        # Échec après toutes les tentatives - Envoyer notification
        logger.critical("✗ Échec après retries")
        if NOTIFICATIONS_ENABLED:
            send_email_notification(
                subject=f"[ALERTE] Échec Synchronisation ZKTeco - {config.DEVICE_IP}",
                message=f"⚠️ ÉCHEC DE SYNCHRONISATION\n\n"
                        f"Le service ZKTeco n'a pas réussi à synchroniser les données de présence.\n\n"
                        f"DÉTAILS DE L'ERREUR:\n"
                        f"Appareil concerné: {config.DEVICE_IP}:{config.DEVICE_PORT}\n"
                        f"Nombre de tentatives: {config.MAX_RETRIES}\n"
                        f"Dernière erreur détectée: {last_error}\n"
                        f"Date et heure: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n\n"
                        f"ACTION REQUISE:\n"
                        f"Veuillez vérifier la connectivité de l'appareil et consulter les logs pour plus de détails."
            )

    except Exception as e:
        logger.error(f"Erreur: {e}")
        if NOTIFICATIONS_ENABLED:
            send_email_notification(
                subject=f"[CRITIQUE] Erreur Système ZKTeco - {config.DEVICE_IP}",
                message=f"🚨 ERREUR CRITIQUE SYSTÈME\n\n"
                        f"Une erreur critique inattendue s'est produite dans le service de synchronisation ZKTeco.\n\n"
                        f"DÉTAILS DE L'ERREUR:\n"
                        f"Type d'erreur: Erreur système critique\n"
                        f"Message d'erreur: {str(e)}\n"
                        f"Appareil: {config.DEVICE_IP}:{config.DEVICE_PORT}\n"
                        f"Date et heure: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n\n"
                        f"ACTION REQUISE:\n"
                        f"Une intervention immédiate est nécessaire. Veuillez consulter les logs système pour diagnostiquer le problème."
            )
    finally:
        sync_lock.release()


def run_scheduler() -> None:
    """Boucle principale du scheduler"""
    while not shutdown_flag.is_set():
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Erreur scheduler: {e}")
            time.sleep(10)


def handle_shutdown(signum, _frame):
    """Gestion arrêt gracieux"""
    logger.info(f"Signal {signum} - Arrêt...")
    shutdown_flag.set()
    sys.exit(0)


def main():
    """Point d'entrée principal"""
    # Gestion des signaux (Linux/macOS uniquement)
    if platform.system() != 'Windows':
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

    logger.info("=== Service ZKTeco ===")
    logger.info(f"OS: {platform.system()}")
    logger.info(f"Appareil: {config.DEVICE_IP}:{config.DEVICE_PORT}")
    logger.info(f"API: {config.API_URL}")
    logger.info(f"Intervalle: {config.SYNC_INTERVAL} min")

    if config.SYNC_INTERVAL > 0:
        # Mode continu
        schedule.every(config.SYNC_INTERVAL).minutes.do(fetch_and_send_attendance)
        fetch_and_send_attendance()  # Première sync immédiate

        try:
            run_scheduler()
        except KeyboardInterrupt:
            logger.info("Arrêt (Ctrl+C)")
        finally:
            logger.info("Service arrêté")
    else:
        # Mode single-run
        fetch_and_send_attendance()


if __name__ == '__main__':
    main()
