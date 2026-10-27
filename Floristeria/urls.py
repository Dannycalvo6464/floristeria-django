from django.contrib import admin
from django.urls import path

from usuarios.views import (
    agregar_al_carrito,
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
    detalle_producto,
    ver_carrito,
    actualizar_carrito,
    quitar_del_carrito,
    mis_pedidos,
    mi_perfil,
    recuperar_contrasena,
    inicio,
)


urlpatterns = [
    path('logout/', logout_usuario, name='logout'),
    path('activar_usuario/', activar_usuario, name='activar_usuario'),
    path('panel_admin/', panel_admin, name='panel_admin'),
    path('panel_usuario/', panel_usuario, name='panel_usuario'),
    path('catalogo/', ver_catalogo, name='catalogo'),
    path('catalogo/<slug:slug>/', detalle_producto, name='detalle_producto'),
    path('carrito/', ver_carrito, name='carrito'),
    path('carrito/agregar/<slug:slug>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<slug:slug>/', actualizar_carrito, name='actualizar_carrito'),
    path('carrito/quitar/<slug:slug>/', quitar_del_carrito, name='quitar_del_carrito'),
    path('mis_pedidos/', mis_pedidos, name='mis_pedidos'),
    path('mi_perfil/', mi_perfil, name='mi_perfil'),
    path('recuperar_contrasena/', recuperar_contrasena, name='recuperar_contrasena'),
    path('login/', login_usuario, name='login'),
    path('', inicio, name='inicio'),
    path('crear_usuario/', crear_usuario, name='crear_usuario'),
    path('buscar_usuario/', buscar_usuario, name='buscar_usuario'),
    path('actualizar_usuario/', actualizar_usuario, name='actualizar_usuario'),
    path('inactivar_usuario/', inactivar_usuario, name='inactivar_usuario'),
]