"""Nodos del grafo de LangGraph para procesamiento de documentos legales."""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.core.config import settings
from app.core.supabase_client import get_supabase_client


# Configuración del modelo Groq
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_MODEL_LARGE = "llama-3.3-70b-versatile"  # Para análisis complejos
MIN_TEXT_LENGTH = 50  # Longitud mínima de texto para considerar válido
MIN_WORDS = 10  # Número mínimo de palabras para considerar válido


async def extract_and_classify_node(state: AgentState) -> AgentState:
    """
    Nodo que extrae y clasifica el tipo de documento usando Groq.
    
    Antes de clasificar, verifica la longitud y coherencia del raw_text.
    Si el texto parece ruido o es demasiado corto, establece error_message
    y termina el procesamiento.
    
    Analiza el raw_text y determina el doc_type con precisión,
    identificando si es legal, administrativo o comercial.
    
    Args:
        state: Estado actual del agente con raw_text
        
    Returns:
        AgentState actualizado con doc_type y language detectados, o error_message si hay problema
    """
    raw_text = state.get("raw_text", "")
    
    # 1. Verificar longitud mínima
    text_clean = raw_text.strip()
    if not text_clean or len(text_clean) < MIN_TEXT_LENGTH:
        return {
            **state,
            "error_message": "Lo siento, el texto extraído de la imagen es demasiado corto o está vacío. Por favor, toma una foto más clara del documento completo, asegurándote de que todo el texto sea visible y legible.",
            "doc_type": "",
            "language": "es",
            "confidence_score": 0.0,
        }
    
    # 2. Verificar número mínimo de palabras
    words = text_clean.split()
    if len(words) < MIN_WORDS:
        return {
            **state,
            "error_message": "El texto extraído parece ser muy corto o incompleto. Por favor, intenta tomar una foto más nítida del documento, asegurándote de capturar todo el contenido visible.",
            "doc_type": "",
            "language": "es",
            "confidence_score": 0.0,
        }
    
    # 3. Verificar ratio de caracteres alfanuméricos (coherencia)
    alphanumeric_count = sum(1 for c in text_clean if c.isalnum() or c.isspace())
    total_chars = len(text_clean)
    if total_chars > 0:
        alphanumeric_ratio = alphanumeric_count / total_chars
        # Si menos del 50% son alfanuméricos, probablemente es ruido
        if alphanumeric_ratio < 0.5:
            return {
                **state,
                "error_message": "El texto extraído parece contener demasiados caracteres especiales o no es legible. Por favor, toma una foto más clara del documento, con buena iluminación y sin reflejos.",
                "doc_type": "",
                "language": "es",
                "confidence_score": 0.0,
            }
    
    # 4. Verificar si hay demasiadas repeticiones de caracteres (posible ruido)
    # Contar secuencias de 3+ caracteres iguales consecutivos
    max_repeat = 0
    current_char = None
    current_count = 0
    for char in text_clean:
        if char == current_char:
            current_count += 1
            max_repeat = max(max_repeat, current_count)
        else:
            current_char = char
            current_count = 1
    
    # Si hay muchas repeticiones (más de 5 caracteres iguales), probablemente es ruido
    if max_repeat > 5:
        return {
            **state,
            "error_message": "El texto extraído parece contener ruido o caracteres repetidos. Por favor, intenta tomar una foto más nítida del documento, evitando sombras y asegurándote de que el texto esté bien enfocado.",
            "doc_type": "",
            "language": "es",
            "confidence_score": 0.0,
        }
    
    # 5. Verificar si hay suficientes palabras únicas (coherencia semántica básica)
    unique_words = set(word.lower().strip(".,;:!?()[]{}\"'") for word in words if len(word) > 2)
    if len(unique_words) < 5:
        return {
            **state,
            "error_message": "El texto extraído parece ser muy repetitivo o no contiene suficiente información. Por favor, toma una foto del documento completo, asegurándote de capturar todo el contenido.",
            "doc_type": "",
            "language": "es",
            "confidence_score": 0.0,
        }
    
    # Si pasa todas las validaciones, proceder con la clasificación
    try:
        # Inicializar el cliente de Groq
        llm = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=settings.groq_api_key,
            temperature=0.3,  # Baja temperatura para mayor precisión
        )

        # Prompt del sistema para clasificación precisa
        system_prompt = """Eres un experto en análisis de documentos legales, administrativos y comerciales.

Tu tarea es analizar el texto proporcionado y determinar con precisión:
1. El tipo de documento (contrato, multa, factura, demanda, notificación, etc.)
2. La categoría principal: LEGAL, ADMINISTRATIVO o COMERCIAL
3. El idioma del documento

Sé muy preciso y específico. Si el documento es legal, identifica el tipo exacto (contrato de arrendamiento, contrato de trabajo, etc.).
Si es administrativo, identifica si es multa, notificación gubernamental, etc.
Si es comercial, identifica si es factura, presupuesto, etc.

Responde SOLO con el tipo de documento y la categoría en este formato exacto:
TIPO: [tipo específico del documento]
CATEGORÍA: [LEGAL/ADMINISTRATIVO/COMERCIAL]
IDIOMA: [es/es-ES/en/etc]

Ejemplo:
TIPO: Contrato de arrendamiento de vivienda
CATEGORÍA: LEGAL
IDIOMA: es"""

        # Crear los mensajes
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analiza este documento:\n\n{state.get('raw_text', '')}"),
        ]

        # Llamar al modelo
        response = await llm.ainvoke(messages)
        response_text = response.content.strip()

        # Parsear la respuesta
        doc_type = "desconocido"
        language = "es"
        
        lines = response_text.split("\n")
        for line in lines:
            if line.startswith("TIPO:"):
                doc_type = line.replace("TIPO:", "").strip()
            elif line.startswith("IDIOMA:"):
                language = line.replace("IDIOMA:", "").strip().lower()

        # Actualizar el estado (sin error_message si todo está bien)
        return {
            **state,
            "doc_type": doc_type,
            "language": language,
            "error_message": "",  # Sin error si llegamos aquí
        }

    except Exception as e:
        # En caso de error en la clasificación, establecer mensaje de error
        return {
            **state,
            "error_message": "Hubo un problema al procesar el documento. Por favor, intenta tomar una foto más clara y vuelve a intentarlo.",
            "doc_type": "",
            "language": "es",
            "confidence_score": 0.0,
        }


async def quality_check_node(state: AgentState) -> AgentState:
    """
    Nodo que verifica la calidad del texto extraído.
    
    Comprueba si el raw_text tiene suficiente información para procesar.
    Si el texto es demasiado corto o ilegible, marca un flag de error.
    
    Args:
        state: Estado actual del agente con raw_text
        
    Returns:
        AgentState actualizado con confidence_score ajustado si hay problemas
    """
    raw_text = state.get("raw_text", "")
    
    # Verificar si el texto existe y tiene suficiente longitud
    text_clean = raw_text.strip() if raw_text else ""
    
    if not text_clean or len(text_clean) < MIN_TEXT_LENGTH:
        # Texto insuficiente o vacío
        return {
            **state,
            "confidence_score": 0.0,
            "doc_type": state.get("doc_type", "texto_insuficiente"),
        }
    
    # Verificar ratio de caracteres alfanuméricos vs caracteres especiales
    alphanumeric_count = sum(1 for c in text_clean if c.isalnum() or c.isspace())
    total_chars = len(text_clean)
    
    if total_chars > 0:
        alphanumeric_ratio = alphanumeric_count / total_chars
        # Si menos del 60% son alfanuméricos, probablemente es ilegible
        if alphanumeric_ratio < 0.6:
            return {
                **state,
                "confidence_score": 0.0,
                "doc_type": state.get("doc_type", "texto_ilegible"),
            }
    
    # Si pasa todas las verificaciones, mantener el confidence_score existente
    # o establecerlo a un valor por defecto si no existe
    current_confidence = state.get("confidence_score", 1.0)
    
    return {
        **state,
        "confidence_score": current_confidence if current_confidence > 0 else 1.0,
    }


async def simplify_and_analyze_node(state: AgentState) -> AgentState:
    """
    Nodo que simplifica y analiza el documento legal usando Groq 70B.
    
    Genera una explicación simplificada, identifica riesgos y sugiere acciones
    concretas usando un lenguaje empático y accesible.
    
    Args:
        state: Estado actual del agente con raw_text y doc_type
        
    Returns:
        AgentState actualizado con simplified_explanation, identified_risks y action_items
    """
    # Verificación defensiva: si hay error, retornar inmediatamente
    error_message = state.get("error_message", "")
    if error_message and error_message.strip():
        return state
    
    try:
        # Inicializar el cliente de Groq con el modelo grande para mejor razonamiento
        llm = ChatGroq(
            model=GROQ_MODEL_LARGE,
            groq_api_key=settings.groq_api_key,
            temperature=0.4,  # Temperatura ligeramente mayor para más naturalidad
        )

        # Prompt del sistema con instrucciones específicas
        system_prompt = """Eres un experto legal especializado en ayudar a ciudadanos comunes. Tu tono es empático, directo y protector.

Tu tarea es tomar el texto del documento y generar:

1. **RESUMEN (3 puntos clave)**: Explica de qué trata este documento en 3 puntos principales. Sé claro y directo.

2. **LETRA CHICA / RIESGOS**: Identifica y explica:
   - Cláusulas abusivas o desfavorables
   - Plazos importantes que vencen
   - Costos ocultos o condiciones que pueden generar gastos inesperados
   - Cualquier punto que pueda perjudicar a la persona

3. **PRÓXIMOS PASOS**: Proporciona acciones concretas que la persona debe realizar:
   - Qué debe hacer inmediatamente
   - Qué debe revisar o verificar
   - A quién debe contactar si es necesario
   - Documentos que debe preparar

**RESTRICCIÓN IMPORTANTE**: 
- No uses palabras técnicas como 'jurisprudencia', 'usufructo' o 'perentorio' sin explicarlas primero en lenguaje simple.
- Habla como si le explicaras esto a un familiar cercano que no tiene conocimientos legales.
- Sé protector y alerta sobre posibles problemas.
- Usa el idioma del documento que estás analizando.

Responde SOLO en este formato exacto:

RESUMEN:
1. [Primer punto clave]
2. [Segundo punto clave]
3. [Tercer punto clave]

LETRA CHICA / RIESGOS:
- [Riesgo o cláusula problemática 1]
- [Riesgo o cláusula problemática 2]
- [Continúa con todos los riesgos identificados]

PRÓXIMOS PASOS:
- [Acción concreta 1]
- [Acción concreta 2]
- [Continúa con todas las acciones necesarias]"""

        # Obtener el idioma del estado para adaptar el prompt
        language = state.get("language", "es")
        doc_type = state.get("doc_type", "documento")
        
        # Crear el mensaje humano con contexto
        human_message = f"""Analiza este {doc_type} y genera el resumen, riesgos y próximos pasos:

{state.get('raw_text', '')}

Recuerda: Habla en {language} y usa un lenguaje simple y empático."""

        # Crear los mensajes
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message),
        ]

        # Llamar al modelo
        response = await llm.ainvoke(messages)
        response_text = response.content.strip()

        # Parsear la respuesta
        simplified_explanation = ""
        identified_risks: list[str] = []
        action_items: list[str] = []
        
        current_section = None
        lines = response_text.split("\n")
        
        for line in lines:
            line = line.strip()
            
            # Detectar secciones
            if line.startswith("RESUMEN:"):
                current_section = "resumen"
                continue
            elif line.startswith("LETRA CHICA / RIESGOS:"):
                current_section = "riesgos"
                continue
            elif line.startswith("PRÓXIMOS PASOS:"):
                current_section = "acciones"
                continue
            
            # Procesar contenido según la sección
            if current_section == "resumen":
                if line and (line.startswith(("1.", "2.", "3.", "-", "*")) or line[0].isdigit()):
                    # Limpiar el formato de lista
                    clean_line = line.lstrip("1234567890.-* ").strip()
                    if clean_line:
                        if simplified_explanation:
                            simplified_explanation += "\n"
                        simplified_explanation += f"• {clean_line}"
            
            elif current_section == "riesgos":
                if line and (line.startswith("-") or line.startswith("*")):
                    risk = line.lstrip("-* ").strip()
                    if risk:
                        identified_risks.append(risk)
            
            elif current_section == "acciones":
                if line and (line.startswith("-") or line.startswith("*")):
                    action = line.lstrip("-* ").strip()
                    if action:
                        action_items.append(action)
        
        # Si no se pudo parsear correctamente, usar la respuesta completa como explicación
        if not simplified_explanation:
            simplified_explanation = response_text[:500]  # Limitar a 500 caracteres
        
        # Actualizar el estado (preservar el user_token para RLS)
        updated_state = {
            **state,
            "simplified_explanation": simplified_explanation,
            "identified_risks": identified_risks,
            "action_items": action_items,
            "user_token": state.get("user_token", ""),  # Preservar el token del usuario
        }
        
        # Insertar en Supabase después de generar el análisis
        try:
            # Obtener el token del usuario desde el estado
            user_token = state.get("user_token", "")
            
            # Usar cliente autenticado si tenemos token, sino usar cliente normal
            supabase = None
            if user_token:
                # Crear cliente autenticado con el token del usuario para RLS
                from app.core.supabase_client import get_authenticated_supabase_client
                supabase = get_authenticated_supabase_client(user_token)
                print(f"🔐 Usando cliente autenticado con token del usuario para RLS")
            else:
                # Usar cliente normal (service_role key debería bypass RLS)
                supabase = get_supabase_client()
                print(f"⚠ Warning: No hay token de usuario, usando cliente sin autenticación")
            
            if supabase:
                thread_id = state.get("thread_id", "")
                doc_type = state.get("doc_type", "")
                confidence_score = state.get("confidence_score", 0.0)
                language = state.get("language", "es")
                
                # Preparar los datos para insertar
                # Extraer user_id del thread_id (formato: user_{user_id}_{uuid} o user_{user_id})
                user_id_from_thread = None
                if thread_id.startswith("user_"):
                    parts = thread_id.split("_")
                    # El formato es: user_{user_id}_{uuid} o user_{user_id}
                    # user_id siempre está en la posición 1 después de "user"
                    if len(parts) >= 2:
                        user_id_from_thread = parts[1]
                
                # Si no se pudo extraer del thread_id, intentar extraer de otro formato
                if not user_id_from_thread:
                    # Si el thread_id es solo un ID simple, podría ser el user_id
                    # Pero mejor intentar extraer de cualquier formato posible
                    print(f"⚠ Warning: No se pudo extraer user_id del thread_id: {thread_id}")
                
                analysis_data = {
                    "thread_id": thread_id,
                    "user_id": user_id_from_thread,  # user_id es obligatorio para RLS
                    "doc_type": doc_type,
                    "simplified_explanation": simplified_explanation,
                    "identified_risks": identified_risks,
                    "action_items": action_items,
                    "confidence_score": confidence_score,
                    "language": language,
                }
                
                # Limitar raw_text a 1000 caracteres si es muy largo
                raw_text = state.get("raw_text", "")
                if raw_text:
                    analysis_data["raw_text"] = raw_text[:1000] if len(raw_text) > 1000 else raw_text
                
                # Log para verificar el user_id antes de insertar
                print(f"Insertando para el usuario: {user_id_from_thread}")
                print(f"Thread ID: {thread_id}")
                print(f"Datos a insertar (sin raw_text): { {k: v for k, v in analysis_data.items() if k != 'raw_text'} }")
                
                # Verificar que user_id no sea None antes de insertar
                if not user_id_from_thread:
                    print("⚠ Error: user_id es None, no se puede insertar debido a RLS")
                    raise ValueError("user_id no puede ser None para insertar en user_analyses con RLS habilitado")
                
                # Insertar en la tabla user_analyses
                supabase.table("user_analyses").insert(analysis_data).execute()
        except Exception as db_error:
            # No fallar el nodo si hay error en la base de datos, solo loguear
            # En producción, podrías usar un logger aquí
            print(f"Error al insertar en Supabase: {str(db_error)}")
        
        return updated_state

    except Exception as e:
        # En caso de error, mantener el estado pero con valores por defecto
        return {
            **state,
            "simplified_explanation": "Error al procesar el documento. Por favor, intenta nuevamente.",
            "identified_risks": ["No se pudieron identificar riesgos debido a un error en el procesamiento."],
            "action_items": ["Contacta con soporte técnico si el problema persiste."],
            "confidence_score": 0.0,
        }
