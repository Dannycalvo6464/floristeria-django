# Despliegue de Flores Cali en Render con Supabase

Render ejecuta el backend Django; Supabase aloja PostgreSQL. Este proyecto usa `DATABASE_URL` cuando existe y `db.sqlite3` en desarrollo local cuando está ausente. `.env` es solo local y está excluido de Git.

## Configuración de Render

Actualiza el servicio web existente conectado al repositorio actual; no hace falta crear otro servicio ni otra base. Configura en **Render → servicio → Environment**:

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | URI PostgreSQL de Supabase, con `sslmode=require`. No la guardes en Git. |
| `DJANGO_SECRET_KEY` | Secreto aleatorio largo y exclusivo de producción. |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `floristeria-django.onrender.com` (dominio actual del proyecto; añade dominios personalizados si los usas). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://floristeria-django.onrender.com` (y cada origen HTTPS personalizado que uses). |

La configuración de seguridad activa cookies Secure/HttpOnly, redirección HTTPS, proxy HTTPS y HSTS cuando `DJANGO_DEBUG=false`. No pongas `https://` en `DJANGO_ALLOWED_HOSTS`; sí se necesita en `DJANGO_CSRF_TRUSTED_ORIGINS`.

Para recuperación de contraseña, configura un proveedor de correo:

| Variable | Uso |
| --- | --- |
| `EMAIL_PROVIDER` | `resend` para API HTTPS o `smtp` para un servidor SMTP (predeterminado: `smtp`). |
| `RESEND_API_KEY` | Clave privada de API de Resend, necesaria cuando `EMAIL_PROVIDER=resend`. |
| `DEFAULT_FROM_EMAIL` | Remitente permitido/verificado por el proveedor. En Resend, verifica el dominio del remitente antes del envío real. |
| `EMAIL_TIMEOUT` | Tiempo máximo en segundos para conectar/enviar (predeterminado: `10`). |
| `EMAIL_HOST`, `EMAIL_PORT` | Servidor SMTP y puerto de tu proveedor. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Credenciales SMTP como variables protegidas de Render. |
| `EMAIL_USE_TLS` | `true` con STARTTLS (habitualmente puerto 587). |
| `EMAIL_USE_SSL` | `true` solo si el proveedor requiere TLS implícito; no combinar con `EMAIL_USE_TLS`. |

En Render puedes usar `EMAIL_PROVIDER=resend`, `RESEND_API_KEY` y un `DEFAULT_FROM_EMAIL` aprobado por Resend. Mantén la clave como variable privada; nunca la guardes en Git ni la compartas por chat. Las cuentas/remitentes de prueba del proveedor pueden tener restricciones de destinatario hasta verificar un dominio. La aplicación maneja fallos del proveedor sin devolver un error 500. Los códigos nunca se muestran en pantalla ni se escriben en consola.

## Comandos del servicio

- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input`
- **Start Command:** `gunicorn Floristeria.wsgi:application`

WhiteNoise sirve los archivos recopilados, incluidos los estáticos del admin de Django. La interfaz de Flores Cali conserva sus plantillas y estilos actuales; la plantilla del catálogo carga fotografías desde Unsplash.

## Base de datos y migraciones

Las migraciones existentes son `usuarios.0001_initial` y `usuarios.0002_usuario_activo`, además de las migraciones estándar de Django. Los cambios de este despliegue no cambian modelos ni esquema, por lo que no se necesita crear una migración nueva. No ejecutes `flush`, no borres tablas y no reemplaces `db.sqlite3`.

Antes de ejecutar un comando de base de datos desde Render Shell, confirma que `DATABASE_URL` corresponde al proyecto Supabase `Flores-cali-bd` y revisa `python manage.py migrate --plan`. Si muestra migraciones pendientes, revisa el plan y toma un respaldo antes de aplicar `python manage.py migrate`. No ejecutes migraciones automáticamente en el build.

## Contraseñas existentes

Las cuentas antiguas guardan su contraseña en texto plano. El nuevo registro almacena hashes PBKDF2 de Django. El login comprueba ambos formatos: al primer inicio de sesión válido de una cuenta antigua, convierte su contraseña a hash sin cambiar la clave que escribe la persona. Las cuentas existentes siguen pudiendo iniciar sesión durante el despliegue progresivo.

Para convertir todas las contraseñas antiguas de una vez, después de desplegar este código y **tras hacer un respaldo** de la base Supabase, abre Render Shell, verifica el servicio y ejecuta:

```sh
python manage.py hash_legacy_passwords
```

El comando solo actualiza el campo de contraseña de filas todavía no hasheadas, no imprime credenciales y se puede volver a ejecutar. No lo ejecutes contra SQLite por accidente ni antes de verificar `DATABASE_URL`. No requiere migración de esquema; el hash predeterminado cabe en el campo actual.

El secreto de conexión PostgreSQL fue compartido durante el trabajo en el chat. Rótalo en Supabase antes de producción y actualiza `DATABASE_URL` en Render y en tu `.env` local. Nunca publiques `.env`, claves de SMTP o secretos de Django en GitHub.

## Pruebas locales

Instala dependencias y usa SQLite o una base de pruebas separada:

```powershell
pip install -r requirements.txt
python manage.py check
python manage.py test --settings=Floristeria.test_settings
python manage.py check --deploy
```

La configuración de pruebas fuerza una base SQLite en memoria, aunque el `.env` local tenga `DATABASE_URL`, para evitar que el test runner cree una base de pruebas remota. `check --deploy` necesita que `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY` y los hosts/orígenes de producción estén configurados; ejecutarlo no despliega nada. Para comprobar estáticos localmente: `python manage.py collectstatic --no-input`.
