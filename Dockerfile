# Dockerfile optimizado para Coolify con multi-stage build
# Stage 1: Builder - Instalar dependencias
FROM python:3.11-slim AS builder

# Variables de entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Instalar dependencias del sistema necesarias (al principio para aprovechar caché)
RUN apt-get update && apt-get install --no-install-recommends -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instalar uv usando el comando oficial (solo copiar el ejecutable)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración de dependencias
COPY pyproject.toml ./
COPY uv.lock* ./

# Sincronizar dependencias usando uv con --no-cache para ahorrar espacio
# Si existe uv.lock, usar --frozen para builds reproducibles
RUN uv sync --frozen --no-cache 2>/dev/null || uv sync --no-cache

# Stage 2: Runtime - Imagen final ligera
FROM python:3.11-slim

# Variables de entorno para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/app/.venv/bin:$PATH"

# Instalar solo dependencias de runtime del sistema (sin dev dependencies)
RUN apt-get update && apt-get install --no-install-recommends -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar el ejecutable uv desde el builder (no reinstalar)
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el entorno virtual desde el builder
COPY --from=builder /app/.venv /app/.venv

# Copiar archivos de configuración
COPY pyproject.toml ./
COPY uv.lock* ./

# Copiar el código de la aplicación
COPY ./app ./app
COPY ./tests ./tests

# Exponer el puerto
EXPOSE 8000

# Comando de inicio usando el venv
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
