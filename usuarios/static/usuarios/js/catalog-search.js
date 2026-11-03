(() => {
    const form = document.querySelector("[data-live-catalog-search]");
    const input = form && form.querySelector('input[name="q"]');
    const category = form && form.querySelector('select[name="categoria"]');
    const cards = Array.from(document.querySelectorAll("[data-product-card]"));
    const status = document.querySelector("[data-search-status]");
    const emptyState = document.querySelector("[data-empty-results]");

    if (!form || !input || !category || !cards.length || !status || !emptyState) {
        return;
    }

    const normalize = (value) => value
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase();

    const filterProducts = () => {
        const searchTerm = normalize(input.value.trim());
        const selectedCategory = category.value;
        let visibleCount = 0;

        cards.forEach((card) => {
            const matchesName = normalize(card.dataset.name || "").includes(searchTerm);
            const matchesCategory = !selectedCategory || card.dataset.category === selectedCategory;
            const isVisible = matchesName && matchesCategory;

            card.hidden = !isVisible;
            if (isVisible) {
                visibleCount += 1;
            }
        });

        emptyState.hidden = visibleCount > 0;
        status.textContent = visibleCount === 1
            ? "1 resultado"
            : `${visibleCount} resultados`;
    };

    input.addEventListener("input", filterProducts);
    category.addEventListener("change", filterProducts);
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        filterProducts();
    });
})();
