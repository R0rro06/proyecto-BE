# TEAcompañamos

Informe técnico de implementación ES3

Programación Backend · Unidad de aprendizaje 2

Versión revisada: noviembre de 2026

Tecnologías: Python, Django 4.2.30 y MySQL/MariaDB

## Síntesis

TEAcompañamos entrega una aplicación web educativa con persistencia relacional, módulos y lecciones, progreso individual, autenticación nativa de Django y permisos diferenciados. La migración de usuarios existente se aplicó en la base de desarrollo conservando perfiles y avances. La suite final reportó 57 pruebas aprobadas. La auditoría de código no encontró una vía crítica de escalada de privilegios, pero sí dejó riesgos abiertos que deben resolverse antes de publicar: Django fuera de soporte, falta de límites de intentos y configuración DEBUG local.

El principal pendiente técnico es actualizar la plataforma de base de datos: la instalación funciona con Django 4.2.30 y MariaDB 10.4.32, pero esa rama de Django ya no recibe correcciones de seguridad. Se debe elevar MariaDB a una versión compatible antes de actualizar Django y desplegar el sistema fuera del entorno local.

## Introducción

El proyecto busca ofrecer una experiencia de aprendizaje digital organizada para estudiantes, familiares, docentes y otras personas interesadas en comprender temas relacionados con el trastorno del espectro autista. La aplicación permite consultar contenidos por módulos, responder ejercicios y conservar el progreso ligado a una cuenta.

La solución contribuye al ODS 4 al ofrecer contenidos de aprendizaje en una estructura clara y accesible. También se relaciona con el ODS 10, en particular con la inclusión social y educativa de personas con discapacidad. Esta relación describe el propósito del producto; no constituye una evaluación de impacto ni una intervención clínica. Las metas de educación inclusiva y de inclusión de personas con discapacidad se describen en la Agenda 2030 de Naciones Unidas.

### Objetivo de la solución

Construir un sistema web que permita gestionar usuarios, roles, módulos y lecciones; autenticar a las personas con el mecanismo integrado de Django; restringir las funciones administrativas y persistir el avance mediante MySQL/MariaDB.

## Arquitectura y organización

El backend sigue el patrón MVT de Django. La aplicación `APP` concentra modelos, formularios, vistas, rutas, migraciones, plantillas y administración. El paquete `Teacompañamos` define settings, middleware, rutas globales y WSGI. La capa de modelos persiste la información; las vistas aplican reglas de negocio y permisos; las plantillas presentan páginas propias para el acceso y el aprendizaje.

| Parte MVT | Responsabilidad en el proyecto |
| --- | --- |
| Modelo | `APP/models.py`: usuarios, perfiles, roles, módulos, lecciones, estados y progreso. |
| Vista | `APP/views.py`: acceso, registro, dashboard, ejercicios y CRUD del panel de contenidos. |
| Plantilla | `APP/templates/APP/`: interfaz de aprendizaje y formularios administrativos. |
| Configuración | `Teacompañamos/settings.py`: apps, middleware, base de datos, sesiones y medidas de despliegue. |

La base `bd` se conecta a través del backend MySQL de Django. La configuración admite variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`. El modo SQL estricto se establece para que MariaDB informe errores de integridad y truncamiento como errores de escritura.

## Modelos y relaciones

En la base de desarrollo verificada se observaron tres módulos, siete lecciones, tres cuentas de aprendizaje, tres perfiles, seis registros de avance y cinco roles. Son cifras de la instalación usada para esta revisión, no datos que la aplicación requiera en otras instalaciones.

| Entidad | Datos y relaciones |
| --- | --- |
| Usuario | Nombre y correo de la cuenta de aprendizaje. Tiene un vínculo uno a uno con `auth.User`. |
| Perfil | Relaciona un usuario de aprendizaje con un rol. |
| Rol | Nombre, descripción y código único para las categorías de acceso. |
| Modulo | Título, descripción y orden de presentación. |
| Leccion | Pregunta, respuesta correcta y explicación; pertenece a un módulo. |
| Progreso | Intentos y fecha de término por perfil y lección; estado opcional. |
| Estado | Catálogo relacionado opcionalmente con un registro de progreso. |

Las relaciones entre perfiles y usuarios, y entre progreso y perfil, usan borrado en cascada. Los vínculos de progreso con lección y de perfil con rol protegen la integridad relacional mediante las reglas de eliminación del modelo. Los cambios de estructura quedan registrados como migraciones versionadas.

## Persistencia y migración de cuentas

La migración `0005_unify_user_auth` transforma las cuentas anteriores en cuentas nativas de Django sin cambiar los identificadores de `APP.Usuario`, sus perfiles ni su progreso. Antes de crear cuentas, valida colisiones normalizadas, nombres reservados, compatibilidad del hash y el límite de longitud del campo de contraseña de Django. Copia el hash válido sin tratarlo como una contraseña en claro y vuelve inutilizable el hash legado para evitar dos fuentes activas de autenticación.

La migración se aplicó a la base de desarrollo. Después de aplicarla se verificaron tres vínculos usuario-cuenta, tres perfiles y seis avances. Se generó un respaldo de MySQL previo a la operación; el archivo se conserva localmente fuera del repositorio y no se incorpora a los entregables.

## Operaciones y administración

La interfaz propia permite listar, buscar, filtrar, crear, modificar y eliminar módulos, lecciones y roles. Los formularios restringen los valores de respuesta a Verdadero o Falso y validan los campos requeridos. Las vistas bloquean la eliminación de módulos que contienen lecciones, de lecciones con progreso asociado y de roles todavía asignados.

El Django Admin muestra únicamente Usuarios, Roles y Perfiles, con columnas, búsquedas y filtros. En Perfiles se puede cambiar el rol de una cuenta normal; la creación y el borrado directos quedan bloqueados para proteger su avance. Módulos y lecciones se gestionan en el panel propio del proyecto. La eliminación individual de una cuenta elimina sus perfiles y progresos asociados y sincroniza la baja de la cuenta de autenticación. La cuenta principal `admin` no se puede modificar ni eliminar desde la gestión de usuarios.

## Autenticación y control de acceso

El registro crea una cuenta en `auth_user`, el registro de aprendizaje enlazado y un perfil con uno de los cuatro roles públicos: estudiante, familiar, profesor u otro. Django aplica el almacenamiento y verificación de contraseñas con hash y los validadores configurados en el proyecto. El inicio de sesión verifica las credenciales con `authenticate` y crea la sesión con `login`; el cierre utiliza `logout`. El rol se lee del perfil y no se acepta como prueba de identidad en el formulario de acceso.

El dashboard, las páginas de módulo y las respuestas de lección requieren una cuenta autenticada. La administración de módulos, lecciones y roles revisa permisos Django y el usuario principal. El sitio Admin usa una clase de administración propia que autoriza únicamente la cuenta `admin`; las demás cuentas no reciben privilegios de personal ni de superusuario.

## Sesiones y cookies

Las sesiones se guardan en `django_session` con una duración máxima de dos horas. La cookie de sesión es `HttpOnly` y `SameSite=Lax`; en modo de despliegue se configura `Secure`. Las vistas usan la identidad autenticada para cargar el perfil y calcular el avance personal. Las sesiones de la implementación antigua no conceden acceso; después de la migración, cada usuario debe volver a iniciar sesión.

La cookie `consentimiento_cookies` guarda la decisión de aceptación o rechazo durante 180 días. Las preferencias funcionales `tema` (180 días) y `lectura_ampliada` (30 días) solo se conservan cuando hay consentimiento. El middleware elimina y oculta esas preferencias si no existe consentimiento aceptado. El tema define la preferencia visual; la opción de lectura amplía la tipografía y el espaciado.

## Medidas de seguridad y riesgos

- Autenticación y hash de contraseñas gestionados por Django, con validadores de similitud, longitud, contraseñas comunes y valores numéricos.

- Middleware de protección CSRF, cookies de sesión HttpOnly y SameSite, y comprobación de destinos de redirección para evitar redirecciones a otros dominios.

- Protección de datos de contraseña en los formularios de ingreso y administración para reducir su aparición en herramientas de depuración.

- Límite de 256 KiB para solicitudes de formulario antes de analizar los datos multipart.

- Las vistas de eliminación del CRUD aceptan solo los métodos HTTP previstos; no admiten DELETE directo que pueda omitir la confirmación del formulario.

- Separación de permisos de cuenta normal y administrador, y consultas con el ORM de Django.

- En producción, settings falla si faltan la clave secreta, los hosts permitidos o un usuario MySQL no root con contraseña. En modo no DEBUG se habilitan HTTPS, redirección SSL y HSTS.

- La configuración local se restringe a hosts de loopback; `.env`, volcados SQL, `staticfiles` y temporales del agente se excluyen del control de versiones.

La auditoría independiente de código no observó una vía crítica para que una cuenta normal escale a administradora ni para que lea el progreso de otra persona. Esto describe la revisión de código realizada, no una prueba de penetración ni una garantía de ausencia de fallos.

Hallazgo alto antes de publicar: Django 4.2.30 quedó fuera de soporte de seguridad en abril de 2026. El entorno existente usa MariaDB 10.4.32, que impide migrar directamente a Django 5.2; primero se debe actualizar MariaDB y luego Django, ejecutar la suite y revisar el despliegue. Fuentes: https://www.djangoproject.com/download/ y https://www.djangoproject.com/weblog/2026/nov/03/security-releases/.

Hallazgos medios: la aplicación aún no limita intentos repetidos de ingreso en la página de acceso ni en Django Admin; antes de publicar conviene añadir límites por cuenta e IP con una estrategia de almacenamiento compartida. Si se expone con el valor local predeterminado `DJANGO_DEBUG=1`, el entorno no es apropiado para producción; debe establecerse explícitamente `DJANGO_DEBUG=0`. La configuración ahora falla de forma cerrada cuando faltan la clave secreta, los hosts o una cuenta MySQL no root con contraseña.

Hallazgo bajo: el registro puede revelar si un nombre de usuario o correo ya está ocupado. Puede reducirse con mensajes genéricos, manteniendo mensajes de ingreso genéricos. Una clave secreta local que haya quedado en el historial del repositorio debe rotarse si se reutilizó fuera del equipo. La configuración pasó `check --deploy` con valores ficticios; eso valida settings, no un servidor desplegado.

## Pruebas y evidencia técnica

La verificación final reportó `manage.py test APP`: 57 de 57 pruebas aprobadas. También pasaron `manage.py check`, `makemigrations --check --dry-run` y `check --deploy` usando valores ficticios de producción. Estos resultados corresponden al entorno local con Django 4.2.30 y MariaDB 10.4.32. La migración 0005 se verificó aplicada sobre la base de desarrollo y se contrastaron los recuentos de cuentas, perfiles y progresos.

## Uso de inteligencia artificial

Codex se utilizó para analizar los requisitos, preparar un plan, implementar y revisar cambios de código, y redactar documentación. Figma se usó para prototipar pantallas. Una ilustración generada durante la exploración fue descartada tras solicitarse una interfaz minimalista y accesible sin ilustraciones; no se integra en la aplicación.

### Prompts representativos

- Analiza el proyecto y el PDF de evaluación; indica qué requisitos están cubiertos y cuáles faltan.

- Implementa el registro con usuarios en la base de datos, autenticación y restricción del administrador.

- Termina el desarrollo y realiza una auditoría para revisar el estado del proyecto y sus vulnerabilidades.

- Replantea el diseño visual como una interfaz minimalista y accesible, sin ilustraciones.

### Validación y reflexión

Las propuestas de IA se revisaron frente a los modelos, las rutas, los permisos, las migraciones y las pruebas. Antes de migrar cuentas se revisaron colisiones y hashes y se obtuvo un respaldo. La persona responsable corrigió la dirección visual propuesta, lo que muestra que la herramienta asiste el proceso pero no sustituye las decisiones de diseño, la validación de código ni la evaluación del equipo. No se entregaron contraseñas ni datos personales a la herramienta.

## Conclusiones y demostración

El sistema integra persistencia relacional, registro de usuarios, autenticación de Django, control administrativo, seguimiento de progreso y cookies de preferencias. La migración preservó el modelo de progreso existente y el acceso de usuarios no administrativos se separó del acceso de gestión. La actualización del motor de base de datos y la migración a una versión de Django con soporte son los pasos técnicos prioritarios antes de un despliegue.

### Secuencia sugerida para la defensa

- Mostrar la página inicial, crear una cuenta y comprobar que aparece en el dashboard y en Django Admin.

- Cerrar sesión, entrar de nuevo y abrir un módulo; responder una lección y mostrar el avance persistido.

- Demostrar que una cuenta normal no entra al panel de gestión y que la cuenta principal puede administrar módulos, lecciones y roles.

- Crear, consultar, editar y eliminar un registro de prueba desde el CRUD y mostrar su validación o mensaje de error pertinente.

- Aceptar o rechazar cookies, cambiar tema y preferencia de lectura y comprobar el efecto tras recargar la página.

- Ejecutar los controles de Django y presentar el estado de migraciones, pruebas y hallazgos de auditoría.

## Fuentes

Pauta de evaluación ES3 de Programación Backend, documento entregado por el equipo: ES3_BACK_END.pdf (2026).

Naciones Unidas, Objetivo de Desarrollo Sostenible 4, Educación de calidad: https://sdgs.un.org/goals/goal4

Naciones Unidas, Objetivo de Desarrollo Sostenible 10, Reducción de las desigualdades: https://sdgs.un.org/goals/goal10

Django, versiones soportadas y calendario de soporte: https://www.djangoproject.com/download/

Django, avisos de seguridad de noviembre de 2026: https://www.djangoproject.com/weblog/2026/nov/03/security-releases/
