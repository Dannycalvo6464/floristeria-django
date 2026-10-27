import re
from io import StringIO

from django.contrib.auth.hashers import check_password, identify_hasher
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from usuarios.models import Usuario


class UsuarioRoutesTest(TestCase):
    def _login_como(self, tipo='Usuario'):
        usuario = Usuario.objects.create(
            nombre='Ana', correo='ana@flores.com', contrasena='legacy', tipo=tipo
        )
        session = self.client.session
        session['usuario_id'] = usuario.pk
        session['usuario_tipo'] = tipo
        session.save()
        return usuario

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

    @override_settings(EMAIL_HOST='', DEFAULT_FROM_EMAIL='')
    def test_recuperacion_informa_configuracion_smtp_pendiente(self):
        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': 'ana@flores.com'},
        )
        self.assertContains(response, 'EMAIL_HOST')
        self.assertContains(response, 'EMAIL_HOST_PASSWORD')
        self.assertNotContains(response, 'código de recuperación es')

    def test_recuperacion_expirada_vuelve_a_mostrar_solicitud_de_correo(self):
        session = self.client.session
        session['recuperar_codigo_hash'] = 'hash-expirado'
        session['recuperar_email'] = 'ana@flores.com'
        session['recuperar_expira'] = 0
        session['recuperar_intentos'] = 0
        session.save()

        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'codigo': '123456', 'nueva_contrasena': 'FloresSeguras!2026'},
        )
        self.assertContains(response, 'name="correo"')
        self.assertNotContains(response, 'name="codigo"')
        self.assertNotIn('recuperar_codigo_hash', self.client.session)

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

    def test_inicio_y_login_tienen_rutas_publicas_distintas(self):
        self.assertEqual(self.client.get(reverse('inicio')).status_code, 200)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertContains(self.client.get(reverse('inicio')), 'Explorar catálogo')

    def test_busqueda_exacta_y_filtro_de_categoria(self):
        response = self.client.get(reverse('catalogo'), {'q': 'Rosa Roja'})
        self.assertContains(response, 'Rosa Roja')
        self.assertEqual(
            [producto['slug'] for producto in response.context['productos']],
            ['rosa-roja'],
        )

        response = self.client.get(reverse('catalogo'), {'q': 'rosa'})
        self.assertContains(response, 'No encontramos una flor con ese nombre exacto')

        response = self.client.get(reverse('catalogo'), {'categoria': 'Tulipanes'})
        self.assertContains(response, 'Ramo de Tulipanes')
        self.assertEqual(
            [producto['slug'] for producto in response.context['productos']],
            ['ramo-tulipanes'],
        )

    def test_detalle_y_carrito_permiten_agregar_editar_y_quitar(self):
        detalle_url = reverse('detalle_producto', kwargs={'slug': 'rosa-roja'})
        self.assertEqual(self.client.get(detalle_url).status_code, 200)

        agregar_url = reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'})
        self.assertEqual(self.client.get(agregar_url).status_code, 405)
        response = self.client.post(agregar_url, {'cantidad': '2'})
        self.assertRedirects(response, reverse('carrito'))
        self.assertContains(self.client.get(reverse('carrito')), '$24.000')

        actualizar_url = reverse('actualizar_carrito', kwargs={'slug': 'rosa-roja'})
        self.client.post(actualizar_url, {'cantidad': '3'})
        self.assertContains(self.client.get(reverse('carrito')), '$36.000')
        self.client.post(
            reverse('quitar_del_carrito', kwargs={'slug': 'rosa-roja'})
        )
        self.assertContains(self.client.get(reverse('carrito')), 'Tu carrito está vacío')

    def test_carrito_rechaza_cantidad_no_entera_o_no_positiva(self):
        response = self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '0'},
        )
        self.assertRedirects(
            response,
            reverse('detalle_producto', kwargs={'slug': 'rosa-roja'}),
        )
        response = self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '1.5'},
        )
        self.assertRedirects(
            response,
            reverse('detalle_producto', kwargs={'slug': 'rosa-roja'}),
        )
        self.assertNotIn('carrito', self.client.session)

    def test_cerrar_sesion_requiere_post_e_invalida_la_sesion(self):
        self._login_como()
        logout_url = reverse('logout')
        self.assertEqual(self.client.get(logout_url).status_code, 405)
        response = self.client.post(logout_url)
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('usuario_id', self.client.session)

    def test_paginas_y_acciones_de_administracion(self):
        self._login_como(tipo='Admin')
        inactivo = Usuario.objects.create(
            nombre='Inactivo', correo='inactivo@flores.com',
            contrasena='legacy', tipo='Usuario', activo=False,
        )
        for name in (
            'buscar_usuario',
            'actualizar_usuario',
            'activar_usuario',
            'inactivar_usuario',
        ):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

        response = self.client.post(
            reverse('actualizar_usuario'),
            {'buscar': '1', 'nombre': 'Inactivo'},
        )
        self.assertEqual(response.context['usuario'].pk, inactivo.pk)
        response = self.client.post(
            reverse('actualizar_usuario'),
            {
                'actualizar': '1',
                'id': inactivo.pk,
                'nombre': 'Cuenta actualizada',
                'correo': 'actualizada@flores.com',
            },
        )
        self.assertRedirects(response, reverse('actualizar_usuario'))
        inactivo.refresh_from_db()
        self.assertEqual(inactivo.nombre, 'Cuenta actualizada')

        self.client.post(
            reverse('activar_usuario'),
            {'id': inactivo.pk},
        )
        inactivo.refresh_from_db()
        self.assertTrue(inactivo.activo)
        self.client.post(
            reverse('inactivar_usuario'),
            {'id': inactivo.pk},
        )
        inactivo.refresh_from_db()
        self.assertFalse(inactivo.activo)
