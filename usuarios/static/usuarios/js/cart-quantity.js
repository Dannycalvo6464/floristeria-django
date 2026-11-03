(() => {
    const forms = Array.from(document.querySelectorAll("[data-cart-quantity-form]"));
    const totalElement = document.querySelector("[data-cart-total]");

    if (!forms.length || !totalElement || !window.fetch || !window.FormData) {
        return;
    }

    const formatCOP = new Intl.NumberFormat("es-CO", {
        maximumFractionDigits: 0,
    });
    const formatMoney = (amount) => `$${formatCOP.format(amount)}`;
    const saveStates = new WeakMap();

    const updateTotals = () => {
        let total = 0;

        forms.forEach((form) => {
            const input = form.querySelector('input[name="cantidad"]');
            const subtotal = form.closest(".cart-line").querySelector("[data-cart-subtotal]");
            const quantity = Number(input.value);

            if (Number.isInteger(quantity) && quantity > 0) {
                const amount = Number(subtotal.dataset.unitPrice) * quantity;
                subtotal.textContent = formatMoney(amount);
                total += amount;
            }
        });

        totalElement.textContent = formatMoney(total);
    };

    const saveQuantity = (form) => {
        const input = form.querySelector('input[name="cantidad"]');
        const status = form.closest(".cart-line").querySelector("[data-cart-quantity-status]");
        const quantity = Number(input.value);
        const state = saveStates.get(form);
        window.clearTimeout(state.timer);
        state.timer = null;

        if (!input.checkValidity() || !Number.isInteger(quantity) || quantity < 1) {
            status.textContent = "Ingresa una cantidad entera mayor que cero.";
            status.hidden = false;
            return Promise.resolve(false);
        }

        if (state.pending) {
            return state.pending.then((success) => {
                if (input.value !== input.dataset.savedQuantity) {
                    return saveQuantity(form);
                }
                return success;
            });
        }

        if (String(quantity) === input.dataset.savedQuantity) {
            status.textContent = "";
            status.hidden = true;
            return Promise.resolve(true);
        }

        status.textContent = "";
        status.hidden = true;
        const body = new FormData(form);

        const request = fetch(form.action, {
            method: "POST",
            body,
            credentials: "same-origin",
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(async (response) => {
                const result = await response.json().catch(() => null);
                if (!response.ok || !result || !result.ok) {
                    throw new Error(
                        result && result.message
                            ? result.message
                            : "No se pudo guardar la cantidad."
                    );
                }

                input.dataset.savedQuantity = String(result.cantidad);
                const subtotal = form.closest(".cart-line").querySelector("[data-cart-subtotal]");
                subtotal.textContent = result.subtotal;
                totalElement.textContent = result.total;
                updateTotals();
                status.textContent = "";
                status.hidden = true;
                return true;
            })
            .catch((error) => {
                if (input.value === body.get("cantidad")) {
                    input.value = input.dataset.savedQuantity;
                    updateTotals();
                }
                status.textContent = error instanceof Error
                    ? error.message
                    : "No se pudo guardar la cantidad.";
                status.hidden = false;
                return false;
            })
            .finally(() => {
                state.pending = null;
            });
        state.pending = request;
        return request;
    };

    forms.forEach((form) => {
        const input = form.querySelector('input[name="cantidad"]');
        const state = { timer: null, pending: null };
        saveStates.set(form, state);

        input.addEventListener("input", () => {
            updateTotals();
            window.clearTimeout(state.timer);
            state.timer = window.setTimeout(() => saveQuantity(form), 350);
        });

        input.addEventListener("change", () => {
            saveQuantity(form);
        });
    });

    document.addEventListener("click", (event) => {
        const link = event.target.closest("[data-cart-continue]");
        if (!link) {
            return;
        }

        event.preventDefault();
        const destination = link.href;
        const saveResults = [];

        forms.forEach((form) => {
            saveResults.push(saveQuantity(form));
        });

        Promise.all(saveResults).then((results) => {
            if (results.every(Boolean)) {
                window.location.assign(destination);
            }
        });
    });
})();
