# config.py - Gestor de configuración de tokens y IDs

import os

# Token y chat ID para Telegram, se leen de variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
    raise ValueError("Debes definir las variables de entorno TELEGRAM_TOKEN y TELEGRAM_CHAT_ID")
