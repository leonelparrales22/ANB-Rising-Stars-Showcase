# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import psutil
import threading
import time

# -------------------------
# Métricas del worker
# -------------------------
videos_processed = Counter(
    "worker_videos_processed_total",
    "Total de videos procesados correctamente"
)

videos_failed = Counter(
    "worker_videos_failed_total",
    "Total de videos que fallaron"
)

video_processing_time = Histogram(
    "worker_video_processing_seconds",
    "Duración del procesamiento de cada video (en segundos)"
)

# -------------------------
# Métricas del sistema
# -------------------------
cpu_usage = Gauge("worker_cpu_percent", "Uso de CPU (%)")
memory_usage = Gauge("worker_memory_percent", "Uso de memoria (%)")
disk_read = Gauge("worker_disk_read_bytes", "Bytes leídos por disco")
disk_write = Gauge("worker_disk_write_bytes", "Bytes escritos por disco")
net_sent = Gauge("worker_network_sent_bytes", "Bytes enviados por red")
net_recv = Gauge("worker_network_recv_bytes", "Bytes recibidos por red")

# -------------------------
# Servidor Prometheus
# -------------------------
def start_metrics_server(port: int = 9000):
    """
    Inicia servidor HTTP para Prometheus y actualiza métricas del sistema.
    """
    start_http_server(port)
    print(f"Prometheus metrics server running on port {port}")

    def update_system_metrics():
        old_disk = psutil.disk_io_counters()
        old_net = psutil.net_io_counters()
        while True:
            # CPU y memoria
            cpu_usage.set(psutil.cpu_percent(interval=None))
            memory_usage.set(psutil.virtual_memory().percent)

            # I/O de disco
            new_disk = psutil.disk_io_counters()
            disk_read.set(new_disk.read_bytes - old_disk.read_bytes)
            disk_write.set(new_disk.write_bytes - old_disk.write_bytes)
            old_disk = new_disk

            # Red
            new_net = psutil.net_io_counters()
            net_sent.set(new_net.bytes_sent - old_net.bytes_sent)
            net_recv.set(new_net.bytes_recv - old_net.bytes_recv)
            old_net = new_net

            time.sleep(5)

    threading.Thread(target=update_system_metrics, daemon=True).start()
