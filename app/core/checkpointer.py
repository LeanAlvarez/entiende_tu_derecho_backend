"""Configuración del checkpointer de LangGraph usando PostgreSQL (Supabase)."""

from typing import Optional

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except ImportError:
    # Fallback si la ruta es diferente
    try:
        from langgraph.checkpoint.postgres import AsyncPostgresSaver
    except ImportError:
        # Si no está disponible, usar None
        AsyncPostgresSaver = None

from app.core.config import settings


# Instancia global del checkpointer y su context manager
_checkpointer: Optional[AsyncPostgresSaver] = None
_checkpointer_cm = None
_setup_done: bool = False


async def get_checkpointer() -> Optional[AsyncPostgresSaver]:
    """
    Obtiene o crea una instancia de AsyncPostgresSaver configurada con Supabase.
    
    Esta función debe llamarse una vez al inicio de la aplicación para inicializar
    las tablas necesarias. Luego retorna la misma instancia en llamadas subsecuentes.
    
    Returns:
        AsyncPostgresSaver configurado o None si no hay cadena de conexión
    """
    global _checkpointer, _checkpointer_cm, _setup_done
    
    if not settings.supabase_db_url or AsyncPostgresSaver is None:
        return None
    
    if _checkpointer is None:
        # from_conn_string retorna un context manager
        # Necesitamos mantenerlo activo durante toda la vida de la aplicación
        
        # El Transaction Pooler de Supabase (puerto 6543) no soporta bien prepared statements
        # Si la URL usa el puerto 6543, cambiar a 5432 (Session Pooler) que soporta prepared statements mejor
        db_url = settings.supabase_db_url
        
        # Si usa el puerto del Transaction Pooler, cambiar al Session Pooler
        if ":6543/" in db_url or ":6543?" in db_url:
            db_url = db_url.replace(":6543/", ":5432/").replace(":6543?", ":5432?")
            print("ℹ Using Session Pooler (5432) instead of Transaction Pooler (6543) for checkpointer")
        
        _checkpointer_cm = AsyncPostgresSaver.from_conn_string(db_url)
        
        # Entrar en el context manager y mantenerlo activo
        _checkpointer = await _checkpointer_cm.__aenter__()
        
        # Inicializar las tablas si no existe (solo una vez)
        # Siempre intentar setup() para asegurar que todas las tablas existan
        if not _setup_done:
            import asyncio
            
            # Intentar setup() con manejo específico del error de prepared statement
            try:
                print("Creating checkpoint tables...")
                await _checkpointer.setup()
                print("✓ Checkpoint tables created successfully")
                _setup_done = True
            except Exception as e:
                error_msg = str(e).lower()
                error_type = type(e).__name__
                
                # El error de "prepared statement already exists" es común en modo reload
                # pero NO significa que las tablas se crearon - puede ser que setup() falló antes
                if "prepared statement" in error_msg and "already exists" in error_msg:
                    # Este error puede ocurrir DURANTE el setup, pero las tablas pueden no estar creadas
                    # Necesitamos verificar si realmente se crearon o reintentar
                    print("⚠ Prepared statement warning during setup. Verifying tables were created...")
                    
                    # Intentar verificar si las tablas existen haciendo una consulta simple
                    try:
                        # Si podemos hacer una consulta, las tablas existen
                        # Intentar acceder a una tabla para verificar
                        import psycopg
                        async with await psycopg.AsyncConnection.connect(settings.supabase_db_url) as conn:
                            async with conn.cursor() as cur:
                                await cur.execute("""
                                    SELECT COUNT(*) FROM information_schema.tables 
                                    WHERE table_schema = 'public' 
                                    AND table_name IN ('checkpoints', 'checkpoint_blobs', 'checkpoint_writes', 'checkpoint_migrations')
                                """)
                                result = await cur.fetchone()
                                table_count = result[0] if result else 0
                                
                                if table_count >= 4:
                                    print(f"✓ Checkpoint tables verified ({table_count}/4 tables exist)")
                                    _setup_done = True
                                else:
                                    print(f"⚠ Only {table_count}/4 checkpoint tables exist. Retrying setup...")
                                    # Reintentar setup después de un breve delay
                                    await asyncio.sleep(0.5)
                                    await _checkpointer.setup()
                                    print("✓ Checkpoint tables created on retry")
                                    _setup_done = True
                    except Exception as verify_error:
                        # Si la verificación falla, asumir que las tablas no existen y reintentar
                        print(f"⚠ Could not verify tables. Retrying setup...")
                        await asyncio.sleep(0.5)
                        try:
                            await _checkpointer.setup()
                            print("✓ Checkpoint tables created on retry")
                            _setup_done = True
                        except Exception as retry_error:
                            print(f"✗ Setup failed on retry: {retry_error}")
                            _setup_done = True
                            raise
                elif "already exists" in error_msg or "duplicate" in error_msg:
                    # Otros errores de "already exists" - probablemente las tablas están creadas
                    print(f"✓ Checkpoint setup completed (some objects already exist)")
                    _setup_done = True
                else:
                    # Otro tipo de error - relanzar para debugging
                    print(f"✗ Error during checkpoint setup: {e}")
                    print(f"  Error type: {error_type}")
                    _setup_done = True
                    raise
    
    return _checkpointer


async def setup_checkpointer() -> None:
    """
    Inicializa el checkpointer y crea las tablas necesarias.
    
    Esta función debe llamarse al inicio de la aplicación (por ejemplo, en un startup event).
    """
    await get_checkpointer()


async def cleanup_checkpointer() -> None:
    """
    Limpia el checkpointer al cerrar la aplicación.
    Debe llamarse al finalizar la aplicación para cerrar el context manager correctamente.
    """
    global _checkpointer, _checkpointer_cm, _setup_done
    
    if _checkpointer_cm is not None:
        try:
            await _checkpointer_cm.__aexit__(None, None, None)
        except Exception:
            # Ignorar errores al cerrar
            pass
        _checkpointer = None
        _checkpointer_cm = None
        _setup_done = False  # Resetear para permitir reinicialización en modo reload
