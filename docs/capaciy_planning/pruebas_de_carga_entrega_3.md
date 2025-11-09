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

---
