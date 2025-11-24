# ANB Rising Stars Showcase

Este proyecto es una aplicación web escalable para la gestión de archivos y procesamiento asíncrono de tareas, orientada al showcase de estrellas emergentes de la ANB (Asociación Nacional de Baloncesto). Construida con FastAPI, PostgreSQL, Docker y más tecnologías para garantizar escalabilidad, seguridad y portabilidad.

## Integrantes del Equipo

| Nombre                              | Email Uniandes               | Usuario GitHub    |
| ----------------------------------- | ---------------------------- | ----------------- |
| Leonel Alexander Parrales Machuca   | l.parrales@uniandes.edu.co   | leonelparrales22  |
| Maycol Steven Avendaño Niño         | m.avendanon@uniandes.edu.co  | maycolan          |
| Cristhian Sneider Contreras Barrera | c.contrerasb@uniandes.edu.co | criscont17        |
| Danny Zamorano Vallejo              | d.zmorano@uniandes.edu.co    | dzamoranouniandes |

## Descripción del Proyecto

La plataforma permite a jugadores aficionados registrarse, subir videos de habilidades, procesarlos de manera asíncrona (recorte a 30s, ajuste a 720p 16:9, cortinillas ANB), y recibir votaciones públicas para generar rankings. Incluye autenticación JWT, gestión de archivos, procesamiento asíncrono con Celery, y orquestación con Docker.

### Tecnologías Principales

- **Backend**: FastAPI (Python)
- **Base de Datos**: PostgreSQL
- **Autenticación**: JWT
- **Procesamiento Asíncrono**: Celery + RabbitMQ
- **Procesamiento de Video**: FFmpeg
- **Almacenamiento**: AWS S3 (configurable) / Sistema de archivos local
- **Proxy Reverso**: NGINX (se elimina en entrega 3 por adición de ALB)
- **Contenedorización**: Docker + Docker Compose
- **Almacenamiento**: Sistema de archivos local (preparado para S3)
- **Logging**: Estructurado con video_id y task_id

## Requisitos Previos

- Docker y Docker Compose instalados.
- Git para clonar el repositorio.
- Postman / Newman para pruebas de API.

## Instalación y Ejecución

### 1. Clonar el Repositorio

```bash
git clone https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase.git
cd ANB-Rising-Stars-Showcase
```

### 3. Configurar Variables de Entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Edita `.env` con tus valores (ej. credenciales de DB, SECRET_KEY).

#### Configuración de Almacenamiento AWS S3

Si deseas usar AWS S3 en lugar de almacenamiento local, configura estas variables en tu `.env`:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=tu-access-key-id
AWS_SECRET_ACCESS_KEY=tu-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET=nombre-de-tu-bucket-s3
```

**Nota**: Si no configuras las variables de AWS, el sistema usará almacenamiento local por defecto.

#### Creación de Bucket S3

1. Ve a la consola de AWS S3
2. Crea un nuevo bucket con el nombre especificado en `S3_BUCKET`
3. Configura las políticas de IAM para permitir acceso de lectura/escritura
4. Asegúrate de que el bucket permita acceso público para los videos procesados

### 3. Ejecutar la Aplicación

Navega al directorio `docker/` y ejecuta:

```bash
cd docker/
docker-compose up --build
```

Esto iniciará:

- PostgreSQL en puerto 5433.
- FastAPI API en puerto 8000 (interno).
- Celery Worker para procesamiento asíncrono.
- RabbitMQ en puerto 5672 (AMQP) y 15672 (Management UI).
- Redis en puerto 6379.
- NGINX proxy en puerto 8080 (accede vía `http://localhost:8080`).

La API estará disponible en `http://localhost:8080/api/...`.

### 4. Detener la Aplicación

```bash
docker-compose down
```

Para limpiar volúmenes (datos de DB):

```bash
docker-compose down -v
```

## Endpoints Disponibles

### Autenticación

- **POST /api/auth/signup**: Registro de nuevos jugadores (201 on success).
- **POST /api/auth/login**: Autenticación y obtención de token JWT (200 on success).

### Gestión de Videos
- **POST /api/videos/upload**: Subir video MP4 (máx 100MB, requiere auth, inicia procesamiento asíncrono).
- **GET /api/videos/**: Lista videos del usuario autenticado.
- **GET /api/videos/{video_id}**: Detalle de un video específico.
- **DELETE /api/videos/{video_id}**: Eliminar video propio (solo si no tiene votos y no está procesado).

### Público
- **GET /api/public/videos**: Lista videos públicos para votación.
- **POST /api/public/videos/{video_id}/vote**: Votar por un video (requiere auth).
- **GET /api/public/rankings**: Ranking de jugadores por votos.

### Procesamiento de Videos
Los videos subidos se procesan automáticamente:
1. **Recorte**: Máximo 30 segundos
2. **Redimensionado**: 720p con relación 16:9
3. **Cortinillas**: Agregado de apertura y cierre ANB (5s cada una)

Documentación completa en OpenAPI: `http://localhost:8080/docs` (cuando esté corriendo).

## Pruebas

### Pruebas Unitarias

Las pruebas unitarias están ubicadas en la carpeta `tests/`. Para ejecutarlas:

1. **Activa el entorno virtual** (si no está activado):

   ```bash
   venv\Scripts\activate  # En Windows
   # source venv/bin/activate  # En Linux/Mac
   ```

2. **Instala dependencias de desarrollo** (si no están instaladas):

   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta todas las pruebas en la carpeta `tests/`**:

   ```bash
   pytest tests/
   ```

4. **Ejecuta un archivo específico** (ej. `test_auth.py`):

   ```bash
   pytest tests/test_auth.py
   ```

5. **Ejecuta con más detalle** (verbose):

   ```bash
   pytest tests/ -v
   ```

Las pruebas incluyen validaciones para endpoints, manejo de errores, y base de datos de prueba (SQLite temporal).

### Con Postman

1. Importa la colección: `collections/postman_collection.json`.
2. Selecciona el entorno: `collections/postman_environment.json`.
3. Ejecuta los requests en orden (signup → login para token → otros).

### Con Newman (CLI)

```bash
npm install -g newman
newman run collections/postman_collection.json -e collections/postman_environment.json
```

## Documentación

La documentación de la `Entrega No. 1` se encuentra en `docs/Entrega_1/`:

- [Diagrama de Componentes](docs/Entrega_1/diagrama-componentes.png)
- [Diagrama de Contenedores](docs/Entrega_1/diagrama-contenedores.png)
- [Diagrama de Contexto](docs/Entrega_1/diagrama-contexto.png)
- [Diagrama de Despliegue](docs/Entrega_1/diagrama-despliegue.png)
- [Diagrama Modelo de Datos](docs/Entrega_1/diagrama-modelo-datos.png)
- [Diagrama de Secuencia (Video)](docs/Entrega_1/diagrama-secuencia-video.md)
- [Link Presentación Vídeo](docs/Entrega_1/link-video-presentacion-e1.txt)

La documentación de la `Entrega No. 2` se encuentra en `docs/Entrega2/`:

- [Diagrama de Componentes](docs/Entrega2/diagrama-componentes.png)
- [Diagrama de Contenedores](docs/Entrega2/diagrama-containers.png)
- [Diagrama de Contexto](docs/Entrega2/diagrama-contexto.png)
- [Diagrama de Despliegue](docs/Entrega2/diagrama-despliegue.png)
- [Diagrama Modelo de Datos](docs/Entrega2/diagrama-modelo-datos.png)
- [Diagrama de Secuencia (Video)](docs/Entrega2/diagrama-secuencia-video.md)
- [Link Presentación Vídeo](docs/Entrega2/link-video-presentacion-e2.txt)

La documentación de la `Entrega No. 3` se encuentra en `docs/Entrega3/`:

- [Diagrama de Contexto](docs/Entrega3/diagrama-contexto.png)
- [Diagrama de Contenedores](docs/Entrega3/diagrama-containers.png)
- [Diagrama de Componentes](docs/Entrega3/diagrama-componentes.png)
- [Diagrama de Despliegue](docs/Entrega3/diagrama-despliegue.png)
- [Diagrama Modelo de Datos](docs/Entrega3/diagrama-modelo-datos.png)
- [Link Presentación Vídeo](docs/Entrega3/link-video-presentacion-e3.txt)

La documentación de la `Entrega No. 4` se encuentra en `docs/Entrega4/`:

- [Diagrama de Contexto](docs/Entrega4/diagrama-contexto.png)
- [Diagrama de Contenedores](docs/Entrega4/diagrama-containers.png)
- [Diagrama de Componentes](docs/Entrega4/diagrama-componentes.png)
- [Diagrama de Despliegue](docs/Entrega4/diagrama-despliegue.png)
- [Diagrama Modelo de Datos](docs/Entrega4/diagrama-modelo-datos.png)
- [Link Presentación Vídeo](docs/Entrega4/link-video-presentacion-e4.txt)

La documentación de la `Entrega No. 5` se encuentra en `docs/Entrega4/`:

- [Diagrama de Contexto](docs/Entrega5/diagrama-contexto.png)
- [Diagrama de Contenedores](docs/Entrega5/diagrama-containers.png)
- [Diagrama de Componentes](docs/Entrega5/diagrama-componentes.png)
- [Diagrama de Despliegue](docs/Entrega5/diagrama-despliegue-uml.png)
- [Diagrama de Despliegue](docs/Entrega5/diagrama-despliegue-aws.png)
- [Diagrama Modelo de Datos](docs/Entrega5/diagrama-modelo-datos.png)
- [Link Presentación Vídeo](docs/Entrega5/link-video-presentacion-e5.txt)

## Sustentación

- [Entrega 1 - Video Sustentación](https://drive.google.com/file/d/1E2BxHXR1p46LTX_4j90l8fgzrZB_dvYb/view?usp=sharing)
- [Entrega 2 - Video Sustentación](https://drive.google.com/file/d/1jyYzLLIPqsP13tP_F5D7CVUCnVsHxLog/view?usp=sharing)
- [Entrega 3 - Video Sustentación](https://drive.google.com/file/d/17o1-KM7doMRGQbl_oAi5ZGCfvuDYhiTz/view?usp=sharing)
- [Entrega 4 - Video Sustentación](https://drive.google.com/file/d/16JZMyQETrGPFgkvm0t55kiglaQxp-XlX/view?usp=sharing)
- [Entrega 5 - Video Sustentación](https://drive.google.com/file/d/17sVqXiw90gBJ8xU9FBz0KxtGPAWYipTv/view?usp=sharing)

## Plan de Pruebas de Capacidad

- [Plan de Pruebas](docs/capaciy_planning/plan_de_pruebas.md)
- [Resultados Pruebas de Carga - Entrega 2](docs/capaciy_planning/pruebas_de_carga_entrega_2.md)
- [Resultados Pruebas de Carga - Entrega 3](docs/capaciy_planning/pruebas_de_carga_entrega_3.md)
- [Resultados Pruebas de Carga - Entrega 4](docs/capaciy_planning/pruebas_de_carga_entrega_4.md)
- [Resultados Pruebas de Carga - Entrega 5](docs/capaciy_planning/pruebas_de_carga_entrega_5.md)

## Releases

- **v1.0.0**: Primera entrega con auth endpoints y Docker setup. [Ver release](https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase/releases/tag/v1.0.0)
- **v2.0.0**: Segunda entrega con despliegue en AWS y pruebas de carga. [Ver release](https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase/releases/tag/v2.0.0)
- **v3.0.0**: Tercera entrega con despliegue en AWS y pruebas de carga. [Ver release](https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase/releases/tag/v3.0.0)
- **v4.0.0**: Cuarta entrega con despliegue en AWS y pruebas de carga. [Ver release](https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase/releases/tag/v4.0.0)
- **v5.0.0**: Quinta entrega con despliegue en AWS y pruebas de carga. [Ver release](https://github.com/leonelparrales22/ANB-Rising-Stars-Showcase/releases/tag/v5.0.0)

## Arquitectura del Sistema

### Estructura de Microservicios
```
ANB-Rising-Stars-Showcase/
├── app/                    # FastAPI (API REST)
├── app-worker/             # Celery Workers (Procesamiento)
├── docker/                 # Configuración Docker Compose
├── shared/                 # Configuración general para API, Base de Datos y Workers
├── uploads/                # Videos originales y procesados
└── assets/                 # Cortinillas ANB
```

### Flujo de Procesamiento
1. **Upload**: Usuario sube video → API guarda archivo → Estado: `UPLOADED`
2. **Encolar**: API envía tarea a cola `uploaded-videos` → Estado: `PROCESSING`
3. **Procesar**: Worker ejecuta tareas de video → Estado: `PROCESSED` o `FAILED`
4. **Resultado**: Video procesado disponible para votación

### Almacenamiento
- **Videos Originales**: `uploads/{video_id}.mp4`
- **Videos Procesados**: `uploads/processed_{video_id}.mp4`
- **Cortinillas**: `assets/anb_intro_5s.mp4`, `assets/anb_outro_5s.mp4`

## Notas Adicionales

- Las tablas se crean automáticamente al iniciar la API.
- Volúmenes Docker persisten datos de DB y archivos.
- Para desarrollo local, usa `docker-compose up` sin `--build` después del primer build.
- Asegúrate de que los puertos 5433, 8000, 8080, 5672, 15672, 6379 estén libres.
- RabbitMQ Management UI disponible en `http://localhost:15672` (admin/admin).
- Los videos se procesan automáticamente en segundo plano.
- Los componetes API y Worker se pueden desacoplar utilizando una variable de entorno.

## Contribución

1. Crea una rama feature desde `main`.
2. Implementa cambios.
3. Ejecuta pruebas y valida con Postman.
4. Crea PR con descripción detallada de la rama feature a  `develop`.
5. Crea PR con descripción detallada de la rama `develop` a `main`.

