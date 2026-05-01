# =========================================================
# BioCell AI — Dockerfile
# Imagen ligera basada en Python 3.12-slim que empaqueta
# Django + el modelo Random Forest entrenado y lo expone
# en el puerto 8030 mediante gunicorn.
# =========================================================
FROM python:3.12-slim

# Buenas prácticas para Python en contenedores.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=biocell_ai.settings

# Dependencias del sistema necesarias para compilar wheels de
# scikit-learn / numpy / pandas en caso de que pip no encuentre
# wheels precompilados para la arquitectura del host.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
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

EXPOSE 8030

# gunicorn como WSGI server. 3 workers es un valor sensato para empezar;
# ajusta según los núcleos disponibles en producción (regla: 2 * CPU + 1).
CMD ["gunicorn", "biocell_ai.wsgi:application", \
     "--bind", "0.0.0.0:8030", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
