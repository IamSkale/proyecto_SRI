#!/bin/bash
# entrypoint.sh - Script de entrada para el contenedor Docker

set -e

echo "=========================================="
echo "🎵 Sistema de Búsqueda Musical con RAG"
echo "=========================================="
echo "Fecha: $(date)"
echo "Python: $(python --version)"
echo "Directorio de trabajo: $(pwd)"
echo "=========================================="

# Verificar si existe el índice, si no, crearlo
if [ ! -f "indice_musica.json" ]; then
    echo "📂 No se encontró índice. Ejecutando indexación inicial..."
    python -c "
from Indexer.indexer import IndexadorTFIDF
indexador = IndexadorTFIDF('Database', 'Database/lyrics')
indexador.ejecutar_indexacion('indice_musica.json')
print('✅ Indexación completada')
"
else
    echo "✅ Índice encontrado: indice_musica.json"
fi

# Verificar modelo de RAG (opcional)
if [ ! -f "models/qwen2.5-3b-instruct-q4_k_m.gguf" ]; then
    echo "⚠️ Modelo Qwen2.5 no encontrado en /app/models/"
    echo "   El RAG usará modo fallback."
    echo "   Para descargar el modelo:"
    echo "   mkdir -p models && cd models"
    echo "   wget https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
else
    echo "✅ Modelo Qwen2.5 encontrado"
fi

# Crear directorios necesarios
mkdir -p logs data

echo "=========================================="
echo "🚀 Iniciando servidor Flask..."
echo "   URL: http://localhost:5000"
echo "=========================================="

# Ejecutar el comando recibido
exec "$@"