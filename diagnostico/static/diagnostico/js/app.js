/* =========================================================
   BioCell AI — Lógica del frontend
   - Validación cliente del formulario.
   - Envío AJAX al endpoint Django.
   - Renderizado dinámico del resultado.
   ========================================================= */

(function () {
    "use strict";

    const form = document.getElementById("form-celula");
    const submitBtn = document.getElementById("btn-submit");
    const resetBtn = document.getElementById("btn-reset");
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
        if (isLoading) {
            submitBtn.classList.add("is-loading");
            submitBtn.disabled = true;
        } else {
            submitBtn.classList.remove("is-loading");
            submitBtn.disabled = false;
        }
    }

    function clearFieldErrors() {
        form.querySelectorAll(".form__error").forEach(el => (el.textContent = ""));
        form.querySelectorAll(".form-input").forEach(el => el.classList.remove("is-invalid"));
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

        const reglas = {
            area:       { min: 0,  max: 10000, label: "Área" },
            perimetro:  { min: 0,  max: 1000,  label: "Perímetro" },
            concavidad: { min: 0,  max: 1,     label: "Concavidad" },
            textura:    { min: 0,  max: 100,   label: "Textura" },
        };

        for (const campo in reglas) {
            const valor = formData.get(campo);
            if (valor === null || valor === "") {
                showFieldError(campo, "Este campo es obligatorio.");
                valido = false;
                continue;
            }
            const num = Number(valor);
            if (Number.isNaN(num)) {
                showFieldError(campo, "Debe ser un número válido.");
                valido = false;
                continue;
            }
            const r = reglas[campo];
            if (num < r.min || num > r.max) {
                showFieldError(campo, `${r.label} debe estar entre ${r.min} y ${r.max}.`);
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
        const diagEl = resultadoCard.querySelector("[data-result-diagnosis]");
        const descEl = resultadoCard.querySelector("[data-result-description]");
        const probEl = resultadoCard.querySelector("[data-result-probability]");
        const barEl = resultadoCard.querySelector("[data-result-bar]");

        statusEl.textContent = esNormal ? "Normal" : "Anormal";
        diagEl.textContent = data.diagnostico;

        descEl.textContent = esNormal
            ? "Las características morfológicas analizadas son consistentes con una célula sanguínea de aspecto normal."
            : "Las características morfológicas analizadas presentan rasgos atípicos. Se recomienda revisión por un especialista.";

        const prob = Number(data.probabilidad) || 0;
        probEl.textContent = `${prob.toFixed(2)}%`;
        // Pequeño retardo para que la transición CSS se vea bien.
        requestAnimationFrame(() => {
            barEl.style.width = `${Math.min(100, Math.max(0, prob))}%`;
        });

        const d = data.datos || {};
        resultadoCard.querySelector("[data-input-area]").textContent = formatNumero(d.area);
        resultadoCard.querySelector("[data-input-perimetro]").textContent = formatNumero(d.perimetro);
        resultadoCard.querySelector("[data-input-concavidad]").textContent = formatNumero(d.concavidad);
        resultadoCard.querySelector("[data-input-textura]").textContent = formatNumero(d.textura);

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

        if (!validarCliente(formData)) {
            return;
        }

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
            renderError("No se pudo conectar con el servidor. Verifica tu conexión.");
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
