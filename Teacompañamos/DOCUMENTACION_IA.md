# Uso de inteligencia artificial en TEAcompañamos

**Proyecto:** TEAcompañamos

**Actualización:** 11 de noviembre de 2026

## Herramientas y alcance

Se utilizó Codex como asistente de análisis, planificación, implementación, documentación y revisión. También se pidió incorporar Figma a la exploración visual. El código se contrastó con herramientas locales de Django, Git y MySQL. No se integró un modelo de IA dentro de la aplicación ni se envían datos de usuarios a un servicio de IA durante su uso normal.

Una ilustración generada durante la exploración visual se descartó después de que la persona responsable pidiera una interfaz minimalista y accesible, sin ilustraciones. El recurso descartado no forma parte del producto.

## Reformulación técnica de las solicitudes realizadas

Los siguientes prompts son **versiones técnicas redactadas a partir de solicitudes reales del responsable del proyecto**. No son transcripciones literales ni se afirma que hayan sido enviados con esta redacción. Conservan el objetivo de cada petición y explicitan alcance, restricciones y criterios de comprobación. La sección **análisis y resultado** describe lo que se hizo o identificó después de la solicitud. Se omiten datos de acceso.

### 1. Separación de HTML y CSS

**Prompt reformulado:**

> Analiza los templates de la aplicación Django e identifica estilos CSS incrustados o duplicados. Traslada las reglas visuales a archivos estáticos organizados por página o componente y enlázalos mediante `{% static %}`. Conserva la estructura semántica, los formularios, las etiquetas de template, los enlaces y el diseño existente. Verifica el renderizado de las vistas principales y el funcionamiento de sus controles.

**Análisis y resultado.** La intención era retirar estilos incrustados de los templates, mantener el diseño y no romper formularios, enlaces ni etiquetas de Django. Codex ayudó a localizar los templates y a organizar los estilos en `APP/static/APP/`. La revisión humana debía comprobar las páginas con ambos temas, los enlaces y los formularios; que el HTML renderice no demuestra por sí solo que el aspecto se conserve.

### 2. Entorno virtual y base de datos

**Prompt reformulado:**

> Diagnostica los errores de ejecución de Python y Django y prepara el proyecto para funcionar desde un entorno virtual aislado. Verifica la versión del intérprete, instala las dependencias fijadas en `requirements.txt`, comprueba la conexión con MySQL/MariaDB y documenta los comandos necesarios para aplicar migraciones e iniciar el servidor. Confirma el resultado con las comprobaciones de Django, sin modificar ni eliminar datos existentes.

**Análisis y resultado.** Esta petición abarcó dependencias, intérprete de Python, arranque de Django y conexión con la base existente. Se fijaron `Django==4.2.30` y `mysqlclient==2.3.0` en `requirements.txt`, y la configuración de MySQL se mantiene en `Teacompañamos/settings.py`. La comprobación relevante es que `manage.py check` funcione en `.venv`, que las migraciones estén aplicadas y que el ORM pueda leer datos. No se debe presentar un servidor MySQL apagado como un fallo del código.

### 3. Plan antes de modificar Django Admin

**Prompt reformulado:**

> Examina los modelos y la configuración de MySQL existentes y prepara un plan para incorporar Django Admin como interfaz de gestión de usuarios. Describe los modelos que se registrarán, la relación con la base de datos, los permisos de acceso, las migraciones necesarias y la forma de verificar la persistencia. Presenta el plan antes de modificar el código y espera autorización expresa para implementarlo.

**Análisis y resultado.** El usuario separó planificación e implementación. La IA debía identificar los modelos, la base de datos y el alcance de administración antes de tocar código. El visto bueno posterior autorizó los cambios. En la versión actual, Django Admin administra `Usuario`, `Rol` y `Perfil`; el contenido educativo tiene su panel propio. Esta decisión limita el alcance frente a una rúbrica que también menciona grupos y permisos.

### 4. Registro, login, roles y único administrador

**Prompt reformulado:**

> Diseña un flujo de registro e inicio de sesión previo al dashboard utilizando la autenticación nativa de Django. Cada cuenta creada debe persistirse en MySQL, quedar vinculada a un perfil con rol de estudiante, familiar, profesor u otro y ser visible en Django Admin. Restringe la administración de módulos, lecciones y roles a una única cuenta administradora autenticada; elimina accesos administrativos públicos. Explica el diseño y las comprobaciones previstas antes de implementar, y ejecuta los cambios después de recibir aprobación.

**Ajustes de alcance reformulados:**

> Sitúa el ingreso y el registro como punto de entrada del sitio y exige autenticación antes de mostrar el dashboard. Tras aprobar el plan, inicia la implementación.

**Análisis y resultado.** La cuenta se autentica mediante `django.contrib.auth`; `APP.Usuario` conserva la identidad educativa y se vincula con la cuenta de Django. El registro crea un perfil con uno de los cuatro roles. El dashboard y las lecciones requieren una sesión válida. La cuenta principal `admin` es la única autorizada para el panel de contenido y Django Admin. La selección de tipo en el ingreso orienta la interfaz, pero no concede privilegios: el servidor verifica la cuenta real y sus permisos. Esta distinción evita tratar una opción enviada por el navegador como autorización.

### 5. Alcance restringido del panel `/admin/`

**Prompt reformulado:**

> Configura `/admin/` para mostrar exclusivamente la gestión de usuarios, roles y perfiles. Retira del índice administrativo los demás modelos y mantén la gestión de módulos y lecciones en el panel de contenido propio del proyecto. Comprueba que una cuenta no autorizada tampoco pueda acceder a las URLs administrativas mediante peticiones directas.

**Análisis y resultado.** Se registraron solo los modelos `Usuario`, `Rol` y `Perfil` en `APP/admin.py`. `auth.User` y `Group` se retiraron de ese panel, mientras que módulos y lecciones se administran desde `/panel_administracion/`. La IA debía respetar este alcance aunque una rúbrica posterior pidiera administrar también grupos y permisos. La contradicción se documenta; no se presenta como si ambas solicitudes estuvieran satisfechas a la vez.

### 6. Sesiones, cookies y límite de intentos

**Prompt reformulado:**

> Implementa un límite de intentos fallidos para el inicio de sesión del sitio y de Django Admin. Al superar el umbral, impide nuevos intentos durante 60 segundos y comunica el tiempo restante sin revelar si la cuenta existe. Añade un aviso de consentimiento para cookies opcionales que aparezca antes de registrar una elección y permanezca cerrado después de aceptar o rechazar. Mantén un control discreto y accesible para revisar o cambiar la decisión posteriormente.

**Ajustes visuales y funcionales reformulados:**

> Presenta el aviso como un panel compacto en una esquina y adapta sus colores al tema activo. Retira el control de lectura ampliada y coloca allí el selector de modo claro u oscuro. Guarda la preferencia del tema solo cuando exista consentimiento para cookies opcionales y conserva el acceso al control de preferencias.

**Análisis y resultado.** El bloqueo actual se activa tras cinco fallos y dura 60 segundos; se comparte entre el ingreso normal y el de Django Admin mediante `APP/login_throttle.py`. Las sesiones autenticadas usan la tabla de sesiones de Django. El aviso de cookies se muestra hasta aceptar o rechazar y queda accesible desde un control lateral; el tema se conserva solo con consentimiento. `APP/middleware.py`, las vistas de cookies, el template `_cookies.html` y `tema.js` cooperan para aplicar esa preferencia. La cookie de sesión es necesaria para autenticar; la de tema es opcional.

### 7. Cambio visual dirigido por la persona responsable

**Prompt reformulado:**

> Revisa la interfaz propuesta y replantea el diseño con una estética minimalista y accesible, sin ilustraciones decorativas. Prioriza jerarquía tipográfica, contraste, navegación clara, controles legibles y consistencia entre modo claro y oscuro. Conserva las funciones existentes y comprueba el resultado en las páginas principales.

**Preferencia que originó esta reformulación:**

> Minimalista y accesible, sin ilustraciones

**Análisis y resultado.** El primer resultado visual no cumplió la preferencia. La corrección humana cambió la dirección del diseño hacia una interfaz sobria, con controles legibles, adaptable a claro/oscuro y sin imágenes decorativas. Esto muestra que una propuesta generada por IA no se aceptó automáticamente: se revisó contra una preferencia explícita y se descartó la ilustración exploratoria.

### 8. Revisión de seguridad y corrección de hallazgos

**Prompt reformulado:**

> Implementa las funcionalidades aprobadas y, al concluir, revisa de forma independiente el estado del proyecto. Examina autenticación, autorización, persistencia, formularios, cookies, sesiones, dependencias y configuración de despliegue. Documenta hallazgos verificables, su impacto y los límites de la revisión; distingue problemas confirmados de riesgos que requieren una prueba adicional.

**Análisis y resultado.** Se pidió revisar el proyecto después de implementarlo, no asumir que las funciones nuevas eran seguras por existir. La revisión examinó autenticación, permisos, cookies, migraciones y configuración. Detectó riesgos históricos, entre ellos falta de bloqueo de intentos; ese control sí está implementado actualmente. Siguen pendientes la actualización de Django y la evaluación del registro que puede revelar nombres o correos existentes. Una auditoría de código no equivale a una prueba de penetración ni certifica ausencia de fallos.

### 9. Simplificación del código y decisiones sobre pruebas

**Prompts reformulados:**

> Identifica duplicación y responsabilidades mezcladas en `APP/views.py` y en los módulos auxiliares. Refactoriza las partes repetidas mediante funciones o clases compartidas, manteniendo rutas, validaciones, permisos, respuestas y persistencia. Evalúa qué pruebas son redundantes y cuáles cubren comportamientos únicos. Tras confirmar que las pruebas no son necesarias para ejecutar la aplicación y recibir la instrucción de retirarlas, elimina sus archivos fuente y documenta la pérdida de verificación automática.

**Análisis y resultado.** Se agruparon funciones relacionadas, se trasladaron y después se eliminaron las pruebas a petición expresa del usuario. Antes de eliminarlas, la suite se había reducido de 59 a 54 casos sin perder las comprobaciones únicas y los 54 casos pasaron. **Estado actual:** no hay pruebas fuente en el proyecto; esos resultados históricos ya no pueden reproducirse con `manage.py test APP` sin restaurarlas. La aplicación puede funcionar sin ellas, pero futuros cambios tienen menos capacidad de detectar regresiones. El README documenta la necesidad de comprobaciones manuales.

### 10. Revisión de la rúbrica y documentación de IA

**Prompts reformulados:**

> Contrasta cada criterio de `rubrica.md` con el código y la configuración actuales. Clasifica los requisitos como cumplidos, parciales o no verificables sin demostración, e identifica la evidencia correspondiente y las contradicciones con decisiones previas del proyecto. Amplía la documentación del uso de IA con una selección de solicitudes reales, su formulación técnica, las decisiones adoptadas, las comprobaciones efectuadas y los límites de la evidencia. No presentes las reformulaciones como citas literales del usuario.

**Análisis y resultado.** La rúbrica motivó este registro de instrucciones y decisiones. El análisis distinguió lo que está implementado de lo que depende de una demostración: conexión MySQL, CRUD, login, sesiones y cookies se pueden mostrar; la defensa oral aún no está evaluada. También identificó una diferencia entre el alcance solicitado para Django Admin y el criterio de administrar grupos, permisos y estados de acceso. Documentarla permite decidir conscientemente si se conserva la preferencia del proyecto o se cambia para aspirar al nivel máximo de ese criterio.

## Validación humana y técnica

Las respuestas de la IA se contrastaron con `models.py`, `views.py`, `forms.py`, `admin.py`, `settings.py`, `urls.py` y las migraciones. No basta con que una respuesta describa un cambio: hay que localizarlo en el repositorio y comprobar su efecto. La tabla resume evidencias disponibles y sus límites.

| Afirmación que debe defenderse | Evidencia concreta | Límite de la evidencia |
| --- | --- | --- |
| Django conecta con MySQL y conserva datos. | `settings.py` usa el backend MySQL; `showmigrations APP` mostró las siete migraciones aplicadas y el ORM leyó registros de usuarios, módulos, lecciones, perfiles y progreso el 11 de noviembre de 2026. | Una lectura confirma conexión y datos existentes; en la presentación hay que demostrar una escritura y su lectura posterior. |
| La cuenta de aprendizaje usa autenticación de Django. | `accounts.py` crea y vincula `auth.User` con `APP.Usuario`; `views.py` utiliza `authenticate`, `login` y `logout`. | Deben demostrarse un acceso válido, uno inválido y el cierre de sesión. |
| Solo el administrador principal gestiona contenido y usuarios. | `is_primary_admin`, `ContentAdminMixin` y `ProjectAdminSite.has_permission` verifican la cuenta y sus permisos. | Un enlace oculto no es control de acceso; debe probarse también una petición directa con otra cuenta. |
| Hay protección contra intentos de acceso excesivos. | `login_throttle.py` define cinco fallos y bloqueo de 60 segundos; las vistas y Django Admin lo llaman. | En una instalación tras proxy hay que revisar qué IP recibe `REMOTE_ADDR`. |
| Cookies y sesiones tienen propósitos distintos. | `SESSION_ENGINE` guarda la sesión en la base; las vistas y `middleware.py` gestionan consentimiento y tema. | La explicación oral debe mostrar cookies del navegador y su efecto al aceptar, rechazar y cerrar sesión. |
| Las modificaciones no alteraron el esquema sin autorización. | `manage.py check` pasó y `makemigrations --check --dry-run` indicó «No changes detected» en la revisión del 11 de noviembre de 2026. | Esto no sustituye pruebas funcionales completas. |

Durante el desarrollo se ejecutaron suites de 59 y luego 54 pruebas, ambas aprobadas. Posteriormente el usuario pidió eliminar los archivos fuente de pruebas. Por eso **no existe una suite automatizada vigente** que permita repetir esas verificaciones. En el entorno local, `manage.py check --deploy` muestra cinco advertencias asociadas a `DEBUG=1` y HTTP; las opciones de HTTPS, HSTS y cookies `Secure` se activan en la configuración cuando `DJANGO_DEBUG=0`, junto con las variables exigidas para producción. No se afirma que el despliegue esté verificado.

Antes de la migración de autenticación se generó un respaldo de la base de datos y se revisaron colisiones de nombres y formatos de hash. La migración conserva los identificadores de usuarios de aprendizaje, perfiles y avances, vincula las cuentas con `auth_user` y desactiva los hashes de contraseña legados. Los prompts reproducidos aquí no contienen contraseñas, secretos ni datos de usuarios reales.

## Reflexión técnica

La IA aceleró tareas de análisis, documentación y propuesta de cambios, pero no determinó por sí sola las decisiones del producto. La revisión humana fue necesaria para definir quién podía administrar el sistema, conservar la información existente, descartar una propuesta visual y decidir eliminar las pruebas. Esta última decisión simplificó la carpeta visible, pero redujo la verificabilidad futura. Las respuestas del asistente deben tratarse como hipótesis hasta contrastarlas con el código y el comportamiento observado.

La comprobación de dependencias detectó que el proyecto conserva Django 4.2.30, mientras la base de desarrollo usa MariaDB 10.4.32. La actualización del framework requiere revisar primero la compatibilidad del servidor de base de datos. La configuración de producción exige clave secreta, hosts explícitos y usuario MySQL distinto de `root` con contraseña. Las cachés `__pycache__` se ignoran en Git; una carpeta temporal de antiguas pruebas puede permanecer en el disco local aunque los archivos fuente se hayan eliminado.

## Aprendizajes que se deben poder explicar sin la IA

1. **Petición y respuesta:** seguir una URL desde `urls.py` hasta una vista, el formulario, el modelo y el template de respuesta.
2. **Identidad y perfil:** explicar por qué `auth.User` autentica y `APP.Usuario` conserva datos de aprendizaje; demostrar que elegir «administrador» en un formulario no concede permisos.
3. **Datos relacionales:** identificar las claves foráneas entre `Usuario`, `Perfil`, `Rol`, `Modulo`, `Leccion` y `Progreso`, y explicar por qué el avance pertenece al perfil.
4. **Sesiones frente a cookies:** diferenciar la cookie de sesión necesaria, la cookie de consentimiento y la cookie opcional del tema; mostrar su duración y efecto.
5. **CRUD y autorización:** crear, consultar, editar y borrar un registro de prueba; explicar por qué el servidor bloquea el borrado de contenido con dependencias y por qué solo `admin` entra a determinados paneles.
6. **Límites de la evidencia:** distinguir un `manage.py check` correcto, una prueba automatizada histórica, una demostración manual y una auditoría de seguridad. Ninguna de ellas por separado garantiza ausencia de errores.

## Privacidad y límites

- No se deben introducir contraseñas, claves, datos identificables ni volcados de la base en prompts.
- Las herramientas de IA no sustituyen la evaluación educativa, la revisión de accesibilidad ni las pruebas sobre una copia de la base.
- La auditoría de código no equivale a una prueba de penetración ni garantiza ausencia de vulnerabilidades.
- El equipo debe revisar la versión, aplicar las migraciones y validar la instalación en el entorno de entrega antes de presentar el proyecto.
