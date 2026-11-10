# =========================================================
# BioCell AI — Dockerfile
# Imagen ligera basada en Python 3.12 (Debian 12) que
# empaqueta Django + el modelo Random Forest entrenado y
# lo expone en el puerto 8000 mediante gunicorn.
# =========================================================
# python:3.12-slim (sin sufijo) hoy es Debian 13 "trixie".
# En el laboratorio apt recibió 404 al pedir trixie, trixie-updates
# y trixie-security. bookworm sigue publicado y es estable.
FROM python:3.12-slim-bookworm

# Buenas prácticas para Python en contenedores.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=biocell_ai.settings

# Dependencias del sistema necesarias para compilar wheels de
# scikit-learn / numpy / pandas en caso de que pip no encuentre
# wheels precompilados para la arquitectura del host.
# libgomp1 es la runtime de OpenMP que esos wheels exigen al importar.
# Si deb.debian.org (Fastly) vuelve a responder 404, se usa otro espejo.
RUN set -eux; \
    if ! apt-get update -o Acquire::Retries=5; then \
      printf '%s\n' \
        'deb http://mirror.csclub.uwaterloo.ca/debian bookworm main' \
        'deb http://mirror.csclub.uwaterloo.ca/debian bookworm-updates main' \
        'deb http://mirror.csclub.uwaterloo.ca/debian-security bookworm-security main' \
        > /etc/apt/sources.list; \
      rm -f /etc/apt/sources.list.d/debian.sources; \
      apt-get update -o Acquire::Retries=5; \
    fi; \
    apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python primero (mejora el cacheo de capas).
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copiar el código fuente del proyecto.
COPY . .

# Crear un usuario sin privilegios y delegarle la propiedad del proyecto.
RUN groupadd --system biocell \
 && useradd  --system --gid biocell --home /app biocell \
 && mkdir -p /app/staticfiles \
 && chown -R biocell:biocell /app

USER biocell

# Recolectar archivos estáticos para que WhiteNoise pueda servirlos.
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# gunicorn como WSGI server. 3 workers es un valor sensato para empezar;
# ajusta según los núcleos disponibles en producción (regla: 2 * CPU + 1).
CMD ["gunicorn", "biocell_ai.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
