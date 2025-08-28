import os

# Variables para entorno producción
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Variables para entorno test
TELEGRAM_TOKEN_TEST = os.getenv('TELEGRAM_TOKEN_TEST')
TELEGRAM_CHAT_ID_TEST = os.getenv('TELEGRAM_CHAT_ID_TEST')

# Puedes añadir validaciones simples para que existan al menos los de test
if TELEGRAM_TOKEN_TEST is None or TELEGRAM_CHAT_ID_TEST is None:
    raise ValueError("Debes definir las variables de entorno TELEGRAM_TOKEN_TEST y TELEGRAM_CHAT_ID_TEST")
