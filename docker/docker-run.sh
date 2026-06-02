#!/bin/bash
# docker-run.sh - Script para facilitar la ejecución con Docker

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🐳 Sistema de Búsqueda Musical - Docker${NC}"
echo -e "${GREEN}========================================${NC}"

# Función para mostrar ayuda
show_help() {
    echo -e "Uso: $0 [comando]"
    echo ""
    echo "Comandos:"
    echo "  build       - Construir la imagen Docker"
    echo "  run         - Ejecutar el contenedor (CPU)"
    echo "  run-gpu     - Ejecutar con soporte GPU"
    echo "  dev         - Ejecutar en modo desarrollo (hot-reload)"
    echo "  stop        - Detener el contenedor"
    echo "  logs        - Ver logs del contenedor"
    echo "  shell       - Abrir shell dentro del contenedor"
    echo "  clean       - Limpiar contenedores e imágenes"
    echo "  download-model - Descargar modelo Qwen2.5"
    echo "  help        - Mostrar esta ayuda"
}

# Construir imagen
build() {
    echo -e "${YELLOW}🔨 Construyendo imagen Docker...${NC}"
    docker-compose build
    echo -e "${GREEN}✅ Imagen construida exitosamente${NC}"
}

# Ejecutar modo CPU
run() {
    echo -e "${YELLOW}🚀 Ejecutando contenedor (CPU)...${NC}"
    echo -e "${YELLOW}   Accede a: http://localhost:5000${NC}"
    docker-compose up music-search
}

# Ejecutar modo GPU
run_gpu() {
    echo -e "${YELLOW}🚀 Ejecutando contenedor con GPU...${NC}"
    echo -e "${YELLOW}   Accede a: http://localhost:5001${NC}"
    docker-compose up music-search-gpu
}

# Modo desarrollo
dev() {
    echo -e "${YELLOW}🔧 Ejecutando en modo desarrollo...${NC}"
    echo -e "${YELLOW}   Hot-reload activado${NC}"
    echo -e "${YELLOW}   Accede a: http://localhost:5002${NC}"
    docker-compose up music-search-dev
}

# Detener contenedores
stop() {
    echo -e "${YELLOW}🛑 Deteniendo contenedores...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Contenedores detenidos${NC}"
}

# Ver logs
logs() {
    docker-compose logs -f --tail=100
}

# Abrir shell
shell() {
    echo -e "${YELLOW}📟 Abriendo shell en el contenedor...${NC}"
    docker-compose exec music-search /bin/bash
}

# Limpiar
clean() {
    echo -e "${RED}⚠️  Esto eliminará contenedores e imágenes${NC}"
    read -p "¿Estás seguro? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker rmi sri-music-search:latest 2>/dev/null || true
        echo -e "${GREEN}✅ Limpieza completada${NC}"
    else
        echo -e "${YELLOW}Operación cancelada${NC}"
    fi
}

# Descargar modelo Qwen2.5
download_model() {
    echo -e "${YELLOW}📥 Descargando modelo Qwen2.5-3B...${NC}"
    mkdir -p models
    cd models
    if [ ! -f "qwen2.5-3b-instruct-q4_k_m.gguf" ]; then
        wget -q --show-progress \
            https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf
        echo -e "${GREEN}✅ Modelo descargado${NC}"
    else
        echo -e "${GREEN}✅ Modelo ya existe${NC}"
    fi
    cd ..
}

# Main
case "${1:-help}" in
    build) build ;;
    run) run ;;
    run-gpu) run_gpu ;;
    dev) dev ;;
    stop) stop ;;
    logs) logs ;;
    shell) shell ;;
    clean) clean ;;
    download-model) download_model ;;
    help|*) show_help ;;
esac