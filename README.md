# Arquitectura de Software - ANB Rising Stars Showcase

## 1. Recolección de Requisitos

**Funcionales:**
- Gestión de usuarios: registro, autenticación, perfiles.
- Carga de videos por jugadores.
- Procesamiento asíncrono de videos: recorte, ajuste de resolución/aspecto, marca de agua, eliminación de audio, cortinilla.
- Votación pública y ranking de jugadores.
- Consulta y descarga de videos procesados.
- Eliminación de videos bajo condiciones.
- Gestión del ciclo de vida de los archivos.
- Exposición de endpoints REST documentados con OpenAPI.

**No funcionales:**
- Escalabilidad (procesamiento y concurrencia).
- Seguridad (autenticación, autorización, gestión de contraseñas, JWT).
- Disponibilidad y resiliencia.
- Portabilidad (contenedores Docker).
- Facilidad de despliegue (docker-compose, Nginx proxy).
- Documentación y pruebas automatizadas.

---

## 2. Restricciones

- Backend en Python (FastAPI) o Go (Gin/Echo). Se opta por **Python + FastAPI** por robustez y ecosistema de procesamiento de videos.
- Base de datos relacional: **PostgreSQL** (alternativa: MySQL).
- Broker de mensajes: **RabbitMQ** (alternativa: Redis, Kafka).
- Procesamiento asíncrono: **Celery** (alternativa: Kafka).
- Almacenamiento inicial: sistema de archivos local (abstraído para futura migración a S3).
- Despliegue en Docker (Ubuntu base).
- Nginx como proxy inverso.
- Pruebas con Postman y Newman.
- SonarQube para análisis de calidad.
- No se permite aún uso de nube pública.
- Autenticación y autorización vía JWT.

---

## 3. Estilo y Principios Arquitectónicos

- **Microservicio modularizado** (aunque todo en una única app web para entrega 1, con separación clara de responsabilidades).
- **Event-driven** para procesamiento asíncrono (tareas encoladas y procesadas por worker).
- **API-first**: contratos claros, documentados y validados.
- **Abstracción de infraestructura** (almacenamiento, procesamiento desacoplado (Para futura migración a S3)).
- **Defensa en profundidad** para seguridad.

---

## 4. Modelado de la Solución (C4, alto nivel)

### Diagrama de Contexto (C4 - Nivel 1)
- Usuarios: Jugadores, Jurado/Público, Admins.
- Sistema: Plataforma ANB Rising Stars Showcase.
- Integraciones: Email (para registro), almacenamiento de archivos, sistema de procesamiento de videos.

### Diagrama de Contenedores (C4 - Nivel 2)

**Componentes principales:**

- **API Gateway (Nginx):** Proxy inverso, redirecciona tráfico HTTP/HTTPS.
- **Backend API (FastAPI):** Expone endpoints REST, gestiona autenticación, usuarios, videos, votos, rankings.
- **Task Worker (Celery):** Procesa videos en segundo plano, conectado al broker de mensajes.
- **Broker de Mensajes (RabbitMQ):** Encola tareas asíncronas.
- **Base de Datos (PostgreSQL):** Persiste usuarios, videos, votos.
- **Almacenamiento de Archivos:** Sistema de archivos local con capa de abstracción.
- **Cache (Redis):** Almacena resultados de ranking y sesiones temporales.
- **SonarQube:** Análisis de calidad del código.
- **Postman/Newman:** Pruebas de API automatizadas.

### Diagrama de Componentes (C4 - Nivel 3)

- **Auth Module:** Registro, login, JWT, gestión de contraseñas.
- **Video Module:** Upload, consulta, detalle, eliminación.
- **Async Task Manager:** Orquestación de procesamiento de video.
- **Voting Module:** Lista de videos públicos, votación, control antifraude.
- **Ranking Module:** Generación dinámica y cache de rankings.
- **Storage Adapter:** Abstracción para sistema de archivos, preparada para S3.
  
---

## 5. Selección de Tecnologías

| Componente               | Tecnología          | Justificación                                      |
|--------------------------|--------------------|----------------------------------------------------|
| API REST                 | FastAPI (Python)   | Alto rendimiento, OpenAPI, fácil de testear        |
| Base de datos            | PostgreSQL         | Escalable, soporte JSON, vistas materializadas     |
| Broker de mensajes       | RabbitMQ           | Fiable, soporta DLQ y reintentos                   |
| Tareas asíncronas        | Celery             | Integración nativa con Python, soporte para RabbitMQ|
| Almacenamiento archivos  | Sistema de archivos (abstracción S3) | Migración futura sencilla                    |
| Proxy reverso            | Nginx              | Estabilidad y rendimiento                          |
| Cache                    | Redis              | TTL rankings, sesiones                             |
| CI/CD                    | GitHub Actions     | Automatización pruebas y SonarQube                 |
| Análisis calidad         | SonarQube          | Control de bugs/vulnerabilidades                   |
| Pruebas de API           | Postman/Newman     | Documentación y automatización                     |
| Contenedores             | Docker/Docker Compose | Portabilidad y consistencia                     |

---

## 6. Patrones y Prácticas

- **Repository Pattern:** Para acceso a la base de datos.
- **Adapter Pattern:** Para almacenamiento de archivos.
- **Service Layer:** Negocio desacoplado de controladores.
- **JWT:** Autenticación y autorización.
- **Retry/Backoff:** Para tareas fallidas en Celery.
- **Dead Letter Queue:** En RabbitMQ para tareas no procesadas.
- **Logging estructurado:** Para trazabilidad.
- **Validación exhaustiva:** Pydantic para entrada de datos.
- **Testing:** Pytest y coverage para unitarias.

---

## 7. Escalabilidad y Seguridad

- **Escalabilidad:** Worker de procesamiento horizontalmente escalable, API stateless, caché para rankings.
- **Seguridad:** JWT, hash de contraseñas (bcrypt), validación de inputs, control de acceso en endpoints.
- **Resiliencia:** Uso de DLQ en RabbitMQ, reintentos automáticos, almacenamiento desacoplado.

---

## 8. Documentación

- **Diagramas:** Incluidos en `/docs/Entrega_1/` (C4, ERD, despliegue).
- **OpenAPI:** Documentación generada automáticamente por FastAPI.
- **Pruebas Postman:** Colecciones en `/collections/`.
- **Guía de despliegue:** Paso a paso reproducible en README.

---

## 9. Validación y Mejora

- **Revisión por equipo y tutor.**
- **Pruebas de carga y stress.**
- **Monitoreo con logs y métricas.**
- **Iteración por feedback.**

---

## 10. Despliegue (Docker Compose)

- **Servicios:** api, worker, rabbitmq, postgres, redis, nginx, sonar.
- **Ambientes:** desarrollo y productivo reproducibles.
- **Scripts de inicialización:** para base de datos y migraciones.
- **Montaje de volúmenes:** para persistencia de archivos y bases de datos.



 

---

## 11. Diagrama de Despliegue


---


## 12. Diagrama Entidad-Relación (ERD) 



## 13. Decisiones arquitectónicas clave (ADR)

- **ADR-001:** Uso de FastAPI por velocidad y OpenAPI.
- **ADR-002:** Procesamiento de videos asíncrono con Celery+RabbitMQ.
- **ADR-003:** Almacenamiento desacoplado para migración futura a S3.
- **ADR-004:** JWT para autenticación.
- **ADR-005:** Caché de ranking con Redis.
- **ADR-006:** Nginx como proxy inverso.

