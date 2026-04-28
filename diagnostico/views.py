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
import pandas as pd
from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import CelulaForm

logger = logging.getLogger(__name__)


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
    feature_names: list[str] = config.feature_names

    try:
        x = pd.DataFrame(
            [[datos["area"], datos["perimetro"], datos["concavidad"], datos["textura"]]],
            columns=feature_names,
        )
    except Exception:  # noqa: BLE001
        x = np.array(
            [[datos["area"], datos["perimetro"], datos["concavidad"], datos["textura"]]],
            dtype=float,
        )

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
