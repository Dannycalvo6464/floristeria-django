from django.db import models


class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20)
    correo = models.EmailField(max_length=100)
    contrasena = models.CharField(max_length=100)

    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return self.nombre

