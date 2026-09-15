FROM python:3.12-slim
LABEL maintainer="angepascal.com"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PATH="/home/django-user/.local/bin:/usr/local/bin:${PATH}"

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ARG DEV=false

# Copie et installation des dépendances Python
COPY ./requirements.txt /app/requirements.txt
COPY ./requirements.dev.txt /app/requirements.dev.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir gunicorn && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        pip install --no-cache-dir -r /app/requirements.dev.txt ; \
    fi

# Copie du code applicatif
COPY ./app /app

# Utilisateur non-root
RUN useradd -m django-user && chown -R django-user:django-user /app
USER django-user

EXPOSE 8080

# Lancement Gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 8 --timeout 0 app.wsgi:application
