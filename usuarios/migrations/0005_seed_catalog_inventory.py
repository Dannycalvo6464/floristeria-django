from django.db import migrations


PRODUCTOS_INICIALES = (
    {
        'slug': 'rosa-roja',
        'nombre': 'Rosa Roja',
        'categoria': 'Rosas',
        'descripcion': 'Rosas intensas y románticas para expresar amor, pasión y complicidad.',
        'precio': '12000.00',
        'imagen_url': 'https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=900&q=80',
    },
    {
        'slug': 'ramo-tulipanes',
        'nombre': 'Ramo de Tulipanes',
        'categoria': 'Tulipanes',
        'descripcion': 'Tulipanes frescos y coloridos ideales para alegrar un día especial.',
        'precio': '18000.00',
        'imagen_url': 'https://images.unsplash.com/photo-1468327768560-75b778cbb551?auto=format&fit=crop&w=900&q=80',
    },
    {
        'slug': 'orquidea-blanca',
        'nombre': 'Orquídea Blanca',
        'categoria': 'Orquídeas',
        'descripcion': 'Elegancia y sofisticación para momentos formales y regalos muy especiales.',
        'precio': '22000.00',
        'imagen_url': 'https://images.unsplash.com/photo-1526047932273-341f2a7631f9?auto=format&fit=crop&w=900&q=80',
    },
    {
        'slug': 'lirio-del-valle',
        'nombre': 'Lirio del Valle',
        'categoria': 'Lirios',
        'descripcion': 'Fragancia suave y apariencia delicada para ocasiones sensibles y emotivas.',
        'precio': '16500.00',
        'imagen_url': 'https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=900&q=80',
    },
)


def crear_inventario_inicial(apps, schema_editor):
    Flor = apps.get_model('usuarios', 'Flor')
    for producto in PRODUCTOS_INICIALES:
        Flor.objects.get_or_create(
            slug=producto['slug'],
            defaults={
                **producto,
                'cantidad': 0,
                'activo': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_flor'),
    ]

    operations = [
        migrations.RunPython(crear_inventario_inicial, migrations.RunPython.noop),
    ]
