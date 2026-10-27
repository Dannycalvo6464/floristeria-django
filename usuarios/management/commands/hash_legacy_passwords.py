from django.contrib.auth.hashers import identify_hasher, make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Hash any remaining legacy plaintext passwords in usuarios.Usuario.'

    def handle(self, *args, **options):
        updated = 0
        with transaction.atomic():
            queryset = Usuario.objects.only('id', 'contrasena').order_by('id')
            offset = 0
            while True:
                batch = list(queryset[offset:offset + 200])
                if not batch:
                    break
                offset += len(batch)
                changed = []
                for usuario in batch:
                    try:
                        identify_hasher(usuario.contrasena)
                    except ValueError:
                        usuario.contrasena = make_password(usuario.contrasena)
                        changed.append(usuario)
                if changed:
                    Usuario.objects.bulk_update(changed, ['contrasena'], batch_size=200)
                    updated += len(changed)
        self.stdout.write(self.style.SUCCESS(f'Contraseñas actualizadas: {updated}'))
