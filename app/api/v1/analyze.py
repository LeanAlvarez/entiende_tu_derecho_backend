"""Endpoint para analizar documentos legales desde imágenes."""

import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Request

from app.agents.state import AgentState
from app.services.ocr import extract_text_from_image
from app.api.deps import get_current_user, security


router = APIRouter(prefix="/analyze", tags=["analyze"])


def get_graph():
    """Obtiene el grafo desde main para evitar importación circular."""
    from app.api.main import graph
    return graph


@router.post("")
async def analyze_document(
    image: UploadFile = File(..., description="Imagen del documento a analizar"),
    thread_id: Optional[str] = Form(None, description="ID del thread/conversación. Si no se proporciona, se genera uno automático"),
    user_id: str = Depends(get_current_user),
    credentials = Depends(security),
) -> dict:
    """
    Analiza un documento legal desde una imagen.
    
    El proceso incluye:
    1. Extracción de texto mediante OCR
    2. Clasificación del documento
    3. Simplificación y análisis del contenido
    4. Identificación de riesgos y próximos pasos
    
    Args:
        image: Archivo de imagen del documento
        thread_id: ID del thread/conversación (opcional, se genera automáticamente si no se proporciona)
        user_id: ID del usuario autenticado (extraído automáticamente del token Bearer)
        
    Returns:
        Estado final del agente con el análisis completo
    """
    # Obtener el grafo
    graph = get_graph()
    
    # Verificar que el grafo esté inicializado
    if graph is None:
        raise HTTPException(
            status_code=503,
            detail="El grafo no está inicializado. Por favor, espera unos segundos e intenta nuevamente."
        )
    
    try:
        # 1. Extraer texto de la imagen usando OCR
        raw_text = await extract_text_from_image(image)
        
        # 2. Generar o normalizar thread_id (siempre debe incluir user_id)
        if not thread_id:
            # Si no se proporciona, generar uno con formato: user_{user_id}_{uuid}
            thread_id_with_user = f"user_{user_id}_{uuid.uuid4().hex[:12]}"
        elif thread_id.startswith(f"user_{user_id}_"):
            # Si ya tiene el formato correcto con el user_id actual, usarlo
            thread_id_with_user = thread_id
        elif thread_id.startswith("user_"):
            # Si tiene formato user_* pero no coincide con el user_id actual, usar el UUID proporcionado
            # Extraer solo el UUID final si existe
            parts = thread_id.split("_")
            if len(parts) >= 3:
                uuid_part = parts[2]
                thread_id_with_user = f"user_{user_id}_{uuid_part}"
            else:
                thread_id_with_user = f"user_{user_id}_{uuid.uuid4().hex[:12]}"
        else:
            # Si no tiene formato user_*, agregar user_id al inicio
            thread_id_with_user = f"user_{user_id}_{thread_id}"
        
        # 3. Obtener el token del usuario para RLS
        user_token = credentials.credentials  # Token del usuario para RLS
        
        # 4. Crear el estado inicial del agente
        initial_state: AgentState = {
            "raw_text": raw_text,
            "doc_type": "",
            "simplified_explanation": "",
            "identified_risks": [],
            "action_items": [],
            "confidence_score": 1.0,
            "language": "es",
            "error_message": "",
            "thread_id": thread_id_with_user,
            "user_token": user_token,  # Token del usuario para RLS en Supabase
        }
        
        # 5. Configurar el thread_id para persistencia
        config = {"configurable": {"thread_id": thread_id_with_user}}
        
        # 6. Ejecutar el grafo de forma asíncrona
        # Manejar errores de prepared statement que pueden ocurrir con PostgreSQL
        max_retries = 3
        retry_count = 0
        final_state = None
        
        while retry_count < max_retries and final_state is None:
            try:
                final_state = await graph.ainvoke(initial_state, config=config)
            except Exception as graph_error:
                error_msg = str(graph_error).lower()
                # Error de prepared statement puede ocurrir con PostgreSQL en modo reload
                if "prepared statement" in error_msg and "already exists" in error_msg and retry_count < max_retries - 1:
                    retry_count += 1
                    print(f"⚠ Prepared statement error, retrying ({retry_count}/{max_retries})...")
                    # Pequeño delay antes de reintentar
                    import asyncio
                    await asyncio.sleep(0.5)
                    # Limpiar el estado para reintentar
                    continue
                else:
                    # Otro error o último intento falló
                    raise
        
        # 7. Devolver el estado final al usuario
        error_message = final_state.get("error_message", "")
        
        # Si hay error, retornar solo el mensaje de error
        if error_message and error_message.strip():
            return {
                "thread_id": thread_id_with_user,
                "error": True,
                "error_message": error_message,
                "doc_type": "",
                "simplified_explanation": "",
                "identified_risks": [],
                "action_items": [],
                "confidence_score": 0.0,
                "language": "es",
            }
        
        # Si no hay error, retornar el análisis completo
        return {
            "thread_id": thread_id_with_user,
            "error": False,
            "raw_text": final_state.get("raw_text", ""),
            "doc_type": final_state.get("doc_type", ""),
            "simplified_explanation": final_state.get("simplified_explanation", ""),
            "identified_risks": final_state.get("identified_risks", []),
            "action_items": final_state.get("action_items", []),
            "confidence_score": final_state.get("confidence_score", 0.0),
            "language": final_state.get("language", "es"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el documento: {str(e)}"
        )
