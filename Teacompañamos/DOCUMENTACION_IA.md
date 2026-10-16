# Documentación sobre el uso de inteligencia artificial

**Proyecto:** Teacompañamos  
**Fecha:** 16 de octubre de 2026

## Propósito

Este documento describe cómo se utilizó un asistente de inteligencia artificial como apoyo durante el desarrollo de Teacompañamos. La IA se usó como herramienta de asistencia para entender requisitos, proponer cambios, redactar y organizar código, y apoyar su verificación.

## Actividades apoyadas por IA

Durante el desarrollo, el asistente colaboró en:

- Completar interfaces HTML para administrar módulos, lecciones y roles.
- Conectar las páginas con vistas y rutas de Django.
- Crear un dashboard de aprendizaje y una navegación para abrir módulos, responder lecciones y consultar la explicación de las respuestas.
- Añadir búsqueda y filtros para los listados administrativos.
- Aplicar estilos compartidos y adaptar las plantillas a pantallas pequeñas.
- Organizar las plantillas en carpetas de administración y aprendizaje.
- Explicar el funcionamiento de los modelos, las vistas y las rutas, así como proponer pasos de implementación antes de hacer cambios.

## Decisiones y límites

- Las decisiones sobre el alcance y el comportamiento de las funciones las confirmó la persona responsable del proyecto.
- La IA no crea ni asigna perfiles o roles por iniciativa propia.
- El flujo de respuesta de lecciones muestra el resultado, pero no registra progreso individual. Ese registro debe asociarse al usuario y al perfil correspondientes cuando se implemente la autenticación.
- No se conectó la aplicación a servicios externos de inteligencia artificial.
- La documentación y el código sugeridos por IA deben ser revisados y validados por el equipo antes de su uso o despliegue.

## Verificación

Los cambios asistidos por IA se comprobaron con verificaciones de Django y pruebas manuales o automatizadas pertinentes, según el alcance. La verificación no reemplaza la revisión funcional del equipo, especialmente antes de desplegar el proyecto en producción.

## Consideraciones de privacidad

No se debe enviar a herramientas de IA información personal, contraseñas, claves, credenciales ni datos sensibles de usuarios. En el estado actual, la IA no procesa datos de la base de datos de la aplicación durante su funcionamiento.
