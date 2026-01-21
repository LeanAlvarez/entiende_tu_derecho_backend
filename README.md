# EntiendeTuDerecho AI

Aplicación de impacto social para simplificar documentos legales usando IA.

## Stack Tecnológico

- **Gestor de paquetes:** `uv`
- **Framework Web:** FastAPI
- **Orquestación de IA:** LangGraph (StateGraph)
- **LLM:** Groq (Llama 3.1 8B / 70B)
- **Base de Datos/Auth/Storage:** Supabase
- **OCR:** Pytesseract (procesamiento local)

## Instalación

### Requisitos previos

- Python 3.11+
- `uv` instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Configuración

1. Instalar dependencias:
```bash
uv pip install -e .
```

2. Configurar variables de entorno (crear `.env`):
```bash
GROQ_API_KEY=tu_api_key
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key
```

3. Ejecutar la aplicación:
```bash
uvicorn app.api.main:app --reload
```

## Estructura del Proyecto

```
/app
    /api: Endpoints de FastAPI (v1)
    /agents: Lógica de LangGraph (states, nodes, graph definition)
    /core: Configuración de entorno y clientes (Groq, Supabase)
    /services: Lógica de soporte (OCR, PDF processing)
    /models: Esquemas Pydantic para API y DB
/tests: Pruebas unitarias para los nodos del grafo
```

## Desarrollo

- **Linting:** `ruff check .`
- **Formateo:** `black .`
- **Type checking:** `mypy app`
- **Tests:** `pytest`

## Docker

Construir y ejecutar con Docker:
```bash
docker build -t etd-ai .
docker run -p 8000:8000 etd-ai
```
