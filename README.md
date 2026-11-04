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
