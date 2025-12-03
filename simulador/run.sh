#!/bin/bash

###############################################################################
# Run Script for MQTT Telemetry Simulator
# Description: Quick start script for the MQTT simulator application
# Author: EmbarcaTech Project
###############################################################################

set -e  # Exit on error

# Resolve script directory and project root (parent of simulador)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Graceful shutdown on interruption
cleanup() {
    echo "\n[simulador/run] Simulador interrompido pelo usuário. Encerrando com segurança... 🚫"
    exit 1
}

trap cleanup INT TERM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emojis
ROCKET="🚀"
CROSS="❌"
INFO="ℹ️"

echo -e "${BLUE}${ROCKET} Starting MQTT Telemetry Simulator...${NC}"
echo ""

# Check if virtual environment exists in project root
if [ ! -d "${PROJECT_ROOT}/venv" ]; then
    echo -e "${CROSS} ${RED}Virtual environment not found in project root!${NC}"
    echo -e "${INFO} Please run the dashboard setup.sh first (or create the venv manually):"
    echo "   cd \"${PROJECT_ROOT}/dashboard\" && ./setup.sh"
    exit 1
fi

# Check if .env exists in project root (workspace)
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${CROSS} ${RED}.env file not found in project root (workspace)!${NC}"
    echo -e "${INFO} The simulator expects MQTT settings in ${PROJECT_ROOT}/.env."
    echo "   cd \"${PROJECT_ROOT}\""
    echo "   cp .env.example .env   # ou copie de dashboard/.env.example se for compartilhado"
    echo "   nano .env"
    exit 1
fi

# Activate virtual environment from project root and run simulator from its directory
cd "${SCRIPT_DIR}"
source "${PROJECT_ROOT}/venv/bin/activate"

echo -e "${INFO} Virtual environment activated. Running mqtt_simulator.py...${NC}"
python mqtt_simulator.py "$@"
