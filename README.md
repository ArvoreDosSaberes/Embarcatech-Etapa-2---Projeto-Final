# Rack Inteligente Workspace

![visitors](https://visitor-badge.laobi.icu/badge?page_id=ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final)
[![Build](https://img.shields.io/github/actions/workflow/status/ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final/ci.yml?branch=main)](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/actions)
[![Issues](https://img.shields.io/github/issues/ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final)](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/issues)
[![Stars](https://img.shields.io/github/stars/ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final)](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/stargazers)
[![Forks](https://img.shields.io/github/forks/ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final)](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/network/members)
[![Language](https://img.shields.io/badge/Language-C%2FC%2B%2B-brightgreen.svg)]()
[![AI Assisted](https://img.shields.io/badge/AI-Assisted-purple.svg)]()
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
![C++](https://img.shields.io/badge/C%2B%2B-17-blue)
![CMake](https://img.shields.io/badge/CMake-%3E%3D3.16-informational)
[![Docs](https://img.shields.io/badge/docs-Doxygen-blueviolet)](docs/index.html)
[![Latest Release](https://img.shields.io/github/v/release/ArvoreDosSaberes.Embarcatech-Etapa-2---Projeto-Final?label=version)](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/releases/latest)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-success.svg)](#contribuindo)

MVP para o projeto Embarcatech, o Rack Inteligente é um sistema IoT para Racks de Redes de Computadores. Ele monitora o Rack quanto a questões ambientais (temperatura, umidade) e segurança (porta, inclinação), alertando uma central através do protocolo MQTT na borda, que recebe subscrição de um servidor na nuvem que centraliza a gestão dos racks.

---

## 📋 Índice

1. [Pré-requisitos](#-pré-requisitos)
2. [Clonagem do Repositório](#-clonagem-do-repositório)
3. [Configuração do Ambiente Python](#-configuração-do-ambiente-python)
4. [Instalação do Granite TSF](#-instalação-do-granite-tsf)
5. [Configuração de Variáveis de Ambiente](#%EF%B8%8F-configuração-de-variáveis-de-ambiente)
6. [Compilação do Firmware](#-compilação-do-firmware)
7. [Gravação no RP2040](#-gravação-no-rp2040)
8. [Configuração no VSCode/Windsurf](#-configuração-no-vscodewindsurf)
9. [Softwares Relevantes](#-softwares-relevantes)

---

## 🔧 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado:

### Sistema Operacional
- **Linux** (Ubuntu 20.04+ recomendado) ou **Windows 10/11**
- **macOS** 10.15+ (Catalina ou superior)

### Ferramentas de Desenvolvimento

| Ferramenta | Versão Mínima | Descrição |
|------------|---------------|-----------|
| **Git** | 2.30+ | Controle de versão |
| **Python** | 3.10+ | Runtime para dashboard e serviços |
| **CMake** | 3.16+ | Sistema de build para firmware |
| **GCC ARM** | 10.3+ | Compilador para RP2040 |
| **Pico SDK** | 2.1.1 | SDK da Raspberry Pi Pico |
| **picotool** | 2.1.1 | Ferramenta para flash do RP2040 |

### Instalação das Ferramentas no Linux (Ubuntu/Debian)

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y git cmake build-essential python3 python3-pip python3-venv

# Instalar ARM toolchain
sudo apt install -y gcc-arm-none-eabi libnewlib-arm-none-eabi

# Instalar dependências do PyQt5 (para o dashboard)
sudo apt install -y libxcb-xinerama0 libxkbcommon-x11-0 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
    libxcb-shape0 qtbase5-dev
```

---

## 📥 Clonagem do Repositório

O repositório utiliza **submódulos Git** para organizar os componentes. É necessário clonar recursivamente.

### Opção 1: Clonagem via SSH (recomendado)

```bash
git clone --recursive git@github.com:ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final.git
cd Embarcatech-Etapa-2---Projeto-Final
```

### Opção 2: Clonagem via HTTPS

```bash
git clone --recursive https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final.git
cd Embarcatech-Etapa-2---Projeto-Final
```

### Caso já tenha clonado sem `--recursive`

```bash
cd Embarcatech-Etapa-2---Projeto-Final
git submodule update --init --recursive
```

### Verificando os submódulos

Após a clonagem, verifique se todos os submódulos estão presentes:

```bash
git submodule status
```

Você deve ver os seguintes submódulos:
- `dashboard/` - Interface de monitoramento (PyQt5)
- `firmware/` - Firmware para RP2040/Pico W
- `FreeRTOS-Kernel/` - Kernel FreeRTOS
- `Keyboard-Menu---workspace/` - Biblioteca de menu para teclado matricial

---

## 🐍 Configuração do Ambiente Python

O projeto utiliza um ambiente virtual Python único na raiz do workspace.

### 1. Criar o ambiente virtual

```bash
# Na raiz do projeto
python3 -m venv venv
```

### 2. Ativar o ambiente virtual

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

### 3. Atualizar pip e instalar dependências base

```bash
pip install --upgrade pip setuptools wheel

# Instalar dependências do workspace principal
pip install -r requirements.txt
```

### 4. Instalar dependências do Dashboard

```bash
pip install -r dashboard/requirements.txt
```

---

## 🔮 Instalação do Granite TSF

O **Granite Time Series Forecasting** é o serviço de previsão de séries temporais que utiliza o modelo IBM Granite TTM-R2.

### 1. Instalar dependências do Granite TSF

```bash
# Com o venv ativado
pip install -r Granite-Time-Series-Forecasting-Python/requirements.txt
```

### 2. Instalar o modelo IBM Granite TTM-R2

Execute o script de instalação fornecido:

```bash
cd Granite-Time-Series-Forecasting-Python
bash install_granite.sh
cd ..
```

O script irá:
- Instalar PyTorch (versão CPU por padrão)
- Instalar transformers
- Baixar e instalar o modelo Granite do repositório IBM

### 3. Verificar a instalação

```bash
python -c "
try:
    from tsfm_public import TimeSeriesForecastingPipeline, TinyTimeMixerForPrediction
    print('✅ Granite TTM-R2 disponível!')
except ImportError:
    print('⚠️  Granite TTM-R2 não disponível - usando modelo alternativo (SARIMA)')
"
```

> **Nota**: Caso o Granite não esteja disponível, o sistema utilizará automaticamente o modelo SARIMA (statsmodels) como fallback.

### 4. Configurar o serviço Granite TSF

```bash
cd Granite-Time-Series-Forecasting-Python
cp .env.example .env
# Edite o arquivo .env conforme necessário
cd ..
```

---

## ⚙️ Configuração de Variáveis de Ambiente

### 1. Criar arquivo `.env` a partir do exemplo

```bash
cp env.example .env
```

### 2. Editar o arquivo `.env`

Abra o arquivo `.env` e configure as seguintes variáveis:

#### Configuração WiFi (Firmware)
```ini
WIFI_SSID="SuaRedeWiFi"
WIFI_PASSWORD="SuaSenhaWiFi"
```

#### Configuração MQTT
```ini
MQTT_SERVER=mqtt.seu-servidor.com
MQTT_PORT=1883
MQTT_USERNAME=usuario
MQTT_PASSWORD=senha_segura
MQTT_KEEPALIVE=60
MQTT_BASE_TOPIC=racks/
MQTT_CLIENT_ID="Rack Inteligente"
MQTT_RACK_NUMBER="PICOW001"
```

#### Configuração de IA Generativa (opcional)
```ini
GENAI_API_KEY=sua-chave-api-aqui
GENAI_URL=generativa.rapport.tec.br/api/v1
GENAI_MODEL=granite4:3b
```

### 3. Criar arquivo `env.cmake` para o firmware

O firmware também requer um arquivo `env.cmake` na raiz do projeto:

```bash
# Criar arquivo env.cmake
cat > env.cmake << 'EOF'
# ===========================================
# Configurações do Firmware - env.cmake
# ===========================================

set(ENV{WIFI_SSID} "SuaRedeWiFi")
set(ENV{WIFI_PASSWORD} "SuaSenhaWiFi")

set(ENV{MQTT_BROKER} "mqtt.seu-servidor.com")
set(ENV{MQTT_PORT} "1883")
set(ENV{MQTT_USERNAME} "usuario")
set(ENV{MQTT_PASSWORD} "senha_segura")
set(ENV{MQTT_CLIENT_ID} "Rack Inteligente")
set(ENV{MQTT_BASE_TOPIC} "racks")
set(ENV{MQTT_RACK_NUMBER} "PICOW001")

# Nível de log: -1=OFF, 0=CRITICAL, 1=ERROR, 2=WARNING, 3=INFO
set(ENV{LOG_LEVEL} "3")
EOF
```

> **⚠️ Importante**: Os arquivos `.env` e `env.cmake` contêm credenciais sensíveis e estão no `.gitignore`.

---

## 🔨 Compilação do Firmware

O firmware é desenvolvido para **Raspberry Pi Pico W** utilizando o **Pico SDK** e **FreeRTOS**.

### Pré-requisitos do Pico SDK

#### Opção 1: Instalação via Extensão VSCode/Windsurf (Recomendado)

A extensão **Raspberry Pi Pico** instala automaticamente o SDK. Veja a seção [Configuração no VSCode/Windsurf](#-configuração-no-vscodewindsurf).

#### Opção 2: Instalação Manual

```bash
# Definir diretório do SDK
export PICO_SDK_PATH=$HOME/pico-sdk

# Clonar o SDK
git clone -b 2.1.1 https://github.com/raspberrypi/pico-sdk.git $PICO_SDK_PATH
cd $PICO_SDK_PATH
git submodule update --init

# Voltar ao projeto
cd -
```

### Compilação via Linha de Comando

```bash
# Criar diretório de build
cd firmware
mkdir -p build
cd build

# Configurar o projeto com CMake
cmake .. -DPICO_BOARD=pico_w

# Compilar
make -j$(nproc)

# Voltar à raiz
cd ../..
```

Após a compilação, o arquivo `rack_inteligente.uf2` estará em `firmware/build/`.

### Compilação via VSCode/Windsurf

1. Abra a pasta `firmware/` como workspace
2. Pressione `Ctrl+Shift+P` → **CMake: Configure**
3. Selecione o kit **Pico ARM GCC**
4. Pressione `F7` ou **CMake: Build** para compilar

---

## 📤 Gravação no RP2040

### Método 1: BOOTSEL (Modo UF2)

1. **Desconecte** a Pico W do USB
2. **Pressione e segure** o botão **BOOTSEL**
3. **Conecte** o cabo USB mantendo o botão pressionado
4. **Solte** o botão - a Pico aparecerá como dispositivo de armazenamento USB
5. **Copie** o arquivo `firmware/build/rack_inteligente.uf2` para o dispositivo

```bash
# No Linux, o dispositivo geralmente monta em /media/$USER/RPI-RP2
cp firmware/build/rack_inteligente.uf2 /media/$USER/RPI-RP2/
```

### Método 2: picotool (via SWD ou USB)

```bash
# Instalar picotool (se não instalado)
sudo apt install picotool

# Gravar firmware
picotool load firmware/build/rack_inteligente.uf2 -f

# Reiniciar a placa
picotool reboot
```

### Método 3: Via VSCode/Windsurf

1. Conecte a Pico W em modo BOOTSEL
2. Pressione `Ctrl+Shift+P` → **Raspberry Pi Pico: Flash**
3. Selecione o arquivo `.uf2` gerado

---

## 💻 Configuração no VSCode/Windsurf

### Extensões Essenciais

| Extensão | ID | Descrição |
|----------|-----|-----------|
| **Raspberry Pi Pico** | `raspberry-pi.raspberry-pi-pico` | Suporte completo ao Pico SDK |
| **C/C++** | `ms-vscode.cpptools` | IntelliSense e debugging C/C++ |
| **CMake Tools** | `ms-vscode.cmake-tools` | Integração com CMake |
| **Python** | `ms-python.python` | Suporte Python |
| **Pylance** | `ms-python.vscode-pylance` | IntelliSense avançado para Python |

### Extensões Recomendadas

| Extensão | ID | Descrição |
|----------|-----|-----------|
| **Cortex-Debug** | `marus25.cortex-debug` | Debug para ARM Cortex-M |
| **Serial Monitor** | `ms-vscode.vscode-serial-monitor` | Monitor serial integrado |
| **GitLens** | `eamodio.gitlens` | Melhorias para Git |
| **Error Lens** | `usernamehw.errorlens` | Exibe erros inline |
| **Todo Tree** | `Gruntfuggly.todo-tree` | Gerenciador de TODOs |

### Instalação das Extensões (Linha de Comando)

```bash
# Extensões essenciais
code --install-extension raspberry-pi.raspberry-pi-pico
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cmake-tools
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance

# Extensões recomendadas
code --install-extension marus25.cortex-debug
code --install-extension ms-vscode.vscode-serial-monitor
code --install-extension eamodio.gitlens
```

### Configuração do Workspace

Ao abrir o projeto, o VSCode/Windsurf solicitará:

1. **Selecionar Kit CMake**: Escolha **Pico ARM GCC**
2. **Configurar Python Interpreter**: Selecione `./venv/bin/python`

### Arquivo `settings.json` Recomendado

Crie ou edite `.vscode/settings.json`:

```json
{
    "cmake.configureOnOpen": true,
    "cmake.buildDirectory": "${workspaceFolder}/firmware/build",
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "files.associations": {
        "*.h": "c",
        "*.hpp": "cpp"
    },
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools"
}
```

---

## 🛠️ Softwares Relevantes

| Software | Descrição | Link |
|----------|-----------|------|
| **MQTTX** | Cliente MQTT GUI para testes | [mqttx.app](https://mqttx.app/) |
| **PuTTY** | Terminal serial (Windows) | [putty.org](https://www.putty.org/) |
| **minicom** | Terminal serial (Linux) | `sudo apt install minicom` |
| **Wireshark** | Análise de pacotes de rede | [wireshark.org](https://www.wireshark.org/) |

### Monitoramento Serial

```bash
# Linux (minicom)
minicom -D /dev/ttyACM0 -b 115200

# Linux (screen)
screen /dev/ttyACM0 115200
```

---

## 📚 Estrutura do Projeto

```
Embarcatech-Etapa-2---Projeto-Final/
├── dashboard/                      # Interface PyQt5 (submódulo)
│   ├── app.py                      # Aplicação principal
│   ├── services/                   # Serviços de negócio
│   └── requirements.txt
├── firmware/                       # Firmware RP2040 (submódulo)
│   ├── CMakeLists.txt              # Build system
│   ├── rack_inteligente.cpp        # Código principal
│   ├── tasks/                      # Tarefas FreeRTOS
│   └── FreeRTOS-Kernel/            # Kernel FreeRTOS
├── Granite-Time-Series-Forecasting-Python/  # Serviço de previsão
│   ├── app.py                      # Servidor Flask
│   ├── src/services/               # Serviços de ML
│   └── install_granite.sh          # Script de instalação
├── docs/                           # Documentação do projeto
├── simulador/                      # Simulador MQTT
├── .env                            # Variáveis de ambiente (gitignored)
├── env.cmake                       # Variáveis para CMake (gitignored)
├── env.example                     # Template de configuração
├── requirements.txt                # Dependências Python (raiz)
└── README.md                       # Este arquivo
```

---

## 🚀 Execução do Sistema Completo

### 1. Iniciar o Serviço Granite TSF (opcional)

```bash
source venv/bin/activate
cd Granite-Time-Series-Forecasting-Python
python app.py
# Acesse: http://localhost:5000
```

### 2. Iniciar o Dashboard

```bash
source venv/bin/activate
cd dashboard
python app.py
```

### 3. Gravar e executar o Firmware

Após gravar o firmware na Pico W, ela iniciará automaticamente e se conectará ao broker MQTT.

### 4. Simulador MQTT (para testes sem hardware)

```bash
source venv/bin/activate
cd simulador
python mqtt_simulator.py
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está licenciado sob a licença **CC BY 4.0**. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📞 Suporte

Para problemas ou dúvidas, abra uma [issue](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final/issues) no repositório.
