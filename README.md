# ANB Rising Stars Showcase

Este proyecto es una aplicación web construida con FastAPI para gestionar un showcase de estrellas emergentes.

## Integrantes del Equipo

- Nombre: [Tu Nombre Completo]
- Correo Uniandes: [tu_correo@uniandes.edu.co]

## Configuración de la Base de Datos PostgreSQL

La base de datos PostgreSQL está configurada para ejecutarse en un contenedor Docker.

### Requisitos Previos

- Docker y Docker Compose instalados en tu sistema.

### Configuración

1. Copia el archivo `.env.example` a `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` con tus credenciales deseadas (por defecto: anb_db, anb_user, anb_password, y una SECRET_KEY segura).

### Ejecutar la Aplicación Completa

1. Navega al directorio `docker/`:

   ```bash
   cd docker/
   ```

2. Ejecuta Docker Compose para iniciar todos los servicios (PostgreSQL, FastAPI API, NGINX):

   ```bash
   docker-compose up --build
   ```

   Esto construirá la imagen de la API, creará las tablas en la base de datos, y expondrá la aplicación en `http://localhost:8080`.

### Detener la Aplicación

Para detener los contenedores:

```bash
docker-compose down
```

### Endpoints Disponibles

- **POST /api/auth/signup**: Registro de nuevos usuarios.
- **POST /api/auth/login**: Autenticación y obtención de token JWT.

La API estará disponible en `http://localhost:8080/api/auth/...`.

### Notas

- Las tablas de la base de datos se crean automáticamente al iniciar el contenedor de la API.
- NGINX actúa como proxy reverso en el puerto 8080, redirigiendo a la API en el puerto 8000.
- Los datos de la base se persisten en un volumen Docker llamado `postgres_data`.
- No se han creado tablas adicionales aún; esto se hará en pasos posteriores con migraciones (probablemente usando Alembic).
- Asegúrate de que los puertos 5432, 8000 y 8080 estén disponibles en tu máquina.
