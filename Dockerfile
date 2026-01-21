# Stage 1: Builder (Preparamos las dependencias de Python)
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Optimizaciones de UV para Docker
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Instalamos dependencias primero (Caché de capas)
# Copiamos solo lo necesario para resolver el entorno
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Runtime (Imagen final que correrá en tu VPS)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Instalamos dependencias de sistema (Tesseract + Librerías de imagen)
# Esto solo se ejecuta una vez y se queda en caché
RUN apt-get update && apt-get install --no-install-recommends -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiamos el entorno virtual (ya listo con las librerías) desde el builder
COPY --from=builder /app/.venv /app/.venv

# Copiamos el código de la aplicación
COPY . .

# Exponer puerto de FastAPI
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]