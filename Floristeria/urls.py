from django.contrib import admin
from django.urls import path

from usuarios.views import (
    login_usuario,
    panel_admin,
    panel_usuario,
    logout_usuario,
    activar_usuario,
    crear_usuario,
    buscar_usuario,
    actualizar_usuario,
    inactivar_usuario,
    ver_catalogo,
    mis_pedidos,
    mi_perfil,
    recuperar_contrasena,
)


urlpatterns = [
    path('logout/', logout_usuario, name='logout'),
    path('activar_usuario/', activar_usuario, name='activar_usuario'),
    path('panel_admin/', panel_admin, name='panel_admin'),
    path('panel_usuario/', panel_usuario, name='panel_usuario'),
    path('catalogo/', ver_catalogo, name='catalogo'),
    path('mis_pedidos/', mis_pedidos, name='mis_pedidos'),
    path('mi_perfil/', mi_perfil, name='mi_perfil'),
    path('recuperar_contrasena/', recuperar_contrasena, name='recuperar_contrasena'),
    path('', login_usuario, name='login'),
    path('crear_usuario/', crear_usuario, name='crear_usuario'),
    path('buscar_usuario/', buscar_usuario, name='buscar_usuario'),
    path('actualizar_usuario/', actualizar_usuario, name='actualizar_usuario'),
    path('inactivar_usuario/', inactivar_usuario, name='inactivar_usuario'),
]