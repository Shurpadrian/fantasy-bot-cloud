# Usa imagen oficial de Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia requirements.txt y luego instala dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código del proyecto (ajusta según estructura)
COPY scripts-onlines/ .

# Comando para ejecutar tu script principal de test
CMD ["python", "enviar_telegram_cloud.py"]
