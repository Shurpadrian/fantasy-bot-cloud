# Usa imagen oficial de Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia requirements.txt y luego instala dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia TODO el código del proyecto (no solo scripts-onlines)
COPY . .

# Variables de entorno necesarias
ENV PORT=8080
ENV PYTHONUNBUFFERED=TRUE

# Expone el puerto que Cloud Run requiere
EXPOSE $PORT

# Usa Gunicorn para producción (requerido por Cloud Run)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 enviar_telegram_cloud:app
