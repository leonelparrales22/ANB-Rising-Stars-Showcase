```mermaid
sequenceDiagram
    participant U as Usuario
    participant V as Video Module
    participant M as Message Broker
    participant W as Celery Worker
    participant S as Storage
    participant DB as Database
    
    U->>V: POST /api/videos/upload
    V->>DB: Guardar metadata (status: uploaded)
    V->>S: Guardar video original
    V->>M: Encolar tarea de procesamiento
    V->>U: 201 - "Procesamiento en curso"
    
    M->>W: Asignar tarea
    W->>S: Descargar video
    W->>W: Procesar video
    W->>S: Guardar procesado
    W->>DB: Actualizar status → processed