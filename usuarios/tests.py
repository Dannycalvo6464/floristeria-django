import json
import re
from io import StringIO
from urllib.error import HTTPError
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, identify_hasher
from django.core import mail
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from usuarios.models import DetalleSolicitudPedido, SolicitudPedido, Usuario


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

    def _datos_entrega(self, **overrides):
        return {
            'direccion': 'Calle 5 # 10-20, San Fernando',
            'codigo_postal': '760001',
            'ciudad': 'Cali',
            'comuna': '19',
            'detalles_domicilio': 'Unidad 3, casa 12, portería principal',
            'acepta_uso_datos': 'on',
            **overrides,
        }

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
        self.assertEqual(self.client.get(reverse('finalizar_pedido')).status_code, 302)

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

    def test_checkout_requiere_sesion_y_regresa_al_checkout_despues_del_login(self):
        usuario = Usuario.objects.create(
            nombre='Ana', correo='ana@flores.com', contrasena='legacy', tipo='Usuario'
        )
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '2'},
        )

        response = self.client.get(reverse('finalizar_pedido'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('next=%2Ffinalizar_pedido%2F', response['Location'])
        login_response = self.client.post(
            reverse('login'),
            {
                'correo': usuario.correo,
                'contrasena': 'legacy',
                'next': reverse('finalizar_pedido'),
            },
        )
        self.assertRedirects(login_response, reverse('finalizar_pedido'))
        self.assertEqual(self.client.session['carrito'], {'rosa-roja': 2})

    def test_login_no_redirige_a_un_host_externo_por_next(self):
        usuario = Usuario.objects.create(
            nombre='Ana', correo='ana@flores.com', contrasena='legacy', tipo='Usuario'
        )

        response = self.client.post(
            reverse('login'),
            {
                'correo': usuario.correo,
                'contrasena': 'legacy',
                'next': 'https://sitio-malicioso.example/',
            },
        )

        self.assertRedirects(response, reverse('panel_usuario'))

    def test_panel_usuario_presenta_accesos_sin_datos_ficticios(self):
        self._login_como()

        response = self.client.get(reverse('panel_usuario'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Todo lo que necesitas, a tu alcance')
        self.assertContains(response, 'Mi perfil')
        self.assertContains(response, 'Mis pedidos')
        self.assertContains(response, 'Catálogo')
        self.assertNotContains(response, 'Total de ventas')

    def test_perfil_presenta_datos_sin_aviso_de_contacto_a_administracion(self):
        usuario = self._login_como()

        response = self.client.get(reverse('mi_perfil'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, usuario.nombre)
        self.assertContains(response, usuario.correo)
        self.assertContains(response, 'profile-card')
        self.assertContains(response, 'Volver a mi espacio')
        self.assertNotContains(response, 'contacta con la administración')

    def test_pedidos_y_panel_admin_no_muestran_avisos_de_funcionalidad_pendiente(self):
        self._login_como(tipo='Administrador')

        orders_response = self.client.get(reverse('mis_pedidos'))
        admin_response = self.client.get(reverse('panel_admin'))

        self.assertEqual(orders_response.status_code, 200)
        self.assertContains(orders_response, 'Aún no hay pedidos para mostrar')
        self.assertNotContains(orders_response, 'pedidos persistentes')
        self.assertEqual(admin_response.status_code, 200)
        self.assertNotContains(admin_response, 'no hay pedidos ni inventario persistente')

    def test_checkout_persiste_solicitud_y_detalles_limpia_carrito_y_muestra_historial(self):
        usuario = self._login_como()
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '2'},
        )
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'ramo-tulipanes'}),
            {'cantidad': '1'},
        )

        checkout_response = self.client.get(reverse('finalizar_pedido'))
        self.assertEqual(checkout_response.status_code, 200)
        self.assertContains(checkout_response, 'Código postal')
        self.assertContains(checkout_response, 'Comuna')
        self.assertContains(checkout_response, 'Detalles adicionales (opcional)')
        self.assertContains(checkout_response, 'Unidad, torre, casa')

        response = self.client.post(
            reverse('finalizar_pedido'),
            self._datos_entrega(),
        )

        solicitud = SolicitudPedido.objects.get(usuario=usuario)
        self.assertRedirects(
            response,
            reverse('confirmacion_pedido', kwargs={'solicitud_id': solicitud.pk}),
        )
        self.assertEqual(solicitud.direccion, 'Calle 5 # 10-20, San Fernando')
        self.assertEqual(solicitud.codigo_postal, '760001')
        self.assertEqual(solicitud.ciudad, 'Cali')
        self.assertEqual(solicitud.comuna, '19')
        self.assertEqual(
            solicitud.detalles_domicilio,
            'Unidad 3, casa 12, portería principal',
        )
        self.assertTrue(solicitud.datos_autorizados)
        self.assertEqual(solicitud.total_referencia, 42000)
        detalles = list(solicitud.productos.order_by('producto_slug'))
        self.assertEqual(len(detalles), 2)
        self.assertEqual(
            [(detalle.producto_slug, detalle.cantidad) for detalle in detalles],
            [('ramo-tulipanes', 1), ('rosa-roja', 2)],
        )
        self.assertEqual(self.client.session['carrito'], {})

        confirmation = self.client.get(
            reverse('confirmacion_pedido', kwargs={'solicitud_id': solicitud.pk})
        )
        self.assertContains(confirmation, 'Solicitud recibida')
        self.assertContains(confirmation, 'Calle 5 # 10-20, San Fernando')
        self.assertContains(confirmation, 'Unidad 3, casa 12')
        self.assertContains(confirmation, '$42.000')

        history = self.client.get(reverse('mis_pedidos'))
        self.assertContains(history, f'Solicitud #{solicitud.pk}')
        self.assertContains(history, 'Pendiente de revisión')

    def test_checkout_rechaza_datos_invalidos_y_conserva_el_carrito(self):
        self._login_como()
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '2'},
        )

        response = self.client.post(
            reverse('finalizar_pedido'),
            self._datos_entrega(codigo_postal='7600', acepta_uso_datos=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'código postal colombiano de 6 dígitos')
        self.assertEqual(
            response.context['form'].errors['acepta_uso_datos'],
            ['Debes autorizar el uso de los datos para enviar la solicitud.'],
        )
        self.assertEqual(SolicitudPedido.objects.count(), 0)
        self.assertEqual(self.client.session['carrito'], {'rosa-roja': 2})

    def test_usuario_no_puede_ver_solicitud_de_otra_cuenta(self):
        propietario = self._login_como()
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '1'},
        )
        self.client.post(
            reverse('finalizar_pedido'),
            self._datos_entrega(),
        )
        solicitud = SolicitudPedido.objects.get(usuario=propietario)
        otro_usuario = Usuario.objects.create(
            nombre='Beatriz',
            correo='beatriz@flores.com',
            contrasena='legacy',
            tipo='Usuario',
        )
        otro_cliente = Client()
        session = otro_cliente.session
        session['usuario_id'] = otro_usuario.pk
        session['usuario_tipo'] = otro_usuario.tipo
        session.save()

        response = otro_cliente.get(
            reverse('confirmacion_pedido', kwargs={'solicitud_id': solicitud.pk})
        )

        self.assertEqual(response.status_code, 404)

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
    def test_recuperacion_envia_codigo_y_restablece_contrasena(self):
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
        codigo = re.search(r'\b(\d{6})\b', mail.outbox[0].body).group(1)
        self.assertNotIn(codigo, response.content.decode())
        self.assertIn('recuperar_codigo_hash', self.client.session)

        unknown_response = self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': 'inexistente@flores.com'},
        )
        self.assertContains(unknown_response, 'recibirás un código')
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            reverse('recuperar_contrasena'),
            {
                'codigo': codigo,
                'nueva_contrasena': 'FloresSeguras!2026',
            },
        )
        self.assertContains(response, 'Tu contraseña se ha actualizado correctamente')
        usuario = Usuario.objects.get(correo='ana@flores.com')
        self.assertTrue(check_password('FloresSeguras!2026', usuario.contrasena))
        self.assertNotIn('recuperar_codigo_hash', self.client.session)

    @override_settings(
        EMAIL_PROVIDER='smtp',
        EMAIL_HOST='',
        DEFAULT_FROM_EMAIL='',
    )
    def test_recuperacion_informa_configuracion_smtp_pendiente(self):
        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': 'ana@flores.com'},
        )
        self.assertContains(response, 'EMAIL_HOST')
        self.assertContains(response, 'EMAIL_HOST_PASSWORD')
        self.assertContains(response, 'La recuperación por correo aún no está configurada')

    @override_settings(
        EMAIL_PROVIDER='resend',
        RESEND_API_KEY='test-resend-key',
        DEFAULT_FROM_EMAIL='Flores Cali <onboarding@resend.dev>',
        EMAIL_TIMEOUT=10,
    )
    @patch('usuarios.views.urlopen')
    def test_recuperacion_envia_codigo_mediante_resend_api(self, urlopen_mock):
        usuario = Usuario.objects.create(
            nombre='Ana',
            correo='ana@flores.com',
            contrasena='vieja123',
            tipo='Usuario',
            activo=True,
        )
        urlopen_mock.return_value.__enter__.return_value.status = 200

        response = self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': usuario.correo},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revisa el correo de tu cuenta')
        api_request = urlopen_mock.call_args.args[0]
        self.assertEqual(api_request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(api_request.get_header('Authorization'), 'Bearer test-resend-key')
        payload = json.loads(api_request.data)
        self.assertEqual(payload['from'], 'Flores Cali <onboarding@resend.dev>')
        self.assertEqual(payload['to'], [usuario.correo])
        self.assertEqual(payload['subject'], 'Código para recuperar tu cuenta de Flores Cali')
        self.assertRegex(
            payload['text'],
            r'Tu código de recuperación es \d{6}\. Vence en 10 minutos\.',
        )
        codigo = re.search(r'\b(\d{6})\b', payload['text']).group(1)
        self.assertIn('html', payload)
        self.assertIn(codigo, payload['html'])
        self.assertNotIn(codigo, response.content.decode())
        self.assertIn('recuperar_codigo_hash', self.client.session)
        urlopen_mock.assert_called_once()

    @override_settings(
        EMAIL_PROVIDER='resend',
        RESEND_API_KEY='test-resend-key',
        DEFAULT_FROM_EMAIL='Flores Cali <onboarding@resend.dev>',
        EMAIL_TIMEOUT=10,
    )
    @patch(
        'usuarios.views.urlopen',
        side_effect=HTTPError('https://api.resend.com/emails', 403, 'rejected', {}, None),
    )
    def test_error_resend_no_devuelve_500_ni_guarda_codigo(self, urlopen_mock):
        Usuario.objects.create(
            nombre='Ana',
            correo='ana@flores.com',
            contrasena='vieja123',
            tipo='Usuario',
            activo=True,
        )

        with self.assertLogs('usuarios.views', level='ERROR'):
            response = self.client.post(
                reverse('recuperar_contrasena'),
                {'correo': 'ana@flores.com'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se pudo enviar el correo de recuperación')
        self.assertNotIn('recuperar_codigo_hash', self.client.session)
        urlopen_mock.assert_called_once()

    @override_settings(
        EMAIL_HOST='smtp.test',
        DEFAULT_FROM_EMAIL='no-reply@flores.test',
    )
    @patch('usuarios.views.EmailMultiAlternatives.send', side_effect=TimeoutError('SMTP connection timed out'))
    def test_recuperacion_smtp_timeout_no_produce_error_500(self, send_mock):
        Usuario.objects.create(
            nombre='Ana',
            correo='ana@flores.com',
            contrasena='vieja123',
            tipo='Usuario',
            activo=True,
        )

        with self.assertLogs('usuarios.views', level='ERROR'):
            response = self.client.post(
                reverse('recuperar_contrasena'),
                {'correo': 'ana@flores.com'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se pudo enviar el correo de recuperación')
        self.assertNotContains(response, 'SMTP connection timed out')
        self.assertNotIn('recuperar_codigo_hash', self.client.session)
        send_mock.assert_called_once()

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST='smtp.test',
        DEFAULT_FROM_EMAIL='no-reply@flores.test',
    )
    def test_codigo_expirado_pide_una_nueva_solicitud(self):
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

        self.assertContains(response, 'La solicitud de recuperación ha expirado')
        self.assertContains(response, 'name="correo"')
        self.assertNotContains(response, 'name="codigo"')
        self.assertNotIn('recuperar_codigo_hash', self.client.session)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST='smtp.test',
        DEFAULT_FROM_EMAIL='no-reply@flores.test',
    )
    def test_codigo_se_invalida_despues_de_cinco_intentos(self):
        usuario = Usuario.objects.create(
            nombre='Ana',
            correo='ana@flores.com',
            contrasena='vieja123',
            tipo='Usuario',
            activo=True,
        )
        self.client.post(
            reverse('recuperar_contrasena'),
            {'correo': usuario.correo},
        )

        for _ in range(5):
            response = self.client.post(
                reverse('recuperar_contrasena'),
                {'codigo': '000000', 'nueva_contrasena': 'FloresSeguras!2026'},
            )

        self.assertContains(response, 'Superaste el número de intentos')
        self.assertNotIn('recuperar_codigo_hash', self.client.session)
        usuario.refresh_from_db()
        self.assertFalse(check_password('FloresSeguras!2026', usuario.contrasena))

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
        self.assertIn('existencia por confirmar', content)
        self.assertNotIn('Este catálogo conserva los productos de demostración existentes', content)
        self.assertIn('Recomendación educativa', content)
        self.assertIn('Aniversario', content)
        self.assertNotContains(response, 'Carrito de demostración')

    def test_catalogo_agrega_al_carrito_sin_redireccion_y_actualiza_contador(self):
        agregar_url = reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'})

        response = self.client.post(
            agregar_url,
            {'cantidad': '2'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), {
            'ok': True,
            'message': 'Rosa Roja se agregó al carrito.',
            'carrito_cantidad': 2,
        })
        self.assertEqual(self.client.session['carrito'], {'rosa-roja': 2})
        catalog_response = self.client.get(reverse('catalogo'))
        self.assertContains(catalog_response, 'Carrito, 2 artículos')
        self.assertContains(catalog_response, 'data-cart-form')
        self.assertContains(catalog_response, 'usuarios/js/cart.js')

        response = self.client.post(
            agregar_url,
            {'cantidad': '3'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.json()['carrito_cantidad'], 5)
        self.assertEqual(self.client.session['carrito'], {'rosa-roja': 5})

    def test_catalogo_ajax_informa_cantidad_invalida_sin_cambiar_sesion(self):
        response = self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '0'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)
        self.assertIn('cantidad entera mayor que cero', response.json()['message'])
        self.assertNotIn('carrito', self.client.session)

    def test_inicio_y_login_tienen_rutas_publicas_distintas(self):
        self.assertEqual(self.client.get(reverse('inicio')).status_code, 200)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        response = self.client.get(reverse('inicio'))
        self.assertContains(response, 'Explorar catálogo')
        self.assertNotContains(response, 'datos de demostración existentes en el catálogo')
        self.assertNotContains(response, 'Catálogo demostrativo.')

    def test_detalle_producto_no_muestra_aviso_de_inventario_no_disponible(self):
        response = self.client.get(
            reverse('detalle_producto', kwargs={'slug': 'rosa-roja'})
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'no tiene inventario disponible')
        self.assertContains(response, 'Precio de referencia')

    def test_busqueda_parcial_sin_distinguir_mayusculas_ni_tildes_y_filtro_de_categoria(self):
        response = self.client.get(reverse('catalogo'), {'q': 'Rosa Roja'})
        self.assertContains(response, 'Rosa Roja')
        self.assertEqual(
            [producto['slug'] for producto in response.context['productos']],
            ['rosa-roja'],
        )

        response = self.client.get(reverse('catalogo'), {'q': 'Ros'})
        self.assertContains(response, 'Rosa Roja')
        self.assertEqual(
            [producto['slug'] for producto in response.context['productos']],
            ['rosa-roja'],
        )

        response = self.client.get(reverse('catalogo'), {'q': 'orquidea'})
        self.assertContains(response, 'Orquídea Blanca')

        response = self.client.get(
            reverse('catalogo'),
            {'q': 'Ros', 'categoria': 'Lirios'},
        )
        self.assertContains(response, 'No encontramos flores que coincidan con esos filtros')
        self.assertEqual(response.context['resultados_count'], 0)

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

    def test_carrito_presenta_resumen_producto_y_controles(self):
        self.client.post(
            reverse('agregar_al_carrito', kwargs={'slug': 'rosa-roja'}),
            {'cantidad': '2'},
        )

        response = self.client.get(reverse('carrito'))

        self.assertContains(response, 'cart-layout')
        self.assertContains(response, 'Rosas')
        self.assertContains(response, 'Precio unitario')
        self.assertContains(response, 'Subtotal')
        self.assertContains(response, 'Total de referencia')
        self.assertContains(response, 'Seguir comprando')
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
