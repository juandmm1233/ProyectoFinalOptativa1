# =========================================================
# BioCell AI — Dockerfile
# Imagen ligera basada en Python 3.12 (Debian 12) que
# empaqueta Django + el modelo Random Forest entrenado y
# lo expone en el puerto 8000 mediante gunicorn.
# =========================================================
# bookworm (Debian 12) queda fijado para no seguir el tag flotante
# python:3.12-slim, que ahora apunta a Debian 13.
FROM python:3.12-slim-bookworm

# Buenas prácticas para Python en contenedores.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=biocell_ai.settings

# Sin apt-get: en el laboratorio deb.debian.org y otros espejos
# responden 404 al pedir el Release, así que no se instalan paquetes
# del sistema. numpy, pandas y scikit-learn traen wheels con sus
# propias librerías (OpenMP, gfortran); no hace falta libgomp1 ni
# build-essential.

WORKDIR /app

# Instalar dependencias Python primero (mejora el cacheo de capas).
COPY requirements.txt .
RUN pip install --upgrade pip --root-user-action=ignore \
 && pip install --root-user-action=ignore -r requirements.txt

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
