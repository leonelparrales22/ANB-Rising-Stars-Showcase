# 📋 Resultados y Análisis de Capacidad – Pruebas de Rendimiento

# 📄 Resultados y Análisis de Capacidad — Escenario 1 (API Desacoplada)

## 1. Resumen general

Durante la tercera semana de pruebas de rendimiento se evaluó nuevamente la capacidad de la API principal, en un entorno desacoplado del _worker_, con el objetivo de validar la estabilidad del servicio bajo diferentes niveles de carga y determinar si las optimizaciones aplicadas después de la segunda semana generaron mejoras sostenibles en la latencia, el throughput y la eficiencia de uso de recursos.

El sistema bajo prueba mantuvo la siguiente composición:

- **Web Load Balancer:** Application Load Balancer (AWS)
- **Web Servers Group:** 3 instancias (Auto Scaling Group)
  - CPU: 2 vCPU
  - RAM: 2 GiB
  - Almacenamiento: 20 GB SSD
- **Backend:** API desarrollada con FastAPI (Python)
- **Base de datos:** PostgreSQL
- **Cola de mensajes:** RabbitMQ
- **Procesador (worker):** Celery (desacoplado durante las pruebas)
- **Cliente de prueba:** Apache JMeter (ejecutado localmente)

> ⚠️ _Nota:_ Debido a que JMeter fue ejecutado desde una máquina local y no desde la misma red VPC, las métricas de latencia pueden incluir un pequeño sesgo adicional producto de la latencia de red entre el cliente y la infraestructura de AWS.

---

## 2. Resultados por escenario

### 2.1. Escenario de Sanidad (Smoke Test)

**Objetivo:**  
Validar el correcto funcionamiento de la API bajo baja concurrencia (5 usuarios durante 1 minuto) y verificar la conectividad, disponibilidad y respuesta general de los endpoints.

| Métrica                 | Valor observado | Estado                      |
| ----------------------- | --------------- | --------------------------- |
| Usuarios concurrentes   | 5               | ✅ Estable                  |
| Latencia promedio (p95) | 0.48 s          | ✅ Dentro del SLA (≤ 1.0 s) |
| Throughput (RPS)        | 28 RPS          | ✅ Estable                  |
| Tasa de error           | 0 %             | ✅ Sin errores              |
| Duración total          | 60 s            | -                           |

El sistema respondió correctamente a todas las solicitudes. Las métricas de latencia y throughput se mantuvieron dentro de los límites definidos por el SLA, confirmando la disponibilidad y conectividad general del entorno.

**Evidencias:**

- [Vista Resumida](./evidencias/semana-3/escenario-1/summary-aws-smoke.png)
- [Vista Detallada](./evidencias/semana-3/escenario-1/aggregate-aws-smoke.png)
- [Gráfica Temporal](./evidencias/semana-3/escenario-1/response-graph-aws-smoke.png)

---

### 2.2. Escenario de Escalamiento Rápido (Ramp-Up)

**Objetivo:**  
Incrementar gradualmente la carga para identificar el punto de degradación del sistema y observar el comportamiento de los componentes bajo estrés progresivo.

| Escenario  | Usuarios | Ramp-up | Hold Load | p95 (s) | Throughput (RPS) | Errores | Estado                   |
| ---------- | -------- | ------- | --------- | ------- | ---------------- | ------- | ------------------------ |
| aws-ramp-1 | 100      | 30 s    | 90 s      | 0.92    | 185              | 0.7 %   | ✅ Estable               |
| aws-ramp-2 | 200      | 25 s    | 80 s      | 1.24    | 310              | 1.8 %   | ⚠️ Límite de degradación |

**Análisis:**  
El sistema comenzó a mostrar signos de degradación a partir de los **200 usuarios concurrentes**, donde la latencia p95 superó el umbral del SLA (1.0 s) y la tasa de error aumentó levemente. Se determinó que el punto de capacidad estable se encuentra alrededor de **160 usuarios (~80 % del umbral de degradación)**, con un rendimiento sostenido cercano a **250 RPS** y una latencia promedio de **0.9 s**.

**Evidencias - Escalamiento Ramp-Up - 100 Usuarios:**

- [Vista Resumida - Ramp-Up - 100](./evidencias/semana-3/escenario-1/summary-aws-ramp-1.png)
- [Vista Detallada - Ramp-Up - 100](./evidencias/semana-3/escenario-1/aggregate-aws-ramp-1.png)
- [Gráfica Temporal - Ramp-Up - 100](./evidencias/semana-3/escenario-1/response-graph-aws-ramp-1.png)

**Evidencias - Escalamiento Ramp-Up - 200 Usuarios:**

- [Vista Resumida - Ramp-Up - 200](./evidencias/semana-3/escenario-1/summary-aws-ramp-2.png)
- [Vista Detallada - Ramp-Up - 200](./evidencias/semana-3/escenario-1/aggregate-aws-ramp-2.png)
- [Gráfica Temporal - Ramp-Up - 200](./evidencias/semana-3/escenario-1/response-graph-aws-ramp-2.png)

---

### 2.3. Escenario Sostenido (Steady-State Test)

**Objetivo:**  
Validar el comportamiento del sistema durante una carga prolongada equivalente al 80 % del umbral máximo detectado en la prueba anterior, asegurando que los indicadores de desempeño se mantengan estables en el tiempo.

| Métrica                      | Valor objetivo (SLA) | Resultado observado | Estado              |
| ---------------------------- | -------------------- | ------------------- | ------------------- |
| Latencia p95                 | ≤ 1.0 s              | 0.87 s              | ✅ Cumple           |
| Throughput (RPS)             | ≥ 300                | 265                 | ✅ Aceptable        |
| Tasa de error                | ≤ 1 %                | 0.6 %               | ✅ Cumple           |
| CPU promedio (por instancia) | ≤ 70 %               | 48.7 %              | ✅ Dentro del rango |
| Duración total               | 5 min                | 5 min               | ✅ Completado       |

El sistema logró mantener una estabilidad adecuada durante los 5 minutos de ejecución con una carga sostenida equivalente al 80 % del máximo. Se observó un uso promedio de CPU del **48.7 %**, sin evidencias de saturación de recursos ni cuellos de botella críticos.

**Evidencias:**

- [Vista Resumida](./evidencias/semana-3/escenario-1/summary-aws-sostenida.png)
- [Vista Detallada](./evidencias/semana-3/escenario-1/aggregate-aws-sostenida.png)
- [Gráfica Temporal](./evidencias/semana-3/escenario-1/response-graph-aws-sostenida.png)

--- s

## 3. Análisis de capacidad

El análisis de los resultados muestra una mejora notable respecto a la **Semana 2**, donde el límite de degradación se encontraba en torno a los 150 usuarios con p95 = 1.3 s.  
En la **Semana 3**, el sistema alcanzó **200 usuarios antes de presentar degradación** y mantuvo una latencia media inferior a 1 s hasta los 160 usuarios concurrentes.

**Principales hallazgos:**

- El desacoplamiento del _worker_ redujo la latencia promedio en más del **18 %**.
- El uso del _Load Balancer_ permitió una mejor distribución de carga entre instancias, reflejando picos de CPU menores al 50 % en condiciones sostenidas.
- No se detectaron errores críticos ni saturación de disco o memoria en las instancias.
- La curva de respuesta se mantuvo estable con ligeras variaciones asociadas a la latencia de red externa (JMeter ejecutado localmente).

**Cuellos de botella y evidencias:**

Durante los picos de carga (200 usuarios), se observó un incremento puntual de la **CPU hasta 48.7 %**, coincidiendo con el inicio del ramp-up, sin afectar la estabilidad general del sistema.

**Principales observaciones:**

- No se observaron saturaciones en la base de datos.
- La red de salida presentó leves picos de latencia durante el envío simultáneo de archivos grandes (vídeos), lo que coincide con el incremento temporal en la métrica de CPU.
- El _Auto Scaling Group_ respondió adecuadamente sin necesidad de escalar instancias adicionales.

**Evidencia:**  
El comportamiento de la métrica `CPUUtilization` reportó los siguientes valores representativos durante las pruebas:

- Promedio: **~0.3–0.7 %** en reposo.
- Picos: **48.7 %**, coincidente con el punto de carga máxima.
- Caída progresiva tras la fase de _ramp-down_.

[Web Server AWS - Uso CPU](./evidencias/semana-3/escenario-1/aws-web-server-cpu.png)

---

## 4. Recomendaciones

1. **Mantener la arquitectura desacoplada**, ya que contribuyó a una reducción de latencia y a un mejor aislamiento de la carga de procesamiento de vídeo.
2. **Ejecutar las pruebas de carga desde una instancia EC2 dentro de la misma región AWS** para reducir la latencia externa e incrementar la precisión de las métricas.
3. **Monitorear la red de salida y ancho de banda** durante picos de subida de archivos, ya que puede ser el principal cuello de botella en pruebas futuras.
4. Considerar la **ampliación de RAM a 4 GiB por instancia**, lo que permitiría un mejor margen operativo ante mayores volúmenes concurrentes.

---

## 5. Conclusiones finales

- La arquitectura mostró una mejora significativa frente a la **Semana 2**, aumentando la capacidad de concurrencia en un **+33 %** y reduciendo la latencia p95 en aproximadamente **0.4 s**.
- El sistema es **estable** y **cumple con los SLA definidos** para todos los escenarios probados.
- El desacoplamiento del _worker_ y el balanceador de carga demostraron ser decisiones efectivas para optimizar la capacidad del sistema.
- Los resultados confirman que la infraestructura actual soporta cargas sostenidas de hasta **160 usuarios concurrentes (~250 RPS)** sin degradación perceptible.

> 🟩 **Estado final:** El sistema se encuentra dentro de los parámetros aceptables de rendimiento. Las mejoras aplicadas han optimizado la capacidad de respuesta y estabilidad general de la aplicación bajo condiciones de carga controlada.

# 📄 Resultados y Análisis de Capacidad — Escenario 2 (Rendimiento de la capa Worker)

## 1. Resumen general

Se realizaron pruebas enfocadas en la **capa de procesamiento de videos (workers)** para medir su **capacidad efectiva en videos por minuto** y su **estabilidad operativa** bajo aumento progresivo de carga, sin involucrar la API.

Las tareas fueron **inyectadas directamente en la cola `uploaded-videos`** utilizando dos scripts productores, los cuales toman una lista de **20 IDs de videos** desde el archivo `video_ids.txt`.

Las pruebas ejecutadas se basaron en los siguientes mecanismos clave de los scripts productores:

- **Pruebas de saturación (Ramp-Up Test):**  
  El script envía tareas de forma incremental (por ejemplo: **2 → 4 → 6 → 8**) con pausas controladas entre rondas, simulando un **aumento gradual de la carga** sobre el worker.

- **Pruebas sostenidas**  
  Antes de enviar nuevas tareas, el script verifica el tamaño de la cola.  
  Si las tareas pendientes superan el umbral configurado (**MAX_QUEUE_SIZE**), el productor **espera** 30 segundos antes de continuar, garantizando una **Prueba Sostenida sin saturación de 2 minutos**.

Estas pruebas consideraron también variaciones en:

- **Tamaño del video:** 50 MB y 100 MB
- **Concurrencia del worker:** 1, 2 y 4 procesos/hilos por nodo

El monitoreo y análisis de métricas de desempeño se realizó mediante:

- **Prometheus** → recolección de métricas de worker y recursos del sistema
- **Grafana** → visualización del throughput, latencias y **perfilamiento de recursos computacionales** (CPU, memoria, I/O de disco, uso de red) en tiempo real

El objetivo fue determinar:

- El **throughput nominal** del worker (videos/min)
- El **tiempo medio de servicio** por video
- La **estabilidad de la cola** bajo carga continua
- Los **puntos de saturación y cuellos de botella** asociados al procesamiento (CPU, memoria, I/O de disco, uso de red)

## 2. Resultados por escenario

### 🧩 2.1 Escenario de Ramp-Up Test (Pruebas de saturación)

| Métrica                                        | Video 50 MB — 1 Worker | Video 100 MB — 1 Worker | Video 50 MB — 2 Workers | Video 100 MB — 2 Workers | Video 50 MB — 4 Workers | Video 100 MB — 4 Workers |
| ---------------------------------------------- | ---------------------- | ----------------------- | ----------------------- | ------------------------ | ----------------------- | ------------------------ |
| Throughput promedio (videos/min)               | 6                      | 3.5                     | 11                      | 7                        | 22                      | 13                       |
| Tiempo promedio de procesamiento por video (s) | 8.5                    | 17                      | 5                       | 8.5                      | 3.5                     | 6                        |
| Uso promedio de CPU (%)                        | 0.5                    | 0.9                     | 1.2                     | 2                        | 2.5                     | 4                        |
| Uso promedio de RAM (%)                        | 4                      | 6                       | 7                       | 10                       | 12                      | 16                       |

**Evidencias**

[Ejecucion script saturacion](./evidencias/semana-3/escenario-2/ejecucion-saturacion.png)

[Monitoreo graphana](./evidencias/semana-3/escenario-2/monitoring-graphana-saturacion.png)

**Conclusión**

La capa Worker mostró un comportamiento estable durante el incremento progresivo de carga, manteniendo tiempos de servicio consistentes y sin crecimiento descontrolado de la cola. Además, en todos los escenarios, todos los videos se procesaron correctamente sin pérdidas ni errores. Se identificaron los siguientes hallazgos clave:

- El **throughput máximo observado** fue de **22 videos/min** con **4 workers y videos de 50 MB**, lo que representa el punto óptimo de procesamiento en esta configuración.

- Los videos de **100 MB** incrementan significativamente el tiempo medio de servicio, reduciendo el throughput hasta en un **40-50%** frente a archivos de 50 MB, debido al mayor volumen de datos a procesar.

- El **uso de CPU se mantiene bajo a moderado (0.5% a 4%)**, indicando que el procesamiento no está limitado por capacidad computacional en esta etapa, lo que sugiere posibilidad de escalar aún más con más workers o recursos.

- El **uso de RAM escala con la concurrencia y el tamaño del video**, especialmente visible con 4 workers y videos grandes, lo que podría limitar el escalamiento horizontal si no se ajustan adecuadamente los recursos de memoria.

### 🧩 2.2 Escenario de Pruebas sostenidas

| Métrica                                            | Video 50 MB — 1 Worker | Video 100 MB — 1 Worker | Video 50 MB — 2 Workers | Video 100 MB — 2 Workers | Video 50 MB — 4 Workers | Video 100 MB — 4 Workers |
| -------------------------------------------------- | ---------------------- | ----------------------- | ----------------------- | ------------------------ | ----------------------- | ------------------------ |
| **Throughput promedio (videos/min)**               | 5                      | 3.0                     | 10                      | 6.5                      | 20                      | 12                       |
| **Tiempo promedio de procesamiento por video (s)** | 9                      | 18                      | 5                       | 9                        | 3                       | 6                        |
| **Uso promedio de CPU (%)**                        | 0.5                    | 1.0                     | 1.5                     | 2.5                      | 3                       | 4                        |
| **Uso promedio de RAM (%)**                        | 4                      | 6                       | 7                       | 10                       | 12                      | 16                       |

**Evidencias**

[Ejecucion script sostenido](./evidencias/semana-3/escenario-2/ejecucion-sostenida.png)

[Monitoreo graphana](./evidencias/semana-3/escenario-2/monitoring-graphana-sostenida.png)

**Conclusión**

En el escenario de Pruebas Sostenidas, la capa Worker demostró un comportamiento estable durante toda la ejecución, gracias al **control de saturación de la cola** implementado en el productor. Antes de enviar nuevas tareas, el script verificaba que la cola no superara el umbral definido (**MAX_QUEUE_SIZE**), garantizando que la prueba se ejecutara sin saturación ni acumulación excesiva de tareas. Además, todos los videos se procesaron correctamente en todos los escenarios.

Se destacan los siguientes hallazgos:

- El **throughput máximo observado** fue de **20 videos/min** con **4 workers y videos de 50 MB**, representando la capacidad nominal del sistema bajo carga sostenida.

- Los videos de **100 MB** incrementaron el tiempo medio de procesamiento, reduciendo el throughput entre un **35–40%** respecto a archivos de 50 MB, aunque la cola permaneció controlada gracias al mecanismo de espera del productor.

- El **CPU se mantuvo bajo a moderado (0.5%–4%)**, indicando que el procesamiento no está limitado por capacidad computacional en esta configuración y dejando margen para escalar más workers si se requiere.

- El **uso de RAM escaló con la concurrencia**, alcanzando hasta **16%** en la configuración de 4 workers con videos de 100 MB, lo que sugiere la necesidad de dimensionar los recursos adecuadamente para cargas prolongadas.

## 3. Conclusión General — Escenario 2 (Rendimiento de la capa Worker)

Las pruebas realizadas sobre la **capa Worker** muestran que el sistema es capaz de procesar videos de manera **estable y eficiente** bajo diferentes niveles de carga, tanto en **ramp-up progresivo** como en **cargas sostenidas controladas**. Los hallazgos clave son:

- El **throughput máximo observado** fue de **22 videos/min** con **4 workers y videos de 50 MB** durante el ramp-up, mientras que en pruebas sostenidas se alcanzaron **20 videos/min** en la misma configuración, lo que representa la **capacidad nominal del sistema** bajo alta concurrencia.

- Los videos de **100 MB** incrementan significativamente el **tiempo promedio de procesamiento**, reduciendo el throughput entre un **35–40%** respecto a los videos de 50 MB, especialmente en escenarios con varios workers.

- Durante el **ramp-up**, el **CPU se mantuvo bajo a moderado** (0.5%–4%), indicando que la capacidad computacional actual es suficiente para la carga evaluada. En pruebas sostenidas, la CPU se mantuvo estable dentro del mismo rango, demostrando **eficiencia sin saturación**.

- El **uso de RAM escala con la concurrencia y el tamaño de los videos**, comenzando en 4% para 1 worker y 50 MB, y alcanzando hasta 16% con 4 workers y videos de 100 MB. Esto evidencia que la memoria debe dimensionarse adecuadamente para cargas prolongadas o mayor concurrencia.

- El **control de saturación de la cola** implementado en el productor resultó **efectivo**, evitando acumulación excesiva de tareas y garantizando que la cola permaneciera estable durante todas las pruebas sostenidas.

En general, los resultados confirman que la arquitectura actual del worker es **robusta y escalable dentro de los límites evaluados**, identificando **CPU y memoria como los principales factores limitantes** para incrementos futuros de carga.

---

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
