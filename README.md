# TEAcompañamos

Aplicación educativa hecha con Django y MySQL/MariaDB para aprender sobre trastorno del espectro autista. Presenta módulos y lecciones con ejercicios de verdadero o falso, guarda el avance por usuario y diferencia los permisos de estudiantes y del administrador.

## Requisitos

- Python 3.12
- MySQL o MariaDB disponible en `localhost:3306`
- Base de datos `bd` creada previamente
- Dependencias fijadas en `requirements.txt`

El repositorio incluye `.venv` en este equipo. Para preparar un entorno virtual nuevo en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Compatibilidad pendiente

La instalación funcional verificada utiliza Django 4.2.30 y MariaDB 10.4.32. Django 4.2 ya no recibe actualizaciones de seguridad; Django 5.2 requiere MariaDB 10.5 o posterior, por lo que la actualización está bloqueada hasta elevar primero la versión del servidor de base de datos. Antes de exponer el sitio fuera del entorno local, planifica esa actualización y vuelve a ejecutar las comprobaciones de compatibilidad.

La auditoría de código detectó además que el registro puede revelar si un nombre o correo ya existe. No publiques el sitio con `DJANGO_DEBUG=1`; habilita `DJANGO_DEBUG=0` y configura valores de producción. Estas tareas pendientes no quedan cubiertas solo porque las pruebas automatizadas pasen.

## Configuración

`Teacompañamos/Teacompañamos/settings.py` lee la configuración desde variables de entorno. No carga automáticamente un archivo `.env`. En PowerShell, define las variables antes de ejecutar Django:

```powershell
$env:DB_NAME = 'bd'
$env:DB_USER = 'usuario_mysql'
$env:DB_PASSWORD = 'contraseña_local'
$env:DB_HOST = 'localhost'
$env:DB_PORT = '3306'
$env:DJANGO_SECRET_KEY = 'una-clave-larga-y-aleatoria'
$env:DJANGO_DEBUG = '1'
$env:DJANGO_ALLOWED_HOSTS = '127.0.0.1,localhost'
```

Para desarrollo local se pueden omitir las variables y se usan los valores locales definidos en settings. Para producción, al configurar `DJANGO_DEBUG=0`, settings exige una clave secreta, una lista explícita de hosts y un usuario MySQL no root con contraseña. No subas secretos al repositorio.

## Ejecutar el proyecto

Desde la raíz:

```powershell
cd Teacompañamos
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

Abre `http://127.0.0.1:8000/`. La página inicial conduce a ingreso o registro. Los usuarios se clasifican como estudiante, familiar, profesor u otro al registrarse; el rol se obtiene de su perfil después de iniciar sesión. El dashboard, módulos y lecciones requieren una sesión autenticada. El panel de gestión de contenido está en `/panel_administracion/` y solo permite el acceso al superusuario principal `admin` con los permisos correspondientes.

Para dar de alta esa cuenta en una instalación nueva, usa una contraseña segura elegida por el equipo:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser --username admin
```

El acceso a `/admin/` también está restringido a la cuenta principal `admin`. Ese apartado muestra únicamente **Usuarios, Roles y Perfiles**. En Perfiles se puede cambiar el rol de una cuenta normal; la creación y el borrado directos de perfiles están bloqueados para proteger el progreso. Los módulos y las lecciones se administran desde `/panel_administracion/`. El acceso administrativo existente en la base del proyecto debe conservarse al instalar una copia; no se documentan contraseñas aquí.

Tras cinco accesos fallidos se bloquean los nuevos intentos durante un minuto. El acceso normal cuenta fallos por usuario e IP; los dos formularios de acceso del administrador comparten el mismo contador por IP. Los contadores se guardan en `login_attempt` dentro de MySQL y se limpian al iniciar sesión correctamente.

## Datos y autenticación

Las cuentas usan la autenticación nativa de Django. La tabla `auth_user` conserva el hash de contraseña y los indicadores de permisos; cada cuenta de aprendizaje queda enlazada a un registro `APP.Usuario`, cuyo identificador y relaciones de perfil/progreso se conservan. La migración `0005_unify_user_auth` enlaza las cuentas anteriores y vuelve inutilizable el hash legado en `usuario.password` para evitar dos credenciales activas.

Los perfiles enlazan usuarios con roles. Los intentos y las fechas de finalización se almacenan en `progreso` asociados al perfil y a la lección. Las migraciones del proyecto están en `Teacompañamos/APP/migrations/`.

## Sesiones y cookies

Django guarda la sesión autenticada en `django_session` (duración máxima de dos horas) y envía al navegador el identificador en una cookie `HttpOnly` y `SameSite=Lax`. El cierre de sesión elimina la sesión. El avance del dashboard se calcula para el usuario conectado.

La aplicación utiliza una cookie de consentimiento durante 180 días. El aviso aparece como una tarjeta pequeña en la esquina inferior derecha y se cierra después de aceptar o rechazar; el botón «Cookies» permite volver a abrirlo y cambiar la decisión. Si el navegador borra las cookies o vence el plazo de 180 días, el aviso se muestra de nuevo. El control de modo claro/oscuro reemplaza la antigua lectura ampliada; al aceptar las cookies opcionales, el tema elegido se guarda durante 180 días. Si se rechazan, el cambio de tema solo dura mientras se permanece en la página. En conexiones HTTPS, las cookies configuradas por las vistas se marcan `Secure`.

## Verificación

Desde `Teacompañamos/` puedes ejecutar:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
..\.venv\Scripts\python.exe manage.py test APP
```

La versión final debe validarse con el resultado de estas comprobaciones después de instalar dependencias. Ejecuta `migrate` sobre una copia de producción solo después de tener un respaldo verificado. El respaldo previo de este desarrollo se creó fuera del repositorio y no debe compartirse públicamente.
