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

    # Nombres de las 27 features que el modelo Random Forest espera, en orden.
    # El formulario solo recoge 4 de ellas (Area, Perímetro, Concavidad, Textura);
    # el resto se rellenan con 0.0 al momento de predecir.
    feature_names: list[str] = [
        "cell_diameter_um",
        "nucleus_area_pct",
        "chromatin_density",
        "cytoplasm_ratio",
        "circularity",
        "eccentricity",
        "granularity_score",
        "lobularity_score",
        "membrane_smoothness",
        "cell_area_px",
        "perimeter_px",
        "mean_r",
        "mean_g",
        "mean_b",
        "stain_intensity",
        "wbc_count_per_ul",
        "rbc_count_millions_per_ul",
        "hemoglobin_g_dl",
        "hematocrit_pct",
        "platelet_count_per_ul",
        "mcv_fl",
        "mchc_g_dl",
        "magnification_x",
        "image_resolution_px",
        "cytodiffusion_anomaly_score",
        "cytodiffusion_classification_confidence",
        "labeller_confidence_score",
    ]

    # Total de features esperadas por el modelo.
    n_features: int = 27

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
