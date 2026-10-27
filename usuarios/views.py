import secrets
import time
from functools import wraps

from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.crypto import constant_time_compare
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.db.models import Q
from django.conf import settings

from .models import Usuario


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
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


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


def inicio(request):
    return HttpResponse("<h1>Bienvenido a Flores Cali</h1>")


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
                    "en_espera": True,
                }
            )

        correo_solicitado = request.POST.get("correo", "").strip()
        mensaje = "Si existe una cuenta activa y el correo está configurado, recibirás instrucciones."
        usuario = Usuario.objects.filter(correo__iexact=correo_solicitado, activo=True).first()
        if (
            correo_solicitado
            and usuario
            and settings.EMAIL_HOST
            and settings.DEFAULT_FROM_EMAIL
        ):
            codigo = f"{secrets.randbelow(900000) + 100000}"
            try:
                sent = send_mail(
                    "Código para recuperar tu cuenta de Flores Cali",
                    f"Tu código de recuperación es {codigo}. Vence en 10 minutos.",
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.correo],
                    fail_silently=False,
                )
            except Exception:
                sent = 0
            if sent:
                request.session[codigo_sesion_key] = make_password(codigo)
                request.session["recuperar_email"] = usuario.correo
                request.session["recuperar_expira"] = time.time() + 600
                request.session["recuperar_intentos"] = 0
                request.session.set_expiry(600)
                correo = usuario.correo
                en_espera = True

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

    if request.method == "POST":
        nombre = request.POST["nombre"]

        usuarios = Usuario.objects.filter(
            nombre__icontains=nombre
        )

    return render(
        request,
        "usuarios/buscar_usuario.html",
        {"usuarios": usuarios}
    )


@_session_required(admin_only=True)
def actualizar_usuario(request):
    usuario = None

    if request.method == "POST":

        if "buscar" in request.POST:
            nombre = request.POST["nombre"]
            usuario = Usuario.objects.filter(
                nombre__icontains=nombre
            ).first()

        elif "actualizar" in request.POST:
            usuario = Usuario.objects.get(
                id=request.POST["id"]
            )

            usuario.nombre = request.POST["nombre"]
            usuario.correo = request.POST["correo"]
            nueva_contrasena = request.POST.get("contrasena", "")
            if nueva_contrasena:
                error_contrasena = _password_error(nueva_contrasena)
                if error_contrasena:
                    return HttpResponse(error_contrasena, status=400)
                usuario.contrasena = make_password(nueva_contrasena)

            usuario.save()

            return HttpResponse(
                "Usuario actualizado correctamente"
            )

    return render(
        request,
        "usuarios/actualizar_usuario.html",
        {"usuario": usuario}
    )


@_session_required(admin_only=True)
def inactivar_usuario(request):
    usuarios = Usuario.objects.filter(activo=True)

    if request.method == "POST":

        usuario = Usuario.objects.get(
            id=request.POST["id"]
        )

        usuario.activo = False
        usuario.save()

        return HttpResponse(
            "Usuario inactivado correctamente"
        )

    return render(
        request,
        "usuarios/inactivar_usuario.html",
        {"usuarios": usuarios}
    )


@_session_required(admin_only=True)
def activar_usuario(request):

    usuarios = Usuario.objects.filter(activo=False)

    if request.method == "POST":

        usuario = Usuario.objects.get(
            id=request.POST["id"]
        )

        usuario.activo = True
        usuario.save()

        return HttpResponse(
            "Usuario activado correctamente"
        )

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
    productos = [
        {
            "nombre": "Rosa Roja",
            "precio": "$12.000",
            "descripcion": "Rosas intensas y románticas para expresar amor, pasión y complicidad.",
            "disponibilidad": "En stock",
            "imagen": "https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=900&q=80",
        },
        {
            "nombre": "Ramo de Tulipanes",
            "precio": "$18.000",
            "descripcion": "Tulipanes frescos y coloridos ideales para alegrar un día especial.",
            "disponibilidad": "Pocas unidades",
            "imagen": "https://images.unsplash.com/photo-1468327768560-75b778cbb551?auto=format&fit=crop&w=900&q=80",
        },
        {
            "nombre": "Orquídea Blanca",
            "precio": "$22.000",
            "descripcion": "Elegancia y sofisticación para momentos formales y regalos muy especiales.",
            "disponibilidad": "En stock",
            "imagen": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?auto=format&fit=crop&w=900&q=80",
        },
        {
            "nombre": "Lirio del Valle",
            "precio": "$16.500",
            "descripcion": "Fragancia suave y apariencia delicada para ocasiones sensibles y emotivas.",
            "disponibilidad": "En stock",
            "imagen": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80",
        },
    ]

    recomendaciones = [
        {
            "titulo": "Aniversario",
            "texto": "Las rosas rojas combinadas con un arreglo elegante transmiten amor y celebración.",
        },
        {
            "titulo": "Cumpleaños",
            "texto": "Los tulipanes y mezclas de colores vivos son una opción alegre y vibrante.",
        },
        {
            "titulo": "Agradecimiento",
            "texto": "Las orquídeas aportan refinamiento y una sensación de gratitud sincera.",
        },
        {
            "titulo": "Condolencias",
            "texto": "Los lirios y arreglos sobrios expresan respeto, calma y apoyo en momentos difíciles.",
        },
    ]

    return render(
        request,
        "usuarios/catalogo.html",
        {"productos": productos, "recomendaciones": recomendaciones}
    )


@_session_required()
def mis_pedidos(request):
    pedidos = [
        {"id": "PED-101", "estado": "Entregado", "total": "$19.000"},
        {"id": "PED-102", "estado": "En tránsito", "total": "$25.500"},
    ]
    return render(
        request,
        "usuarios/mis_pedidos.html",
        {"pedidos": pedidos}
    )


@_session_required()
def mi_perfil(request):
    return render(
        request,
        "usuarios/mi_perfil.html",
        {"usuario": request.current_usuario}
    )


def logout_usuario(request):
    request.session.flush()
    return redirect("login")
