import django.core.validators
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_add_delivery_order_requests'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('categoria', models.CharField(max_length=80)),
                ('descripcion', models.CharField(max_length=500)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('cantidad', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(2147483647)])),
                ('imagen_url', models.URLField(blank=True, max_length=500)),
                ('activo', models.BooleanField(default=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'flores',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddConstraint(
            model_name='flor',
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower('nombre'),
                condition=models.Q(('activo', True)),
                name='flor_nombre_activo_ci_uniq',
            ),
        ),
    ]
