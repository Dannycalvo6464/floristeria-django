from django.db import migrations, models


IMAGENES_FLORES = (
    (
        'rosa-blanca',
        'https://upload.wikimedia.org/wikipedia/commons/2/2e/White_Rose_%28flower%29.jpg',
        'Kiruthikapalani · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:White_Rose_(flower).jpg',
    ),
    (
        'rosa-amarilla',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e7/Yellow-Rose-Sitia-Crete.jpg/960px-Yellow-Rose-Sitia-Crete.jpg',
        'Petro Stelte · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Yellow-Rose-Sitia-Crete.jpg',
    ),
    (
        'rosa-rosada',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/2/20/Pink-Rose-Sitia-Crete-Greece.jpg/960px-Pink-Rose-Sitia-Crete-Greece.jpg',
        'Petro Stelte · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Pink-Rose-Sitia-Crete-Greece.jpg',
    ),
    (
        'clavel-rojo',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f8/Red_Carnation_Flower.jpg/960px-Red_Carnation_Flower.jpg',
        'Rick Kimpel · CC BY-SA 2.0',
        'https://commons.wikimedia.org/wiki/File:Red_Carnation_Flower.jpg',
    ),
    (
        'clavel-blanco',
        'https://upload.wikimedia.org/wikipedia/commons/0/0c/White_carnation.jpg',
        'Dysepsion · Dominio público',
        'https://commons.wikimedia.org/wiki/File:White_carnation.jpg',
    ),
    (
        'mini-clavel-surtido',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/38/Carnation_flower.jpg/960px-Carnation_flower.jpg',
        'Aftabbanoori · CC BY-SA 3.0',
        'https://commons.wikimedia.org/wiki/File:Carnation_flower.jpg',
    ),
    (
        'crisantemo-blanco',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/98/White_Chrysanthemum_Flowers.jpg/960px-White_Chrysanthemum_Flowers.jpg',
        'Adbh266 · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:White_Chrysanthemum_Flowers.jpg',
    ),
    (
        'crisantemo-pompon-amarillo',
        'https://upload.wikimedia.org/wikipedia/commons/8/84/Chrysanthemum.JPG',
        'Aruna · CC BY-SA',
        'https://commons.wikimedia.org/wiki/File:Chrysanthemum.JPG',
    ),
    (
        'hortensia-azul',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Blue_Hydrangea_%28common_names_hydrangea_or_hortensia%29.jpg/960px-Blue_Hydrangea_%28common_names_hydrangea_or_hortensia%29.jpg',
        'Subhrajyoti07 · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Blue_Hydrangea_(common_names_hydrangea_or_hortensia).jpg',
    ),
    (
        'hortensia-rosada',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f4/Pink_Hydrangea_%28common_names_hydrangea_or_hortensia%29.jpg/960px-Pink_Hydrangea_%28common_names_hydrangea_or_hortensia%29.jpg',
        'Subhrajyoti07 · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Pink_Hydrangea_(common_names_hydrangea_or_hortensia).jpg',
    ),
    (
        'astromelia-surtida',
        'https://upload.wikimedia.org/wikipedia/commons/a/a7/Alstroemeria_aurantiaca.jpg',
        'JJ Harrison · CC BY-SA',
        'https://commons.wikimedia.org/wiki/File:Alstroemeria_aurantiaca.jpg',
    ),
    (
        'astromelia-blanca',
        'https://upload.wikimedia.org/wikipedia/commons/1/10/Alstroemeria_in_a_flower_arrangement.jpg',
        'Almapayokels · CC0 1.0',
        'https://commons.wikimedia.org/wiki/File:Alstroemeria_in_a_flower_arrangement.jpg',
    ),
    (
        'gerbera-naranja',
        'https://upload.wikimedia.org/wikipedia/commons/9/9a/Orange_Gerbera_flower.jpg',
        'Juan Carlos Torres V · CC0 1.0',
        'https://commons.wikimedia.org/wiki/File:Orange_Gerbera_flower.jpg',
    ),
    (
        'gerbera-fucsia',
        'https://upload.wikimedia.org/wikipedia/commons/8/8f/Pink_gerbera_flower.jpg',
        'George E. Koronaios · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Pink_gerbera_flower.jpg',
    ),
    (
        'lirio-oriental-blanco',
        'https://upload.wikimedia.org/wikipedia/commons/3/30/Lilium_candidum_1.jpg',
        'Stan Shebs · CC BY-SA',
        'https://commons.wikimedia.org/wiki/File:Lilium_candidum_1.jpg',
    ),
    (
        'lirio-asiatico-amarillo',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/6/66/Asiatic_yellow_lily_or_Lilium.jpg/500px-Asiatic_yellow_lily_or_Lilium.jpg',
        'Prianxi · CC BY-SA',
        'https://commons.wikimedia.org/wiki/File:Asiatic_yellow_lily_or_Lilium.jpg',
    ),
    (
        'orquidea-cattleya',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/f/ff/Cattleya_Orchids.jpg/960px-Cattleya_Orchids.jpg',
        'Zyrahila · CC BY-SA 4.0',
        'https://commons.wikimedia.org/wiki/File:Cattleya_Orchids.jpg',
    ),
    (
        'orquidea-cymbidium',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c1/Cymbidium_Clarisse_Austin_%27Best_Pink%27_Flowers_2000px.JPG/960px-Cymbidium_Clarisse_Austin_%27Best_Pink%27_Flowers_2000px.JPG',
        'Derek Ramsey · GFDL 1.2',
        'https://commons.wikimedia.org/wiki/File:Cymbidium_Clarisse_Austin_%27Best_Pink%27_Flowers_2000px.JPG',
    ),
    (
        'girasol',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/8/88/Sonnenblume_Helianthus_2.JPG/960px-Sonnenblume_Helianthus_2.JPG',
        'Böhringer Friedrich · CC BY-SA',
        'https://commons.wikimedia.org/wiki/File:Sonnenblume_Helianthus_2.JPG',
    ),
    (
        'heliconia-rostrata',
        'https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9e/Heliconia_rostrata_-_Flower_Photomontage.jpg/960px-Heliconia_rostrata_-_Flower_Photomontage.jpg',
        "Filo gèn' · CC BY-SA 4.0",
        'https://commons.wikimedia.org/wiki/File:Heliconia_rostrata_-_Flower_Photomontage.jpg',
    ),
)


def asignar_imagenes_y_atribuciones(apps, schema_editor):
    Flor = apps.get_model('usuarios', 'Flor')
    for slug, imagen_url, imagen_credito, imagen_fuente in IMAGENES_FLORES:
        Flor.objects.filter(slug=slug, imagen_url='').update(
            imagen_url=imagen_url,
            imagen_credito=imagen_credito,
            imagen_fuente=imagen_fuente,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_seed_colombian_flowers'),
    ]

    operations = [
        migrations.AddField(
            model_name='flor',
            name='imagen_credito',
            field=models.CharField(blank=True, default='', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flor',
            name='imagen_fuente',
            field=models.URLField(blank=True, default='', max_length=500),
            preserve_default=False,
        ),
        migrations.RunPython(
            asignar_imagenes_y_atribuciones,
            migrations.RunPython.noop,
        ),
    ]
