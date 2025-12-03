#!/bin/bash

###############################################################################
# 🚀 Granite Time Series Forecasting - Startup Script
# 
# Este script facilita a inicialização do sistema de previsão de séries
# temporais. Ele verifica dependências, configura o ambiente e inicia o servidor.
###############################################################################

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$PURPLE" "═══════════════════════════════════════════════════════════════"
    print_message "$PURPLE" "  🔮 Granite Time Series Forecasting System"
    print_message "$PURPLE" "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Verificar Python
check_python() {
    print_message "$BLUE" "🔍 [Check] Verificando instalação do Python..."
    
    if ! command -v python &> /dev/null; then
        print_message "$RED" "❌ [Error] Python  não encontrado!"
        print_message "$YELLOW" "💡 [Tip] Instale Python + antes de continuar"
        exit 1
    fi
    
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    print_message "$GREEN" "✅ [OK] Python $PYTHON_VERSION encontrado"
}

# Verificar/Criar ambiente virtual
setup_venv() {
    print_message "$BLUE" "🔍 [Check] Verificando ambiente virtual..."
    
    if [ ! -d "venv" ]; then
        print_message "$YELLOW" "⚠️  [Warning] Ambiente virtual não encontrado"
        print_message "$BLUE" "📦 [Setup] Criando ambiente virtual..."
        python -m venv venv
        print_message "$GREEN" "✅ [OK] Ambiente virtual criado"
    else
        print_message "$GREEN" "✅ [OK] Ambiente virtual encontrado"
    fi
}

# Ativar ambiente virtual
activate_venv() {
    print_message "$BLUE" "🔌 [Setup] Ativando ambiente virtual..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_message "$GREEN" "✅ [OK] Ambiente virtual ativado"
    else
        print_message "$RED" "❌ [Error] Não foi possível ativar o ambiente virtual"
        exit 1
    fi
}

# Instalar dependências
install_dependencies() {
    print_message "$BLUE" "📦 [Setup] Verificando dependências..."
    
    if [ ! -f "requirements.txt" ]; then
        print_message "$RED" "❌ [Error] Arquivo requirements.txt não encontrado"
        exit 1
    fi
    
    print_message "$BLUE" "⏳ [Setup] Instalando dependências (isso pode levar alguns minutos)..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    print_message "$GREEN" "✅ [OK] Dependências instaladas"
}

# Verificar arquivo .env
check_env() {
    print_message "$BLUE" "🔍 [Check] Verificando configuração..."
    
    if [ ! -f ".env" ]; then
        print_message "$YELLOW" "⚠️  [Warning] Arquivo .env não encontrado"
        
        if [ -f ".env.example" ]; then
            print_message "$BLUE" "📋 [Setup] Criando .env a partir de .env.example..."
            cp .env.example .env
            print_message "$GREEN" "✅ [OK] Arquivo .env criado"
            print_message "$YELLOW" "💡 [Tip] Edite o arquivo .env para ajustar configurações"
        else
            print_message "$RED" "❌ [Error] .env.example não encontrado"
            exit 1
        fi
    else
        print_message "$GREEN" "✅ [OK] Arquivo .env encontrado"
    fi
}

# Verificar GPU (opcional)
check_gpu() {
    print_message "$BLUE" "🔍 [Check] Verificando disponibilidade de GPU..."
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
        print_message "$GREEN" "✅ [OK] GPU detectada: $GPU_INFO"
        print_message "$GREEN" "🚀 [Info] O modelo usará aceleração GPU"
    else
        print_message "$YELLOW" "⚠️  [Warning] GPU não detectada"
        print_message "$BLUE" "ℹ️  [Info] O modelo usará CPU (mais lento)"
    fi
}

# Iniciar servidor
start_server() {
    print_message "$BLUE" "🚀 [Start] Iniciando servidor..."
    echo ""
    print_message "$GREEN" "═══════════════════════════════════════════════════════════════"
    print_message "$GREEN" "  ✅ Sistema pronto!"
    print_message "$GREEN" "  🌐 Acesse: http://localhost:5000"
    print_message "$GREEN" "  ⌨️  Pressione Ctrl+C para parar"
    print_message "$GREEN" "═══════════════════════════════════════════════════════════════"
    echo ""
    
    python app.py
}

# Função principal
main() {
    print_header
    
    check_python
    setup_venv
    activate_venv
    install_dependencies
    check_env
    check_gpu
    
    echo ""
    start_server
}

# Executar
main
