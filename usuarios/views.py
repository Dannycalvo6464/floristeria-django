from django.http import HttpResponse
from django.shortcuts import render
from .models import Usuario
from django.shortcuts import render, redirect
from .models import Usuario
from django.shortcuts import redirect
from django.db.models import Q


from django.db.models import Q

def login_usuario(request):

    mensaje = ""

    if request.method == "POST":

        correo = request.POST["correo"]
        contrasena = request.POST["contrasena"]

        usuario = Usuario.objects.filter(
            Q(correo=correo) |
            Q(nombre=correo),
            contrasena=contrasena,
            activo=True
        ).first()

        if usuario:

            if usuario.tipo == "Admin":
                return render(
                    request,
                    "usuarios/panel_admin.html",
                    {"usuario": usuario}
                )

            return render(
                request,
                "usuarios/panel_usuario.html",
                {"usuario": usuario}
            )

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

        nombre = request.POST["nombre"].strip()
        correo = request.POST["correo"].strip()
        contrasena = request.POST["contrasena"].strip()

        if Usuario.objects.filter(correo=correo).exists():

            mensaje = "Este correo ya está registrado"

        else:

            Usuario.objects.create(
                nombre=nombre,
                tipo="Usuario",
                correo=correo,
                contrasena=contrasena
            )

            return redirect('login')

    return render(
        request,
        "usuarios/crear_usuario.html",
        {"mensaje": mensaje}
    )

   


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
            usuario.contrasena = request.POST["contrasena"]

            usuario.save()

            return HttpResponse(
                "Usuario actualizado correctamente"
            )

    return render(
        request,
        "usuarios/actualizar_usuario.html",
        {"usuario": usuario}
    )

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

def panel_admin(request):
    return render(
        request,
        "usuarios/panel_admin.html"
    )

def logout_usuario(request):
    return redirect("login")