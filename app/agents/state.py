"""Definición del estado del agente usando TypedDict para LangGraph."""

from typing import TypedDict, List


class AgentState(TypedDict):
    """
    Estado del agente que actúa como única fuente de verdad en el flujo de LangGraph.
    
    Este estado se pasa entre nodos del grafo y contiene toda la información
    necesaria para el procesamiento y análisis de documentos legales.
    """
    
    raw_text: str
    """Texto bruto extraído del OCR o del documento procesado."""
    
    doc_type: str
    """Categoría detectada del documento (contrato, multa, factura, etc.)."""
    
    simplified_explanation: str
    """Versión simplificada y fácil de entender para el usuario final."""
    
    identified_risks: List[str]
    """Lista de cláusulas o puntos peligrosos identificados en el documento."""
    
    action_items: List[str]
    """Lista de acciones que el usuario debe realizar a continuación."""
    
    confidence_score: float
    """Puntuación de confianza del agente sobre su análisis (0.0 a 1.0)."""
    
    language: str
    """Idioma detectado del documento para asegurar respuestas en el mismo idioma."""
    
    error_message: str
    """Mensaje de error si el procesamiento falla. Vacío si no hay error."""
    
    thread_id: str
    """ID del thread/conversación para identificar la sesión del usuario."""
    
    user_token: str
    """Token JWT del usuario autenticado para RLS en Supabase. Vacío si no está disponible."""
