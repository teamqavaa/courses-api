FROM python:3.12-slim
LABEL maintainer="angepascal.com"

# Variables d'environnement indispensables (Local et Prod)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. On déclare l'argument ICI pour qu'il soit accessible en dessous
ARG DEV=false

# Installation des dépendances Python
COPY ./requirements.txt /app/requirements.txt
COPY ./requirements.dev.txt /app/requirements.dev.txt

# 2. Correction de la syntaxe Bash (espaces et enchaînement)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        pip install --no-cache-dir -r /app/requirements.dev.txt ; \
    fi

# Copie du code
COPY ./app /app

# Sécurisation
RUN useradd -m django-user && chown -R django-user:django-user /app
USER django-user

EXPOSE 8080

# --- ASTUCE DE TRANSITION LOCAL/PROD ---
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "mon_projet.wsgi:application"]
