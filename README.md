BioCell AI
Sistema web para el diagnóstico automatizado de células sanguíneas, construido sobre Django 5 y un modelo Random Forest pre‑entrenado (scikit-learn).
La aplicación permite ingresar las características morfológicas de una célula y devuelve, mediante AJAX, un diagnóstico Normal o Anormal junto con la probabilidad asociada, todo dentro de una interfaz limpia y profesional con estilo Smart Casual médico.

✅ Historial de cambios y correcciones
v2.0 — Reentrenamiento completo del modelo (03/05/2026)
Problemas resueltos:

Data Leakage grave en el modelo original (ia_celulas_sanguineas_rf_v1.pkl):

Las variables cytodiffusion_anomaly_score, cytodiffusion_classification_confidence, labeller_confidence_score, disease_category (correlación 0.83 con el target) y cell_type se generaron después de conocer el diagnóstico. El modelo hacía trampa → 100% accuracy falso.


Valores escalados fuera de rango (error 19.93):

El StandardScaler recibía valores imposibles en los JSONs de prueba (fuera del rango real del dataset). Por ejemplo, stain_intensity: 2.1 cuando el máximo real es 1.0, o cell_area_px: 1200 cuando el máximo es 901.
Esto generaba puntuaciones Z absurdas (19.93 desviaciones estándar) que el Random Forest clasificaba siempre como anomalía.


feature_names_in_: N/A:

El modelo anterior fue entrenado con X_train.values (ndarray puro), perdiendo los nombres de columnas. Si el orden del JSON no coincidía exactamente con el orden de entrenamiento, el modelo recibía las variables en posiciones equivocadas.



Solución aplicada:

Reentrenamiento con solo 24 features morfológicas y clínicas reales, sin variables de leakage.
Entrenamiento con modelo.fit(X_train, y_train) pasando el DataFrame directamente → feature_names_in_ guardado.
Tres archivos nuevos reemplazan al .pkl original: modelo_anomalias.pkl, scaler_anomalias.pkl, features_modelo.json.

Resultados del nuevo modelo:
EnfoqueAccuracyObservaciónCon leakage total100.00%❌ FalsoSin disease_category99.91%❌ Aún con leakageModelo final limpio96.94%✅ Honesto y real

ROC-AUC: 0.9977
Solo 36 errores en 1176 predicciones


Estructura del proyecto
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
│       ├── modelo_anomalias.pkl       ← Modelo RF limpio (v2)
│       ├── scaler_anomalias.pkl       ← StandardScaler del modelo limpio
│       └── features_modelo.json       ← Orden exacto de las 24 features
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

Requisitos

Python 3.11 o superior.
scikit-learn 1.7.2 (versión con la que se entrenó el modelo).
Los archivos modelo_anomalias.pkl, scaler_anomalias.pkl y features_modelo.json deben existir en core/ml_models/.


Instalación
bashpython -m venv env
env\Scripts\activate          # Windows (PowerShell)
# source env/bin/activate     # macOS / Linux

pip install -r requirements.txt

Ejecución
bashpython manage.py migrate
python manage.py runserver
Luego abre http://127.0.0.1:8000/ en el navegador.

Rangos válidos de las variables

⚠️ Los valores ingresados deben estar dentro del rango real del dataset de entrenamiento. Valores fuera de rango generan puntuaciones Z absurdas y predicciones incorrectas.

VariableMínimoMáximoUnidadcell_diameter_um~4~18μmnucleus_area_pct~5~90%chromatin_density0.01.0—cytoplasm_ratio~0.1~0.95—circularity~0.1~1.0—eccentricity~0.0~0.99—granularity_score~0.0~5.0—lobularity_score~0.0~5.0—membrane_smoothness~0.1~1.0—cell_area_px10901pxperimeter_px8128pxmean_r0255—mean_g0255—mean_b0255—stain_intensity0.3071.0—wbc_count_per_ul~2000~60000/μLrbc_count_millions_per_ul~1.5~6.5millones/μLhemoglobin_g_dl~5.0~18.0g/dLhematocrit_pct~15~55%platelet_count_per_ul~50000~999000/μLmcv_fl~60~120fLmchc_g_dl~25~38g/dLpatient_age_group0 = Adult1 = Elderly2 = Pediatricpatient_sex0 = F1 = M—

Endpoints
MétodoRutaDescripciónGET/Renderiza la interfaz con el formulario.POST/predecir/Recibe datos morfológicos (form) y devuelve JSON.POST/predecir-json/Acepta JSON crudo con una o varias muestras.

Casos de prueba JSON
Pega cualquiera de estos en la sección "Análisis desde JSON" de la interfaz.
Prueba 1 — Adulto femenino normal → esperado: NORMAL 🟢
json{
  "cell_diameter_um": 7.8,
  "nucleus_area_pct": 30.0,
  "chromatin_density": 0.30,
  "cytoplasm_ratio": 0.40,
  "circularity": 0.88,
  "eccentricity": 0.25,
  "granularity_score": 1.0,
  "lobularity_score": 0.6,
  "membrane_smoothness": 0.92,
  "cell_area_px": 300,
  "perimeter_px": 60,
  "mean_r": 200,
  "mean_g": 170,
  "mean_b": 150,
  "stain_intensity": 0.60,
  "wbc_count_per_ul": 6500,
  "rbc_count_millions_per_ul": 4.5,
  "hemoglobin_g_dl": 13.8,
  "hematocrit_pct": 41.0,
  "platelet_count_per_ul": 220000,
  "mcv_fl": 85.0,
  "mchc_g_dl": 33.0,
  "patient_age_group": 0,
  "patient_sex": 0
}
Prueba 2 — Pediátrico anómalo (leucemia) → esperado: ANORMAL 🔴
json{
  "cell_diameter_um": 14.0,
  "nucleus_area_pct": 80.0,
  "chromatin_density": 0.92,
  "cytoplasm_ratio": 0.88,
  "circularity": 0.20,
  "eccentricity": 0.95,
  "granularity_score": 4.8,
  "lobularity_score": 4.0,
  "membrane_smoothness": 0.15,
  "cell_area_px": 880,
  "perimeter_px": 125,
  "mean_r": 85,
  "mean_g": 55,
  "mean_b": 35,
  "stain_intensity": 0.92,
  "wbc_count_per_ul": 50000,
  "rbc_count_millions_per_ul": 1.8,
  "hemoglobin_g_dl": 6.5,
  "hematocrit_pct": 20.0,
  "platelet_count_per_ul": 950000,
  "mcv_fl": 115.0,
  "mchc_g_dl": 27.0,
  "patient_age_group": 2,
  "patient_sex": 1
}
Prueba 3 — Adulto mayor borderline → esperado: ANORMAL 🔴
json{
  "cell_diameter_um": 9.5,
  "nucleus_area_pct": 45.0,
  "chromatin_density": 0.55,
  "cytoplasm_ratio": 0.55,
  "circularity": 0.65,
  "eccentricity": 0.55,
  "granularity_score": 2.5,
  "lobularity_score": 2.0,
  "membrane_smoothness": 0.55,
  "cell_area_px": 500,
  "perimeter_px": 85,
  "mean_r": 150,
  "mean_g": 120,
  "mean_b": 100,
  "stain_intensity": 0.75,
  "wbc_count_per_ul": 12000,
  "rbc_count_millions_per_ul": 3.5,
  "hemoglobin_g_dl": 10.5,
  "hematocrit_pct": 32.0,
  "platelet_count_per_ul": 450000,
  "mcv_fl": 95.0,
  "mchc_g_dl": 30.0,
  "patient_age_group": 1,
  "patient_sex": 0
}
Prueba 4 — Adulto joven masculino sano → esperado: NORMAL 🟢
json{
  "cell_diameter_um": 8.0,
  "nucleus_area_pct": 28.0,
  "chromatin_density": 0.25,
  "cytoplasm_ratio": 0.35,
  "circularity": 0.90,
  "eccentricity": 0.20,
  "granularity_score": 0.8,
  "lobularity_score": 0.5,
  "membrane_smoothness": 0.95,
  "cell_area_px": 280,
  "perimeter_px": 55,
  "mean_r": 215,
  "mean_g": 185,
  "mean_b": 165,
  "stain_intensity": 0.55,
  "wbc_count_per_ul": 5500,
  "rbc_count_millions_per_ul": 5.2,
  "hemoglobin_g_dl": 15.5,
  "hematocrit_pct": 46.0,
  "platelet_count_per_ul": 200000,
  "mcv_fl": 82.0,
  "mchc_g_dl": 34.0,
  "patient_age_group": 0,
  "patient_sex": 1
}
Prueba 5 — Adulto mayor con anemia → esperado: ANORMAL 🔴
json{
  "cell_diameter_um": 11.0,
  "nucleus_area_pct": 60.0,
  "chromatin_density": 0.78,
  "cytoplasm_ratio": 0.72,
  "circularity": 0.35,
  "eccentricity": 0.80,
  "granularity_score": 3.5,
  "lobularity_score": 3.0,
  "membrane_smoothness": 0.30,
  "cell_area_px": 700,
  "perimeter_px": 110,
  "mean_r": 100,
  "mean_g": 75,
  "mean_b": 55,
  "stain_intensity": 0.88,
  "wbc_count_per_ul": 35000,
  "rbc_count_millions_per_ul": 2.5,
  "hemoglobin_g_dl": 8.0,
  "hematocrit_pct": 25.0,
  "platelet_count_per_ul": 750000,
  "mcv_fl": 105.0,
  "mchc_g_dl": 28.5,
  "patient_age_group": 1,
  "patient_sex": 0
}
Prueba 6 — Pediátrico sano → esperado: NORMAL 🟢
json{
  "cell_diameter_um": 7.2,
  "nucleus_area_pct": 25.0,
  "chromatin_density": 0.22,
  "cytoplasm_ratio": 0.30,
  "circularity": 0.91,
  "eccentricity": 0.18,
  "granularity_score": 0.7,
  "lobularity_score": 0.4,
  "membrane_smoothness": 0.96,
  "cell_area_px": 250,
  "perimeter_px": 50,
  "mean_r": 220,
  "mean_g": 190,
  "mean_b": 170,
  "stain_intensity": 0.52,
  "wbc_count_per_ul": 8000,
  "rbc_count_millions_per_ul": 4.2,
  "hemoglobin_g_dl": 12.5,
  "hematocrit_pct": 38.0,
  "platelet_count_per_ul": 280000,
  "mcv_fl": 80.0,
  "mchc_g_dl": 32.5,
  "patient_age_group": 2,
  "patient_sex": 0
}
Prueba múltiple — 3 muestras en una sola petición
json{
  "muestras": [
    {
      "cell_diameter_um": 7.8, "nucleus_area_pct": 30.0, "chromatin_density": 0.30,
      "cytoplasm_ratio": 0.40, "circularity": 0.88, "eccentricity": 0.25,
      "granularity_score": 1.0, "lobularity_score": 0.6, "membrane_smoothness": 0.92,
      "cell_area_px": 300, "perimeter_px": 60, "mean_r": 200, "mean_g": 170, "mean_b": 150,
      "stain_intensity": 0.60, "wbc_count_per_ul": 6500, "rbc_count_millions_per_ul": 4.5,
      "hemoglobin_g_dl": 13.8, "hematocrit_pct": 41.0, "platelet_count_per_ul": 220000,
      "mcv_fl": 85.0, "mchc_g_dl": 33.0, "patient_age_group": 0, "patient_sex": 0
    },
    {
      "cell_diameter_um": 14.0, "nucleus_area_pct": 80.0, "chromatin_density": 0.92,
      "cytoplasm_ratio": 0.88, "circularity": 0.20, "eccentricity": 0.95,
      "granularity_score": 4.8, "lobularity_score": 4.0, "membrane_smoothness": 0.15,
      "cell_area_px": 880, "perimeter_px": 125, "mean_r": 85, "mean_g": 55, "mean_b": 35,
      "stain_intensity": 0.92, "wbc_count_per_ul": 50000, "rbc_count_millions_per_ul": 1.8,
      "hemoglobin_g_dl": 6.5, "hematocrit_pct": 20.0, "platelet_count_per_ul": 950000,
      "mcv_fl": 115.0, "mchc_g_dl": 27.0, "patient_age_group": 2, "patient_sex": 1
    },
    {
      "cell_diameter_um": 8.0, "nucleus_area_pct": 28.0, "chromatin_density": 0.25,
      "cytoplasm_ratio": 0.35, "circularity": 0.90, "eccentricity": 0.20,
      "granularity_score": 0.8, "lobularity_score": 0.5, "membrane_smoothness": 0.95,
      "cell_area_px": 280, "perimeter_px": 55, "mean_r": 215, "mean_g": 185, "mean_b": 165,
      "stain_intensity": 0.55, "wbc_count_per_ul": 5500, "rbc_count_millions_per_ul": 5.2,
      "hemoglobin_g_dl": 15.5, "hematocrit_pct": 46.0, "platelet_count_per_ul": 200000,
      "mcv_fl": 82.0, "mchc_g_dl": 34.0, "patient_age_group": 0, "patient_sex": 1
    }
  ]
}
Resultado esperado: Muestra 1 → Normal 🟢, Muestra 2 → Anormal 🔴, Muestra 3 → Normal 🟢

Notas técnicas

Carga del modelo: se realiza en DiagnosticoConfig.ready() y queda disponible en apps.get_app_config("diagnostico").ml_model. Esto evita relectura del .pkl en cada petición.
Vector de entrada: el modelo fue entrenado con 24 features morfológicas y clínicas. El orden exacto está en features_modelo.json y es respetado por views.py mediante pd.DataFrame([fila])[feats].
Escalado: scaler_anomalias.pkl contiene el StandardScaler ajustado durante el entrenamiento. Siempre se aplica antes de llamar a modelo.predict().
Versión de scikit-learn: el modelo fue entrenado con 1.7.2. El entorno debe tener la misma versión para evitar advertencias de compatibilidad.
Validación: doble capa — cliente (JavaScript) y servidor (forms.CelulaForm).


Despliegue con Docker
bashdocker compose up --build
Accede en http://localhost:8030.
bashdocker compose up --build -d     # segundo plano
docker compose logs -f web       # ver logs
docker compose down              # detener

Aviso
Esta herramienta es un sistema de apoyo diagnóstico y no sustituye el criterio clínico de un profesional de la salud.