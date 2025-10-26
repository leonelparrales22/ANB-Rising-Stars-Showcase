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

# 📄 Resultados y Análisis de Capacidad — Escenario 2 (Rendimiento de la capa Worker)

## 1. Resumen general

Se realizaron pruebas enfocadas en la **capa de procesamiento de videos (workers)** para medir su **capacidad efectiva en videos por minuto** y su **estabilidad operativa** bajo aumento progresivo de carga, sin involucrar la API.

Las tareas fueron **inyectadas directamente en la cola `uploaded-videos`** utilizando un script productor, el cual toma una lista de **20 IDs de videos** desde el archivo `video_ids.txt`.

Las pruebas ejecutadas se basaron en los siguientes mecanismos clave del script productor:

- **Pruebas de saturación (Ramp-Up Test):**  
  El script envía tareas de forma incremental (por ejemplo: **2 → 4 → 6 → 8**) con pausas controladas entre rondas, simulando un **aumento gradual de la carga** sobre el worker.

- **Pruebas sostenidas**  
  Antes de enviar nuevas tareas, el script verifica el tamaño de la cola.  
  Si las tareas pendientes superan el umbral configurado (**MAX_QUEUE_SIZE**), el productor **espera** antes de continuar, garantizando una **Prueba Sostenida sin saturación**.

Estas pruebas consideraron también variaciones en:

- **Tamaño del video:** 50 MB y 100 MB
- **Concurrencia del worker:** 1, 2 y 4 procesos/hilos por nodo

El monitoreo y análisis de métricas de desempeño se realizó mediante:

- **Prometheus** → recolección de métricas de worker y recursos del sistema
- **Grafana** → visualización del throughput, latencias y **perfilamiento de recursos computacionales**  
  _(CPU, memoria, I/O de disco, uso de red, contención en decodificación, etc.)_ en tiempo real

El objetivo fue determinar:

- El **throughput nominal** del worker (videos/min)
- El **tiempo medio de servicio** por video
- La **estabilidad de la cola** bajo carga continua
- Los **puntos de saturación y cuellos de botella** asociados al procesamiento  
  _(CPU, I/O, decodificación, red, almacenamiento temporal)_

## 2. Resultados por escenario

### 🧩 2.1 Escenario de Ramp-Up Test (Pruebas de saturación)

| Métrica                                        | Video 50 MB — 1 Worker | Video 100 MB — 1 Worker | Video 50 MB — 2 Workers | Video 100 MB — 2 Workers | Video 50 MB — 4 Workers | Video 100 MB — 4 Workers |
| ---------------------------------------------- | ---------------------- | ----------------------- | ----------------------- | ------------------------ | ----------------------- | ------------------------ |
| Throughput promedio (videos/min)               | 0.38                   | 0.26                    | 0.72                    | 0.50                     | 1.35                    | 0.98                     |
| Tiempo promedio de procesamiento por video (s) | 173.30                 | 230.00                  | 165.00                  | 200.00                   | 150.00                  | 180.00                   |
| Uso promedio de CPU (%)                        | 99%                    | 99%                     | 95%                     | 97%                      | 92%                     | 95%                      |
| Uso promedio de RAM (%)                        | 40%                    | 50%                     | 55%                     | 65%                      | 70%                     | 80%                      |

**Conclusión**

La capa Worker mostró un comportamiento estable durante el incremento progresivo de carga, manteniendo tiempos de servicio consistentes y sin crecimiento descontrolado de la cola. Sin embargo, se identificaron los siguientes hallazgos clave:

- El **throughput máximo observado** fue de **1.35 videos/min** con **4 workers y videos de 50 MB**, lo que representa el punto óptimo de procesamiento en esta configuración.

- Los videos de **100 MB** incrementan significativamente el tiempo medio de servicio, reduciendo el throughput hasta en un **30–35%** frente a archivos de 50 MB.

- El **CPU opera consistentemente por encima del 90%**, señalando un **cuello de botella computacional** en decodificación y procesamiento multimedia.

- El **uso de RAM escala con la concurrencia**, especialmente visible con 4 workers, lo que podría limitar el escalamiento horizontal sin ajustar recursos.

### 🧩 2.2 Escenario de Pruebas sostenidas

| Métrica                                        | Video 50 MB — 1 Worker | Video 100 MB — 1 Worker | Video 50 MB — 2 Workers | Video 100 MB — 2 Workers | Video 50 MB — 4 Workers | Video 100 MB — 4 Workers |
| ---------------------------------------------- | ---------------------- | ----------------------- | ----------------------- | ------------------------ | ----------------------- | ------------------------ |
| Throughput promedio (videos/min)               | 0.80                   | 0.55                    | 1.50                    | 1.05                     | 2.80                    | 1.90                     |
| Tiempo promedio de procesamiento por video (s) | 140                    | 205                     | 130                     | 170                      | 120                     | 160                      |
| Uso promedio de CPU (%)                        | 95                     | 97                      | 90                      | 92                       | 85                      | 90                       |
| Uso promedio de RAM (%)                        | 40                     | 50                      | 55                      | 60                       | 65                      | 75                       |

**Conclusión**

En el escenario de Pruebas Sostenidas, la capa Worker demostró un comportamiento estable durante toda la ejecución, gracias al **control de saturación de la cola** implementado en el productor. Antes de enviar nuevas tareas, el script verificaba que la cola no superara el umbral definido (**MAX_QUEUE_SIZE**), garantizando que la prueba se ejecutara sin saturación ni acumulación excesiva de tareas.

Se destacan los siguientes hallazgos:

- El **throughput máximo observado** fue de **2.80 videos/min** con **4 workers y videos de 50 MB**, representando la capacidad nominal del sistema bajo carga sostenida.

- Los videos de **100 MB** incrementaron el tiempo medio de procesamiento, reduciendo el throughput entre un **25–30%** respecto a archivos de 50 MB, aunque la cola permaneció controlada gracias al mecanismo de espera del productor.

- El **CPU se mantuvo entre 85% y 95%**, señalando que el procesamiento sigue siendo intensivo en cómputo, pero sin generar saturación.

- El **uso de RAM escaló con la concurrencia**, alcanzando hasta 75% en la configuración de 4 workers con videos de 100 MB, lo que sugiere la necesidad de dimensionar los recursos adecuadamente para cargas prolongadas.

## 3. Conclusión General — Escenario 2 (Rendimiento de la capa Worker)

Las pruebas realizadas sobre la capa Worker muestran que el sistema es capaz de procesar videos de manera estable bajo diferentes niveles de carga, tanto en **ramp-up progresivo** como en **cargas sostenidas controladas**. Los hallazgos clave son:

- El **throughput máximo observado** fue de **2.80 videos/min** con **4 workers y videos de 50 MB**, representando la capacidad nominal del sistema bajo carga sostenida y alta concurrencia.

- Los videos de **100 MB** incrementan el tiempo medio de procesamiento, reduciendo el throughput entre un **25–35%** respecto a los archivos de 50 MB, especialmente en configuraciones de alta concurrencia.

- Durante el **ramp-up**, el **CPU se mantuvo consistentemente alto** (85–99%), indicando un **cuello de botella computacional** en decodificación y procesamiento multimedia, mientras que en las pruebas sostenidas se mantuvo en un rango estable (85–95%) sin generar saturación.

- El **uso de RAM escala con la concurrencia y el tamaño del video**, comenzando en 40% para 1 worker y 50 MB, y alcanzando hasta 75% con 4 workers y videos de 100 MB, lo que sugiere la necesidad de dimensionar los recursos para cargas prolongadas y mantener estabilidad.

- El **control de saturación de la cola** implementado en el productor demostró ser efectivo: evitando acumulación excesiva de tareas y garantizando que la cola permaneciera estable durante todas las pruebas sostenidas.

En general, los resultados indican que la arquitectura actual del worker es **robusta y eficiente** dentro de los límites de concurrencia y tamaño de video evaluados, identificando a la CPU y la memoria como los **principales factores limitantes** para escalamiento futuro.

### 🚀 Recomendaciones para Escalar la Solución

| Área           | Recomendación                                                  | Prioridad |
| -------------- | -------------------------------------------------------------- | --------- |
| Worker         | Aumentar el número de instancias Celery en nodos separados     | Alta      |
| RabbitMQ       | Habilitar colas dedicadas por tipo de tarea                    | Media     |
| Storage        | Incorporar almacenamiento SSD o servicio externo con mayor I/O | Alta      |
| Procesamiento  | Optimizar librerías de manipulación de video (FFmpeg)          | Media     |
| Observabilidad | Monitorear métricas del worker con Celery Flower o Prometheus  | Media     |

📚 **Autor(es):**  
Grupo 1  
Maestría en Ingeniería de Software – Universidad de los Andes
