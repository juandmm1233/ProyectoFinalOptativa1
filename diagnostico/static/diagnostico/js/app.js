/* =========================================================
   BioCell AI — Frontend (formulario + JSON, tarjetas / tabla)
   ========================================================= */

(function () {
    "use strict";

    const form = document.getElementById("form-celula");
    const submitBtn = document.getElementById("btn-submit");
    const resetBtn = document.getElementById("btn-reset");
    const resultadoCard = document.getElementById("resultado");

    const jsonInput = document.getElementById("json-input");
    const jsonFile = document.getElementById("json-file");
    const jsonFileName = document.getElementById("json-file-name");
    const btnJsonAnalizar = document.getElementById("btn-json-analizar");
    const btnJsonLimpiar = document.getElementById("btn-json-limpiar");

    /** Orden estable para el resumen de variables (coincide con el modelo). */
    const FEATURE_DISPLAY_ORDER = [
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
    ];

    const VAR_LABELS = {
        cell_diameter_um: "Diámetro celular (μm)",
        nucleus_area_pct: "Área núcleo (%)",
        chromatin_density: "Densidad cromatina",
        cytoplasm_ratio: "Ratio citoplasma",
        circularity: "Circularidad",
        eccentricity: "Excentricidad",
        granularity_score: "Granularidad",
        lobularity_score: "Lobularidad",
        membrane_smoothness: "Suavidad membrana",
        cell_area_px: "Área celular (px)",
        perimeter_px: "Perímetro (px)",
        mean_r: "Color medio R",
        mean_g: "Color medio G",
        mean_b: "Color medio B",
        stain_intensity: "Intensidad tinción",
        wbc_count_per_ul: "Leucocitos (WBC/μL)",
        rbc_count_millions_per_ul: "Eritrocitos (millones/μL)",
        hemoglobin_g_dl: "Hemoglobina (g/dL)",
        hematocrit_pct: "Hematocrito (%)",
        platelet_count_per_ul: "Plaquetas (/μL)",
        mcv_fl: "VCM — MCV (fL)",
        mchc_g_dl: "CHCM — MCHC (g/dL)",
        patient_age_group: "Grupo de edad (0–3)",
        patient_sex: "Sexo (0 F / 1 M)",
    };

    const UMBRAL_TABLA = 3;

    if (!form || !resultadoCard) return;

    const PREDICT_URL = window.BIOCELL_PREDICT_URL || "/predecir/";
    const PREDICT_JSON_URL = window.BIOCELL_PREDICT_JSON_URL || "/predecir-json/";

    function getCSRFToken() {
        const input = document.querySelector("input[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function setState(state) {
        resultadoCard.setAttribute("data-state", state);
    }

    function setLoading(isLoading) {
        submitBtn.classList.toggle("is-loading", isLoading);
        submitBtn.disabled = isLoading;
    }

    function setJsonLoading(isLoading) {
        if (!btnJsonAnalizar) return;
        btnJsonAnalizar.classList.toggle("is-loading", isLoading);
        btnJsonAnalizar.disabled = isLoading;
    }

    function clearFieldErrors() {
        form.querySelectorAll(".form__error").forEach((el) => {
            el.textContent = "";
        });
        form.querySelectorAll(".form-input").forEach((el) => {
            el.classList.remove("is-invalid");
        });
    }

    function showFieldError(name, message) {
        const errorEl = form.querySelector(`[data-error-for="${name}"]`);
        const input = form.querySelector(`[name="${name}"]`);
        if (errorEl) errorEl.textContent = message;
        if (input) input.classList.add("is-invalid");
    }

    function validarCliente(formData) {
        let valido = true;
        clearFieldErrors();

        const camposNumericos = [
            "cell_diameter_um", "nucleus_area_pct", "chromatin_density",
            "cytoplasm_ratio", "circularity", "eccentricity",
            "granularity_score", "lobularity_score", "membrane_smoothness",
            "cell_area_px", "perimeter_px", "mean_r", "mean_g", "mean_b",
            "stain_intensity", "wbc_count_per_ul", "rbc_count_millions_per_ul",
            "hemoglobin_g_dl", "hematocrit_pct", "platelet_count_per_ul",
            "mcv_fl", "mchc_g_dl",
        ];

        for (const campo of camposNumericos) {
            const valor = formData.get(campo);
            if (valor === null || valor === "") {
                showFieldError(campo, "Este campo es obligatorio.");
                valido = false;
                continue;
            }
            if (Number.isNaN(Number(valor))) {
                showFieldError(campo, "Debe ser un número válido.");
                valido = false;
            }
        }

        const selAge = formData.get("patient_age_group");
        const selSex = formData.get("patient_sex");
        if (selAge === null || selAge === "") {
            showFieldError("patient_age_group", "Seleccione un grupo de edad.");
            valido = false;
        }
        if (selSex === null || selSex === "") {
            showFieldError("patient_sex", "Seleccione sexo.");
            valido = false;
        }

        return valido;
    }

    function formatNumero(valor) {
        if (valor === null || valor === undefined) return "—";
        const num = Number(valor);
        if (Number.isNaN(num)) return String(valor);
        return num.toLocaleString("es-CO", {
            maximumFractionDigits: 4,
            minimumFractionDigits: 0,
        });
    }

    function fillSummaryInputsFromDatos(datos) {
        if (!datos) return;
        const keys = [
            ["cell_area_px", "[data-input-cell_area_px]"],
            ["perimeter_px", "[data-input-perimeter_px]"],
            ["circularity", "[data-input-circularity]"],
            ["eccentricity", "[data-input-eccentricity]"],
            ["cell_diameter_um", "[data-input-cell_diameter_um]"],
            ["hemoglobin_g_dl", "[data-input-hemoglobin_g_dl]"],
        ];
        keys.forEach(([k, sel]) => {
            const el = resultadoCard.querySelector(sel);
            if (el) el.textContent = formatNumero(datos[k]);
        });
    }

    function renderResultado(data, datosFuente) {
        resultadoCard.removeAttribute("data-multi-layout");
        const esNormal = data.es_normal === true;
        const tipo = esNormal ? "normal" : "anormal";
        resultadoCard.setAttribute("data-result", tipo);

        const statusEl = resultadoCard.querySelector("[data-result-status]");
        const diagEl = resultadoCard.querySelector("[data-result-diagnosis]");
        const descEl = resultadoCard.querySelector("[data-result-description]");
        const probEl = resultadoCard.querySelector("[data-result-probability]");
        const barEl = resultadoCard.querySelector("[data-result-bar]");

        if (statusEl) statusEl.textContent = esNormal ? "Normal" : "Anormal";
        if (diagEl) diagEl.textContent = data.diagnostico;

        if (descEl) {
            descEl.textContent = esNormal
                ? "Las características morfológicas analizadas son consistentes con una célula sanguínea de aspecto normal."
                : `Características atípicas detectadas. Riesgo: ${data.riesgo}. Se recomienda revisión por un especialista.`;
        }

        const prob = Number(data.probabilidad) || 0;
        if (probEl) probEl.textContent = `${prob.toFixed(2)}%`;
        if (barEl) {
            requestAnimationFrame(() => {
                barEl.style.width = `${Math.min(100, Math.max(0, prob))}%`;
            });
        }

        if (datosFuente) {
            fillSummaryInputsFromDatos(datosFuente);
        } else {
            const fd = new FormData(form);
            fillSummaryInputsFromDatos({
                cell_area_px: fd.get("cell_area_px"),
                perimeter_px: fd.get("perimeter_px"),
                circularity: fd.get("circularity"),
                eccentricity: fd.get("eccentricity"),
                cell_diameter_um: fd.get("cell_diameter_um"),
                hemoglobin_g_dl: fd.get("hemoglobin_g_dl"),
            });
        }

        setState("success");
    }

    function escapeHtml(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
    }

    /**
     * SVG inline — célula sana (simétrica, estilo orgánico limpio / Plague-like UI).
     */
    function svgCellHealthy() {
        return (
            '<svg class="result-card__svg result-card__svg--healthy" ' +
                'viewBox="0 0 80 80" width="56" height="56" ' +
                'aria-hidden="true" focusable="false">' +
            '<circle cx="40" cy="40" r="31" fill="rgba(34,197,94,0.12)" ' +
                'stroke="#22c55e" stroke-width="2.2"/>' +
            '<circle cx="40" cy="40" r="22" fill="rgba(22,163,74,0.18)" ' +
                'stroke="#16a34a" stroke-width="1.2" opacity="0.95"/>' +
            '<circle cx="40" cy="40" r="11" fill="rgba(21,128,61,0.55)" ' +
                'stroke="#15803d" stroke-width="1"/>' +
            '<circle cx="40" cy="40" r="5.5" fill="#166534" opacity="0.85"/>' +
            '<ellipse cx="32" cy="30" rx="7" ry="4" fill="#ffffff" opacity="0.22"/>' +
            '</svg>'
        );
    }

    /**
     * SVG inline — célula mutada (asimétrica, protuberancias, tonos carmesí).
     */
    function svgCellMutant() {
        return (
            '<svg class="result-card__svg result-card__svg--mutant" ' +
                'viewBox="0 0 80 80" width="56" height="56" ' +
                'aria-hidden="true" focusable="false">' +
            '<path d="M40 6 C48 4 56 10 58 18 C66 20 72 30 68 40 C74 48 70 60 58 64 C54 74 42 78 30 72 C18 76 8 66 10 52 C2 44 4 28 16 22 C14 10 28 4 40 6 Z" ' +
                'fill="rgba(220,38,38,0.15)" stroke="#b91c1c" stroke-width="2" ' +
                'stroke-linejoin="round"/>' +
            '<path d="M2 38 L8 32 L10 40 Z M78 36 L72 42 L70 34 Z M48 2 L52 10 L44 10 Z M26 74 L32 78 L30 70 Z" ' +
                'fill="#991b1b" opacity="0.88" stroke="#7f1d1d" stroke-width="0.5"/>' +
            '<path d="M40 16 C50 14 56 26 54 36 C56 46 46 54 36 52 C24 56 14 46 18 34 C14 22 26 14 40 16 Z" ' +
                'fill="rgba(185,28,28,0.28)" stroke="#dc2626" stroke-width="1.4"/>' +
            '<path d="M40 30 C44 28 48 34 46 40 C48 46 40 50 34 48 C28 52 22 42 26 36 C22 32 32 28 40 30 Z" ' +
                'fill="rgba(69,10,10,0.55)" stroke="#450a0a" stroke-width="0.6"/>' +
            '<ellipse cx="32" cy="36" rx="4" ry="5" transform="rotate(-18 32 36)" ' +
                'fill="#7f1d1d" opacity="0.4"/>' +
            '</svg>'
        );
    }

    /** Icono neutro para muestras con error de validación. */
    function svgCellUnknown() {
        return (
            '<svg class="result-card__svg result-card__svg--unknown" ' +
                'viewBox="0 0 80 80" width="48" height="48" ' +
                'aria-hidden="true" focusable="false">' +
            '<circle cx="40" cy="40" r="28" fill="rgba(100,116,139,0.1)" ' +
                'stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 3"/>' +
            '<path d="M40 24v20M40 52h0.01" stroke="#64748b" stroke-width="3" ' +
                'stroke-linecap="round"/>' +
            '</svg>'
        );
    }

    function buildVariablesResumen(datos) {
        if (!datos) return "";
        const parts = [];
        FEATURE_DISPLAY_ORDER.forEach((key) => {
            if (!(key in datos)) return;
            const label = VAR_LABELS[key] || key;
            const val = formatNumero(datos[key]);
            parts.push(
                `<div class="result-card__grid-item">` +
                    `<span class="result-card__grid-label">${escapeHtml(label)}</span>` +
                    `<span class="result-card__grid-value">${escapeHtml(val)}</span>` +
                `</div>`
            );
        });
        return parts.join("");
    }

    function renderBatchCards(resultados) {
        const wrap = resultadoCard.querySelector("[data-batch-cards]");
        if (!wrap) return;

        wrap.innerHTML = "";
        resultados.forEach((r) => {
            const article = document.createElement("article");
            article.className = "result-card" + (r.ok ? "" : " result-card--error");
            article.setAttribute("data-sample-index", String(r.indice + 1));

            if (!r.ok) {
                article.innerHTML =
                    `<div class="result-card__top result-card__top--error">` +
                    `<div class="result-card__cell-wrap result-card__cell-wrap--unknown" aria-hidden="true">` +
                    svgCellUnknown() +
                    `</div>` +
                    `<div class="result-card__top-main">` +
                    `<div class="result-card__head">` +
                    `<span class="result-card__index">Muestra ${r.indice + 1}</span>` +
                    `</div>` +
                    `<p class="result-card__diag result-card__diag--error-label">No procesada</p>` +
                    `</div></div>` +
                    `<p class="result-card__err-msg">${escapeHtml(String(r.error || "Error desconocido"))}</p>`;
            } else {
                const esNormal = r.es_normal === true;
                const clsDiag = esNormal ? "result-card__diag--normal" : "result-card__diag--anormal";
                const clsProb = esNormal ? "result-card__prob-value--normal" : "result-card__prob-value--anormal";
                const clsWrap = esNormal
                    ? "result-card__cell-wrap result-card__cell-wrap--healthy"
                    : "result-card__cell-wrap result-card__cell-wrap--mutant";
                const iconSvg = esNormal ? svgCellHealthy() : svgCellMutant();
                const probTxt = `${Number(r.probabilidad).toFixed(2)}%`;
                const grid = buildVariablesResumen(r.datos);

                article.innerHTML =
                    `<div class="result-card__top">` +
                    `<div class="${clsWrap}" aria-hidden="true">${iconSvg}</div>` +
                    `<div class="result-card__top-main">` +
                    `<div class="result-card__head">` +
                    `<span class="result-card__index">Muestra ${r.indice + 1}</span>` +
                    `</div>` +
                    `<h3 class="result-card__diag ${clsDiag}">${escapeHtml(r.diagnostico)}</h3>` +
                    `</div></div>` +
                    `<dl class="result-card__meta">` +
                    `<div><dt>Probabilidad (clase anomalía)</dt>` +
                    `<dd class="${clsProb}">${escapeHtml(probTxt)}</dd></div>` +
                    `<div><dt>Riesgo</dt><dd>${escapeHtml(String(r.riesgo))}</dd></div>` +
                    `</dl>` +
                    (grid ? `<div class="result-card__grid" role="group" aria-label="Variables de entrada">${grid}</div>` : "");
            }
            wrap.appendChild(article);
        });
    }

    function renderBatchTable(resultados) {
        const tbody = resultadoCard.querySelector("[data-batch-tbody]");
        if (!tbody) return;

        tbody.innerHTML = "";
        resultados.forEach((r) => {
            const tr = document.createElement("tr");
            if (r.ok) {
                const esNormal = r.es_normal === true;
                const cellCls = esNormal ? "result-table__cell--positive" : "result-table__cell--alert";
                tr.innerHTML =
                    `<td class="num">${r.indice + 1}</td>` +
                    `<td><span class="tag-ok">OK</span></td>` +
                    `<td class="${cellCls}">${escapeHtml(r.diagnostico)}</td>` +
                    `<td class="num ${cellCls}">${Number(r.probabilidad).toFixed(2)}%</td>` +
                    `<td>${escapeHtml(String(r.riesgo))}</td>`;
            } else {
                tr.innerHTML =
                    `<td class="num">${r.indice + 1}</td>` +
                    `<td><span class="tag-err">Error</span></td>` +
                    `<td colspan="3">${escapeHtml(String(r.error || "Error desconocido"))}</td>`;
            }
            tbody.appendChild(tr);
        });
    }

    function clearMultiDom() {
        const cards = resultadoCard.querySelector("[data-batch-cards]");
        const tbody = resultadoCard.querySelector("[data-batch-tbody]");
        const summary = resultadoCard.querySelector("[data-batch-summary]");
        if (cards) cards.innerHTML = "";
        if (tbody) tbody.innerHTML = "";
        if (summary) summary.textContent = "";
        resultadoCard.removeAttribute("data-multi-layout");
    }

    /**
     * Resultados del endpoint JSON: &lt;3 muestras → tarjetas; ≥3 → tabla con colores.
     */
    function renderJsonResults(lista) {
        const tbody = resultadoCard.querySelector("[data-batch-tbody]");
        const cards = resultadoCard.querySelector("[data-batch-cards]");
        if (tbody) tbody.innerHTML = "";
        if (cards) cards.innerHTML = "";

        const summary = resultadoCard.querySelector("[data-batch-summary]");
        const okN = lista.filter((x) => x.ok).length;
        if (summary) {
            summary.textContent = `${okN} de ${lista.length} muestra(s) analizadas correctamente.`;
        }

        resultadoCard.removeAttribute("data-result");

        if (lista.length < UMBRAL_TABLA) {
            resultadoCard.setAttribute("data-multi-layout", "cards");
            renderBatchCards(lista);
        } else {
            resultadoCard.setAttribute("data-multi-layout", "table");
            renderBatchTable(lista);
        }

        setState("success-batch");
    }

    function renderError(mensaje) {
        const msgEl = resultadoCard.querySelector("[data-error-message]");
        if (msgEl) msgEl.textContent = mensaje || "Ocurrió un error inesperado.";
        setState("error");
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(form);

        if (!validarCliente(formData)) return;

        setLoading(true);
        setState("loading");

        try {
            const response = await fetch(PREDICT_URL, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            });

            const payload = await response.json().catch(() => ({}));

            if (!response.ok || !payload.ok) {
                if (payload.errores_campo) {
                    Object.keys(payload.errores_campo).forEach((campo) => {
                        const errores = payload.errores_campo[campo];
                        const msg = Array.isArray(errores) ? errores.join(" ") : String(errores);
                        showFieldError(campo, msg);
                    });
                }
                renderError(payload.error || `Error del servidor (HTTP ${response.status}).`);
                return;
            }

            renderResultado(payload, null);
        } catch (err) {
            console.error(err);
            renderError("No se pudo conectar con el servidor.");
        } finally {
            setLoading(false);
        }
    });

    resetBtn.addEventListener("click", () => {
        clearFieldErrors();
        resultadoCard.removeAttribute("data-result");
        resultadoCard.removeAttribute("data-multi-layout");
        clearMultiDom();
        setState("empty");
    });

    if (jsonFile && jsonInput) {
        jsonFile.addEventListener("change", () => {
            const f = jsonFile.files && jsonFile.files[0];
            if (!f) {
                if (jsonFileName) jsonFileName.textContent = "";
                return;
            }
            if (jsonFileName) jsonFileName.textContent = f.name;
            const reader = new FileReader();
            reader.onload = () => {
                jsonInput.value = String(reader.result || "");
            };
            reader.onerror = () => {
                if (jsonFileName) jsonFileName.textContent = "No se pudo leer el archivo.";
            };
            reader.readAsText(f, "UTF-8");
        });
    }

    if (btnJsonLimpiar && jsonInput) {
        btnJsonLimpiar.addEventListener("click", () => {
            jsonInput.value = "";
            if (jsonFile) jsonFile.value = "";
            if (jsonFileName) jsonFileName.textContent = "";
        });
    }

    if (btnJsonAnalizar && jsonInput) {
        btnJsonAnalizar.addEventListener("click", async () => {
            const raw = jsonInput.value.trim();
            if (!raw) {
                renderError("Escribe o pega un JSON, o elige un archivo.");
                return;
            }

            let body;
            try {
                body = JSON.parse(raw);
            } catch (e) {
                renderError("El texto no es un JSON válido.");
                return;
            }

            setJsonLoading(true);
            setState("loading");

            try {
                const response = await fetch(PREDICT_JSON_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify(body),
                });

                const payload = await response.json().catch(() => ({}));

                if (!response.ok || !payload.ok) {
                    renderError(payload.error || `Error del servidor (HTTP ${response.status}).`);
                    return;
                }

                const lista = payload.resultados || [];
                renderJsonResults(lista);
            } catch (err) {
                console.error(err);
                renderError("No se pudo conectar con el servidor.");
            } finally {
                setJsonLoading(false);
            }
        });
    }
})();
