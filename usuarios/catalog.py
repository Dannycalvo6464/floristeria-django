from decimal import Decimal


PRODUCTOS = (
    {
        "slug": "rosa-roja",
        "nombre": "Rosa Roja",
        "categoria": "Rosas",
        "precio": Decimal("12000"),
        "descripcion": "Rosas intensas y románticas para expresar amor, pasión y complicidad.",
        "imagen": "https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=900&q=80",
        "alt": "Rosas rojas en un arreglo floral",
    },
    {
        "slug": "ramo-tulipanes",
        "nombre": "Ramo de Tulipanes",
        "categoria": "Tulipanes",
        "precio": Decimal("18000"),
        "descripcion": "Tulipanes frescos y coloridos ideales para alegrar un día especial.",
        "imagen": "https://images.unsplash.com/photo-1468327768560-75b778cbb551?auto=format&fit=crop&w=900&q=80",
        "alt": "Ramo de tulipanes de colores",
    },
    {
        "slug": "orquidea-blanca",
        "nombre": "Orquídea Blanca",
        "categoria": "Orquídeas",
        "precio": Decimal("22000"),
        "descripcion": "Elegancia y sofisticación para momentos formales y regalos muy especiales.",
        "imagen": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?auto=format&fit=crop&w=900&q=80",
        "alt": "Orquídea blanca en flor",
    },
    {
        "slug": "lirio-del-valle",
        "nombre": "Lirio del Valle",
        "categoria": "Lirios",
        "precio": Decimal("16500"),
        "descripcion": "Fragancia suave y apariencia delicada para ocasiones sensibles y emotivas.",
        "imagen": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80",
        "alt": "Flores de lirio en un arreglo",
    },
)

PRODUCTOS_POR_SLUG = {producto["slug"]: producto for producto in PRODUCTOS}

RECOMENDACIONES = (
    {
        "ocasion": "Aniversario",
        "categoria": "Rosas",
        "criterio": "Las rosas aparecen en el catálogo como una opción romántica.",
    },
    {
        "ocasion": "Cumpleaños",
        "categoria": "Tulipanes",
        "criterio": "El catálogo describe los tulipanes como una opción colorida y alegre.",
    },
    {
        "ocasion": "Agradecimiento",
        "categoria": "Orquídeas",
        "criterio": "La descripción de las orquídeas destaca su elegancia para regalar.",
    },
    {
        "ocasion": "Condolencias",
        "categoria": "Lirios",
        "criterio": "La descripción de los lirios destaca su carácter delicado y sereno.",
    },
)


def formato_cop(valor):
    return f"${int(valor):,}".replace(",", ".")


def producto_para_vista(producto):
    return {**producto, "precio_formateado": formato_cop(producto["precio"])}
