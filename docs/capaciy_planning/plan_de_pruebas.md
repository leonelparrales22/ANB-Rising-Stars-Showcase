# 📊 Análisis de Capacidad – Pruebas de Rendimiento

## 🎯 Objetivo General

Evaluar la capacidad máxima que pueden soportar los principales componentes del sistema (API y Worker) bajo diferentes niveles de carga, identificando los límites de rendimiento y posibles cuellos de botella.

---

## 🎯 Objetivos Específicos

- Determinar el número máximo de usuarios concurrentes que puede manejar la API de subida de videos cumpliendo con los SLO definidos.
- Medir el rendimiento del procesador de videos (worker) en términos de videos procesados por minuto a distintos niveles de concurrencia.
- Identificar los recursos limitantes (CPU, memoria, ancho de banda, disco o red) bajo condiciones de alta demanda.
- Validar la estabilidad del sistema ante cargas sostenidas y escenarios de estrés.

---

## 🧩 Descripción General del Sistema

La aplicación está compuesta por los siguientes componentes desplegados en contenedores Docker:

| Componente       | Tecnología                                | Función Principal                                          |
| ---------------- | ----------------------------------------- | ---------------------------------------------------------- |
| API Backend      | **FastAPI (Python)**                      | Gestión de peticiones HTTP y subida de videos.             |
| Cola de Mensajes | **RabbitMQ**                              | Encolamiento de tareas para procesamiento asíncrono.       |
| Worker           | **Celery (Python)**                       | Procesamiento de videos en segundo plano.                  |
| Base de Datos    | **PostgreSQL**                            | Almacenamiento de datos de usuarios y metadatos de videos. |
| Storage          | **Sistema de archivos local** (futuro S3) | Almacenamiento de los videos originales y procesados.      |

---

## 🧪 Tipos de Pruebas a Realizar

### **Escenario 1 – Capacidad de la capa Web (API)**

Medir el número máximo de usuarios concurrentes que pueden subir videos cumpliendo con los SLOs:

- **p95 de latencia ≤ 1 segundo**
- **Errores ≤ 5%**

**Pruebas incluidas:**

- **Smoke Test:** Validar estabilidad inicial (5 usuarios / 1 minuto).
- **Ramp Test:** Escalar de 0 a X usuarios (100 → 200 → 300...) hasta detectar degradación.
- **Sostenida:** Carga estable al 80% del límite máximo encontrado.

### **Escenario 2 – Rendimiento del Worker (procesamiento de videos)**

Evaluar la capacidad del worker midiendo el throughput (videos/minuto) según:

- Tamaño de video: **50 MB y 100 MB**
- Paralelismo: **1, 2 y 4 hilos de ejecución**

---

## ✅ Criterios de Aceptación

| Métrica                | Criterio                                    |
| ---------------------- | ------------------------------------------- |
| p95 Latencia (API)     | ≤ 1 segundo                                 |
| Errores 4xx/5xx        | ≤ 5%                                        |
| Estabilidad del worker | La cola no debe crecer sin control          |
| CPU del API            | < 90% durante carga sostenida               |
| Procesamiento          | Al menos 15 videos/min con 100 MB por video |
| Sin fallos críticos    | Sin timeouts o caídas del sistema           |

---

## 🧾 Datos de Prueba

- Videos de prueba en formato **MP4** con duración entre **20 y 60 segundos**.
- Tamaños simulados: **50 MB y 100 MB**.
- Usuarios simulados: **hasta 300 concurrentes**.
- Requests enviados a los endpoints principales de subida y consulta de videos.

---

## 🔁 Iteraciones

| Iteración | Tipo        | Descripción                                    | Duración  |
| --------- | ----------- | ---------------------------------------------- | --------- |
| 1         | Smoke Test  | Validar funcionamiento básico                  | 1 minuto  |
| 2         | Ramp Up     | Escalamiento progresivo de usuarios (100→300)  | 8 minutos |
| 3         | Sostenida   | Carga estable al 80% del umbral máximo         | 5 minutos |
| 4         | Worker Load | Procesamiento de 50MB y 100MB a 1, 2 y 4 hilos | Variable  |

---

## ⚙️ Configuración del Sistema

| Componente         | Configuración               |
| ------------------ | --------------------------- |
| Sistema operativo  | Ubuntu Server 24.04 LTS     |
| API                | FastAPI (Python 3.11)       |
| Worker             | Celery con RabbitMQ         |
| Base de datos      | PostgreSQL 15               |
| Proxy inverso      | Nginx                       |
| Generador de carga | Apache JMeter               |
| Hardware estimado  | 4 vCPU, 8 GB RAM            |
| Red                | 100 Mbps mínimo             |

---

## 🧰 Herramientas para la Prueba

| Herramienta                   | Uso                                                     |
| ----------------------------- | ------------------------------------------------------- |
| **Apache JMeter**             | Generador de carga y simulador de usuarios concurrentes |
| **htop / docker stats**       | Monitoreo en tiempo real de consumo CPU/Memoria         |
| **Python + Celery Inspector** | Trazabilidad y estado de tareas en cola                 |

---

## 📈 Métricas a Recolectar

| Tipo              | Métrica                         | Unidad              |
| ----------------- | ------------------------------- | ------------------- |
| **Rendimiento**   | Requests por segundo (RPS)      | req/s               |
| **Latencia**      | Promedio y p95                  | milisegundos        |
| **Errores**       | % de respuestas 4xx / 5xx       | porcentaje          |
| **Procesamiento** | Videos/minuto (Worker)          | videos/min          |
| **Recurso**       | CPU, RAM, ancho de banda        | % / MB              |
| **Estabilidad**   | Crecimiento de la cola RabbitMQ | mensajes pendientes |

---

## ⚠️ Riesgos Identificados

| Riesgo                              | Impacto | Mitigación                                            |
| ----------------------------------- | ------- | ----------------------------------------------------- |
| Saturación de CPU en API            | Alta    | Monitorear con Grafana y escalar verticalmente        |
| Cuello de botella en almacenamiento | Medio   | Usar disco SSD local y limitar concurrencia de subida |
| Sobrecarga del worker               | Alta    | Incrementar hilos o nodos Celery                      |
| Errores de timeout o latencia alta  | Alta    | Aplicar caching o balanceo con Nginx                  |
| Fallo en conexión RabbitMQ          | Medio   | Implementar reintentos automáticos                    |
| Datos de prueba insuficientes       | Bajo    | Generar dataset controlado de videos simulados        |

---

## 📄 Conclusión (previa)

Este análisis de capacidad permitirá identificar la cantidad máxima de usuarios concurrentes que la API puede soportar manteniendo tiempos de respuesta aceptables, así como la capacidad de procesamiento del worker para videos de diferentes tamaños. Los resultados servirán para establecer una línea base de rendimiento y detectar los principales cuellos de botella del sistema.

---

📚 **Autor(es):**  
Grupo 1
Maestría en Ingeniería de Software – Universidad de los Andes
