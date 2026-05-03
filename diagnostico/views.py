from __future__ import annotations

import json
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

MAX_MUESTRAS_JSON = 50

# Orden exacto de columnas con el que se ajustó StandardScaler + RF (ver scaler_anomalias.pkl:
# scaler.feature_names_in_). El bosque entrenado con ndarray no tiene feature_names_in_;
# el escalado es el que impone el orden del vector. Debe coincidir con core/ml_models/features_modelo.json.
EXPECTED_FEATURE_ORDER: tuple[str, ...] = (
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
    "patient_age_group",
    "patient_sex",
)


def _inference_feature_order(scaler: Any) -> list[str]:
    """
    Orden de columnas para inferencia: el StandardScaler guarda feature_names_in_ al entrenar
    con DataFrame; es la fuente de verdad frente al RF sin nombres de features.
    """
    if hasattr(scaler, "feature_names_in_"):
        arr = getattr(scaler, "feature_names_in_", None)
        if arr is not None and len(arr) > 0:
            names = [str(x) for x in np.asarray(arr).ravel().tolist()]
            exp = list(EXPECTED_FEATURE_ORDER)
            if names != exp:
                logger.warning(
                    "[BioCell AI] feature_names_in_ del scaler difiere de EXPECTED_FEATURE_ORDER; "
                    "se usa el orden del scaler (entrenamiento). scaler=%s constante=%s",
                    names,
                    exp,
                )
            return names
    return list(EXPECTED_FEATURE_ORDER)


def _fila_valores_desde_json(obj: dict[str, Any], order: list[str]) -> tuple[dict[str, float] | None, str | None]:
    """
    Construye la fila en el orden de `order` leyendo solo por nombre de clave (el orden del JSON
    en el request no importa). Requiere todas las claves; no usa defaults silenciosos.
    """
    missing = [k for k in order if k not in obj]
    if missing:
        return None, f"Faltan claves obligatorias: {', '.join(missing)}"
    fila: dict[str, float] = {}
    for k in order:
        try:
            val = obj[k]
            if val is None:
                return None, f"El campo '{k}' no puede ser nulo."
            fila[k] = float(val)
        except (TypeError, ValueError):
            return None, f"El campo '{k}' debe ser numérico."
    return fila, None


def _probabilidad_clase_anomalia(modelo: Any, probas: np.ndarray) -> float:
    """P(clase 1) usando el índice correcto según model.classes_ (orden de predict_proba)."""
    pro = np.asarray(probas, dtype=float).ravel()
    classes = getattr(modelo, "classes_", None)
    if classes is not None and len(classes) == len(pro):
        cl = np.asarray(classes).ravel()
        for j, c in enumerate(cl):
            try:
                if int(c) == 1:
                    return float(pro[j])
            except (ValueError, TypeError):
                continue
    if len(pro) > 1:
        return float(pro[1])
    return float(pro[0])


def _predecir_una_fila(
    fila: dict[str, float],
    ordered_features: list[str],
    scaler: Any,
    modelo: Any,
    *,
    debug_log: bool = False,
    muestra_idx: int | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Construye una fila en el orden exacto de ordered_features (debe coincidir con StandardScaler
    / EXPECTED_FEATURE_ORDER), escala y predice. Convención: clase 0 -> Normal, clase 1 -> Anormal.
    """
    try:
        row_values = [float(fila[name]) for name in ordered_features]
        X = pd.DataFrame([row_values], columns=ordered_features)

        if debug_log:
            prefix = f"[BioCell AI DEBUG muestra={muestra_idx}] " if muestra_idx is not None else "[BioCell AI DEBUG] "
            sfn = getattr(scaler, "feature_names_in_", None)
            mfn = getattr(modelo, "feature_names_in_", None)
            print(f"{prefix}feature_names_in_ (scaler): {list(sfn) if sfn is not None else 'N/A'}")
            print(f"{prefix}feature_names_in_ (modelo): {list(mfn) if mfn is not None else 'N/A'}")
            print(f"{prefix}columnas DataFrame: {list(X.columns)}")
            print(f"{prefix}X_raw (1 fila, orden inferencia): {row_values}")

        X_scaled = scaler.transform(X)

        if debug_log:
            prefix = f"[BioCell AI DEBUG muestra={muestra_idx}] " if muestra_idx is not None else "[BioCell AI DEBUG] "
            print(f"{prefix}X_scaled (antes de predict): {np.asarray(X_scaled).tolist()}")
            print(f"{prefix}model.classes_: {getattr(modelo, 'classes_', None)}")

        prediccion = int(modelo.predict(X_scaled)[0])
        probas = modelo.predict_proba(X_scaled)[0]
        probabilidad = _probabilidad_clase_anomalia(modelo, probas)

        # Convención explícita: 0 = Normal, 1 = Anormal (validar contra classes_ si existe)
        classes = getattr(modelo, "classes_", None)
        if classes is not None:
            cl_vals = {int(np.asarray(x).item()) for x in np.asarray(classes).ravel()}
            if cl_vals and not cl_vals.issubset({0, 1}):
                logger.warning(
                    "[BioCell AI] model.classes_ no es subconjunto de {0, 1}: %s; "
                    "se mantiene mapeo 0->Normal, 1->Anormal según la etiqueta entera predicha.",
                    classes,
                )

        es_normal = prediccion == 0
        etiqueta = "Normal" if es_normal else "Anormal"
        riesgo = "ALTO" if probabilidad > 0.7 else "MEDIO" if probabilidad > 0.4 else "BAJO"
        return {
            "diagnostico": etiqueta,
            "es_normal": es_normal,
            "probabilidad": round(probabilidad * 100, 2),
            "riesgo": riesgo,
            "clase_predicha": prediccion,
        }, None
    except Exception as exc:
        logger.exception("Error en predicción")
        return None, str(exc)


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

    if modelo is None or scaler is None:
        return JsonResponse(
            {"ok": False, "error": "Modelo no disponible en el servidor."},
            status=503,
        )

    ordered = _inference_feature_order(scaler)
    datos = form.cleaned_data
    try:
        fila = {k: float(datos[k]) for k in ordered}
    except KeyError as exc:
        return JsonResponse(
            {"ok": False, "error": f"Falta el campo esperado por el modelo: {exc.args[0]}"},
            status=400,
        )

    out, err = _predecir_una_fila(fila, ordered, scaler, modelo, debug_log=False)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=500)
    resp = {k: v for k, v in out.items() if k != "clase_predicha"}
    return JsonResponse({"ok": True, **resp})


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
    if modelo is None or scaler is None:
        return JsonResponse(
            {"ok": False, "error": "Modelo no disponible en el servidor."},
            status=503,
        )

    ordered = _inference_feature_order(scaler)
    resultados: list[dict[str, Any]] = []
    for i, raw in enumerate(muestras):
        if not isinstance(raw, dict):
            resultados.append({"indice": i, "ok": False, "error": "Cada muestra debe ser un objeto JSON."})
            continue
        fila, err_parse = _fila_valores_desde_json(raw, ordered)
        if err_parse:
            resultados.append({"indice": i, "ok": False, "error": err_parse})
            continue
        pred, err_pred = _predecir_una_fila(
            fila,
            ordered,
            scaler,
            modelo,
            debug_log=False,
            muestra_idx=i,
        )
        if err_pred:
            resultados.append({"indice": i, "ok": False, "error": err_pred})
        else:
            payload = {k: v for k, v in pred.items() if k != "clase_predicha"}
            resultados.append({"indice": i, "ok": True, **payload, "datos": fila})

    return JsonResponse(
        {
            "ok": True,
            "total": len(resultados),
            "exitosos": sum(1 for r in resultados if r.get("ok")),
            "resultados": resultados,
        }
    )
