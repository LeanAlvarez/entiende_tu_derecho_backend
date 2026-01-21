"""Servicio de OCR para extraer texto de imágenes usando Pytesseract."""

import io
from typing import Optional

from fastapi import UploadFile, HTTPException
from PIL import Image
import pytesseract


async def extract_text_from_image(file: UploadFile) -> str:
    """
    Extrae texto de una imagen usando OCR (Pytesseract).
    
    Args:
        file: Archivo de imagen subido (UploadFile)
        
    Returns:
        Texto extraído de la imagen
        
    Raises:
        HTTPException: Si el archivo no es una imagen válida o hay error en OCR
    """
    try:
        # Leer el contenido del archivo
        contents = await file.read()
        
        # Verificar que sea una imagen
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo no es una imagen válida: {str(e)}"
            )
        
        # Convertir a RGB si es necesario (para imágenes con transparencia)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Extraer texto usando Pytesseract
        # Configurar para español e inglés
        text = pytesseract.image_to_string(
            image,
            lang="spa+eng",  # Español e inglés
        )
        
        # Limpiar el texto (eliminar espacios extra)
        text = text.strip()
        
        if not text:
            raise HTTPException(
                status_code=400,
                detail="No se pudo extraer texto de la imagen. Asegúrate de que la imagen contenga texto legible."
            )
        
        return text
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la imagen con OCR: {str(e)}"
        )
