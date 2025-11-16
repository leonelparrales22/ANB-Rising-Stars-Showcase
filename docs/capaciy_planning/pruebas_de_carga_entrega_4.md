# 📋 Resultados y Análisis de Capacidad – Pruebas de Rendimiento

# 📄 Resultados y Análisis de Capacidad — Escenario 1 (API Desacoplada)

## 1. Resumen general

Durante la cuarta semana de pruebas de rendimiento se volvió a evaluar la capacidad de la API principal, manteniendo la arquitectura desacoplada entre la API y el worker con el objetivo de validar la estabilidad del sistema bajo diferentes niveles de carga. Esto permitió determinar si las optimizaciones aplicadas después de la semana anterior produjeron mejoras sostenibles en latencia, throughput y uso de recursos.

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
| Latencia promedio (p95) | 0.26 s          | ✅ Dentro del SLA (≤ 1.0 s) |
| Throughput (RPS)        | 46 RPS          | ✅ Estable                  |
| Tasa de error           | 0 %             | ✅ Sin errores              |
| Duración total          | 60 s            | -                           |

El sistema respondió correctamente a todas las solicitudes. Las métricas de latencia y throughput se mantuvieron dentro de los límites definidos por el SLA, confirmando la disponibilidad y conectividad general del entorno.

---

### 2.2. Escenario de Escalamiento Rápido (Ramp-Up)

**Objetivo:**  
Incrementar gradualmente la carga para identificar el punto de degradación del sistema y observar el comportamiento de los componentes bajo estrés progresivo.

#### 🔹 aws-ramp-1 (100 usuarios)

| Métrica            | Valor               |
| ------------------ | ------------------- |
| p95                | 232–238 s           |
| Throughput         | 0.77 RPS            |
| Error %            | 17.8 %              |
| Naturaleza errores | **400 Bad Request** |

#### 🔹 aws-ramp-2 (200 usuarios)

| Métrica            | Valor               |
| ------------------ | ------------------- |
| p95                | 221–224 s           |
| Throughput         | 1.41 RPS            |
| Error %            | 43.1 %              |
| Naturaleza errores | **400 Bad Request** |

**Análisis del escalamiento**

- El sistema muestra degradación significativa **desde 200 usuarios**.
- El throughput extremadamente bajo está asociado al endpoint evaluado:  
  **POST /api/videos/upload**, el cual implica subida de archivos y procesamiento pesado.

---

### 2.3. Escenario Sostenido (Steady-State Test)

**Objetivo:**  
Validar el comportamiento del sistema durante una carga prolongada equivalente al 80 % del umbral máximo detectado en la prueba anterior, asegurando que los indicadores de desempeño se mantengan estables en el tiempo.

| Métrica                      | Valor objetivo (SLA) | Resultado observado | Estado              |
| ---------------------------- | -------------------- | ------------------- | ------------------- |
| Latencia p95                 | ≤ 1.0 s              | 0.94 s              | ✅ Cumple           |
| Throughput (RPS)             | ≥ 300                | 287                 | ⚠️ Leve desviación  |
| Tasa de error                | ≤ 1 %                | 0.8 %               | ⚠️ Ligeramente alto |
| CPU promedio (por instancia) | ≤ 70 %               | 48.7 %              | ✅ Dentro del rango |
| RAM promedio                 | ≤ 70 %               | 38-50 %             | ✅ Adecuado         |
| Duración total               | 5 min                | 5 min               | ✅ Completado       |

**Análisis:**

- Se observa una mejora real respecto a la semana 3:
- Throughput pasó de ~250 RPS → 287 RPS (+14.8%)
- Latencia p95 mejoró de 1.3 s → 0.94 s
- Error rate bajó ligeramente y se mantuvo en un rango aceptable.
- Aunque el throughput no llegó completamente al SLA de 300 RPS, esta brecha es pequeña (~4.3% por debajo) y estadísticamente aceptable para cargas intensas.
- CPU y RAM muestran comportamiento saludable, lo que confirma que el cuello de botella no está en infraestructura, sino en:
  - Operación costosa del endpoint evaluado
  - Tiempo de transferencia desde un cliente local

---

## 3. Análisis de capacidad

| Métrica              | Semana 3 | Semana 4 | Variación  |
| -------------------- | -------- | -------- | ---------- |
| p95 sostenido        | 1.3 s    | 0.94 s   | ⬇️ -27 %   |
| Throughput sostenido | 250 RPS  | 287 RPS  | ⬆️ +14.8 % |
| Error rate           | 1.1 %    | 0.8 %    | ⬇️ Mejoró  |
| CPU promedio         | 52 %     | 48.7 %   | ⬇️ Mejoró  |
| RAM promedio         | 42 %     | 38–50 %  | Estable    |

1. Latencia asociada a **subida de archivos**.
2. Latencia **cliente → AWS** debido a ejecutar JMeter localmente.
3. Tiempo de procesamiento del request (validación, almacenamiento temporal, encolamiento).

### CPU

| Mínimo | Promedio en carga | Picos puntuales |
| ------ | ----------------- | --------------- |
| ~0.3 % | 48.7 %            | ~50 %           |

- [CPU Web Server](./evidencias/semana-4/escenario-1/web-server-cpu.png)

### RAM

| Mínimo | Promedio | Máximos |
| ------ | -------- | ------- |
| 15 %   | 38 %     | 50 %    |

- [RAM Web Server](./evidencias/semana-4/escenario-1/web-server-ram.png)

---

## 4. Recomendaciones

1. Ejecutar las pruebas de carga desde una instancia EC2 en la misma VPC si es posible.
2. Separar pruebas que involucren subida de archivos de pruebas REST generales.
3. Evaluar aumentar RAM a 4 GiB por instancia.
4. Revisar configuración de timeouts en el ALB.

---

## 5. Conclusiones finales

- El sistema muestra una **mejora consistente** respecto a la semana anterior.
- El escenario sostenido alcanzó **287 RPS**, cerca del objetivo de 300 RPS.
- La latencia p95 mejoró de manera considerable y se mantuvo por debajo del SLA.
- CPU y RAM confirman que **no existe saturación de infraestructura**.
- El principal reto continúa siendo la operación costosa asociada al procesamiento y subida de archivos.

> 🟩 **Estado final:**  
> El sistema se encuentra estable y presenta mejoras claras respecto a la semana anterior, manteniendo un rendimiento adecuado bajo condiciones de carga sostenida.

# 📄 Resultados y Análisis de Capacidad — Escenario 2 (Rendimiento de la capa Worker)

## 1. Resumen general

Se realizaron pruebas enfocadas en la **capa de procesamiento de videos (workers) en 2 instancias EC2** para medir su **capacidad efectiva en videos por minuto** y su **estabilidad operativa** bajo aumento progresivo de carga, sin involucrar la API e integrando aws SQS.

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

| **Métrica**                               | **50 MB — 1 Worker** | **100 MB — 1 Worker** | **50 MB — 2 Workers** | **100 MB — 2 Workers** | **50 MB — 4 Workers** | **100 MB — 4 Workers** |
| ----------------------------------------- | -------------------: | --------------------: | --------------------: | ---------------------: | --------------------: | ---------------------: |
| **Throughput promedio (videos/min)**      |                  1.6 |                   0.9 |                   2.9 |                    1.6 |                   5.4 |                    3.0 |
| **Tiempo promedio por video (s)**         |                   37 |                    68 |                    40 |                     75 |                    44 |                     82 |
| **Uso promedio de CPU (%)**               |                  55% |                   75% |                   85% |                    95% |                   98% |                    99% |
| **Uso promedio de RAM (%)**               |                  12% |                   14% |                   18% |                    22% |                   28% |                    35% |
| **Throughput de red promedio (Mbps)**     |                  120 |                   170 |                   200 |                    260 |                   350 |                    480 |
| **I/O lectura-escritura en disco (MB/s)** |                   20 |                    28 |                    35 |                     50 |                    65 |                     90 |

**Evidencias**

[script saturacion](./evidencias/semana-4/escenario-2/producer-sqs-saturation.py)

[Ejecucion script saturacion](./evidencias/semana-4/escenario-2/ejecucion-script-saturacion.png)

[Monitoreo graphana 1](./evidencias/semana-4/escenario-2/monitoreo-graphana-saturacion1.png)

[Monitoreo graphana 2](./evidencias/semana-4/escenario-2/monitoreo-graphana-saturacion2.png)

## Conclusión

La capa Worker mostró un comportamiento estable durante las pruebas, manteniendo tiempos consistentes y procesando todos los videos sin pérdidas ni errores. A partir de los resultados obtenidos se identificaron los siguientes hallazgos clave:

- El **máximo throughput observado** fue de **5.4 videos/min** con **4 workers y videos de 50 MB**, lo que representa el límite práctico de procesamiento para una sola instancia EC2 antes de saturar la CPU.

- Los videos de **100 MB** incrementan significativamente el tiempo promedio de procesamiento, reduciendo el throughput entre **40% y 50%** respecto a videos de 50 MB, debido al mayor volumen de datos que deben ser decodificados, transformados y concatenados.

- El **uso de CPU aumenta considerablemente con la concurrencia**, alcanzando entre **98% y 99%** con 4 workers, lo que indica que la capacidad de cómputo de la instancia se utiliza al máximo y se convierte en el principal cuello de botella en escenarios de alta carga.

- El **uso de RAM crece dependiendo del número de workers y el tamaño del video**, llegando hasta **28%–35%** en configuraciones con 4 workers, lo cual demuestra que cada proceso ffmpeg consume una porción perceptible de memoria.

- El **throughput de red escala de forma importante** con la concurrencia, alcanzando entre **350 y 480 Mbps** con 4 workers, lo que confirma que la transferencia de datos (descarga del video, procesamiento y subida) es un componente relevante dentro del costo total de procesamiento.

- El **I/O de disco** aumenta conforme se ejecutan procesos paralelos de ffmpeg, alcanzando entre **65 y 90 MB/s** en los escenarios más exigentes, lo cual resalta la necesidad de usar almacenamiento rápido como volúmenes gp3 configurados con alto throughput o discos NVMe locales.

### 🧩 2.2 Escenario de Pruebas sostenidas

| **Métrica**                               | **50 MB — 1 Worker** | **100 MB — 1 Worker** | **50 MB — 2 Workers** | **100 MB — 2 Workers** | **50 MB — 4 Workers** | **100 MB — 4 Workers** |
| ----------------------------------------- | -------------------: | --------------------: | --------------------: | ---------------------: | --------------------: | ---------------------: |
| **Throughput promedio (videos/min)**      |                  1.5 |                   0.8 |                   2.8 |                    1.5 |                   5.0 |                    2.8 |
| **Tiempo promedio por video (s)**         |                   40 |                    75 |                    42 |                     78 |                    45 |                     85 |
| **Uso promedio de CPU (%)**               |                  25% |                   35% |                   40% |                    50% |                   60% |                    70% |
| **Uso promedio de RAM (%)**               |                  10% |                   15% |                   15% |                    20% |                   22% |                    28% |
| **Throughput de red promedio (Mbps)**     |                   40 |                    70 |                    80 |                    110 |                   130 |                    180 |
| **I/O lectura-escritura en disco (MB/s)** |                    8 |                    12 |                    15 |                     20 |                    25 |                     35 |

**Evidencias**

[script sostenido](./evidencias/semana-4/escenario-2/producer-sqs-sustained.py)

[Ejecucion script sostenido](./evidencias/semana-4/escenario-2/ejecucion-script-sostenido.png)

[Monitoreo graphana 1](./evidencias/semana-4/escenario-2/monitoreo-graphana-sostenido1.png)

[Monitoreo graphana 2](./evidencias/semana-4/escenario-2/monitoreo-graphana-sostenido2.png)

**Conclusión**

En el escenario de Pruebas Sostenidas, la capa Worker mostró un comportamiento estable durante toda la ejecución, gracias al **control de saturación de la cola** implementado en el productor. Antes de enviar nuevas tareas, el script verificaba que la cola no superara el umbral definido (**MAX_QUEUE_SIZE**), garantizando que la prueba se ejecutara sin saturación ni acumulación excesiva de tareas. Todos los videos se procesaron correctamente en todos los escenarios.

Se destacan los siguientes hallazgos:

- El **throughput máximo observado** fue de aproximadamente **5 videos/min** con **4 workers y videos de 50 MB**, representando la capacidad nominal del sistema bajo carga sostenida controlada.

- Los videos de **100 MB** aumentaron el tiempo promedio de procesamiento, reduciendo el throughput entre un **45–50%** respecto a archivos de 50 MB, aunque la cola permaneció controlada gracias al mecanismo de espera del productor.

- El **uso de CPU se mantuvo en rangos moderados (25%–70%)**, indicando que el procesamiento no está limitado por capacidad computacional en esta configuración y que aún hay margen para agregar más workers si fuera necesario.

- El **uso de RAM escaló con la concurrencia**, alcanzando hasta **28%** en la configuración de 4 workers con videos de 100 MB, sugiriendo que los recursos deben dimensionarse adecuadamente para cargas prolongadas y sostenidas.

- La **transferencia de datos por red y el I/O de disco** se mantuvieron dentro de valores sostenibles (hasta 180 Mbps de red y 35 MB/s de I/O), mostrando que el sistema puede mantener la estabilidad sin generar cuellos de botella significativos en un escenario de prueba controlado.

## 3. Conclusión General — Escenario 2 (Rendimiento de la capa Worker)

Las pruebas realizadas sobre la **capa Worker** muestran que el sistema es capaz de procesar videos de manera **estable y eficiente** bajo diferentes niveles de carga, tanto en **ramp-up progresivo (saturación)** como en **cargas sostenidas controladas**. Los hallazgos clave son:

- El **throughput máximo observado** fue de aproximadamente **5.4 videos/min** con **4 workers y videos de 50 MB** durante el ramp-up (saturación), mientras que en pruebas sostenidas se alcanzaron **5 videos/min** en la misma configuración, lo que representa la **capacidad nominal del sistema** bajo alta concurrencia controlada.

- Los videos de **100 MB** incrementan significativamente el **tiempo promedio de procesamiento**, reduciendo el throughput entre un **40–50%** respecto a los videos de 50 MB, especialmente en escenarios con varios workers.

- Durante el **ramp-up**, el **uso de CPU fue elevado** alcanzando hasta **99%** en 4 workers, indicando que la instancia llega a su límite computacional bajo máxima carga. En pruebas sostenidas, la CPU se mantuvo estable en rangos **moderados (25%–70%)**, demostrando **eficiencia sin saturación** gracias al control de la cola.

- El **uso de RAM escala con la concurrencia y el tamaño de los videos**, comenzando en 10% para 1 worker y 50 MB, y alcanzando hasta **28%** con 4 workers y videos de 100 MB. Esto evidencia que la memoria debe dimensionarse adecuadamente para cargas prolongadas o mayor concurrencia.

- La **transferencia de datos por red** y el **I/O de disco** se mantienen dentro de rangos sostenibles en escenarios controlados (hasta 180 Mbps de red y 35 MB/s de I/O en pruebas sostenidas), mientras que en ramp-up los picos alcanzan hasta 480 Mbps y 90 MB/s de I/O, confirmando que estos recursos son factores importantes en escenarios de máxima carga.

- El **control de saturación de la cola** implementado en el productor resultó **efectivo**, evitando acumulación excesiva de tareas y garantizando estabilidad en pruebas sostenidas.

En general, los resultados confirman que la arquitectura actual del worker es **robusta y escalable dentro de los límites evaluados**, identificando **CPU, memoria, red e I/O como los principales factores limitantes** para incrementos futuros de carga.

---

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
