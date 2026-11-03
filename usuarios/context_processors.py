def get_cart_quantity(carrito):
    if not isinstance(carrito, dict):
        return 0
    return sum(
        unidades
        for unidades in carrito.values()
        if isinstance(unidades, int) and not isinstance(unidades, bool) and unidades > 0
    )


def carrito_context(request):
    carrito = request.session.get("carrito", {})
    return {"carrito_cantidad": get_cart_quantity(carrito)}
