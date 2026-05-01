from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from .forms import CelulaForm

logger = logging.getLogger(__name__)

@require_GET
def index(request):
    form = CelulaForm()
    return render(request, "diagnostico/index.html", {"form": form})

@require_POST
def predecir(request):
    form = CelulaForm(request.POST)

    if not form.is_valid():
        return JsonResponse({
            "ok": False,
            "error": "Datos inválidos.",
            "errores_campo": form.errors
        }, status=400)

    config  = apps.get_app_config("diagnostico")
    modelo  = config.ml_model
    scaler  = config.ml_scaler
    features = config.ml_features

    if modelo is None or scaler is None:
        return JsonResponse({
            "ok": False,
            "error": "Modelo no disponible en el servidor."
        }, status=503)

    datos = form.cleaned_data

    # Construir DataFrame en el orden exacto de features
    fila = {
        "cell_diameter_um":          float(datos["cell_diameter_um"]),
        "nucleus_area_pct":          float(datos["nucleus_area_pct"]),
        "chromatin_density":         float(datos["chromatin_density"]),
        "cytoplasm_ratio":           float(datos["cytoplasm_ratio"]),
        "circularity":               float(datos["circularity"]),
        "eccentricity":              float(datos["eccentricity"]),
        "granularity_score":         float(datos["granularity_score"]),
        "lobularity_score":          float(datos["lobularity_score"]),
        "membrane_smoothness":       float(datos["membrane_smoothness"]),
        "cell_area_px":              float(datos["cell_area_px"]),
        "perimeter_px":              float(datos["perimeter_px"]),
        "mean_r":                    float(datos["mean_r"]),
        "mean_g":                    float(datos["mean_g"]),
        "mean_b":                    float(datos["mean_b"]),
        "stain_intensity":           float(datos["stain_intensity"]),
        "wbc_count_per_ul":          float(datos["wbc_count_per_ul"]),
        "rbc_count_millions_per_ul": float(datos["rbc_count_millions_per_ul"]),
        "hemoglobin_g_dl":           float(datos["hemoglobin_g_dl"]),
        "hematocrit_pct":            float(datos["hematocrit_pct"]),
        "platelet_count_per_ul":     float(datos["platelet_count_per_ul"]),
        "mcv_fl":                    float(datos["mcv_fl"]),
        "mchc_g_dl":                 float(datos["mchc_g_dl"]),
        "patient_age_group":         float(datos["patient_age_group"]),
        "patient_sex":               float(datos["patient_sex"]),
    }

    try:
        df = pd.DataFrame([fila])[features]
        df_scaled   = scaler.transform(df)
        prediccion  = modelo.predict(df_scaled)[0]
        probas      = modelo.predict_proba(df_scaled)[0]
        probabilidad = float(probas[1])

        etiqueta = "Anormal" if prediccion == 1 else "Normal"
        riesgo   = "ALTO" if probabilidad > 0.7 else "MEDIO" if probabilidad > 0.4 else "BAJO"

        return JsonResponse({
            "ok": True,
            "diagnostico":  etiqueta,
            "es_normal":    etiqueta == "Normal",
            "probabilidad": round(probabilidad * 100, 2),
            "riesgo":       riesgo,
        })

    except Exception as exc:
        logger.exception("Error en predicción")
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)