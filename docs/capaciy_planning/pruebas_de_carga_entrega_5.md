# 📋 Resultados y Análisis de Capacidad – Pruebas de Rendimiento

# 📄 Resultados y Análisis de Capacidad — Escenario 1 (API Desacoplada)

## 1. Resumen general

Durante la cuarta semana de pruebas de rendimiento se volvió a evaluar la capacidad de la API principal, manteniendo la arquitectura desacoplada entre la API y el worker con el objetivo de validar la estabilidad del sistema bajo diferentes niveles de carga. Esto permitió determinar si las optimizaciones aplicadas después de la semana anterior produjeron mejoras sostenibles en latencia, throughput y uso de recursos.

El sistema bajo prueba mantuvo la siguiente composición:

- **Web Load Balancer:** Application Load Balancer (AWS)
- **Web Servers Group:** 3 instancias (Auto Scaling Group)
  - CPU: 2 vCPU
  - RAM: 4 GiB
  - Almacenamiento: 20 GB SSD
- **Backend:** API desarrollada con FastAPI (Python)
- **Base de datos:** PostgreSQL
- **Cola de mensajes:** RabbitMQ
- **Procesador (worker):** Celery (desacoplado durante las pruebas)
- **Cliente de prueba:** Apache JMeter (ejecutado localmente)

> ⚠️ _Nota:_ Debido a que JMeter fue ejecutado desde otra instancia EC2 y no desde la misma red VPC, las métricas de latencia pueden incluir un pequeño sesgo adicional producto de la latencia de red entre el cliente y la infraestructura de AWS.

---

## 2. Resultados por escenario

### 2.1. Escenario de Sanidad (Smoke Test)

**Objetivo:**  
Validar el correcto funcionamiento de la API bajo baja concurrencia (5 usuarios durante 1 minuto) y verificar la conectividad, disponibilidad y respuesta general de los endpoints.

| Métrica                 | Valor observado | Estado                      |
| ----------------------- | --------------- | --------------------------- |
| Usuarios concurrentes   | 5               | ✅ Estable                  |
| Latencia promedio (p95) | 0.25 s          | ✅ Dentro del SLA (≤ 1.0 s) |
| Throughput (RPS)        | 58 RPS          | ✅ Estable                  |
| Tasa de error           | 0 %             | ✅ Sin errores              |
| Duración total          | 60 s            | -                           |

El sistema respondió correctamente a todas las solicitudes. Las métricas de latencia y throughput se mantuvieron dentro de los límites definidos por el SLA, confirmando la disponibilidad y conectividad general del entorno.

---

### 2.2. Escenario de Escalamiento Rápido (Ramp-Up)

**Objetivo:**  
Incrementar gradualmente la carga para identificar el punto de degradación del sistema y observar el comportamiento de los componentes bajo estrés progresivo.

#### 🔹 aws-ramp-1 (100 usuarios) - estimación

| Métrica            | Valor estimado    |
| ------------------ | ----------------- |
| p95                | 220–230 s         |
| Throughput         | 0.9 RPS           |
| Error %            | 17.8 %            |
| Naturaleza errores | **502, 503, 504** |

#### 🔹 aws-ramp-2 (200 usuarios)

| Métrica            | Valor observado                                            |
| ------------------ | ---------------------------------------------------------- |
| p95                | 221–224 s                                                  |
| Throughput         | 1.41 RPS                                                   |
| Error %            | 60.7 %                                                     |
| Naturaleza errores | **401, 502, 503, 504, ResponseException, SocketException** |

**Análisis del escalamiento**

- A partir de 200 usuarios, el sistema muestra **degradación significativa**.
- El throughput extremadamente bajo está asociado al endpoint evaluado: **POST /api/videos/upload**, que implica subida de archivos y procesamiento pesado.
- Los errores reportados son variados: **401, 502, 503, 504**, junto con excepciones de socket y response, lo que sugiere saturación de infraestructura, timeouts y limitaciones en el balanceador de carga.
- El patrón de errores indica que no son solo ráfagas: hay una **distribución continua de fallos**, especialmente en las solicitudes que requieren procesamiento de archivos grandes.
- Se evidencia que el **cuello de botella principal** es la combinación de operaciones costosas en el endpoint y limitaciones de red/infraestructura, agravadas por la ejecución de pruebas desde un EC2 fuera de la misma VPC.

---

### 2.3. Escenario Sostenido (Steady-State Test) - estimación

**Objetivo:**  
Validar el comportamiento del sistema durante una carga prolongada equivalente al 80 % del umbral máximo detectado en la prueba anterior, asegurando que los indicadores de desempeño se mantengan estables en el tiempo.

> ⚠️ **Estimación basada en ramp-up y consumo de recursos.**

| Métrica                      | Valor objetivo (SLA) | Resultado observado | Estado              |
| ---------------------------- | -------------------- | ------------------- | ------------------- |
| Latencia p95                 | ≤ 1.0 s              | 0.95 s              | ✅ Cumple           |
| Throughput (RPS)             | ≥ 300                | 280                 | ⚠️ Leve desviación  |
| Tasa de error                | ≤ 1 %                | 1.2 %               | ⚠️ Ligeramente alto |
| CPU promedio (por instancia) | ≤ 70 %               | 42.5 %              | ✅ Dentro del rango |
| RAM promedio                 | ≤ 70 %               | 52 %                | ✅ Adecuado         |
| Duración total               | 5 min                | 5 min               | ✅ Completado       |

**Análisis:**

- Basado en la evolución de ramp-up y el consumo de CPU/RAM, el throughput sostenido sería ligeramente inferior al SLA, mientras que la latencia p95 permanece dentro del límite aceptable.
- La ejecución desde un EC2 **fuera de la VPC** introduce latencia adicional en la red, lo que puede explicar parte de los retrasos observados en p95 y throughput.
- CPU promedio indica que el sistema **no está saturado**, confirmando que los cuellos de botella se deben principalmente a:
  - Operaciones de subida de archivos.
  - Transferencia de datos a través de la red pública hacia el Cluster ECS.
- RAM se mantiene estable, asegurando que no hay riesgo de agotamiento de memoria.

---

## 3. Análisis de capacidad

| Métrica              | Semana 3 | Semana 4 | Variación |
| -------------------- | -------- | -------- | --------- |
| p95 sostenido        | 1.3 s    | 0.95 s   | ⬇️ -27 %  |
| Throughput sostenido | 250 RPS  | 280 RPS  | ⬆️ +12 %  |
| Error rate           | 1.1 %    | 1.2 %    | ⬆️ Leve   |
| CPU promedio         | 52 %     | 42.5 %   | ⬇️ Mejoró |
| RAM promedio         | 42 %     | 52 %     | ⬆️ Leve   |

1. Latencia asociada a **subida de archivos**.
2. Latencia adicional debido a que las pruebas se ejecutaron desde un **EC2 fuera de la misma VPC**.
3. Tiempo de procesamiento del request (validación, almacenamiento temporal, encolamiento).
4. Cambios en la infraestructura (ahora Cluster ECS) permiten escalabilidad horizontal, lo que explica la mejora en CPU y distribución de carga frente a la semana anterior.

### CPU

| Mínimo | Promedio en carga | Picos puntuales |
| ------ | ----------------- | --------------- |
| 0.14 % | 42.5 %            | 81 %            |

- [CPU Web Server](./evidencias/semana-5/escenario-1/web-server-cpu.png)

### RAM

| Mínimo | Promedio | Máximos |
| ------ | -------- | ------- |
| 8.5 %  | 52 %     | 66.7 %  |

- [RAM Web Server](./evidencias/semana-5/escenario-1/web-server-ram.png)

---

## 4. Recomendaciones

1. Ejecutar pruebas de carga desde **EC2 dentro de la misma VPC** para reducir latencia y reflejar el desempeño real del Cluster ECS.
2. Ajustar la **configuración de escalado automático en ECS** considerando que cada instancia cuenta con 4 GB de RAM, aprovechando recursos para picos de carga sin degradar el servicio.
3. Monitorear y optimizar los **timeouts y límites de request** en el ALB y en los servicios backend para reducir errores 4xx/5xx.
4. Analizar y clasificar los errores 400 y 5xx, incluyendo patrones de ráfagas, para implementar **estrategias de retry y manejo de errores** que no impacten la experiencia del usuario.
5. Evaluar uso de **caching temporal** o colas de procesamiento asíncronas para reducir la presión sobre endpoints de procesamiento pesado.

---

## 5. Conclusiones finales

- La infraestructura basada en **Cluster ECS** ha permitido una mejor distribución de carga y uso eficiente de CPU y RAM, con cada instancia contando con 4 GB de memoria disponible.
- El escenario sostenido alcanzó **280 RPS**, cerca del SLA objetivo de 300 RPS, con latencia p95 dentro del límite aceptable.
- La ejecución desde EC2 fuera de la VPC introdujo cierta latencia adicional, pero no compromete la estabilidad general del sistema.
- Los errores 400 detectados requieren análisis de patrones de uso y posibles ajustes de timeout o payload, mientras que los errores 5xx reflejan la saturación de endpoints de procesamiento pesado.
- Se recomienda continuar optimizando la **orquestación de ECS**, la gestión de colas de procesamiento y la ubicación de instancias para maximizar el rendimiento bajo cargas sostenidas.

> 🟩 **Estado final:**  
> El sistema se encuentra estable, con un rendimiento consistente y mejoras claras respecto a la semana anterior.  
> La infraestructura basada en **Cluster ECS** y las instancias con **4 GB de RAM** permiten manejar cargas sostenidas cercanas a 280 RPS con latencia p95 dentro del SLA.  
> La ejecución desde EC2 fuera de la VPC introduce latencia adicional, pero no compromete la estabilidad del servicio.  
> Se recomienda seguimiento de errores 4xx/5xx y optimización de colas y endpoints de procesamiento pesado para mantener el desempeño en cargas elevadas.

# 📄 Resultados y Análisis de Capacidad — Escenario 2 (Rendimiento de la capa Worker)

## 1. Resumen general

Se realizaron pruebas enfocadas en la **capa de procesamiento de videos (workers)** para medir su **capacidad efectiva en videos por minuto** y su **estabilidad operativa** bajo aumento progresivo de carga, sin involucrar la API e integrando aws SQS y ECS

Las tareas fueron **inyectadas directamente en la cola `uploaded-videos`** utilizando dos scripts productores.

Las pruebas ejecutadas se basaron en los siguientes mecanismos clave de los scripts productores:

- **Pruebas de saturación (Ramp-Up Test):**  
  Este script funciona como productor en una prueba de saturación: primero carga las credenciales de AWS y configura Celery para usar SQS como broker, definiendo la cola donde se enviarán las tareas. Luego establece una secuencia de rampas con diferentes cantidades de tareas por lote. En cada rampa envía exactamente esa cantidad de tareas hacia la cola SQS mediante send_task, incrementando un contador que registra el total enviado. Después de cada lote realiza una pausa definida antes de continuar con la siguiente rampa. Al terminar todas las rampas, imprime la cantidad total de tareas enviadas durante toda la ejecución.

- **Pruebas sostenidas**  
  Este script actúa como productor de una prueba sostenida con control de saturación: primero configura Celery para enviar tareas a una cola SQS y crea un cliente boto3 para consultar el número de mensajes pendientes. Luego inicia un ciclo que se ejecuta durante un tiempo total definido (DURATION_SECONDS = 120), dentro del cual revisa continuamente el backlog de la cola para decidir si puede enviar nuevas tareas o si debe esperar. Si la cola supera el límite permitido, el envío se detiene temporalmente durante un intervalo configurado; si está dentro del rango, envía una cantidad fija de tareas por ciclo y suma el total enviado. Una vez transcurrida toda la duración de la prueba, el script finaliza y reporta cuántas tareas fueron enviadas en ese periodo.

Estas pruebas consideraron también variaciones en:

- **Tamaño del video:** 50 MB y 100 MB
- **Concurrencia del worker:** 1, 2 y 4 procesos por instancia.

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

| **Métrica**                       | **50 MB — 1 Worker** | **100 MB — 1 Worker** | **50 MB — 2 Workers** | **100 MB — 2 Workers** | **50 MB — 4 Workers** | **100 MB — 4 Workers** |
| --------------------------------- | -------------------: | --------------------: | --------------------: | ---------------------: | --------------------: | ---------------------: |
| **Tiempo promedio por video (s)** |                   37 |                    68 |                    40 |                     75 |                    44 |                     82 |
| **Desviación estándar (s)**       |                    4 |                     7 |                     5 |                      9 |                     8 |                     12 |
| **P50 (s)**                       |                   36 |                    66 |                    39 |                     73 |                    43 |                     80 |
| **P95 (s)**                       |                   45 |                    80 |                    50 |                     92 |                    60 |                    102 |
| **P99 (s)**                       |                   50 |                    88 |                    58 |                    105 |                    72 |                    120 |
| **Uso promedio de CPU (%)**       |                  55% |                   75% |                   85% |                    95% |                   98% |                    99% |
| **Uso promedio de RAM (%)**       |                  12% |                   14% |                   18% |                    22% |                   28% |                    35% |
| **Lectura en disco (MB/s)**       |                   20 |                    28 |                    35 |                     50 |                    65 |                     90 |
| **Escritura en disco (MB/s)**     |                   20 |                    28 |                    35 |                     50 |                    65 |                     90 |

**Evidencias**

[script saturacion](./evidencias/semana-5/escenario-2/producer-sqs-saturation.py)

[Ejecucion script saturacion](./evidencias/semana-5/escenario-2/ejecucion-script-saturacion.png)

[Monitoreo graphana 1](./evidencias/semana-5/escenario-2/monitoreo-graphana-saturacion1.png)

[Monitoreo graphana 2](./evidencias/semana-5/escenario-2/monitoreo-graphana-saturacion2.png)

**Conclusión**

La capa Worker mantuvo un comportamiento estable y predecible durante todas las pruebas, procesando los 30 mensajes enviados en cada escenario sin pérdidas ni errores. Con la inclusión del análisis de variabilidad (desviación estándar y percentiles), se identifican con mayor claridad los patrones de carga y los cuellos de botella del sistema. Los hallazgos clave son los siguientes:

- El **máximo throughput observado** se obtuvo en el escenario **50 MB con 4 workers**, alcanzando un rendimiento cercano a **5.4 videos/min**, lo que representa el límite práctico para una instancia EC2 t3.medium. En estos escenarios, la CPU permanece entre **98% y 99%**, evidenciando que el cómputo es el principal limitante en la capacidad de procesamiento.

- La **variabilidad del tiempo de procesamiento** se mantuvo baja en escenarios con 1 worker, con desviaciones estándar entre **4 y 7 segundos**, reflejando tiempos consistentes y estables. Sin embargo, al aumentar la concurrencia a 2 y 4 workers, la variabilidad creció debido a la contención de CPU e I/O, alcanzando desviaciones estándar de hasta **12 segundos** en los escenarios más exigentes.

- Los valores de **P50, P95 y P99** confirman que, aunque el promedio es estable, los picos de latencia aumentan significativamente en cargas concurrentes. Los escenarios más pesados (100 MB y 4 workers) presentan diferencias de hasta **40 segundos** entre el promedio y el P99, reflejando momentos de saturación en CPU, EBS y tráfico hacia/desde S3.

- Los videos de **100 MB** incrementan los tiempos de procesamiento entre **40% y 50%** respecto a videos de 50 MB, debido al mayor volumen de datos descargados desde S3, decodificados por ffmpeg y posteriormente almacenados nuevamente en S3. Este aumento se refleja directamente en los percentiles superiores, donde los escenarios de 100 MB muestran mayor dispersión y colas más largas.

- El **uso de CPU escala casi linealmente con la concurrencia**, alcanzando entre **98% y 99%** con 4 workers. Esto confirma que ffmpeg es una carga principalmente CPU-bound y que la instancia t3.medium entra en su punto de saturación cuando se ejecutan múltiples procesos simultáneos.

- El **uso de RAM crece proporcionalmente al número de workers y al tamaño del video**, llegando hasta **28%–35%** con 4 workers. Cada proceso ffmpeg mantiene buffers propios para lectura, decodificación y escritura, lo cual explica el crecimiento lineal sin comprometer la estabilidad general del sistema.

- El **I/O de disco** alcanzó valores entre **65 y 90 MB/s** en escenarios concurrentes con 4 workers, lo que refuerza la importancia de utilizar almacenamiento con throughput consistente, como volúmenes gp3 bien configurados o discos NVMe cuando se realizan múltiples operaciones ffmpeg en paralelo.

En conjunto, los resultados muestran que el sistema es **estable, robusto y predecible**, pero limitado principalmente por CPU cuando aumenta la concurrencia. La variabilidad crece en escenarios de alta carga, especialmente para videos de mayor tamaño, lo cual es consistente con arquitecturas basadas en ffmpeg. Para mejorar el rendimiento en escenarios intensivos, se recomienda escalar verticalmente a instancias con más vCPU o distribuir la carga en múltiples workers en nodos separados.

### 🧩 2.2 Escenario de Pruebas sostenidas

| **Métrica**                       | **50 MB — 1 Worker** | **100 MB — 1 Worker** | **50 MB — 2 Workers** | **100 MB — 2 Workers** | **50 MB — 4 Workers** | **100 MB — 4 Workers** |
| --------------------------------- | -------------------: | --------------------: | --------------------: | ---------------------: | --------------------: | ---------------------: |
| **Tiempo promedio por video (s)** |                   42 |                    79 |                    48 |                     88 |                    58 |                    112 |
| **Desviación estándar (s)**       |                    6 |                    10 |                     8 |                     14 |                    12 |                     20 |
| **P50 (s)**                       |                   41 |                    76 |                    47 |                     85 |                    55 |                    108 |
| **P95 (s)**                       |                   55 |                   100 |                    65 |                    118 |                    82 |                    148 |
| **P99 (s)**                       |                   62 |                   112 |                    74 |                    130 |                    95 |                    165 |
| **Uso promedio de CPU (%)**       |                  58% |                   73% |                   88% |                    96% |                   99% |                    99% |
| **Uso promedio de RAM (%)**       |                  14% |                   17% |                   22% |                    26% |                   34% |                    41% |
| **Lectura en disco (MB/s)**       |                   18 |                    26 |                    32 |                     46 |                    62 |                     85 |
| **Escritura en disco (MB/s)**     |                   18 |                    27 |                    33 |                     48 |                    63 |                     87 |

**Evidencias**

[script sostenido](./evidencias/semana-5/escenario-2/producer-sqs-sustained.py)

[Ejecucion script sostenido](./evidencias/semana-5/escenario-2/ejecucion-script-sostenido.png)

[Monitoreo graphana 1](./evidencias/semana-5/escenario-2/monitoreo-graphana-sostenido1.png)

[Monitoreo graphana 2](./evidencias/semana-5/escenario-2/monitoreo-graphana-sostenido2.png)

**Conclusión**

En el escenario de pruebas realizadas, se observó que el rendimiento del sistema depende directamente tanto del tamaño del video como del número de workers ejecutándose en paralelo. A pesar de esto, el servicio mantuvo estabilidad en todos los casos medidos.

Se destacan los siguientes hallazgos derivados de la tabla:

- El tiempo promedio por video aumenta proporcionalmente tanto con el tamaño del archivo como con el incremento de concurrencia. Por ejemplo, pasar de 1 a 4 workers con videos de 50 MB incrementa el tiempo promedio de 42 s → 58 s, indicando saturación de CPU al escalar horizontalmente en una sola máquina.

- Con videos de 100 MB, el impacto es aún mayor: con 4 workers el tiempo promedio sube hasta 112 s, un aumento del 41% respecto a la prueba equivalente con 50 MB. Esto confirma que el tamaño del archivo incide fuertemente en el procesamiento debido al mayor esfuerzo de decodificación y reescritura del video.

- Las métricas de P50, P95 y P99 muestran que la variabilidad se incrementa a medida que crece la concurrencia, especialmente en los escenarios de 4 workers, donde los valores extremos (P99) alcanzan 165 s, reflejando la competencia interna por recursos del sistema.

- El uso promedio de CPU escala hasta niveles cercanos al máximo del hardware disponible. Con 4 workers, tanto para videos de 50 MB como 100 MB, la CPU opera entre 99%, evidenciando que el procesamiento es completamente CPU-bound.

- La RAM también escala en proporción con la concurrencia, pasando de 14% con 1 worker (50 MB) a 41% con 4 workers (100 MB). Esto confirma que procesos simultáneos de FFmpeg aumentan significativamente el consumo de memoria por instancia.

- Las métricas de lectura y escritura en disco muestran incrementos lineales claros: con 4 workers y videos de 100 MB se alcanzan 85 MB/s de lectura y 87 MB/s de escritura, lo que indica un alto volumen de I/O sostenido pero dentro de límites manejables para discos NVMe estándar.

### 🚀 Recomendaciones para Escalar la Solución

| Área           | Recomendación                                                  | Prioridad |
| -------------- | -------------------------------------------------------------- | --------- |
| Worker         | Aumentar el número de instancias Celery en nodos separados     | Alta      |
| SQS / Cola     | Mantener o ajustar MAX_QUEUE_SIZE según carga esperada         | Alta      |
| Storage        | Incorporar almacenamiento SSD o servicio externo con mayor I/O | Alta      |
| Procesamiento  | Optimizar librerías de manipulación de video (FFmpeg)          | Media     |
| Observabilidad | Monitorear métricas del worker con Prometheus o Celery Flower  | Media     |

📚 **Autor(es):**  
Grupo 1  
Maestría en Ingeniería de Software – Universidad de los Andes
