# 📋 Resultados y Análisis de Capacidad – Pruebas de Rendimiento

## 🧪 Escenario 1 – Prueba de Carga y Estrés sobre la API

### 🔍 Descripción General

Este escenario evalúa la capacidad de la API desarrollada en **FastAPI (Python)** frente a múltiples usuarios concurrentes enviando solicitudes de subida y consulta de videos.  
El objetivo es determinar el punto máximo de carga antes de que los tiempos de respuesta o la tasa de error excedan los criterios de aceptación definidos.

---

### 📊 Resultados del Escenario

| Métrica                                   | Valor Observado | Unidad       | Umbral Esperado | Cumple |
| ----------------------------------------- | --------------- | ------------ | --------------- | ------ |
| Usuarios concurrentes máximos sostenibles |                 | usuarios     | ≥ 200           |        |
| Latencia promedio (p50)                   |                 | ms           | ≤ 1000          |        |
| Latencia p95                              |                 | ms           | ≤ 1500          |        |
| Throughput promedio                       |                 | req/s        | ≥ 50            |        |
| % de errores (4xx / 5xx)                  |                 | %            | ≤ 5%            |        |
| Uso CPU promedio API                      |                 | %            | ≤ 90%           |        |
| Uso RAM promedio API                      |                 | %            | ≤ 80%           |        |
| Crecimiento de la cola RabbitMQ           |                 | mensajes/min | Controlado      |        |

> 🧾 **Nota:** completar con los valores obtenidos desde JMeter y métricas del sistema (Prometheus / docker stats).

---

### 🧠 Análisis Detallado de Capacidad

- **Rendimiento general:**  
  _(Describe cómo se comportó la API bajo carga: estabilidad, latencias crecientes, comportamiento de la cola, saturación de CPU, etc.)_

- **Identificación de cuellos de botella:**  
  _(Ejemplo: el tiempo de escritura en el almacenamiento fue el principal limitante o el número de workers concurrentes en Celery no fue suficiente)._

- **Límite de capacidad identificado:**  
  _(Indica cuántos usuarios concurrentes puede manejar la API manteniendo los SLO definidos)._

---

### ✅ Conclusiones Derivadas

- _(Redacta 2 a 3 conclusiones claras sobre el comportamiento del sistema durante las pruebas de estrés: estabilidad, eficiencia, límites de rendimiento, etc.)_

Ejemplo:

> - La API mantuvo una latencia promedio menor a 1 segundo hasta 180 usuarios concurrentes.
> - A partir de 220 usuarios, se observó un aumento progresivo de errores HTTP 500 debido a saturación del worker.
> - La infraestructura actual puede sostener una carga media sin degradación perceptible en los tiempos de respuesta.

---

### 🚀 Recomendaciones para Escalar la Solución

| Área           | Recomendación                                                       | Prioridad |
| -------------- | ------------------------------------------------------------------- | --------- |
| API            | Implementar balanceo de carga (Nginx + múltiples réplicas)          | Alta      |
| Worker         | Incrementar número de instancias Celery o hilos por nodo            | Alta      |
| Base de datos  | Revisar índices en tablas de videos y usuarios                      | Media     |
| Almacenamiento | Mover a servicio externo (S3 o similar) para descargas concurrentes | Media     |
| Observabilidad | Integrar métricas automáticas con Prometheus + Grafana              | Media     |
| Caching        | Aplicar cache Redis para consultas frecuentes                       | Baja      |

---

## 🧪 Escenario 2 – Prueba de Capacidad del Worker (Procesador de Videos)

### 🔍 Descripción General

Este escenario mide la capacidad del **worker (Celery)** para procesar videos de diferentes tamaños bajo distintos niveles de paralelismo, evaluando la eficiencia del procesamiento en segundo plano.

---

### 📊 Resultados del Escenario

| Configuración | Tamaño Video | Paralelismo | Videos Procesados | Tiempo Promedio | Throughput | CPU Worker | RAM Worker |
| ------------- | ------------ | ----------- | ----------------- | --------------- | ---------- | ---------- | ---------- |
| Config 1      | 50 MB        | 1 hilo      |                   |                 |            |            |            |
| Config 2      | 50 MB        | 2 hilos     |                   |                 |            |            |            |
| Config 3      | 100 MB       | 1 hilo      |                   |                 |            |            |            |
| Config 4      | 100 MB       | 4 hilos     |                   |                 |            |            |            |

> 📘 **Sugerencia:** anotar tiempos medidos con Celery logs o métricas personalizadas.

---

### 🧠 Análisis Detallado de Capacidad

- **Desempeño por tamaño de video:**  
  _(Describe el comportamiento observado según el tamaño de los archivos y la cantidad de hilos)._

- **Uso de recursos:**  
  _(Analiza el consumo de CPU y memoria del worker, la velocidad de escritura en disco, y el impacto sobre RabbitMQ y PostgreSQL)._

- **Límite de capacidad:**  
  _(Indica el punto máximo de throughput alcanzado sin crecimiento sostenido de la cola)._

---

### ✅ Conclusiones Derivadas

- _(Resume los hallazgos más relevantes del worker: capacidad de procesamiento, estabilidad, limitantes de hardware, etc.)_

Ejemplo:

> - El worker logró procesar 20 videos/minuto de 50MB con 2 hilos activos.
> - El rendimiento disminuyó con archivos de 100MB debido a limitaciones de I/O.
> - El uso de CPU se mantuvo por debajo del 80% durante toda la ejecución.

---

### 🚀 Recomendaciones para Escalar la Solución

| Área           | Recomendación                                                  | Prioridad |
| -------------- | -------------------------------------------------------------- | --------- |
| Worker         | Aumentar el número de instancias Celery en nodos separados     | Alta      |
| RabbitMQ       | Habilitar colas dedicadas por tipo de tarea                    | Media     |
| Storage        | Incorporar almacenamiento SSD o servicio externo con mayor I/O | Alta      |
| Procesamiento  | Optimizar librerías de manipulación de video (FFmpeg)          | Media     |
| Observabilidad | Monitorear métricas del worker con Celery Flower o Prometheus  | Media     |

---

## 📄 Conclusión General

_(Espacio para un resumen global de ambas pruebas, limitaciones del sistema y próximos pasos para optimización de rendimiento.)_

Ejemplo:

> Las pruebas evidencian que la arquitectura actual soporta adecuadamente la carga esperada del entorno universitario.  
> Sin embargo, se identifican oportunidades de mejora en el procesamiento paralelo y en la infraestructura de almacenamiento.  
> Se recomienda priorizar el escalamiento horizontal del worker y el uso de caché en la API para optimizar tiempos de respuesta.

---

📚 **Autor(es):**  
Grupo 1  
Maestría en Ingeniería de Software – Universidad de los Andes
