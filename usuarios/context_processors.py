def carrito_context(request):
    carrito = request.session.get("carrito", {})
    cantidad = 0
    if isinstance(carrito, dict):
        for unidades in carrito.values():
            if isinstance(unidades, int) and not isinstance(unidades, bool) and unidades > 0:
                cantidad += unidades
    return {"carrito_cantidad": cantidad}
