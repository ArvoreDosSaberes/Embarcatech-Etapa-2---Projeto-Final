#!/bin/bash
# =============================================================================
# Script para geração de documentação Doxygen
# Projeto Rack Inteligente - EmbarcaTech TIC-27
# =============================================================================

set -e  # Sai em caso de erro

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Geração de Documentação Doxygen          ${NC}"
echo -e "${BLUE}  Projeto Rack Inteligente                 ${NC}"
echo -e "${BLUE}============================================${NC}"

# Verifica se Doxygen está instalado
if ! command -v doxygen &> /dev/null; then
    echo -e "${RED}[ERRO] Doxygen não está instalado.${NC}"
    echo -e "${YELLOW}Instale com: sudo apt install doxygen graphviz${NC}"
    exit 1
fi

# Verifica se Graphviz está instalado (para gráficos)
if ! command -v dot &> /dev/null; then
    echo -e "${YELLOW}[AVISO] Graphviz não está instalado. Gráficos não serão gerados.${NC}"
    echo -e "${YELLOW}Instale com: sudo apt install graphviz${NC}"
fi

# Função para gerar documentação de um projeto
generate_docs() {
    local project_name="$1"
    local project_dir="$2"
    
    if [ ! -f "$project_dir/Doxyfile" ]; then
        echo -e "${YELLOW}[AVISO] Doxyfile não encontrado em $project_dir${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}[INFO] Gerando documentação: $project_name${NC}"
    echo -e "       Diretório: $project_dir"
    
    # Cria diretório de saída se não existir
    mkdir -p "$project_dir/docs/doxygen"
    
    # Executa Doxygen
    cd "$project_dir"
    doxygen Doxyfile 2>&1 | grep -E "(Generating|warning:|error:)" || true
    
    # Verifica se foi gerado
    if [ -f "$project_dir/docs/doxygen/html/index.html" ]; then
        echo -e "${GREEN}[OK] Documentação gerada com sucesso!${NC}"
        echo -e "     Abra: $project_dir/docs/doxygen/html/index.html"
    else
        echo -e "${RED}[ERRO] Falha ao gerar documentação${NC}"
        return 1
    fi
    
    return 0
}

# Gera documentação para cada projeto
echo ""

# Dashboard (Python)
generate_docs "Dashboard" "$PROJECT_ROOT/dashboard" || true

# Firmware (C/C++)
generate_docs "Firmware" "$PROJECT_ROOT/firmware" || true

# Simulador (Python)
generate_docs "Simulador" "$PROJECT_ROOT/simulador" || true

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}  Documentação gerada com sucesso!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Para visualizar a documentação, abra os arquivos index.html:"
echo -e "  - ${YELLOW}dashboard/docs/doxygen/html/index.html${NC}"
echo -e "  - ${YELLOW}firmware/docs/doxygen/html/index.html${NC}"
echo -e "  - ${YELLOW}simulador/docs/doxygen/html/index.html${NC}"
echo ""
