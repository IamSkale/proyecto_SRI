# Dockerfile para Sistema de Búsqueda Musical con RAG
# Imagen base: Python 3.10 con soporte para CPU y GPU

FROM python:3.10-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    USE_GPU=false

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Para compilar algunas dependencias Python
    gcc \
    g++ \
    make \
    # Para procesamiento de texto
    curl \
    wget \
    # Para beautifulsoup y scraping
    ca-certificates \
    # Limpiar caché para reducir tamaño de imagen
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache

# Copiar archivo de dependencias primero (mejor caché)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/models \
    && mkdir -p /app/Database/lyrics \
    && mkdir -p /app/templates \
    && mkdir -p /app/static \
    && mkdir -p /app/Indexer \
    && mkdir -p /app/rag \
    && mkdir -p /app/data

# Copiar código fuente
COPY . /app/

# Copiar script de entrada y dar permisos de ejecución
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponer puerto de Flask
EXPOSE 5000

# Script de entrada
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto
CMD ["python", "app.py"]