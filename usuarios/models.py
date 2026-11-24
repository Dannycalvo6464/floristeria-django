from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20)
    correo = models.EmailField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True)
    contrasena = models.CharField(max_length=100)

    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return self.nombre


class SolicitudPedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de revisión'
        CONTACTADO = 'contactado', 'En gestión'
        CERRADO = 'cerrado', 'Cerrado'

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='solicitudes_pedido',
    )
    direccion = models.CharField(max_length=200)
    codigo_postal = models.CharField(
        max_length=6,
    )
    ciudad = models.CharField(max_length=100)
    comuna = models.CharField(max_length=100)
    detalles_domicilio = models.CharField(max_length=250, blank=True)
    datos_autorizados = models.BooleanField(default=False)
    total_referencia = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'solicitudes_pedido'
        ordering = ['-creado_en']

    def __str__(self):
        return f'Solicitud #{self.pk} · {self.usuario.nombre}'


class DetalleSolicitudPedido(models.Model):
    solicitud = models.ForeignKey(
        SolicitudPedido,
        on_delete=models.CASCADE,
        related_name='productos',
    )
    producto_slug = models.SlugField(max_length=100)
    producto_nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario_referencia = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'detalles_solicitud_pedido'
        ordering = ['id']

    @property
    def subtotal_referencia(self):
        return self.precio_unitario_referencia * self.cantidad

    def __str__(self):
        return f'{self.producto_nombre} × {self.cantidad}'


class Flor(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    categoria = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=500)
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    cantidad = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(2_147_483_647)],
    )
    imagen_url = models.URLField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'flores'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('nombre'),
                condition=models.Q(activo=True),
                name='flor_nombre_activo_ci_uniq',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)[:100] or 'flor'
            slug = base_slug
            suffix = 2
            while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug[:110]}-{suffix}'
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
