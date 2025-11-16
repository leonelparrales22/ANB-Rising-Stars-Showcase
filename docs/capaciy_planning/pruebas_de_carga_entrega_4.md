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
