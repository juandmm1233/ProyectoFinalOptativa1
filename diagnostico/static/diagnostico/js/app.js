/* =========================================================
   BioCell AI — Lógica del frontend (v2 — 24 features + JSON)
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

    function renderBatch(resultados) {
        const tbody = resultadoCard.querySelector("[data-batch-tbody]");
        const summary = resultadoCard.querySelector("[data-batch-summary]");
        if (!tbody || !summary) return;

        const okN = resultados.filter((r) => r.ok).length;
        summary.textContent = `${okN} de ${resultados.length} muestra(s) analizadas correctamente.`;

        tbody.innerHTML = "";
        resultados.forEach((r) => {
            const tr = document.createElement("tr");
            if (r.ok) {
                tr.innerHTML = `
                    <td class="num">${r.indice + 1}</td>
                    <td><span class="tag-ok">OK</span></td>
                    <td>${r.diagnostico}</td>
                    <td class="num">${Number(r.probabilidad).toFixed(2)}%</td>
                    <td>${r.riesgo}</td>`;
            } else {
                tr.innerHTML = `
                    <td class="num">${r.indice + 1}</td>
                    <td><span class="tag-err">Error</span></td>
                    <td colspan="3">${escapeHtml(String(r.error || "Error desconocido"))}</td>`;
            }
            tbody.appendChild(tr);
        });
        resultadoCard.removeAttribute("data-result");
        setState("success-batch");
    }

    function escapeHtml(s) {
        const div = document.createElement("div");
        div.textContent = s;
        return div.innerHTML;
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
        setState("empty");
    });

    /* ---------- JSON ---------- */
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
                if (lista.length === 1) {
                    const r = lista[0];
                    if (r.ok) {
                        renderResultado(
                            {
                                diagnostico: r.diagnostico,
                                es_normal: r.es_normal,
                                probabilidad: r.probabilidad,
                                riesgo: r.riesgo,
                            },
                            r.datos || null
                        );
                    } else {
                        renderError(r.error || "Error al procesar la muestra.");
                    }
                } else {
                    renderBatch(lista);
                }
            } catch (err) {
                console.error(err);
                renderError("No se pudo conectar con el servidor.");
            } finally {
                setJsonLoading(false);
            }
        });
    }
})();
