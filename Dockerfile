# Dockerfile optimizado para Coolify
FROM python:3.11-slim

# Variables de entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install --no-install-recommends -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar uv usando el comando oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración de dependencias
COPY pyproject.toml ./
# Copiar uv.lock si existe (el wildcard no falla si no existe)
COPY uv.lock* ./

# Sincronizar dependencias usando uv
# Si existe uv.lock, usar --frozen para builds reproducibles
# Si no existe, uv sync generará uno y sincronizará
RUN uv sync --frozen 2>/dev/null || uv sync

# Copiar el código de la aplicación
COPY ./app ./app
COPY ./tests ./tests

# Exponer el puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
