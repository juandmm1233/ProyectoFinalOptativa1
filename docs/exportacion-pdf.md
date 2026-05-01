# Exportación a PDF en BioCell AI

Este documento describe cómo está implementada la función **«Exportar Reporte a PDF»** en el frontend del proyecto: qué librería se usa, qué parte del DOM se captura y cómo encajan las piezas entre el HTML, el CSS y el JavaScript.

---

## Objetivo

Permitir que el usuario descargue un archivo **`Reporte_Diagnostico_BioCell.pdf`** con una captura visual del bloque **«Resultado del análisis»** (una sola predicción desde el formulario, error del servidor, o bien tarjetas / tabla cuando el análisis viene de JSON).

La generación ocurre **en el navegador** (cliente). No hay un endpoint Django que construya el PDF.

---

## Librería: html2pdf.js

Se carga **html2pdf.js** desde CDN (bundle que incluye dependencias como **jsPDF** y **html2canvas**):

- URL: `https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js`
- Ubicación en el proyecto: al final de `diagnostico/templates/diagnostico/index.html`, en el bloque `extra_js`, **antes** de `app.js`, para que exista la función global `html2pdf` cuando se ejecute nuestro código.

**Idea general:** `html2canvas` “fotografía” un elemento del DOM (como imagen), y **jsPDF** coloca esa imagen en páginas PDF. **html2pdf.js** encadena ambos pasos con una API sencilla (`.set(...).from(elemento).save()`).

---

## Estructura HTML

### Botón fuera de la tarjeta de resultados

El botón **no** está dentro del `<article id="resultado">`. Está en un contenedor hermano:

```text
.result-column
├── .result-toolbar.no-print   ← botón «Exportar Reporte a PDF»
└── article#resultado          ← solo esto se convierte en PDF
```

Motivos:

1. El PDF debe mostrar lo mismo que la tarjeta de resultados, **sin** el botón de exportación.
2. La clase `no-print` sirve para reglas `@media print` si el usuario imprime desde el navegador (el botón puede ocultarse).

El botón tiene `id="btn-export-pdf"` para enlazarlo desde `app.js`.

### Elemento capturado

La exportación usa **`document.getElementById("resultado")`**, es decir, el `<article class="card card--result">` que contiene:

- Cabecera (“Resultado del análisis”).
- Estados conmutados por CSS según `data-state`: vacío, carga, error, éxito (formulario) o lote JSON (tarjetas o tabla).

Solo el bloque visible según `data-state` se pinta en pantalla; el resto suele tener `display: none`. **html2canvas** captura el nodo tal como se renderiza (lo visible en ese momento).

---

## JavaScript (`diagnostico/static/diagnostico/js/app.js`)

### Referencia al botón

```javascript
const btnExportPdf = document.getElementById("btn-export-pdf");
```

### `setState(state)` y el botón habilitado / deshabilitado

Cada vez que cambia el estado de la tarjeta de resultados (`empty`, `loading`, `success`, `success-batch`, `error`), se llama a **`syncExportPdfButton()`**:

- **Habilitado** si hay algo exportable: `success`, `success-batch` o `error`.
- **Deshabilitado** si está `empty` o `loading`.

Así se evita exportar cuando no hay diagnóstico o mientras llega la respuesta del servidor.

Al cargar la página se ejecuta **`syncExportPdfButton()`** una vez al final del script para alinear el botón con el estado inicial (`empty` → deshabilitado).

### Clic en el botón → `exportResultadoPdf()`

1. **Comprueba que exista `html2pdf`** (si el CDN falló o está bloqueado, se muestra un mensaje).
2. **Comprueba `data-state`** del `#resultado`: no permite exportar en `empty` ni `loading`.
3. **Arma el objeto de opciones** `opt` (ver siguiente sección).
4. **Feedback visual:** añade la clase `is-loading` al botón y lo deshabilita durante la generación.
5. **Llama a la API encadenada:**
   - `html2pdf().set(opt).from(resultadoCard)` — asocia el elemento y la configuración.
   - `.save()` — dispara la descarga del PDF con el nombre configurado.
6. **Al terminar** (Promise resuelta, error capturado o fallback por timeout): función `done()` quita `is-loading` y vuelve a sincronizar el estado del botón con `syncExportPdfButton()`.

Compatibilidad: si `.save()` no devuelve una `Promise` (versiones antiguas), se usa un **`setTimeout`** de respaldo para llamar a `done()` y no dejar el botón colgado.

---

## Opciones de configuración (`opt`)

| Opción | Valor usado | Rol |
|--------|-------------|-----|
| `margin` | `10` | Márgenes del PDF (en la unidad que use jsPDF con la config actual; aquí va ligado a `unit: "mm"`). |
| `filename` | `"Reporte_Diagnostico_BioCell.pdf"` | Nombre del archivo descargado. |
| `image.type` / `image.quality` | `jpeg` / `0.98` | Cómo se comprime la captura raster al incrustarla en el PDF. |
| `html2canvas.scale` | `2` | Mayor resolución de la captura (más nitidez, más trabajo en CPU). |
| `html2canvas.useCORS` | `true` | Ayuda con recursos externos que permitan CORS (p. ej. fuentes o imágenes remotas). |
| `html2canvas.letterRendering` | `true` | Mejora el renderizado de texto en algunos casos. |
| `html2canvas.scrollY` | `0` | Evita desfases por scroll vertical al capturar. |
| `html2canvas.windowWidth` | ancho del documento | Contexto de ancho para el canvas. |
| `jsPDF.unit` / `format` / `orientation` | `mm`, `a4`, `portrait` | Tamaño y orientación de página. |
| `pagebreak.mode` | `["avoid-all", "css", "legacy"]` | Heurísticas para partir contenido largo entre páginas. |

---

## CSS relacionado

En `diagnostico/static/diagnostico/css/styles.css`:

- **`.btn--export-pdf`**: aspecto del botón (estilo acorde al resto de la UI).
- **`.btn--export-pdf.is-loading`**: opacidad y bloqueo de clics mientras se genera el PDF.
- **`@media print { .no-print { display: none !important; } }`**: oculta elementos marcados como `no-print` si el usuario usa **Imprimir** del navegador (el flujo principal de PDF sigue siendo **html2pdf**, no la impresión del sistema).

---

## Limitaciones prácticas

- El resultado es una **rasterización** del HTML: puede haber pequeñas diferencias respecto a la pantalla (fuentes web, sombras muy complejas, animaciones congeladas en un frame).
- Si el CDN de **html2pdf.js** no carga (sin red, bloqueador, etc.), la exportación no funcionará hasta que el script esté disponible.

---

## Resumen de archivos

| Archivo | Qué aporta |
|---------|------------|
| `diagnostico/templates/diagnostico/index.html` | Botón, contenedor `result-toolbar`, `<article id="resultado">`, script CDN de html2pdf.js. |
| `diagnostico/static/diagnostico/js/app.js` | `syncExportPdfButton`, `exportResultadoPdf`, integración con `setState`, listener del botón. |
| `diagnostico/static/diagnostico/css/styles.css` | Estilos del botón, `is-loading`, `@media print` para `.no-print`. |

---

## Flujo en una frase

**Cambias el estado de la tarjeta → se actualiza si el botón está activo → al hacer clic, html2pdf convierte `#resultado` en imagen(es) y las empaqueta en un PDF A4 que se descarga con nombre fijo.**
