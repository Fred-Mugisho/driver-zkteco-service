"""Configuration pour ZKTeco Service"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Appareil ZKTeco
    DEVICE_IP = os.getenv('DEVICE_IP', '192.168.1.100')
    DEVICE_PORT = int(os.getenv('DEVICE_PORT', '4370'))
    DEVICE_TIMEOUT = int(os.getenv('DEVICE_TIMEOUT', '60'))

    # API
    API_URL = os.getenv('API_URL', 'BACKEND_URL')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

    # Synchronisation
    SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', '5'))
    SYNC_FILE = os.getenv('SYNC_FILE', 'sync_state.json')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '10'))

    # Logging
    LOG_FILE = os.getenv('LOG_FILE', 'zkteco_sync.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Notifications par email
    API_ENDPOINT_SEND_MAIL = os.getenv('API_ENDPOINT_SEND_MAIL', "API_ENDPOINT_SEND_MAIL")
    RECEIVERS_EMAILS = os.getenv('RECEIVERS_EMAILS', '').split(',')
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

config = Config()
