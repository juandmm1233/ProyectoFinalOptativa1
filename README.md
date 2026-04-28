# BioCell AI

**Sistema web para el diagnóstico automatizado de células sanguíneas**, construido sobre Django 5 y un modelo Random Forest pre‑entrenado (`scikit-learn`).

La aplicación permite ingresar las características morfológicas de una célula (Área, Perímetro, Concavidad y Textura) y devuelve, mediante AJAX, un diagnóstico **Normal** o **Anormal** junto con la probabilidad asociada, todo dentro de una interfaz limpia y profesional con estilo *Smart Casual* médico.

---

## Estructura del proyecto

```
ProyectoFinalOptativa1/
├── manage.py
├── requirements.txt
├── README.md
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
- El archivo `ia_celulas_sanguineas_rf_v1.pkl` debe existir en `core/ml_models/`.

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

## Notas técnicas

- **Carga del modelo**: se realiza en `DiagnosticoConfig.ready()` con `joblib.load(...)` y queda disponible en `apps.get_app_config("diagnostico").ml_model`. Esto evita relectura del `.pkl` en cada petición.
- **Orden de las features**: la app envía las features al modelo en el orden `[area, perimetro, concavidad, textura]`. Si tu modelo fue entrenado con otros nombres o un orden distinto, ajusta `feature_names` en `diagnostico/apps.py` y, si es necesario, los campos de `forms.py`.
- **Validación**: doble capa de validación, en cliente (JavaScript) y en servidor (`forms.CelulaForm`).
- **Frontend**: AJAX con `fetch`, sin dependencias externas, y tipografía *Inter* con paleta de blancos, azules y grises.

---

## Aviso

Esta herramienta es un **sistema de apoyo diagnóstico** y **no sustituye** el criterio clínico de un profesional de la salud.
