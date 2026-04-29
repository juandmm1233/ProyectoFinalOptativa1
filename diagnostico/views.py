"""
Vistas para la app `diagnostico`.

- `index`: renderiza el formulario principal con el diseño Smart Casual.
- `predecir`: recibe vía POST los datos morfológicos, ejecuta la
  predicción usando el modelo cargado en memoria y devuelve un JSON
  con el diagnóstico ("Normal" / "Anormal") y la probabilidad.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import CelulaForm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vector base (imputación) para las 27 features que espera el modelo.
#
# El modelo Random Forest fue entrenado con un contexto hematológico
# completo. Si lo alimentamos con ceros, el ejemplo se sale por completo
# de la distribución de entrenamiento y la salida queda sesgada hacia
# "Normal". Por eso construimos un vector inicial con valores promedio
# de un adulto sano y luego sobrescribimos los índices correspondientes
# con los 4 datos morfológicos que aporta el formulario.
#
# Orden de las 27 features (definido también en DiagnosticoConfig):
#   0  cell_diameter_um                 14 stain_intensity
#   1  nucleus_area_pct                 15 wbc_count_per_ul          [CLÍNICO]
#   2  chromatin_density   ← Textura    16 rbc_count_millions_per_ul
#   3  cytoplasm_ratio                  17 hemoglobin_g_dl            [CLÍNICO]
#   4  circularity         ← Concavidad 18 hematocrit_pct             [CLÍNICO]
#   5  eccentricity                     19 platelet_count_per_ul
#   6  granularity_score                20 mcv_fl                     [CLÍNICO]
#   7  lobularity_score                 21 mchc_g_dl
#   8  membrane_smoothness              22 magnification_x
#   9  cell_area_px        ← Area       23 image_resolution_px
#  10  perimeter_px        ← Perímetro  24 cytodiffusion_anomaly_score
#  11  mean_r                           25 cytodiffusion_classification_confidence
#  12  mean_g                           26 labeller_confidence_score
#  13  mean_b
# ---------------------------------------------------------------------------
FEATURE_BASELINE: list[float] = [
    1.0,      # 0  cell_diameter_um
    1.0,      # 1  nucleus_area_pct
    0.5,      # 2  chromatin_density           (sobrescrito por Textura)
    0.5,      # 3  cytoplasm_ratio
    0.5,      # 4  circularity                 (sobrescrito por Concavidad)
    0.5,      # 5  eccentricity
    0.5,      # 6  granularity_score
    0.5,      # 7  lobularity_score
    0.5,      # 8  membrane_smoothness
    1.0,      # 9  cell_area_px                (sobrescrito por Area)
    1.0,      # 10 perimeter_px                (sobrescrito por Perímetro)
    1.0,      # 11 mean_r
    1.0,      # 12 mean_g
    1.0,      # 13 mean_b
    0.5,      # 14 stain_intensity
    7000.0,   # 15 wbc_count_per_ul             [CLÍNICO]
    1.0,      # 16 rbc_count_millions_per_ul
    14.0,     # 17 hemoglobin_g_dl              [CLÍNICO]
    42.0,     # 18 hematocrit_pct               [CLÍNICO]
    1.0,      # 19 platelet_count_per_ul
    90.0,     # 20 mcv_fl                       [CLÍNICO]
    1.0,      # 21 mchc_g_dl
    1.0,      # 22 magnification_x
    1.0,      # 23 image_resolution_px
    0.5,      # 24 cytodiffusion_anomaly_score
    0.5,      # 25 cytodiffusion_classification_confidence
    1.0,      # 26 labeller_confidence_score
]
assert len(FEATURE_BASELINE) == 27, "FEATURE_BASELINE debe tener 27 elementos."

# Índices dentro del vector de 27 donde se inyectan los datos del formulario.
# Si decides reasignar la correspondencia semántica solo cambias estos enteros.
INDEX_AREA: int = 9          # cell_area_px
INDEX_PERIMETRO: int = 10    # perimeter_px
INDEX_CONCAVIDAD: int = 4    # circularity         (proxy morfológico)
INDEX_TEXTURA: int = 2       # chromatin_density   (proxy de textura visual)


@require_GET
def index(request):
    """Renderiza la página principal con el formulario."""
    form = CelulaForm()
    return render(request, "diagnostico/index.html", {"form": form})


@require_POST
def predecir(request):
    """
    Recibe los datos del formulario por POST y devuelve la predicción
    en formato JSON para que el frontend la muestre por AJAX.
    """
    form = CelulaForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Datos inválidos. Por favor revisa el formulario.",
                "errores_campo": form.errors,
            },
            status=400,
        )

    config = apps.get_app_config("diagnostico")
    modelo = config.ml_model

    if modelo is None:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "El modelo de IA no está disponible en el servidor. "
                    "Verifica que el archivo .pkl exista en core/ml_models/."
                ),
            },
            status=503,
        )

    datos = form.cleaned_data

    # 1) Partimos del vector base con valores clínicos/morfológicos típicos
    #    de un adulto sano (evita el sesgo "todo cero → siempre Normal").
    # 2) Inyectamos los 4 datos del formulario en sus posiciones reales
    #    dentro de las 27 features que espera el modelo.
    x = np.array([FEATURE_BASELINE], dtype=float)  # shape (1, 27)
    x[0, INDEX_AREA] = datos["area"]
    x[0, INDEX_PERIMETRO] = datos["perimetro"]
    x[0, INDEX_CONCAVIDAD] = datos["concavidad"]
    x[0, INDEX_TEXTURA] = datos["textura"]

    assert x.shape == (1, 27), f"Se esperaba shape (1, 27), se obtuvo {x.shape}"

    try:
        prediccion = modelo.predict(x)[0]
        probas = (
            modelo.predict_proba(x)[0]
            if hasattr(modelo, "predict_proba")
            else None
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[BioCell AI] Error al ejecutar la predicción.")
        return JsonResponse(
            {"ok": False, "error": f"Error al procesar la predicción: {exc}"},
            status=500,
        )

    etiqueta, probabilidad = _interpretar_resultado(modelo, prediccion, probas)

    return JsonResponse(
        {
            "ok": True,
            "diagnostico": etiqueta,
            "es_normal": etiqueta.lower() == "normal",
            "probabilidad": round(probabilidad * 100, 2),
            "datos": {
                "area": datos["area"],
                "perimetro": datos["perimetro"],
                "concavidad": datos["concavidad"],
                "textura": datos["textura"],
            },
        }
    )


def _interpretar_resultado(modelo: Any, prediccion: Any, probas) -> tuple[str, float]:
    """
    Convierte la salida cruda del modelo a una etiqueta legible
    ("Normal" / "Anormal") y la probabilidad asociada.

    Soporta modelos entrenados con etiquetas de texto o numéricas.
    """
    etiqueta_raw = str(prediccion).strip().lower()

    if etiqueta_raw in {"0", "normal", "benigno", "benign"}:
        etiqueta = "Normal"
    elif etiqueta_raw in {"1", "anormal", "maligno", "malignant"}:
        etiqueta = "Anormal"
    else:
        etiqueta = "Anormal" if etiqueta_raw not in {"0"} else "Normal"

    probabilidad = 0.0
    if probas is not None and hasattr(modelo, "classes_"):
        try:
            indice = list(modelo.classes_).index(prediccion)
            probabilidad = float(probas[indice])
        except (ValueError, IndexError):
            probabilidad = float(np.max(probas))
    elif probas is not None:
        probabilidad = float(np.max(probas))

    return etiqueta, probabilidad
