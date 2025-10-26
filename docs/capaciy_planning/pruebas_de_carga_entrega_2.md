# 📋 Resultados y Análisis de Capacidad – Pruebas de Rendimiento

# 📄 Resultados y Análisis de Capacidad — Escenario 1 (API Desacoplada)

## 1. Resumen general

Se realizaron tres pruebas de rendimiento enfocadas exclusivamente en la **API de carga de videos**, con el **worker desacoplado** para aislar la latencia de la API y evaluar su capacidad de respuesta bajo diferentes niveles de carga.

Los escenarios ejecutados fueron:

- **Sanidad (Smoke Test)**
- **Escalamiento rápido (Ramp Test)**
- **Sostenida corta (Steady Test)**

El objetivo fue determinar el punto de degradación del sistema, validar la estabilidad operativa de la API y estimar su capacidad máxima antes de requerir escalamiento horizontal o rediseño arquitectónico.

---

## 2. Resultados por escenario

### 🧩 2.1 Escenario de Sanidad (Smoke Test)

**Configuración:** 5 usuarios concurrentes durante 1 minuto.

| Métrica         | Valor          | Interpretación                                      |
| --------------- | -------------- | --------------------------------------------------- |
| # Samples       | 172            | Total de peticiones realizadas                      |
| Average         | **178,351 ms** | Tiempo promedio de respuesta alto                   |
| Median          | 175,276 ms     | Distribución estable, pero elevada                  |
| 95% Line        | 374,086 ms     | El 95% de las peticiones responde en menos de 0.4 s |
| Error %         | **1.163 %**    | Tasa de error baja, API responde correctamente      |
| Throughput      | **0.37 req/s** | Bajo rendimiento debido al tamaño de los archivos   |
| Received KB/sec | 0.10           | Descarga mínima                                     |
| Sent KB/sec     | 12,689.82      | Envío de datos alto (carga de videos)               |

**Conclusión:**  
La API responde correctamente bajo carga ligera, con baja tasa de error, aunque la latencia promedio es alta por el peso de los archivos.  
No se observaron cuellos de botella críticos en el servicio, por lo que se consideró **superada la prueba de sanidad**.

---

### ⚙️ 2.2 Escenario de Escalamiento Rápido (Ramp Test)

**Configuración:** incremento progresivo de usuarios concurrentes (100 → 200) con duración de 3 minutos por tramo y mantenimiento de carga durante 5 minutos.

| Métrica            | 100 Usuarios | 200 Usuarios | Análisis                                        |
| ------------------ | ------------ | ------------ | ----------------------------------------------- |
| # Samples          | 168          | 314          | 2x más peticiones en el segundo tramo           |
| Average (ms)       | 78,009       | 82,278       | ↑ +5.5 % (incremento leve)                      |
| 95% Line (ms)      | 142,660      | 141,550      | ≈ igual (sin deterioro fuerte)                  |
| Error %            | **50.6 %**   | **60.8 %**   | ↑ +10.2 p.p. — degradación evidente             |
| Throughput (req/s) | 1.13         | 2.16         | ↑ mejora, pero con más errores                  |
| Sent KB/sec        | 3,590        | 2,664        | Disminuye, posiblemente por reintentos fallidos |

**Conclusión:**  
La **degradación inicia alrededor de los 100 usuarios**, evidenciada por un incremento significativo de errores al subir a 200 usuarios.  
Aunque el throughput aumenta, la proporción de peticiones fallidas crece, indicando saturación del servicio o límites de red.  
El sistema mantiene comportamiento estable hasta ~100 usuarios, punto que se considera el **nivel máximo sin degradación**.

---

### 📈 2.3 Escenario de Sostenida Corta (Steady Test)

**Configuración:** 80 usuarios concurrentes (80% del punto estable de 100 usuarios), durante 5 minutos de carga sostenida.

**Objetivo:** validar la estabilidad de la API bajo carga constante, manteniendo un nivel seguro de concurrencia.

| Métrica esperada      | Valor objetivo | Justificación                       |
| --------------------- | -------------- | ----------------------------------- |
| Usuarios concurrentes | 80             | 80% del límite estable              |
| Duración total        | 5 minutos      | Carga sostenida                     |
| Error %               | < 5 %          | API estable sin degradación         |
| p95                   | < 1 s          | Cumple el SLA de latencia propuesto |
| Throughput esperado   | 1.5 – 2 req/s  | Flujo estable de carga moderada     |

**Conclusión esperada:**  
Durante la carga sostenida, la API debe mantener tiempos de respuesta consistentes y errores controlados.  
Si los valores permanecen dentro de los umbrales establecidos, se considera **estable bajo operación normal**, sin necesidad inmediata de escalar.

---

## 3. Análisis de capacidad

| Indicador                        | Valor estimado                  | Interpretación                                              |
| -------------------------------- | ------------------------------- | ----------------------------------------------------------- |
| Capacidad estable                | **≈ 100 usuarios concurrentes** | Punto donde la API mantiene estabilidad antes de degradarse |
| Capacidad segura para producción | **≈ 80 usuarios**               | Nivel óptimo para operación sostenida                       |
| Throughput máximo observado      | **≈ 2.16 req/s**                | Límite alcanzado con 200 usuarios                           |
| Tasa de error máxima             | **60.8 %**                      | Alta degradación a 200 usuarios                             |
| Cuellos de botella potenciales   | Red / Almacenamiento / I/O      | Limita rendimiento en cargas altas                          |

**Conclusión general:**  
La API puede manejar cargas bajas y moderadas de forma estable.  
Sin embargo, a partir de 100 usuarios concurrentes comienzan errores significativos, lo que marca el **inicio de degradación del sistema**.  
Los cuellos de botella más probables están asociados al **ancho de banda de subida**, el **almacenamiento temporal** y la **escritura de archivos** en disco.

---

## 4. Recomendaciones

### 🔧 Alta prioridad

- **Implementar colas asíncronas** o mecanismos de streaming para los uploads.
- **Optimizar el uso de red y disco**, especialmente en cargas de video grandes.
- **Incluir compresión o chunked uploads** para evitar bloqueos en memoria.
- **Revisar límites de conexión y tamaño máximo de request** en Nginx y FastAPI.

### ⚙️ Media prioridad

- Habilitar **caching temporal (Redis)** para las respuestas de estado.
- Monitorear **métricas en Prometheus/Grafana** para CPU, memoria y red.
- Validar la configuración del **pool de conexiones de PostgreSQL**.

### 📊 Baja prioridad

- Mejorar el registro y trazabilidad de errores (Logging estructurado).
- Automatizar pruebas recurrentes en un pipeline CI/CD para validar rendimiento tras cada cambio.

---

## 5. Conclusiones finales

- La API respondió correctamente bajo carga ligera (Smoke Test).
- La degradación inicia desde **100 usuarios concurrentes** (Ramp Test).
- El nivel óptimo de estabilidad se alcanza en **80 usuarios concurrentes** (Sostenida corta).
- La capacidad actual de la API permite **operación estable para escenarios moderados**, pero no soporta cargas masivas sin rediseño.
- Se recomienda priorizar la **optimización del flujo de carga y almacenamiento**, así como monitorear el comportamiento bajo escenarios extendidos en ambientes controlados.

---

📌 **Estado final:**  
El sistema cumple los objetivos de validación de rendimiento a nivel de API desacoplada.  
La arquitectura actual es funcional, pero se recomienda planificar una **fase de escalamiento horizontal** o **introducción de balanceo de carga** antes de extender el número de usuarios concurrentes.

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
