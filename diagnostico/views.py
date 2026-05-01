from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import CelulaForm

logger = logging.getLogger(__name__)

MAX_MUESTRAS_JSON = 50


def _predecir_una_fila(
    fila: dict[str, float],
    features: list[str],
    scaler: Any,
    modelo: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        df = pd.DataFrame([fila])[features]
        df_scaled = scaler.transform(df)
        prediccion = modelo.predict(df_scaled)[0]
        probas = modelo.predict_proba(df_scaled)[0]
        probabilidad = float(probas[1])
        etiqueta = "Anormal" if prediccion == 1 else "Normal"
        riesgo = "ALTO" if probabilidad > 0.7 else "MEDIO" if probabilidad > 0.4 else "BAJO"
        return {
            "diagnostico": etiqueta,
            "es_normal": etiqueta == "Normal",
            "probabilidad": round(probabilidad * 100, 2),
            "riesgo": riesgo,
        }, None
    except Exception as exc:
        logger.exception("Error en predicción")
        return None, str(exc)


def _fila_desde_objeto(obj: Any, features: list[str]) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(obj, dict):
        return None, "Cada muestra debe ser un objeto JSON."
    missing = [k for k in features if k not in obj]
    if missing:
        return None, f"Faltan claves obligatorias: {', '.join(missing)}"
    fila: dict[str, float] = {}
    for k in features:
        try:
            val = obj[k]
            if val is None:
                return None, f"El campo '{k}' no puede ser nulo."
            fila[k] = float(val)
        except (TypeError, ValueError):
            return None, f"El campo '{k}' debe ser numérico."
    return fila, None


def _extraer_lista_muestras(body: Any) -> list[Any] | None:
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for key in ("muestras", "samples", "registros"):
            if key in body and isinstance(body[key], list):
                return body[key]
        return [body]
    return None


@require_GET
def index(request):
    form = CelulaForm()
    return render(request, "diagnostico/index.html", {"form": form})


@require_POST
def predecir(request):
    form = CelulaForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "error": "Datos inválidos.",
                "errores_campo": form.errors,
            },
            status=400,
        )

    config = apps.get_app_config("diagnostico")
    modelo = config.ml_model
    scaler = config.ml_scaler
    features = config.ml_features

    if modelo is None or scaler is None:
        return JsonResponse(
            {"ok": False, "error": "Modelo no disponible en el servidor."},
            status=503,
        )

    datos = form.cleaned_data
    try:
        fila = {k: float(datos[k]) for k in features}
    except KeyError as exc:
        return JsonResponse(
            {"ok": False, "error": f"Falta el campo esperado por el modelo: {exc.args[0]}"},
            status=400,
        )

    out, err = _predecir_una_fila(fila, features, scaler, modelo)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=500)
    return JsonResponse({"ok": True, **out})


@require_POST
def predecir_json(request):
    ct = (request.content_type or "").split(";")[0].strip().lower()
    if ct != "application/json":
        return JsonResponse(
            {"ok": False, "error": "Content-Type debe ser application/json."},
            status=415,
        )

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido o codificación incorrecta."}, status=400)

    muestras = _extraer_lista_muestras(body)
    if muestras is None:
        return JsonResponse(
            {"ok": False, "error": "Se esperaba un objeto, una lista de objetos o un objeto con la clave 'muestras'."},
            status=400,
        )

    if len(muestras) == 0:
        return JsonResponse({"ok": False, "error": "La lista de muestras está vacía."}, status=400)

    if len(muestras) > MAX_MUESTRAS_JSON:
        return JsonResponse(
            {
                "ok": False,
                "error": f"Máximo {MAX_MUESTRAS_JSON} muestras por solicitud.",
            },
            status=400,
        )

    config = apps.get_app_config("diagnostico")
    modelo = config.ml_model
    scaler = config.ml_scaler
    features = config.ml_features

    if modelo is None or scaler is None or not features:
        return JsonResponse(
            {"ok": False, "error": "Modelo no disponible en el servidor."},
            status=503,
        )

    resultados: list[dict[str, Any]] = []
    for i, raw in enumerate(muestras):
        fila, err_parse = _fila_desde_objeto(raw, features)
        if err_parse:
            resultados.append({"indice": i, "ok": False, "error": err_parse})
            continue
        pred, err_pred = _predecir_una_fila(fila, features, scaler, modelo)
        if err_pred:
            resultados.append({"indice": i, "ok": False, "error": err_pred})
        else:
            resultados.append({"indice": i, "ok": True, **pred, "datos": fila})

    return JsonResponse(
        {
            "ok": True,
            "total": len(resultados),
            "exitosos": sum(1 for r in resultados if r.get("ok")),
            "resultados": resultados,
        }
    )
