"""Definición y compilación del grafo de LangGraph."""

from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.nodes import extract_and_classify_node, simplify_and_analyze_node
from app.core.checkpointer import get_checkpointer


def should_continue(state: AgentState) -> str:
    """
    Función condicional que determina si el grafo debe continuar o terminar.
    
    Si hay un error_message, termina inmediatamente sin procesar más.
    Si no hay error, continúa con el análisis.
    
    Args:
        state: Estado actual del agente
        
    Returns:
        "end" si hay error, "continue" si debe continuar
    """
    error_message = state.get("error_message", "")
    if error_message and error_message.strip():
        return "end"
    return "continue"


# Crear el StateGraph usando AgentState
workflow = StateGraph(AgentState)

# Agregar los nodos al grafo
workflow.add_node("extract_and_classify", extract_and_classify_node)
workflow.add_node("simplify_and_analyze", simplify_and_analyze_node)

# Definir el flujo: START -> extract_and_classify_node -> (condicional) -> simplify_and_analyze_node -> END
workflow.set_entry_point("extract_and_classify")

# Después de extract_and_classify, verificar si hay error
workflow.add_conditional_edges(
    "extract_and_classify",
    should_continue,
    {
        "end": END,  # Terminar si hay error
        "continue": "simplify_and_analyze",  # Continuar si no hay error
    }
)

# Si no hay error, continuar con simplify_and_analyze y luego terminar
workflow.add_edge("simplify_and_analyze", END)


async def compile_graph():
    """
    Compila el grafo con el PostgresSaver (checkpointer) para persistencia.
    
    Esta función debe llamarse al inicio de la aplicación después de
    inicializar el checkpointer.
    
    Returns:
        Grafo compilado con persistencia
    """
    # Obtener el checkpointer (PostgresSaver)
    checkpointer = await get_checkpointer()
    
    # Compilar el grafo con el checkpointer para persistencia
    if checkpointer:
        compiled_graph = workflow.compile(checkpointer=checkpointer)
    else:
        # Fallback: compilar sin persistencia si no hay checkpointer
        compiled_graph = workflow.compile()
    
    return compiled_graph


# Variable global para almacenar el grafo compilado
graph = None
