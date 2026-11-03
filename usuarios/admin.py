from django.contrib import admin
from .models import DetalleSolicitudPedido, SolicitudPedido, Usuario


admin.site.register(Usuario)


class DetalleSolicitudPedidoInline(admin.TabularInline):
    model = DetalleSolicitudPedido
    extra = 0
    can_delete = False
    readonly_fields = (
        'producto_slug',
        'producto_nombre',
        'categoria',
        'cantidad',
        'precio_unitario_referencia',
    )


@admin.register(SolicitudPedido)
class SolicitudPedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'estado',
        'ciudad',
        'comuna',
        'creado_en',
        'total_referencia',
    )
    list_filter = ('estado', 'ciudad', 'creado_en')
    search_fields = (
        'usuario__nombre',
        'usuario__correo',
        'direccion',
        'codigo_postal',
        'ciudad',
        'comuna',
    )
    readonly_fields = (
        'usuario',
        'direccion',
        'codigo_postal',
        'ciudad',
        'comuna',
        'detalles_domicilio',
        'datos_autorizados',
        'total_referencia',
        'creado_en',
    )
    inlines = [DetalleSolicitudPedidoInline]