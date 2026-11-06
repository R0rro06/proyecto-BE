# TEAcompañamos

## Entorno local (Windows)

El proyecto funciona con Python 3.12, Django 4.2 y MariaDB 10.4. Usa la base
`bd` en `localhost:3306`, con el usuario y la contraseña definidos en
`Teacompañamos/Teacompañamos/settings.py`. Antes de iniciar, verifica que el
servidor MariaDB esté encendido y que la base `bd` exista.

El entorno virtual `.venv` ya está creado. Para iniciar la aplicación desde la
raíz del repositorio:

```powershell
cd Teacompañamos
..\.venv\Scripts\python.exe manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El panel de contenido está en
`http://127.0.0.1:8000/panel_administracion/`.

## Django Admin

El administrador de Django está en `http://127.0.0.1:8000/admin/` y utiliza
la misma base `bd`. Para entrar, crea una cuenta administradora de Django con
una contraseña elegida por ti:

```powershell
cd Teacompañamos
..\.venv\Scripts\python.exe manage.py createsuperuser
```

El admin permite gestionar los registros de la tabla `usuario` del proyecto.
Las cuentas que entran al admin se almacenan por separado en `auth_user`.
La gestión de grupos está deshabilitada en el administrador; los usuarios de
Django se pueden editar sin cambiar su pertenencia a grupos.
En **APP > Usuarios**, la eliminación individual de un estudiante borra también
sus perfiles y registros de progreso después de la confirmación del Admin.
Los roles y las lecciones permanecen disponibles.

## Sesiones de estudiantes y cookies

Las cuentas creadas en `/admin/` dentro de **APP > Usuarios** pueden ingresar en
`/acceso/`. La contraseña se comprueba contra el hash guardado en `usuario`.
El primer acceso reutiliza un perfil existente o prepara uno con el rol
`Estudiante` si la cuenta todavía no tiene perfil.
El dashboard sigue siendo público; los intentos y las lecciones completadas se
guardan en `progreso` únicamente cuando el estudiante ha iniciado sesión.

La sesión se guarda en la tabla `django_session` de la misma base `bd`. Su
identificador viaja en una cookie del navegador que caduca al cerrar el
navegador o después de una hora. El botón **Salir** cierra la sesión actual.
La opción **Ampliar lectura** usa otra cookie durante 30 días y no contiene
datos del usuario. El panel de contenido y sus rutas requieren una cuenta
administradora de Django con los permisos correspondientes.

Si la base no tiene aplicadas las migraciones de Django, ejecuta
`..\.venv\Scripts\python.exe manage.py migrate` desde `Teacompañamos` antes de
probar el acceso. Apache por sí solo no sirve este proyecto Django: para el
entorno local usa `manage.py runserver`, salvo que hayas configurado Django en
Apache por separado.

Para recrear el entorno en este equipo y ejecutar las pruebas:

```powershell
py -3.14 -m uv python install 3.12
py -3.14 -m uv venv --python 3.12 --seed .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd Teacompañamos
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py test APP
```

En un equipo con Python 3.12 registrado en el lanzador de Windows, también se
puede crear el entorno con `py -3.12 -m venv .venv`.
