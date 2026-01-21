# Guía de Uso de thread_id en FastAPI

## ¿Qué es thread_id?

El `thread_id` es un identificador único que permite mantener el estado de cada conversación o sesión de usuario de forma persistente en la base de datos. Cada usuario debe tener su propio `thread_id` para que sus conversaciones no se mezclen.

## Configuración Inicial

### 1. Variables de Entorno

Asegúrate de tener en tu archivo `.env`:

```bash
GROQ_API_KEY=tu_api_key_de_groq
SUPABASE_DB_URL=postgresql://postgres:[TU_PASSWORD]@[TU_HOST]:5432/postgres
```

**Importante:** Para obtener la cadena de conexión de Supabase:
1. Ve a tu proyecto en Supabase
2. Settings → Database
3. Busca "Connection string" → "URI"
4. Reemplaza `[YOUR-PASSWORD]` con tu contraseña de base de datos

### 2. Instalación de Dependencias

```bash
uv pip install -e .
```

## Uso en los Endpoints

### Endpoint Principal: `/api/v1/process-document`

Este endpoint procesa documentos y mantiene el estado por `thread_id`.

#### Request

```json
{
  "raw_text": "Texto del documento a procesar...",
  "thread_id": "user_123"  // Opcional: si no se envía, se genera uno automático
}
```

#### Response

```json
{
  "doc_type": "Contrato de arrendamiento",
  "simplified_explanation": "Este es un contrato...",
  "identified_risks": ["Cláusula de penalización alta", "..."],
  "action_items": ["Revisar cláusula 5", "..."],
  "confidence_score": 0.95,
  "language": "es",
  "thread_id": "user_123"
}
```

### Ejemplo de Uso con cURL

```bash
# Procesar un documento con thread_id específico
curl -X POST "http://localhost:8000/api/v1/process-document" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "CONTRATO DE ARRENDAMIENTO...",
    "thread_id": "user_123"
  }'
```

### Ejemplo de Uso con Python

```python
import httpx

async def process_document(text: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/process-document",
            json={
                "raw_text": text,
                "thread_id": user_id  # Usa el ID del usuario autenticado
            }
        )
        return response.json()
```

## Estrategias de thread_id

### Opción 1: Un thread por usuario (Recomendado para MVP)

```python
# Usa el ID del usuario autenticado directamente
thread_id = f"user_{authenticated_user.id}"
```

**Ventajas:**
- Simple de implementar
- Cada usuario mantiene una sola conversación continua

**Desventajas:**
- Si el usuario quiere múltiples conversaciones, se mezclan

### Opción 2: Un thread por conversación

```python
# Genera un nuevo thread_id para cada nueva conversación
import uuid
thread_id = f"user_{user_id}_conv_{uuid.uuid4()}"
```

**Ventajas:**
- Permite múltiples conversaciones por usuario
- Mejor organización

**Desventajas:**
- Requiere gestión de múltiples threads por usuario

### Opción 3: Thread por documento

```python
# Un thread por documento procesado
import hashlib
document_hash = hashlib.md5(document_text.encode()).hexdigest()
thread_id = f"user_{user_id}_doc_{document_hash}"
```

**Ventajas:**
- Cada documento tiene su propio historial
- Fácil de rastrear

## Endpoints Adicionales

### Obtener Estado Actual de un Thread

```bash
GET /api/v1/thread/{thread_id}/state
```

Útil para recuperar el estado de una conversación anterior sin procesar un nuevo documento.

### Obtener Historial de un Thread

```bash
GET /api/v1/thread/{thread_id}/history?limit=10
```

Retorna el historial de estados de un thread específico.

## Integración con Autenticación

Si estás usando Supabase Auth, puedes obtener el `thread_id` del usuario autenticado:

```python
from fastapi import Depends
from supabase import create_client, Client

def get_current_user(token: str) -> dict:
    # Validar token y obtener usuario
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    user = supabase.auth.get_user(token)
    return user

@app.post("/api/v1/process-document")
async def process_document(
    request: DocumentProcessRequest,
    current_user: dict = Depends(get_current_user)
):
    # Usar el ID del usuario como thread_id
    thread_id = f"user_{current_user['id']}"
    
    # ... resto del código
```

## Notas Importantes

1. **Persistencia:** El estado se guarda automáticamente en PostgreSQL (Supabase) después de cada nodo del grafo.

2. **Threads Únicos:** Cada `thread_id` mantiene su propio estado independiente. No compartas `thread_id` entre usuarios.

3. **Limpieza:** Considera implementar una tarea periódica para eliminar threads antiguos si no se usan más.

4. **Seguridad:** En producción, siempre valida que el `thread_id` pertenezca al usuario autenticado para evitar acceso no autorizado.
