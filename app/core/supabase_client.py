"""Cliente de Supabase para operaciones de base de datos."""

from typing import Optional

from supabase import create_client, Client

from app.core.config import settings


# Instancia global del cliente de Supabase
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Obtiene o crea una instancia del cliente de Supabase.
    
    Returns:
        Cliente de Supabase configurado o None si no hay configuración
    """
    global _supabase_client
    
    if not settings.supabase_url or not settings.supabase_key:
        return None
    
    if _supabase_client is None:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    
    return _supabase_client


def get_authenticated_supabase_client(user_token: str) -> Optional[Client]:
    """
    Crea un cliente de Supabase autenticado con el token del usuario.
    
    Esto es necesario para que RLS (Row Level Security) funcione correctamente,
    ya que el cliente autenticado tiene el contexto del usuario.
    
    Args:
        user_token: Token JWT del usuario autenticado
        
    Returns:
        Cliente de Supabase autenticado o None si no hay configuración
    """
    if not settings.supabase_url or not settings.supabase_key:
        return None
    
    # Crear cliente con la anon key (no service_role) para que RLS funcione
    # El cliente se autentica usando el token del usuario en los headers
    client = create_client(settings.supabase_url, settings.supabase_key)
    
    # Establecer el token en los headers para autenticación
    # En Supabase Python SDK, necesitamos establecer el token en el cliente postgrest
    try:
        # El cliente de Supabase Python SDK usa postgrest para las queries
        # Necesitamos establecer el header Authorization en el cliente postgrest
        if hasattr(client, 'postgrest'):
            # Verificar que el cliente postgrest tenga el atributo headers
            if hasattr(client.postgrest, 'headers'):
                # Establecer el header de autorización directamente en el cliente postgrest
                # Esto es lo que permite que RLS funcione correctamente
                # IMPORTANTE: También necesitamos establecer el apikey (anon key)
                client.postgrest.headers["Authorization"] = f"Bearer {user_token}"
                client.postgrest.headers["apikey"] = settings.supabase_key
                print(f"✅ Token de autorización establecido correctamente en cliente postgrest")
                print(f"   Headers: Authorization = Bearer {user_token[:20]}..., apikey = {settings.supabase_key[:20]}...")
            else:
                print(f"⚠ Warning: Cliente postgrest no tiene atributo 'headers'")
                # Intentar usar auth.set_session como fallback
                client.auth.set_session(access_token=user_token, refresh_token="")
                print(f"✅ Token establecido usando auth.set_session")
        else:
            # Si no tiene postgrest, intentar usar auth.set_session
            print(f"⚠ Warning: Cliente no tiene atributo postgrest, intentando auth.set_session")
            client.auth.set_session(access_token=user_token, refresh_token="")
    except Exception as e:
        print(f"⚠ Warning: Error al establecer token de autorización: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        # Intentar usar auth.set_session como fallback
        try:
            client.auth.set_session(access_token=user_token, refresh_token="")
            print(f"✅ Token establecido usando auth.set_session (fallback)")
        except Exception as e2:
            print(f"⚠ Warning: Error en fallback auth.set_session: {str(e2)}")
            # Si todo falla, retornar el cliente sin autenticación (puede que necesitemos service_role key)
            pass
    
    return client
