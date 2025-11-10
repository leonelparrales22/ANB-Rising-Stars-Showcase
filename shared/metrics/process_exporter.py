import os
import time
import psutil
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from threading import Thread
from celery.signals import task_prerun, task_postrun

# ---------- Métricas de proceso ----------
CPU_PERCENT = Gauge(
    "celery_worker_cpu_percent", 
    "CPU usage percent of the Celery worker process (including children)"
)
MEMORY_PERCENT = Gauge(
    "celery_worker_memory_percent", 
    "Memory usage percent of the Celery worker process (including children)"
)
MEMORY_RSS = Gauge(
    "celery_worker_memory_rss_bytes", 
    "Resident memory of the Celery worker process (including children)"
)
MEMORY_VMS = Gauge(
    "celery_worker_memory_vms_bytes", 
    "Virtual memory of the Celery worker process (including children)"
)
IO_READ = Gauge(
    "celery_worker_io_read_bytes", 
    "Bytes read by the Celery worker process (including children)"
)
IO_WRITE = Gauge(
    "celery_worker_io_write_bytes", 
    "Bytes written by the Celery worker process (including children)"
)

# ---------- Métricas de throughput ----------
TASKS_PROCESSED = Counter("celery_tasks_total", "Total number of Celery tasks processed")
TASK_DURATION = Histogram("celery_task_duration_seconds", "Duration of Celery tasks in seconds")

# ---------- Diccionario de tiempos ----------
_task_start_times = {}

# ---------- Proceso actual ----------
process = psutil.Process(os.getpid())

# ---------- Función para agregar métricas de hijos ----------
def aggregate_process_metrics(proc):
    """
    Devuelve diccionario con CPU%, memoria RSS/VMS e I/O incluyendo procesos hijos.
    """
    try:
        cpu = proc.cpu_percent(interval=None)
        mem_percent = proc.memory_percent()
        mem_info = proc.memory_info()
        rss = mem_info.rss
        vms = mem_info.vms

        io_info = proc.io_counters()
        read_bytes = io_info.read_bytes
        write_bytes = io_info.write_bytes

        for child in proc.children(recursive=True):
            try:
                cpu += child.cpu_percent(interval=None)
                mem_percent += child.memory_percent()
                c_mem = child.memory_info()
                rss += c_mem.rss
                vms += c_mem.vms
                c_io = child.io_counters()
                read_bytes += c_io.read_bytes
                write_bytes += c_io.write_bytes
            except psutil.NoSuchProcess:
                continue

        return {
            "cpu": cpu,
            "mem_percent": mem_percent,
            "rss": rss,
            "vms": vms,
            "read_bytes": read_bytes,
            "write_bytes": write_bytes,
        }
    except psutil.NoSuchProcess:
        return {
            "cpu": 0,
            "mem_percent": 0,
            "rss": 0,
            "vms": 0,
            "read_bytes": 0,
            "write_bytes": 0,
        }

# ---------- Función principal de recolección ----------
def collect_metrics(interval=2):
    # Inicializar CPU para obtener porcentaje correcto
    aggregate_process_metrics(process)

    while True:
        metrics = aggregate_process_metrics(process)
        CPU_PERCENT.set(metrics["cpu"])
        MEMORY_PERCENT.set(metrics["mem_percent"])
        MEMORY_RSS.set(metrics["rss"])
        MEMORY_VMS.set(metrics["vms"])
        IO_READ.set(metrics["read_bytes"])
        IO_WRITE.set(metrics["write_bytes"])
        time.sleep(interval)

# ---------- Función para iniciar exporter ----------
def start_exporter(port=9001):
    start_http_server(port)
    thread = Thread(target=collect_metrics, daemon=True)
    thread.start()
    print(f"Prometheus metrics available at http://localhost:{port}/metrics")

# ---------- Señales de Celery ----------
@task_prerun.connect
def record_start_time(sender=None, task_id=None, task=None, args=None, kwargs=None, **extras):
    _task_start_times[task_id] = time.time()

@task_postrun.connect
def update_task_metrics(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extras):
    start_time = _task_start_times.pop(task_id, None)
    if start_time:
        duration = time.time() - start_time
        TASK_DURATION.observe(duration)
    TASKS_PROCESSED.inc()
