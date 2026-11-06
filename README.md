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

Abre `http://127.0.0.1:8000/` para elegir el tipo de usuario, ingresar o
registrarte. El dashboard está en `/dashboard/` y requiere iniciar sesión.
El panel de contenido está en `/panel_administracion/` y solo se muestra a
la cuenta `admin` después de ingresar como administrador desde la página inicial.

## Django Admin

El administrador de Django está en `http://127.0.0.1:8000/admin/` y utiliza
la misma base `bd`. En esta instalación la cuenta autorizada es `admin`, que
usa su misma contraseña al ingresar desde la página inicial. En una instalación
nueva, crea esa cuenta con una contraseña elegida por ti:

```powershell
cd Teacompañamos
..\.venv\Scripts\python.exe manage.py createsuperuser --username admin
```

El Admin de Django solo muestra la gestión de **APP > Usuarios**. La cuenta
`admin` conserva su autenticación en `auth_user` y tiene un registro enlazado
en `usuario` para aparecer también en el dashboard; ese registro no se puede
editar ni borrar desde el Admin. Los demás usuarios se registran en la tabla
`usuario` y no reciben permisos administrativos.
En **APP > Usuarios**, la eliminación individual de un estudiante borra también
sus perfiles y registros de progreso después de la confirmación del Admin.
Los roles y las lecciones permanecen disponibles.

## Sesiones de estudiantes y cookies

Las cuentas creadas en `/registro/` o en **APP > Usuarios** pueden ingresar en
`/acceso/` después de elegir Estudiante, Familiar, Profesor u Otro. La
contraseña se comprueba contra el hash guardado en `usuario`.
El primer acceso reutiliza un perfil existente o prepara uno con el rol
`Estudiante` si la cuenta todavía no tiene perfil.
El dashboard, los módulos y las lecciones requieren una sesión. Los intentos
y las lecciones completadas se guardan en `progreso` por perfil.

La sesión se guarda en la tabla `django_session` de la misma base `bd`. Su
identificador viaja en una cookie del navegador con una duración máxima de dos
horas. El botón **Salir** cierra la sesión actual.
La opción **Ampliar lectura** usa otra cookie durante 30 días y no contiene
datos del usuario. El panel de contenido y sus rutas requieren la sesión
autenticada de `admin`.

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
