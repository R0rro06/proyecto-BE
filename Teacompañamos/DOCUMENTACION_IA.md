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


## Decisiones y límites

- Las decisiones sobre el alcance y el comportamiento de las funciones las confirmó la persona responsable del proyecto.
- El flujo de respuesta de lecciones muestra el resultado, pero no registra progreso individual. Ese registro debe asociarse al usuario y al perfil correspondientes cuando se implemente la autenticación.
- No se conectó la aplicación a servicios externos de inteligencia artificial.
- La documentación y el código sugeridos por IA deben ser revisados y validados por el equipo antes de su uso o despliegue.

## Verificación

Los cambios asistidos por IA se comprobaron con verificaciones de Django y pruebas manuales o automatizadas pertinentes, según el alcance. La verificación no reemplaza la revisión funcional del equipo, especialmente antes de desplegar el proyecto en producción.

## Consideraciones de privacidad

No se debe enviar a herramientas de IA información personal, contraseñas, claves, credenciales ni datos sensibles de usuarios. En el estado actual, la IA no procesa datos de la base de datos de la aplicación durante su funcionamiento.

## Ejemplos de instrucciones dadas a la IA

Los siguientes ejemplos resumen solicitudes realizadas durante el desarrollo:

### Interfaces y administración

- «Quiero que el CRUD se maneje desde un panel llamado `panel_admin`
- «Agrega desde el dashboard un botón para acceder al panel de administración».
- «Aplica CSS al panel de administración y a las demás plantillas».


### Roles y filtros

- «Implementa un CRUD para crear, editar, eliminar y actualizar roles en la tabla `rol`».
- «Agrega búsqueda y filtros para módulos y lecciones en el panel de administración».
- «Impide eliminar un rol mientras esté asociado a un perfil».

### Organización y documentación

- «Organiza las plantillas HTML en carpetas para que el proyecto quede más ordenado».

### Contenido educativo

- «Propón tres módulos con tres lecciones cada uno, con preguntas de Verdadero o Falso».
