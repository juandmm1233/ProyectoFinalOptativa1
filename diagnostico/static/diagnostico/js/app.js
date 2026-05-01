/* =========================================================
   BioCell AI — Lógica del frontend (v2 — 24 features)
   ========================================================= */

(function () {
    "use strict";

    const form        = document.getElementById("form-celula");
    const submitBtn   = document.getElementById("btn-submit");
    const resetBtn    = document.getElementById("btn-reset");
    const resultadoCard = document.getElementById("resultado");

    if (!form || !resultadoCard) return;

    const PREDICT_URL = window.BIOCELL_PREDICT_URL || "/predecir/";

    // ---------- utilidades ----------
    function getCSRFToken() {
        const input = form.querySelector("input[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function setState(state) {
        resultadoCard.setAttribute("data-state", state);
    }

    function setLoading(isLoading) {
        submitBtn.classList.toggle("is-loading", isLoading);
        submitBtn.disabled = isLoading;
    }

    function clearFieldErrors() {
        form.querySelectorAll(".form__error").forEach(el => el.textContent = "");
        form.querySelectorAll(".form-input").forEach(el => el.classList.remove("is-invalid"));
    }

    function showFieldError(name, message) {
        const errorEl = form.querySelector(`[data-error-for="${name}"]`);
        const input   = form.querySelector(`[name="${name}"]`);
        if (errorEl) errorEl.textContent = message;
        if (input)   input.classList.add("is-invalid");
    }

    // Validación de todos los campos numéricos — solo verifica que
    // no estén vacíos y sean números válidos. Los rangos los valida Django.
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

    // ---------- renderizado de resultado ----------
    function renderResultado(data) {
        const esNormal = data.es_normal === true;
        const tipo = esNormal ? "normal" : "anormal";
        resultadoCard.setAttribute("data-result", tipo);

        const statusEl = resultadoCard.querySelector("[data-result-status]");
        const diagEl   = resultadoCard.querySelector("[data-result-diagnosis]");
        const descEl   = resultadoCard.querySelector("[data-result-description]");
        const probEl   = resultadoCard.querySelector("[data-result-probability]");
        const barEl    = resultadoCard.querySelector("[data-result-bar]");

        if (statusEl) statusEl.textContent = esNormal ? "Normal" : "Anormal";
        if (diagEl)   diagEl.textContent   = data.diagnostico;

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

        // Mostrar algunos datos clave en el resultado
        const areaEl = resultadoCard.querySelector("[data-input-cell_area_px]");
        const perEl  = resultadoCard.querySelector("[data-input-perimeter_px]");
        const circEl = resultadoCard.querySelector("[data-input-circularity]");
        const eccEl  = resultadoCard.querySelector("[data-input-eccentricity]");
        const diamEl = resultadoCard.querySelector("[data-input-cell_diameter_um]");
        const hemoEl = resultadoCard.querySelector("[data-input-hemoglobin_g_dl]");

        const fd = new FormData(form);
        if (areaEl) areaEl.textContent = formatNumero(fd.get("cell_area_px"));
        if (perEl)  perEl.textContent  = formatNumero(fd.get("perimeter_px"));
        if (circEl) circEl.textContent = formatNumero(fd.get("circularity"));
        if (eccEl)  eccEl.textContent  = formatNumero(fd.get("eccentricity"));
        if (diamEl) diamEl.textContent = formatNumero(fd.get("cell_diameter_um"));
        if (hemoEl) hemoEl.textContent = formatNumero(fd.get("hemoglobin_g_dl"));

        setState("success");
    }

    function renderError(mensaje) {
        const msgEl = resultadoCard.querySelector("[data-error-message]");
        if (msgEl) msgEl.textContent = mensaje || "Ocurrió un error inesperado.";
        setState("error");
    }

    // ---------- envío del formulario ----------
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

            renderResultado(payload);

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

})();