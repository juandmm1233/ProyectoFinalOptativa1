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
- **Vector de entrada**: el modelo Random Forest fue entrenado con **27 features**. Como el formulario solo recoge 4 (Area, Perímetro, Concavidad, Textura), `views.py` construye un `np.zeros((1, 27))` y coloca esos 4 valores en las primeras 4 posiciones; las 23 restantes quedan en `0.0`. La lista completa y ordenada de features está documentada en `diagnostico/apps.py` (`DiagnosticoConfig.feature_names`).
- **Validación**: doble capa de validación, en cliente (JavaScript) y en servidor (`forms.CelulaForm`).
- **Frontend**: AJAX con `fetch`, sin dependencias externas, y tipografía *Inter* con paleta de blancos, azules y grises.

---

## Aviso

Esta herramienta es un **sistema de apoyo diagnóstico** y **no sustituye** el criterio clínico de un profesional de la salud.
