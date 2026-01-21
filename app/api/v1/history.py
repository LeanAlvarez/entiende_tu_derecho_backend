"""Endpoint para obtener el historial de análisis del usuario."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.supabase_client import get_supabase_client
from app.api.deps import get_current_user


router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def get_history(
    user_id: str = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de análisis a retornar"),
    offset: int = Query(0, ge=0, description="Número de análisis a omitir para paginación"),
) -> dict:
    """
    Obtiene el historial de análisis de documentos del usuario autenticado.
    
    Los resultados están filtrados automáticamente por el user_id extraído
    del token Bearer de autenticación.
    
    Args:
        user_id: ID del usuario autenticado (extraído automáticamente del token Bearer)
        limit: Número máximo de análisis a retornar (1-100)
        offset: Número de análisis a omitir para paginación
        
    Returns:
        Lista de análisis del usuario con paginación
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Servicio de base de datos no disponible"
            )
        
        # Consultar análisis filtrados por user_id
        response = supabase.table("user_analyses") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Obtener el total de registros para paginación
        count_response = supabase.table("user_analyses") \
            .select("id", count="exact") \
            .eq("user_id", user_id) \
            .execute()
        
        total_count = count_response.count if hasattr(count_response, "count") else len(response.data)
        
        return {
            "user_id": user_id,
            "analyses": response.data if response.data else [],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial: {str(e)}"
        )


@router.get("/{thread_id}")
async def get_analysis_by_thread_id(
    thread_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Obtiene un análisis específico por thread_id.
    
    Solo retorna el análisis si pertenece al usuario autenticado.
    
    Args:
        thread_id: ID del thread/conversación
        user_id: ID del usuario autenticado (extraído automáticamente del token Bearer)
        
    Returns:
        Análisis específico del usuario
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Servicio de base de datos no disponible"
            )
        
        # Consultar análisis específico filtrado por user_id y thread_id
        response = supabase.table("user_analyses") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("thread_id", thread_id) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Análisis no encontrado o no tienes permisos para acceder a él"
            )
        
        return {
            "user_id": user_id,
            "analysis": response.data[0],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el análisis: {str(e)}"
        )
