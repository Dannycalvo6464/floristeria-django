from django.contrib import admin
from django.urls import path

from usuarios.views import (
    login_usuario,
    panel_admin,
    logout_usuario,
    activar_usuario,  
    crear_usuario,
    buscar_usuario,
    actualizar_usuario,
    inactivar_usuario
)


urlpatterns = [
    path('logout/', logout_usuario, name='logout'),
    path('activar_usuario/', activar_usuario, name='activar_usuario'),
    path('panel_admin/', panel_admin, name='panel_admin'),
    path('', login_usuario, name='login'),
    path('crear_usuario/', crear_usuario, name='crear_usuario'),
    path('buscar_usuario/', buscar_usuario, name='buscar_usuario'),
    path('actualizar_usuario/', actualizar_usuario, name='actualizar_usuario'),
    path('inactivar_usuario/', inactivar_usuario, name='inactivar_usuario'),
]