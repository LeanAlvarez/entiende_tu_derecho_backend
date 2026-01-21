"""Endpoints principales de FastAPI para el procesamiento de documentos."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.graph import compile_graph
from app.agents.state import AgentState
from app.core.checkpointer import setup_checkpointer, cleanup_checkpointer
from app.core.config import settings
from app.api.v1 import analyze as analyze_router
from app.api.v1 import history as history_router

# Instancia global del grafo
graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    
    Inicializa el checkpointer y compila el grafo al iniciar,
    y limpia recursos al cerrar.
    """
    global graph
    
    # Inicializar checkpointer y crear tablas
    await setup_checkpointer()
    
    # Compilar el grafo con persistencia
    graph = await compile_graph()
    
    yield
    
    # Cleanup si es necesario
    await cleanup_checkpointer()
    graph = None


# Crear la aplicación FastAPI
app = FastAPI(
    title="EntiendeTuDerecho AI",
    description="API para simplificar documentos legales usando IA",
    version="0.1.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modelos Pydantic para los endpoints
class DocumentProcessRequest(BaseModel):
    """Request para procesar un documento."""
    
    raw_text: str
    thread_id: Optional[str] = None
    """ID del thread/conversación. Si no se proporciona, se genera uno nuevo."""


class DocumentProcessResponse(BaseModel):
    """Response del procesamiento de documento."""
    
    doc_type: str
    simplified_explanation: str
    identified_risks: list[str]
    action_items: list[str]
    confidence_score: float
    language: str
    thread_id: str


# Incluir routers de v1
app.include_router(analyze_router.router, prefix="/api/v1")
app.include_router(history_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint de salud."""
    return {"message": "EntiendeTuDerecho AI API", "status": "ok"}


@app.post("/api/v1/process-document", response_model=DocumentProcessResponse)
async def process_document(request: DocumentProcessRequest):
    """
    Procesa un documento legal usando el grafo de LangGraph.
    
    Cada usuario debe proporcionar un thread_id único para mantener
    su propia conversación y estado persistente.
    
    Args:
        request: Request con el texto del documento y thread_id opcional
        
    Returns:
        Response con el análisis del documento
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    # Generar thread_id si no se proporciona
    # En producción, esto debería venir del sistema de autenticación
    thread_id = request.thread_id or f"user_{hash(request.raw_text) % 1000000}"
    
    # Crear el estado inicial
    initial_state: AgentState = {
        "raw_text": request.raw_text,
        "doc_type": "",
        "simplified_explanation": "",
        "identified_risks": [],
        "action_items": [],
        "confidence_score": 1.0,
        "language": "es",
        "error_message": "",
        "thread_id": thread_id,
    }
    
    # Configurar el thread_id para persistencia
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Invocar el grafo de forma asíncrona
        result = await graph.ainvoke(initial_state, config=config)
        
        return DocumentProcessResponse(
            doc_type=result.get("doc_type", ""),
            simplified_explanation=result.get("simplified_explanation", ""),
            identified_risks=result.get("identified_risks", []),
            action_items=result.get("action_items", []),
            confidence_score=result.get("confidence_score", 0.0),
            language=result.get("language", "es"),
            thread_id=thread_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.get("/api/v1/thread/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """
    Obtiene el estado actual de un thread específico.
    
    Útil para recuperar el estado de una conversación anterior.
    
    Args:
        thread_id: ID del thread a consultar
        
    Returns:
        Estado actual del thread
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Obtener el estado actual del thread
        state_snapshot = await graph.aget_state(config=config)
        
        if state_snapshot.values:
            return {
                "thread_id": thread_id,
                "state": state_snapshot.values,
                "next": state_snapshot.next,
            }
        else:
            raise HTTPException(status_code=404, detail="Thread not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thread state: {str(e)}")


@app.get("/api/v1/thread/{thread_id}/history")
async def get_thread_history(thread_id: str, limit: int = 10):
    """
    Obtiene el historial de estados de un thread.
    
    Args:
        thread_id: ID del thread a consultar
        limit: Número máximo de estados a retornar
        
    Returns:
        Historial de estados del thread
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Obtener el historial del thread
        history = []
        async for state in graph.astream(None, config=config):
            history.append(state)
            if len(history) >= limit:
                break
        
        return {
            "thread_id": thread_id,
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thread history: {str(e)}")
