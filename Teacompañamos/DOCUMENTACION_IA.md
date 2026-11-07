# Uso de inteligencia artificial en TEAcompañamos

**Proyecto:** TEAcompañamos

**Actualización:** noviembre de 2026

## Herramientas y alcance

Se utilizó Codex como asistente de desarrollo y revisión. También se usaron Figma para preparar pantallas de referencia y herramientas de verificación del entorno para ejecutar controles de Django, migraciones y pruebas. No se integró un modelo de IA dentro de la aplicación ni se envían datos de usuarios a un servicio de IA durante el uso normal.

Una ilustración generada durante la exploración visual se descartó después de que la persona responsable pidiera una interfaz minimalista y accesible, sin ilustraciones. El recurso descartado no forma parte del producto.

## Ejemplos representativos de instrucciones

- «Analiza los requisitos del PDF y el proyecto, enumera lo que existe y lo que falta, y propón un plan detallado antes de implementar».
- «Implementa el registro con persistencia, autenticación de Django, distinción de roles y acceso administrativo restringido».
- «Revisa el proyecto al terminar y audita sus vulnerabilidades».
- «El diseño no me gustó; quiero algo minimalista y accesible, sin ilustraciones».

Estas instrucciones orientaron el análisis de requisitos, los cambios de backend, la revisión de seguridad y la corrección del diseño a partir de comentarios de la persona responsable.

## Validación humana y técnica

Las sugerencias de código se contrastaron con los modelos, vistas, formularios, permisos, rutas y migraciones del repositorio. En la verificación final comunicada por el equipo, `manage.py test APP` reportó 57 de 57 pruebas aprobadas; también pasaron `manage.py check`, `makemigrations --check --dry-run` y `check --deploy` con valores ficticios de producción. La auditoría independiente de código identificó la versión de Django fuera de soporte, falta de límites de intentos en login/Admin, riesgo de exposición si se deja DEBUG activo y enumeración de nombre/correo en registro. La revisión no observó escalada de una cuenta normal a administradora ni lectura de progreso ajeno; el trabajo fue una revisión de código, no una prueba de penetración.

Antes de la migración de autenticación se generó un respaldo de la base de datos y se revisaron colisiones de nombres y formatos de hash. La migración conserva los identificadores de usuarios de aprendizaje, perfiles y avances, vincula las cuentas con `auth_user` y desactiva los hashes de contraseña legados. Los datos personales, contraseñas y secretos no se incluyeron en prompts.

## Reflexión técnica

La IA aceleró tareas de análisis, documentación y propuesta de cambios, pero no determinó por sí sola las decisiones del producto. La revisión humana fue necesaria para definir quién podía administrar el sistema, conservar la información existente y corregir una propuesta visual que no coincidía con la preferencia del equipo. Las respuestas del asistente deben tratarse como hipótesis hasta verificarlas con código, pruebas y datos del proyecto.

La comprobación de dependencias detectó que el proyecto conserva Django 4.2.30, mientras la base de desarrollo usa MariaDB 10.4.32. Django 4.2 está fuera de soporte de seguridad; la actualización a Django 5.2 requiere primero subir MariaDB a una versión compatible. Ese trabajo queda señalado como prioridad; no se afirma que la versión vigente tenga soporte de seguridad actual. La configuración de producción requiere clave secreta, hosts explícitos y usuario MySQL no root con contraseña. Una auditoría también encontró bytecode antiguo versionado; se agregaron reglas de exclusión y esos archivos se retiraron del índice. Si la clave histórica se reutilizó fuera del entorno local, debe rotarse.

## Privacidad y límites

- No se deben introducir contraseñas, claves, datos identificables ni volcados de la base en prompts.
- Las herramientas de IA no sustituyen la evaluación educativa, la revisión de accesibilidad ni las pruebas sobre una copia de la base.
- La auditoría de código no equivale a una prueba de penetración ni garantiza ausencia de vulnerabilidades.
- El equipo debe revisar la versión, aplicar las migraciones y validar la instalación en el entorno de entrega antes de presentar el proyecto.
