"""Dependencias de FastAPI para autenticación y autorización."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.supabase_client import get_supabase_client


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Valida el token Bearer de autenticación y retorna el user_id.
    
    Esta función se usa como dependencia en los endpoints protegidos.
    Extrae el token del header Authorization: Bearer <TOKEN> y lo valida
    con Supabase Auth.
    
    Args:
        credentials: Credenciales HTTP Bearer del header Authorization
        
    Returns:
        user_id: ID del usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido, expirado o no está presente
    """
    token = credentials.credentials
    
    # Obtener cliente de Supabase
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de autenticación no disponible",
        )
    
    try:
        # Validar el token con Supabase Auth
        user_response = supabase.auth.get_user(token)
        
        # Verificar que la respuesta tenga un usuario válido
        if not user_response or not hasattr(user_response, "user") or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = user_response.user.id
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se pudo obtener el ID del usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        # Si hay un error al validar el token (expired, invalid, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error al validar el token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
