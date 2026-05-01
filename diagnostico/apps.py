from __future__ import annotations
import json
import logging
import os
import pickle
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class DiagnosticoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "diagnostico"

    ml_model  = None
    ml_scaler = None
    ml_features: list[str] = []

    def ready(self) -> None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ml_dir = os.path.join(base, "core", "ml_models")

        modelo_path   = os.path.join(ml_dir, "modelo_anomalias.pkl")
        scaler_path   = os.path.join(ml_dir, "scaler_anomalias.pkl")
        features_path = os.path.join(ml_dir, "features_modelo.json")

        try:
            with open(modelo_path, "rb") as f:
                DiagnosticoConfig.ml_model = pickle.load(f)
            with open(scaler_path, "rb") as f:
                DiagnosticoConfig.ml_scaler = pickle.load(f)
            with open(features_path, "r") as f:
                DiagnosticoConfig.ml_features = json.load(f)

            logger.info(f"✅ Modelo cargado: {len(DiagnosticoConfig.ml_features)} features")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")