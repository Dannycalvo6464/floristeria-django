from django.db import migrations


FLORES_COLOMBIANAS = (
    {
        'slug': 'rosa-blanca',
        'nombre': 'Rosa Blanca',
        'categoria': 'Rosas',
        'descripcion': 'Rosa de corte cultivada en Colombia, de pétalos claros y estilo elegante.',
        'precio': '12000.00',
    },
    {
        'slug': 'rosa-amarilla',
        'nombre': 'Rosa Amarilla',
        'categoria': 'Rosas',
        'descripcion': 'Rosa amarilla de cultivo colombiano, ideal para arreglos alegres y luminosos.',
        'precio': '12000.00',
    },
    {
        'slug': 'rosa-rosada',
        'nombre': 'Rosa Rosada',
        'categoria': 'Rosas',
        'descripcion': 'Rosa rosada de cultivo colombiano con una apariencia suave y romántica.',
        'precio': '12000.00',
    },
    {
        'slug': 'clavel-rojo',
        'nombre': 'Clavel Rojo',
        'categoria': 'Claveles',
        'descripcion': 'Clavel rojo de producción floricultora colombiana, vistoso y duradero.',
        'precio': '9000.00',
    },
    {
        'slug': 'clavel-blanco',
        'nombre': 'Clavel Blanco',
        'categoria': 'Claveles',
        'descripcion': 'Clavel blanco cultivado en Colombia para arreglos frescos y elegantes.',
        'precio': '9000.00',
    },
    {
        'slug': 'mini-clavel-surtido',
        'nombre': 'Mini Clavel Surtido',
        'categoria': 'Claveles',
        'descripcion': 'Selección de mini claveles colombianos en tonos variados para ramos.',
        'precio': '11000.00',
    },
    {
        'slug': 'crisantemo-blanco',
        'nombre': 'Crisantemo Blanco',
        'categoria': 'Crisantemos',
        'descripcion': 'Crisantemo blanco de cultivo colombiano, con flores abundantes para arreglos.',
        'precio': '10000.00',
    },
    {
        'slug': 'crisantemo-pompon-amarillo',
        'nombre': 'Crisantemo Pompón Amarillo',
        'categoria': 'Crisantemos',
        'descripcion': 'Crisantemo tipo pompón amarillo cultivado en Colombia, compacto y alegre.',
        'precio': '10000.00',
    },
    {
        'slug': 'hortensia-azul',
        'nombre': 'Hortensia Azul',
        'categoria': 'Hortensias',
        'descripcion': 'Hortensia azul de cultivo colombiano, apreciada por sus ramos voluminosos.',
        'precio': '18000.00',
    },
    {
        'slug': 'hortensia-rosada',
        'nombre': 'Hortensia Rosada',
        'categoria': 'Hortensias',
        'descripcion': 'Hortensia rosada colombiana para dar volumen y color a los arreglos.',
        'precio': '18000.00',
    },
    {
        'slug': 'astromelia-surtida',
        'nombre': 'Astromelia Surtida',
        'categoria': 'Astromelias',
        'descripcion': 'Astromelias de cultivo colombiano en colores surtidos, frescas y versátiles.',
        'precio': '12000.00',
    },
    {
        'slug': 'astromelia-blanca',
        'nombre': 'Astromelia Blanca',
        'categoria': 'Astromelias',
        'descripcion': 'Astromelia blanca cultivada en Colombia, delicada y fácil de combinar.',
        'precio': '12000.00',
    },
    {
        'slug': 'gerbera-naranja',
        'nombre': 'Gerbera Naranja',
        'categoria': 'Gerberas',
        'descripcion': 'Gerbera naranja de cultivo colombiano que aporta un acento cálido al ramo.',
        'precio': '10000.00',
    },
    {
        'slug': 'gerbera-fucsia',
        'nombre': 'Gerbera Fucsia',
        'categoria': 'Gerberas',
        'descripcion': 'Gerbera fucsia colombiana de color intenso para composiciones alegres.',
        'precio': '10000.00',
    },
    {
        'slug': 'lirio-oriental-blanco',
        'nombre': 'Lirio Oriental Blanco',
        'categoria': 'Lirios',
        'descripcion': 'Lirio oriental blanco cultivado en Colombia, de presencia elegante y fragancia marcada.',
        'precio': '18000.00',
    },
    {
        'slug': 'lirio-asiatico-amarillo',
        'nombre': 'Lirio Asiático Amarillo',
        'categoria': 'Lirios',
        'descripcion': 'Lirio asiático amarillo de cultivo colombiano, luminoso y sin fragancia intensa.',
        'precio': '16000.00',
    },
    {
        'slug': 'orquidea-cattleya',
        'nombre': 'Orquídea Cattleya',
        'categoria': 'Orquídeas',
        'descripcion': 'Orquídea Cattleya, género emblemático de la diversidad floral colombiana.',
        'precio': '25000.00',
    },
    {
        'slug': 'orquidea-cymbidium',
        'nombre': 'Orquídea Cymbidium',
        'categoria': 'Orquídeas',
        'descripcion': 'Orquídea Cymbidium cultivada en Colombia, con flores de aspecto refinado.',
        'precio': '28000.00',
    },
    {
        'slug': 'girasol',
        'nombre': 'Girasol',
        'categoria': 'Girasoles',
        'descripcion': 'Girasol de cultivo colombiano, una opción radiante para arreglos y regalos.',
        'precio': '10000.00',
    },
    {
        'slug': 'heliconia-rostrata',
        'nombre': 'Heliconia Rostrata',
        'categoria': 'Heliconias',
        'descripcion': 'Heliconia tropical cultivada en Colombia, reconocida por sus brácteas coloridas.',
        'precio': '18000.00',
    },
)


def agregar_flores_colombianas(apps, schema_editor):
    Flor = apps.get_model('usuarios', 'Flor')
    for producto in FLORES_COLOMBIANAS:
        Flor.objects.get_or_create(
            slug=producto['slug'],
            defaults={
                **producto,
                'imagen_url': '',
                'cantidad': 0,
                'activo': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0006_usuario_direccion'),
    ]

    operations = [
        migrations.RunPython(
            agregar_flores_colombianas,
            migrations.RunPython.noop,
        ),
    ]
