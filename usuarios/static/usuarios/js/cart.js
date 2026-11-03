(() => {
    const forms = document.querySelectorAll("[data-cart-form]");
    const count = document.getElementById("cart-count");
    const cartLink = count ? count.closest("a") : null;
    const notice = document.getElementById("cart-notice");

    if (!forms.length || !count || !notice || !window.fetch || !window.FormData) {
        return;
    }

    let noticeTimer;

    const showNotice = (message, isError = false) => {
        notice.textContent = message;
        notice.classList.toggle("error", isError);
        notice.hidden = false;
        window.clearTimeout(noticeTimer);
        noticeTimer = window.setTimeout(() => {
            notice.hidden = true;
        }, 4000);
    };

    forms.forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const button = form.querySelector('button[type="submit"]');
            const originalText = button.textContent;

            button.disabled = true;
            button.textContent = "Agregando…";
            form.setAttribute("aria-busy", "true");

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                const result = await response.json().catch(() => null);

                if (!response.ok || !result || !result.ok) {
                    throw new Error(
                        result && result.message
                            ? result.message
                            : "No pudimos agregar el producto. Inténtalo de nuevo."
                    );
                }

                count.textContent = String(result.carrito_cantidad);
                if (cartLink) {
                    cartLink.setAttribute(
                        "aria-label",
                        `Carrito, ${result.carrito_cantidad} artículos`
                    );
                }
                showNotice(result.message);
            } catch (error) {
                showNotice(
                    error instanceof Error && error.message
                        ? error.message
                        : "No pudimos agregar el producto. Inténtalo de nuevo.",
                    true
                );
            } finally {
                button.disabled = false;
                button.textContent = originalText;
                form.removeAttribute("aria-busy");
            }
        });
    });
})();
