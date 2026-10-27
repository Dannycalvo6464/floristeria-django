import re
from io import StringIO

from django.contrib.auth.hashers import check_password, identify_hasher
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from usuarios.models import Usuario


class UsuarioRoutesTest(TestCase):
    def test_rutas_del_panel_usuario_existen(self):
        usuario = Usuario.objects.create(
            nombre='Ana', correo='ana@flores.com', contrasena='legacy', tipo='Usuario'
        )
        session = self.client.session
        session['usuario_id'] = usuario.pk
        session.save()
        self.assertEqual(self.client.get(reverse('catalogo')).status_code, 200)
        self.assertEqual(self.client.get(reverse('mis_pedidos')).status_code, 200)
        self.assertEqual(self.client.get(reverse('mi_perfil')).status_code, 200)

    def test_rutas_privadas_exigen_sesion_y_admin(self):
        self.assertRedirects(self.client.get(reverse('panel_usuario')), reverse('login'))
        self.assertRedirects(self.client.get(reverse('panel_admin')), reverse('login'))
        self.assertRedirects(self.client.get(reverse('buscar_usuario')), reverse('login'))

        usuario = Usuario.objects.create(
            nombre='Ana', correo='ana@flores.com', contrasena='legacy', tipo='Usuario'
        )
        session = self.client.session
        session['usuario_id'] = usuario.pk
        session.save()
        self.assertEqual(self.client.get(reverse('panel_usuario')).status_code, 200)
        self.assertEqual(self.client.get(reverse('buscar_usuario')).status_code, 403)

        usuario.tipo = 'Administrador'
        usuario.save(update_fields=['tipo'])
        self.assertEqual(self.client.get(reverse('panel_admin')).status_code, 200)
        self.assertEqual(self.client.get(reverse('buscar_usuario')).status_code, 200)

    def test_formulario_de_registro_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse('crear_usuario'),
            {'nombre': 'Ana', 'correo': 'csrf@flores.com', 'contrasena': 'FloresSeguras!2026'},
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST='smtp.test',
        DEFAULT_FROM_EMAIL='no-reply@flores.test',
    )
    def test_recuperacion_envia_codigo_sin_exponerlo_y_guarda_hash(self):
        Usuario.objects.create(
            nombre='Ana',
            correo='ana@flores.com',
            contrasena='vieja123',
            tipo='Usuario',
            activo=True,
        )

        response = self.client.get(reverse('recuperar_contrasena'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': 'ana@flores.com'}
        )
        self.assertEqual(len(mail.outbox), 1)
        code = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
        self.assertNotIn(code, response.content.decode())

        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'codigo': code, 'nueva_contrasena': 'FloresSeguras!2026'}
        )
        self.assertEqual(response.status_code, 200)
        usuario = Usuario.objects.get(correo='ana@flores.com')
        self.assertTrue(check_password('FloresSeguras!2026', usuario.contrasena))

    def test_registro_guarda_hash_y_login_autentica(self):
        response = self.client.post(
            reverse('crear_usuario'),
            {
                'nombre': 'Lucia',
                'correo': 'lucia@flores.com',
                'contrasena': 'FloresSeguras!2026',
            },
        )
        self.assertRedirects(response, reverse('login'))
        usuario = Usuario.objects.get(correo='lucia@flores.com')
        identify_hasher(usuario.contrasena)
        self.assertNotEqual(usuario.contrasena, 'FloresSeguras!2026')

        response = self.client.post(
            reverse('login'),
            {'correo': 'lucia@flores.com', 'contrasena': 'FloresSeguras!2026'},
        )
        self.assertRedirects(response, reverse('panel_usuario'))

    def test_login_migra_contrasena_legacy_sin_cambiarla(self):
        usuario = Usuario.objects.create(
            nombre='Legacy',
            correo='legacy@flores.com',
            contrasena='ClaveVieja!2026',
            tipo='Usuario',
            activo=True,
        )
        response = self.client.post(
            reverse('login'),
            {'correo': 'legacy@flores.com', 'contrasena': 'ClaveVieja!2026'},
        )
        self.assertRedirects(response, reverse('panel_usuario'))
        usuario.refresh_from_db()
        self.assertTrue(check_password('ClaveVieja!2026', usuario.contrasena))

    def test_comando_hash_legacy_no_imprime_credenciales(self):
        Usuario.objects.create(
            nombre='Legacy',
            correo='legacy2@flores.com',
            contrasena='ClaveVieja!2026',
            tipo='Usuario',
            activo=True,
        )
        output = StringIO()
        call_command('hash_legacy_passwords', stdout=output)
        usuario = Usuario.objects.get(correo='legacy2@flores.com')
        self.assertTrue(check_password('ClaveVieja!2026', usuario.contrasena))
        self.assertNotIn('ClaveVieja!2026', output.getvalue())

    def test_catalogo_muestra_flores_con_disponibilidad_y_recomendaciones(self):
        response = self.client.get(reverse('catalogo'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        self.assertIn('Rosa Roja', content)
        self.assertIn('Disponibilidad', content)
        self.assertIn('Recomendación educativa', content)
        self.assertIn('Aniversario', content)
