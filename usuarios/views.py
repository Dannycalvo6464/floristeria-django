import logging
import secrets
import smtplib
import time
from functools import wraps

from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils.crypto import constant_time_compare
from django.db.models import Q
from django.conf import settings
from django.contrib import messages

from .catalog import (
    PRODUCTOS,
    PRODUCTOS_POR_SLUG,
    RECOMENDACIONES,
    formato_cop,
    producto_para_vista,
)
from .models import Usuario


logger = logging.getLogger(__name__)


def _verify_and_upgrade_password(usuario, raw_password):
    """Verify a Django hash or upgrade a legacy plaintext password on success."""
    stored_password = usuario.contrasena
    try:
        hasher = identify_hasher(stored_password)
    except ValueError:
        if not constant_time_compare(raw_password, stored_password):
            return False
        usuario.contrasena = make_password(raw_password)
        usuario.save(update_fields=['contrasena'])
        return True

    if not check_password(raw_password, stored_password):
        return False
    if hasher.must_update(stored_password):
        usuario.contrasena = make_password(raw_password)
        usuario.save(update_fields=['contrasena'])
    return True


def _password_error(raw_password):
    try:
        validate_password(raw_password)
    except ValidationError as error:
        return ' '.join(error.messages)
    return ''


def _session_required(admin_only=False):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            usuario = Usuario.objects.filter(
                id=request.session.get('usuario_id'),
                activo=True,
            ).first()
            if not usuario:
                return redirect('login')
            if admin_only and usuario.tipo not in {'Admin', 'Administrador'}:
                return HttpResponseForbidden('No tienes permiso para realizar esta acción.')
            request.current_usuario = usuario
            response = view(request, *args, **kwargs)
            return never_cache(lambda _request: response)(request)
        return wrapped
    return decorator


def inicio(request):
    return render(
        request,
        "usuarios/inicio.html",
        {"productos_destacados": [producto_para_vista(p) for p in PRODUCTOS[:3]]},
    )


def login_usuario(request):

    mensaje = ""

    if request.method == "POST":

        correo = request.POST.get("correo", "").strip()
        contrasena = request.POST.get("contrasena", "")

        usuario = Usuario.objects.filter(
            Q(correo=correo) |
            Q(nombre=correo),
            activo=True
        ).first()

        if usuario and _verify_and_upgrade_password(usuario, contrasena):
            request.session.cycle_key()
            request.session["usuario_id"] = usuario.id
            request.session["usuario_nombre"] = usuario.nombre
            request.session["usuario_tipo"] = usuario.tipo

            if usuario.tipo in {"Admin", "Administrador"}:
                return redirect("panel_admin")

            return redirect("panel_usuario")

        mensaje = "Credenciales incorrectas"

    return render(
        request,
        "usuarios/login.html",
        {"mensaje": mensaje}
    )


def crear_usuario(request):

    mensaje = ""

    if request.method == "POST":

        nombre = request.POST.get("nombre", "").strip()
        correo = request.POST.get("correo", "").strip()
        contrasena = request.POST.get("contrasena", "")

        if not nombre or not correo or not contrasena:
            mensaje = "Completa todos los campos."
        elif Usuario.objects.filter(correo__iexact=correo).exists():

            mensaje = "Este correo ya está registrado"

        else:
            mensaje = _password_error(contrasena)
            if not mensaje:
                Usuario.objects.create(
                    nombre=nombre,
                    tipo="Usuario",
                    correo=correo,
                    contrasena=make_password(contrasena),
                )
                return redirect('login')

    return render(
        request,
        "usuarios/crear_usuario.html",
        {"mensaje": mensaje}
    )


def recuperar_contrasena(request):
    mensaje = ""
    correo = request.session.get("recuperar_email")
    en_espera = bool(request.session.get("recuperar_codigo_hash") and correo)
    codigo_sesion_key = "recuperar_codigo_hash"

    if request.method == "POST":
        if "codigo" in request.POST:
            codigo_ingresado = request.POST.get("codigo", "").strip()
            nueva_contrasena = request.POST.get("nueva_contrasena", "")
            codigo_guardado = request.session.get(codigo_sesion_key)
            correo_guardado = request.session.get("recuperar_email")
            vencimiento = request.session.get("recuperar_expira", 0)
            intentos = request.session.get("recuperar_intentos", 0)

            if not codigo_guardado or not correo_guardado or time.time() > vencimiento:
                request.session.pop(codigo_sesion_key, None)
                request.session.pop("recuperar_email", None)
                request.session.pop("recuperar_expira", None)
                request.session.pop("recuperar_intentos", None)
                mensaje = "La solicitud de recuperación ha expirado. Solicita un nuevo código."
            elif intentos >= 5 or not check_password(codigo_ingresado, codigo_guardado):
                intentos += 1
                request.session["recuperar_intentos"] = intentos
                if intentos >= 5:
                    request.session.pop(codigo_sesion_key, None)
                    request.session.pop("recuperar_email", None)
                    request.session.pop("recuperar_expira", None)
                mensaje = "El código de confirmación no es correcto."
            elif not nueva_contrasena:
                mensaje = "Debes ingresar una nueva contraseña."
            else:
                mensaje = _password_error(nueva_contrasena)
                usuario = Usuario.objects.filter(correo=correo_guardado, activo=True).first()
                if usuario and not mensaje:
                    usuario.contrasena = make_password(nueva_contrasena)
                    usuario.save(update_fields=["contrasena"])
                    request.session.pop(codigo_sesion_key, None)
                    request.session.pop("recuperar_email", None)
                    request.session.pop("recuperar_expira", None)
                    request.session.pop("recuperar_intentos", None)
                    mensaje = "Tu contraseña se ha actualizado correctamente."
                    return render(
                        request,
                        "usuarios/recuperar_contrasena.html",
                        {"mensaje": mensaje, "exito": True}
                    )
                elif not usuario:
                    mensaje = "No se pudo completar la recuperación. Solicita un nuevo código."

            return render(
                request,
                "usuarios/recuperar_contrasena.html",
                {
                    "mensaje": mensaje,
                    "correo": correo_guardado,
                    "en_espera": bool(
                        request.session.get(codigo_sesion_key)
                        and request.session.get("recuperar_email")
                    ),
                }
            )

        correo_solicitado = request.POST.get("correo", "").strip()
        if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
            mensaje = (
                "La recuperación por correo aún no está configurada. "
                "El administrador debe definir EMAIL_HOST, EMAIL_PORT, "
                "EMAIL_HOST_USER, EMAIL_HOST_PASSWORD y DEFAULT_FROM_EMAIL en Render."
            )
            return render(
                request,
                "usuarios/recuperar_contrasena.html",
                {"mensaje": mensaje, "correo": correo, "en_espera": en_espera},
            )

        mensaje = "Si existe una cuenta activa, recibirás instrucciones."
        usuario = Usuario.objects.filter(correo__iexact=correo_solicitado, activo=True).first()
        if correo_solicitado and usuario:
            codigo = f"{secrets.randbelow(900000) + 100000}"
            try:
                sent = send_mail(
                    "Código para recuperar tu cuenta de Flores Cali",
                    f"Tu código de recuperación es {codigo}. Vence en 10 minutos.",
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.correo],
                    fail_silently=False,
                )
            except (OSError, smtplib.SMTPException):
                logger.exception("No se pudo enviar el correo de recuperación.")
                sent = 0
            if sent:
                request.session[codigo_sesion_key] = make_password(codigo)
                request.session["recuperar_email"] = usuario.correo
                request.session["recuperar_expira"] = time.time() + 600
                request.session["recuperar_intentos"] = 0
                request.session.set_expiry(600)
                correo = usuario.correo
                en_espera = True
            else:
                mensaje = (
                    "No se pudo enviar el correo de recuperación. "
                    "Inténtalo más tarde o contacta al administrador."
                )

    return render(
        request,
        "usuarios/recuperar_contrasena.html",
        {
            "mensaje": mensaje,
            "correo": correo,
            "en_espera": en_espera,
        }
    )


@_session_required(admin_only=True)
def buscar_usuario(request):
    usuarios = []
    mensaje = ""

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if nombre:
            usuarios = Usuario.objects.filter(nombre__icontains=nombre)
            if not usuarios:
                mensaje = "No encontramos usuarios con ese nombre."
        else:
            mensaje = "Escribe un nombre para iniciar la búsqueda."

    return render(
        request,
        "usuarios/buscar_usuario.html",
        {"usuarios": usuarios, "mensaje": mensaje}
    )


@_session_required(admin_only=True)
def actualizar_usuario(request):
    usuario = None

    if request.method == "POST":

        if "buscar" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            if nombre:
                usuario = Usuario.objects.filter(nombre__icontains=nombre).first()
            if not usuario:
                messages.error(request, "No encontramos una cuenta con ese nombre.")

        elif "actualizar" in request.POST:
            usuario = get_object_or_404(Usuario, id=request.POST.get("id"))
            usuario.nombre = request.POST.get("nombre", "").strip()
            usuario.correo = request.POST.get("correo", "").strip()
            nueva_contrasena = request.POST.get("contrasena", "")
            if nueva_contrasena:
                error_contrasena = _password_error(nueva_contrasena)
                if error_contrasena:
                    messages.error(request, error_contrasena)
                    return render(
                        request,
                        "usuarios/actualizar_usuario.html",
                        {"usuario": usuario},
                        status=400,
                    )
                usuario.contrasena = make_password(nueva_contrasena)

            usuario.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("actualizar_usuario")

    return render(
        request,
        "usuarios/actualizar_usuario.html",
        {"usuario": usuario}
    )


@_session_required(admin_only=True)
def inactivar_usuario(request):
    usuarios = Usuario.objects.filter(activo=True)

    if request.method == "POST":

        usuario = get_object_or_404(Usuario, id=request.POST.get("id"), activo=True)

        usuario.activo = False
        usuario.save()
        messages.success(request, "Usuario inactivado correctamente.")
        return redirect("inactivar_usuario")

    return render(
        request,
        "usuarios/inactivar_usuario.html",
        {"usuarios": usuarios}
    )


@_session_required(admin_only=True)
def activar_usuario(request):

    usuarios = Usuario.objects.filter(activo=False)

    if request.method == "POST":

        usuario = get_object_or_404(Usuario, id=request.POST.get("id"), activo=False)

        usuario.activo = True
        usuario.save()
        messages.success(request, "Usuario activado correctamente.")
        return redirect("activar_usuario")

    return render(
        request,
        "usuarios/activar_usuario.html",
        {"usuarios": usuarios}
    )


@_session_required(admin_only=True)
def panel_admin(request):
    return render(
        request,
        "usuarios/panel_admin.html",
        {"usuario": request.current_usuario}
    )


@_session_required()
def panel_usuario(request):
    return render(
        request,
        "usuarios/panel_usuario.html",
        {"usuario": request.current_usuario}
    )


def ver_catalogo(request):
    consulta = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    categorias = sorted({producto["categoria"] for producto in PRODUCTOS})
    productos = list(PRODUCTOS)
    mensaje_busqueda = ""

    if len(consulta) > 100:
        consulta = consulta[:100]
        mensaje_busqueda = "La búsqueda se limitó a 100 caracteres."
    if consulta:
        productos = [
            producto for producto in productos
            if producto["nombre"].casefold() == consulta.casefold()
        ]
        if not productos:
            mensaje_busqueda = "No encontramos una flor con ese nombre exacto."

    if categoria:
        if categoria not in categorias:
            productos = []
            mensaje_busqueda = "Selecciona un tipo de flor disponible en el catálogo."
        else:
            productos = [
                producto for producto in productos
                if producto["categoria"] == categoria
            ]
            if not productos and not mensaje_busqueda:
                mensaje_busqueda = "No hay resultados con esos criterios."

    recomendaciones = []
    for recomendacion in RECOMENDACIONES:
        producto = next(
            (p for p in PRODUCTOS if p["categoria"] == recomendacion["categoria"]),
            None,
        )
        if producto:
            recomendaciones.append({**recomendacion, "producto": producto})
    return render(
        request,
        "usuarios/catalogo.html",
        {
            "productos": [producto_para_vista(p) for p in productos],
            "categorias": categorias,
            "categoria_seleccionada": categoria,
            "consulta": consulta,
            "mensaje_busqueda": mensaje_busqueda,
            "recomendaciones": recomendaciones,
            "formato_cop": formato_cop,
        },
    )


def detalle_producto(request, slug):
    producto = PRODUCTOS_POR_SLUG.get(slug)
    if not producto:
        raise Http404("Producto no encontrado")
    return render(
        request,
        "usuarios/detalle_producto.html",
        {"producto": producto_para_vista(producto)},
    )


@require_POST
def agregar_al_carrito(request, slug):
    producto = PRODUCTOS_POR_SLUG.get(slug)
    if not producto:
        raise Http404("Producto no encontrado")

    try:
        cantidad = int(request.POST.get("cantidad", ""))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        messages.error(request, "Ingresa una cantidad entera mayor que cero.")
        return redirect("detalle_producto", slug=slug)

    carrito = request.session.get("carrito", {})
    if not isinstance(carrito, dict):
        carrito = {}
    actual = carrito.get(slug, 0)
    if not isinstance(actual, int) or isinstance(actual, bool) or actual < 0:
        actual = 0
    carrito[slug] = actual + cantidad
    request.session["carrito"] = carrito
    messages.success(request, f"{producto['nombre']} se agregó al carrito.")
    return redirect("carrito")


def ver_carrito(request):
    carrito_sesion = request.session.get("carrito", {})
    if not isinstance(carrito_sesion, dict):
        carrito_sesion = {}

    productos_carrito = []
    carrito_limpio = {}
    total = 0
    for slug, cantidad in carrito_sesion.items():
        producto = PRODUCTOS_POR_SLUG.get(slug)
        if (
            not producto
            or not isinstance(cantidad, int)
            or isinstance(cantidad, bool)
            or cantidad < 1
        ):
            continue
        subtotal = producto["precio"] * cantidad
        total += subtotal
        productos_carrito.append(
            {
                **producto_para_vista(producto),
                "cantidad": cantidad,
                "subtotal_formateado": formato_cop(subtotal),
            }
        )
        carrito_limpio[slug] = cantidad

    if carrito_limpio != carrito_sesion:
        request.session["carrito"] = carrito_limpio
    return render(
        request,
        "usuarios/carrito.html",
        {
            "productos_carrito": productos_carrito,
            "total": formato_cop(total),
        },
    )


@require_POST
def actualizar_carrito(request, slug):
    if slug not in PRODUCTOS_POR_SLUG:
        raise Http404("Producto no encontrado")
    try:
        cantidad = int(request.POST.get("cantidad", ""))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        messages.error(request, "La cantidad debe ser un entero mayor que cero.")
        return redirect("carrito")
    carrito = request.session.get("carrito", {})
    if not isinstance(carrito, dict) or slug not in carrito:
        messages.error(request, "Ese producto ya no está en el carrito.")
        return redirect("carrito")
    carrito[slug] = cantidad
    request.session["carrito"] = carrito
    messages.success(request, "Cantidad actualizada.")
    return redirect("carrito")


@require_POST
def quitar_del_carrito(request, slug):
    carrito = request.session.get("carrito", {})
    if isinstance(carrito, dict) and slug in carrito:
        carrito.pop(slug)
        request.session["carrito"] = carrito
        messages.success(request, "Producto eliminado del carrito.")
    return redirect("carrito")


@_session_required()
def mis_pedidos(request):
    return render(
        request,
        "usuarios/mis_pedidos.html",
    )


@_session_required()
def mi_perfil(request):
    return render(
        request,
        "usuarios/mi_perfil.html",
        {"usuario": request.current_usuario}
    )


@require_POST
def logout_usuario(request):
    request.session.flush()
    return redirect("login")
