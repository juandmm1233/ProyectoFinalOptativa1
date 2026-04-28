"""
Configuración de la app `diagnostico`.

El modelo de Machine Learning (Random Forest) se carga UNA SOLA VEZ
al iniciar el servidor mediante `ready()`, y queda disponible como
atributo de clase `DiagnosticoConfig.ml_model`. De esta forma evitamos
recargar el archivo `.pkl` en cada petición y mantenemos un rendimiento
óptimo.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class DiagnosticoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "diagnostico"
    verbose_name = "Diagnóstico de Células Sanguíneas"

    # Atributo de clase que mantiene la instancia del modelo en memoria.
    ml_model: Any = None

    # Nombres de las features esperadas por el modelo, en el orden correcto.
    # Si tu .pkl fue entrenado con otros nombres, ajústalos aquí y en forms.py.
    feature_names: list[str] = ["area", "perimetro", "concavidad", "textura"]

    def ready(self) -> None:  # noqa: D401
        """Carga el modelo cuando Django termina de inicializar la app."""
        model_path: Path = Path(getattr(settings, "ML_MODEL_PATH", ""))

        if not model_path or not model_path.exists():
            logger.warning(
                "[BioCell AI] No se encontró el modelo en %s. "
                "Las predicciones no estarán disponibles hasta que se "
                "ubique el archivo .pkl en core/ml_models/.",
                model_path,
            )
            DiagnosticoConfig.ml_model = None
            return

        try:
            DiagnosticoConfig.ml_model = joblib.load(model_path)
            logger.info(
                "[BioCell AI] Modelo cargado correctamente desde %s", model_path
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "[BioCell AI] Error al cargar el modelo desde %s", model_path
            )
            DiagnosticoConfig.ml_model = None
