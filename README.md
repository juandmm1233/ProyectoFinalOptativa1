# BioCell AI  Autores: Juan Diego Martinez Morales, Kevin Julian Guerrero, Jhonantan Alejandro Beltran

**Sistema web para el diagnóstico automatizado de células sanguíneas**, construido sobre Django 5 y un modelo Random Forest pre‑entrenado (`scikit-learn`).

La aplicación permite ingresar las características morfológicas de una célula (Área, Perímetro, Concavidad y Textura) y devuelve, mediante AJAX, un diagnóstico **Normal** o **Anormal** junto con la probabilidad asociada, todo dentro de una interfaz limpia y profesional con estilo *Smart Casual* médico.

---

## ✅ Historial de cambios y correcciones

### v2.0 — Reentrenamiento completo del modelo (03/05/2026)

**Problemas resueltos:**

1. **Data Leakage grave en el modelo original** (`ia_celulas_sanguineas_rf_v1.pkl`):
   - Las variables `cytodiffusion_anomaly_score`, `cytodiffusion_classification_confidence`, `labeller_confidence_score`, `disease_category` (correlación 0.83 con el target) y `cell_type` se generaron **después** de conocer el diagnóstico. El modelo hacía trampa → 100% accuracy falso.

2. **Valores escalados fuera de rango (error 19.93)**:
   - El `StandardScaler` recibía valores imposibles en los JSONs de prueba (fuera del rango real del dataset). Por ejemplo, `stain_intensity: 2.1` cuando el máximo real es `1.0`, o `cell_area_px: 1200` cuando el máximo es `901`.
   - Esto generaba puntuaciones Z absurdas (19.93 desviaciones estándar) que el Random Forest clasificaba siempre como anomalía.

3. **`feature_names_in_: N/A`**:
   - El modelo anterior fue entrenado con `X_train.values` (ndarray puro), perdiendo los nombres de columnas. Si el orden del JSON no coincidía exactamente con el orden de entrenamiento, el modelo recibía las variables en posiciones equivocadas.

**Solución aplicada (rama de trabajo con modelo “limpio”):**
- Reentrenamiento con **solo features morfológicas y clínicas reales**, sin variables de leakage.
- Artefactos habituales en esa línea: `modelo_anomalias.pkl`, `scaler_anomalias.pkl`, `features_modelo.json`.

**En la rama `main` por defecto** el proyecto usa `core/ml_models/ia_celulas_sanguineas_rf_v1.pkl` (ver `ML_MODEL_PATH` en `biocell_ai/settings.py`). La imputación de las restantes características cuando solo se envían las 4 del formulario se hace en `diagnostico/views.py` mediante `FEATURE_BASELINE`.

**Resultados del modelo reentrenado (referencia):**

| Enfoque | Accuracy | Observación |
|---|---|---|
| Con leakage total | 100.00% | ❌ Falso |
| Sin disease_category | 99.91% | ❌ Aún con leakage |
| **Modelo final limpio** | **96.94%** | ✅ Honesto y real |

- ROC-AUC: **0.9977**
- Solo **36 errores** en 1176 predicciones

---

## Estructura del proyecto

```
ProyectoFinalOptativa1/
├── manage.py
├── requirements.txt
├── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── biocell_ai/                 # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   └── ml_models/
│       └── ia_celulas_sanguineas_rf_v1.pkl
└── diagnostico/                # App principal
    ├── __init__.py
    ├── apps.py                 # Carga el modelo .pkl una sola vez
    ├── forms.py                # Formulario con validación
    ├── views.py                # index (GET) y predecir (POST -> JSON)
    ├── urls.py
    ├── admin.py
    ├── models.py
    ├── tests.py
    ├── migrations/
    ├── templates/diagnostico/
    │   ├── base.html
    │   └── index.html
    └── static/diagnostico/
        ├── css/styles.css
        └── js/app.js
```

---

## Requisitos

- Python 3.11 o superior.
- El archivo `ia_celulas_sanguineas_rf_v1.pkl` debe existir en `core/ml_models/` (ruta configurada como `ML_MODEL_PATH`).

---

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell)
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

---

## Ejecución

```bash
python manage.py migrate
python manage.py runserver
```

Luego abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en el navegador.

Al iniciar el servidor, en la consola verás un mensaje similar a:

```
[BioCell AI] Modelo cargado correctamente desde .../core/ml_models/ia_celulas_sanguineas_rf_v1.pkl
```

confirmando que el modelo Random Forest se cargó **una sola vez** en memoria a través de `diagnostico/apps.py`.

---

## Rangos válidos de las variables (referencia del dataset)

> ⚠️ Valores muy alejados de la distribución de entrenamiento pueden sesgar la predicción. El formulario web solo envía **Área**, **Perímetro**, **Concavidad** y **Textura**; el resto del vector se rellena con `FEATURE_BASELINE` en `diagnostico/views.py`.

| Variable | Mínimo | Máximo | Unidad |
|---|---|---|---|
| `cell_diameter_um` | ~4 | ~18 | μm |
| `nucleus_area_pct` | ~5 | ~90 | % |
| `chromatin_density` | 0.0 | 1.0 | — |
| `cytoplasm_ratio` | ~0.1 | ~0.95 | — |
| `circularity` | ~0.1 | ~1.0 | — |
| `eccentricity` | ~0.0 | ~0.99 | — |
| `granularity_score` | ~0.0 | ~5.0 | — |
| `lobularity_score` | ~0.0 | ~5.0 | — |
| `membrane_smoothness` | ~0.1 | ~1.0 | — |
| `cell_area_px` | 10 | 901 | px |
| `perimeter_px` | 8 | 128 | px |
| `mean_r` | 0 | 255 | — |
| `mean_g` | 0 | 255 | — |
| `mean_b` | 0 | 255 | — |
| `stain_intensity` | 0.307 | 1.0 | — |
| `wbc_count_per_ul` | ~2000 | ~60000 | /μL |
| `rbc_count_millions_per_ul` | ~1.5 | ~6.5 | millones/μL |
| `hemoglobin_g_dl` | ~5.0 | ~18.0 | g/dL |
| `hematocrit_pct` | ~15 | ~55 | % |
| `platelet_count_per_ul` | ~50000 | ~999000 | /μL |
| `mcv_fl` | ~60 | ~120 | fL |
| `mchc_g_dl` | ~25 | ~38 | g/dL |
| `patient_age_group` | 0 = Adult | 1 = Elderly | 2 = Pediatric |
| `patient_sex` | 0 = F | 1 = M | — |

---

## Endpoints

| Método | Ruta          | Descripción                                                                 |
|--------|---------------|-----------------------------------------------------------------------------|
| GET    | `/`           | Renderiza la interfaz con el formulario.                                    |
| POST   | `/predecir/`  | Recibe los datos morfológicos y devuelve un JSON con el diagnóstico.        |

### Ejemplo de respuesta JSON de `/predecir/`

```json
{
  "ok": true,
  "diagnostico": "Normal",
  "es_normal": true,
  "probabilidad": 92.34,
  "datos": {
    "area": 654.89,
    "perimetro": 98.45,
    "concavidad": 0.1245,
    "textura": 17.33
  }
}
```

---

## Despliegue con Docker

El proyecto incluye un `Dockerfile` y un `docker-compose.yml` listos para usar. La imagen empaqueta Django, el modelo `.pkl`, gunicorn como WSGI server y WhiteNoise para servir los archivos estáticos.

### Opción A — `docker compose` (recomendado)

```bash
docker compose up --build
```

Esto construye la imagen, levanta el servicio `web` y expone la aplicación en [http://localhost:8000](http://localhost:8000). Para ejecutarlo en segundo plano usa `-d`:

```bash
docker compose up --build -d
docker compose logs -f web      # ver logs
docker compose down             # detener
```

### Opción B — `docker` directo

```bash
docker build -t biocell-ai .
docker run --rm -p 8000:8000 --name biocell-ai biocell-ai
```

### Detalles importantes

- La imagen se basa en `python:3.12-slim` y corre como un usuario sin privilegios (`biocell`).
- Durante la build se ejecuta `python manage.py collectstatic --noinput` para que WhiteNoise pueda servir el CSS / JS.
- El modelo `ia_celulas_sanguineas_rf_v1.pkl` viaja **dentro** de la imagen (vía `COPY . .`). En `docker-compose.yml` además se monta `./core/ml_models` como volumen de solo lectura, lo que permite intercambiar el modelo sin reconstruir la imagen.
- La base SQLite se persiste en el volumen nombrado `biocell_db`.

---

## Notas técnicas

- **Carga del modelo**: se realiza en `DiagnosticoConfig.ready()` con `joblib.load(...)` y queda disponible en `apps.get_app_config("diagnostico").ml_model`. Esto evita relectura del `.pkl` en cada petición.
- **Vector de entrada**: el modelo Random Forest fue entrenado con **27 features**. El formulario solo recoge 4 (Área → `cell_area_px`, Perímetro → `perimeter_px`, Concavidad → proxy en `circularity`, Textura → `chromatin_density`); las demás se rellenan con `FEATURE_BASELINE` antes de inferir (`diagnostico/views.py`). Los nombres y el orden están en `DiagnosticoConfig.feature_names`.
- **Validación**: doble capa de validación, en cliente (JavaScript) y en servidor (`forms.CelulaForm`).
- **Frontend**: AJAX con `fetch`, sin dependencias externas, y tipografía *Inter* con paleta de blancos, azules y grises.

---

## Aviso

Esta herramienta es un **sistema de apoyo diagnóstico** y **no sustituye** el criterio clínico de un profesional de la salud.
