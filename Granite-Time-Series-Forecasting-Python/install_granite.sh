#!/bin/bash

###############################################################################
# 🚀 Script de Instalação do IBM Granite TTM-R2
# 
# Este script instala o modelo Granite Time Series diretamente do GitHub
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
print_message "$BLUE" "  🔮 Instalando IBM Granite Time Series Model"
print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
echo ""

# Verificar se está no ambiente virtual
if [ -z "$VIRTUAL_ENV" ]; then
    print_message "$YELLOW" "⚠️  [Warning] Ambiente virtual não detectado"
    print_message "$BLUE" "🔌 [Setup] Ativando ambiente virtual..."
    source venv/bin/activate
fi

print_message "$GREEN" "✅ [OK] Ambiente virtual ativo: $VIRTUAL_ENV"
echo ""

# Instalar dependências base primeiro
print_message "$BLUE" "📦 [Install] Instalando dependências base..."
pip install -q --upgrade pip setuptools wheel

print_message "$BLUE" "📦 [Install] Instalando PyTorch (pode demorar)..."
# Granite requer torch<2.9
pip install 'torch<2.9' torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

print_message "$BLUE" "📦 [Install] Instalando transformers e dependências..."
pip install 'transformers>=4.35.0,<4.57'

# Tentar instalar tsfm_public do GitHub
print_message "$BLUE" "📦 [Install] Tentando instalar granite-tsfm do GitHub..."
echo ""

# Opção 1: Repositório oficial IBM
if pip install git+https://github.com/ibm-granite/granite-tsfm.git@main 2>/dev/null; then
    print_message "$GREEN" "✅ [OK] granite-tsfm instalado com sucesso!"
else
    print_message "$YELLOW" "⚠️  [Warning] Não foi possível instalar do repositório oficial"
    
    # Opção 2: Tentar repositório alternativo
    print_message "$BLUE" "📦 [Install] Tentando repositório alternativo..."
    if pip install git+https://github.com/IBM/tsfm.git 2>/dev/null; then
        print_message "$GREEN" "✅ [OK] tsfm instalado com sucesso!"
    else
        print_message "$RED" "❌ [Error] Não foi possível instalar o modelo Granite"
        print_message "$YELLOW" "💡 [Tip] O sistema funcionará com modelo alternativo (statsmodels)"
    fi
fi

echo ""
print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
print_message "$GREEN" "  ✅ Instalação concluída!"
print_message "$BLUE" "═══════════════════════════════════════════════════════════════"
echo ""

# Verificar instalação
print_message "$BLUE" "🔍   [Check] Verificando instalação..."
python -c "
try:
    from tsfm_public import TimeSeriesForecastingPipeline, TinyTimeMixerForPrediction
    print('✅ Granite TTM-R2 disponível!')
except ImportError:
    print('⚠️  Granite TTM-R2 não disponível - usando modelo alternativo')
" || true

echo ""
print_message "$GREEN" "🚀 Pronto para usar! Execute: python app.py"
