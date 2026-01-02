# Tutorial: Compilação e Gravação do Firmware no RP2040

Este tutorial explica passo a passo como configurar o ambiente, compilar o firmware do projeto **Rack Inteligente** e gravá-lo no microcontrolador **RP2040** (Raspberry Pi Pico W).

---

## Sumário

1. [Pré-requisitos](#1-pré-requisitos)
2. [Instalação do Ambiente](#2-instalação-do-ambiente)
3. [Configuração do Projeto](#3-configuração-do-projeto)
4. [Compilação do Firmware](#4-compilação-do-firmware)
5. [Gravação no RP2040](#5-gravação-no-rp2040)
6. [Verificação e Depuração](#6-verificação-e-depuração)
7. [Resolução de Problemas](#7-resolução-de-problemas)

---

## 1. Pré-requisitos

### Hardware Necessário

- **Raspberry Pi Pico W** (RP2040 com módulo WiFi CYW43439)
- Cabo USB micro-B para conexão com o computador
- (Opcional) Adaptador UART para depuração serial

### Software Necessário

| Software | Versão Mínima | Descrição |
|----------|---------------|-----------|
| CMake | 3.13+ | Sistema de build |
| ARM GCC Toolchain | 14.2 | Compilador para ARM Cortex-M0+ |
| Pico SDK | 2.1.1 | SDK oficial da Raspberry Pi |
| Git | 2.0+ | Controle de versão |
| picotool | 2.1.1 | Ferramenta de gravação e diagnóstico |

---

## 2. Instalação do Ambiente

### 2.1 Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependências básicas
sudo apt update
sudo apt install -y cmake gcc-arm-none-eabi libnewlib-arm-none-eabi \
    build-essential git libstdc++-arm-none-eabi-newlib

# 2. Clonar o Pico SDK (caso não use a extensão do VS Code)
cd ~
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init

# 3. Configurar variável de ambiente
echo 'export PICO_SDK_PATH=~/pico-sdk' >> ~/.bashrc
source ~/.bashrc
```

### 2.2 Usando a Extensão Raspberry Pi Pico (VS Code) - **Recomendado**

A forma mais simples é utilizar a extensão oficial:

1. Abra o **VS Code**
2. Vá em **Extensions** (Ctrl+Shift+X)
3. Pesquise por **"Raspberry Pi Pico"**
4. Instale a extensão oficial da Raspberry Pi
5. A extensão instalará automaticamente:
   - Pico SDK 2.1.1
   - ARM Toolchain 14.2
   - picotool 2.1.1
   - CMake e Ninja

Os arquivos são instalados em: `~/.pico-sdk/`

### 2.3 Windows

1. Baixe e instale o **Pico Setup for Windows** do site oficial:
   - https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html
2. Ou use a extensão do VS Code (recomendado)

---

## 3. Configuração do Projeto

### 3.1 Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd Projeto_Final
git submodule update --init --recursive
```

### 3.2 Criar o Arquivo de Configuração `env.cmake`

O projeto requer um arquivo `env.cmake` na **raiz do projeto** com as variáveis de configuração. Este arquivo **não está no repositório** por motivos de segurança.

1. Crie o arquivo `env.cmake` na raiz do projeto:

```bash
touch env.cmake
```

2. Adicione o seguinte conteúdo (ajuste com seus dados):

```cmake
# ===========================================
# Configuração do Firmware - env.cmake
# ===========================================

# WiFi
set(ENV{WIFI_SSID} "SuaRedeWiFi")
set(ENV{WIFI_PASSWORD} "SuaSenhaWiFi")

# MQTT Broker (OBRIGATÓRIO)
set(ENV{MQTT_BROKER} "mqtt.seu-servidor.com")
set(ENV{MQTT_PORT} "1883")
set(ENV{MQTT_USERNAME} "seu_usuario")
set(ENV{MQTT_PASSWORD} "sua_senha")

# MQTT Client
set(ENV{MQTT_CLIENT_ID} "Rack Inteligente")
set(ENV{MQTT_BASE_TOPIC} "racks")
set(ENV{MQTT_RACK_NUMBER} "001")

# Log Level: -1=OFF, 0=ERROR, 1=WARN, 2=INFO, 3=DEBUG
set(ENV{LOG_LEVEL} "2")

# Análise RTOS (opcional, para debug)
# set(ENV{ENABLE_RTOS_ANALYSIS} "1")
# set(ENV{ENABLE_STACK_WATERMARK} "1")
```

### 3.3 Variáveis Obrigatórias

| Variável | Descrição |
|----------|-----------|
| `WIFI_SSID` | Nome da rede WiFi |
| `WIFI_PASSWORD` | Senha da rede WiFi |
| `MQTT_BROKER` | Endereço do broker MQTT |
| `MQTT_USERNAME` | Usuário do broker MQTT |
| `MQTT_PASSWORD` | Senha do broker MQTT |
| `MQTT_RACK_NUMBER` | Identificador único do rack |

---

## 4. Compilação do Firmware

### 4.1 Criar Diretório de Build

```bash
cd firmware
mkdir -p build
cd build
```

### 4.2 Configurar o CMake

```bash
cmake ..
```

**Saída esperada:**
```
-- Arquivo env.cmake carregado com sucesso.
-- WIFI_SSID: SuaRedeWiFi
-- MQTT_BROKER: mqtt.seu-servidor.com
-- LOG_LEVEL: 2
-- Build files have been written to: .../firmware/build
```

### 4.3 Compilar o Projeto

```bash
make -j$(nproc)
```

Ou usando Ninja (mais rápido):

```bash
cmake -G Ninja ..
ninja
```

### 4.4 Arquivos Gerados

Após a compilação bem-sucedida, os seguintes arquivos são gerados em `firmware/build/`:

| Arquivo | Descrição |
|---------|-----------|
| `rack_inteligente.uf2` | Firmware para gravação via USB (modo BOOTSEL) |
| `rack_inteligente.elf` | Binário com símbolos para debug |
| `rack_inteligente.bin` | Binário puro |
| `rack_inteligente.hex` | Formato Intel HEX |

---

## 5. Gravação no RP2040

### 5.1 Método 1: Modo BOOTSEL (USB Mass Storage)

Este é o método mais simples e não requer software adicional.

1. **Desconecte** o Pico W do USB (se estiver conectado)

2. **Pressione e segure** o botão **BOOTSEL** na placa

3. **Conecte** o cabo USB ao computador **mantendo o botão pressionado**

4. **Solte** o botão BOOTSEL após conectar

5. O Pico aparecerá como um **dispositivo de armazenamento USB** chamado `RPI-RP2`

6. **Copie** o arquivo `.uf2` para o dispositivo:

```bash
# Linux
cp firmware/build/rack_inteligente.uf2 /media/$USER/RPI-RP2/

# Ou arraste o arquivo para a unidade RPI-RP2 no gerenciador de arquivos
```

7. O Pico **reiniciará automaticamente** e executará o firmware

### 5.2 Método 2: Usando picotool (Recomendado para Desenvolvimento)

O `picotool` permite gravar sem entrar manualmente no modo BOOTSEL.

```bash
# Gravar o firmware (força modo BOOTSEL via software)
picotool load firmware/build/rack_inteligente.uf2 -f

# Reiniciar o dispositivo após gravação
picotool reboot
```

**Opções úteis:**

```bash
# Verificar informações do firmware atual
picotool info

# Gravar e reiniciar em um comando
picotool load firmware/build/rack_inteligente.uf2 -f -x

# Verificar se o arquivo é válido antes de gravar
picotool verify firmware/build/rack_inteligente.uf2
```

### 5.3 Método 3: Debug via SWD (Avançado)

Para depuração em tempo real com GDB:

1. Conecte um **Raspberry Pi Debug Probe** ou outro adaptador SWD

2. Inicie o OpenOCD:
```bash
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg
```

3. Em outro terminal, inicie o GDB:
```bash
arm-none-eabi-gdb firmware/build/rack_inteligente.elf
(gdb) target remote localhost:3333
(gdb) load
(gdb) monitor reset init
(gdb) continue
```

---

## 6. Verificação e Depuração

### 6.1 Monitorar Saída Serial (USB CDC)

O firmware está configurado para saída via **USB CDC** (serial sobre USB).

**Linux:**
```bash
# Identificar a porta serial
ls /dev/ttyACM*

# Conectar usando minicom
minicom -D /dev/ttyACM0 -b 115200

# Ou usando screen
screen /dev/ttyACM0 115200

# Ou usando picocom
picocom -b 115200 /dev/ttyACM0
```

**Permissões (Linux):**
```bash
# Adicionar usuário ao grupo dialout para acesso à serial
sudo usermod -a -G dialout $USER
# Reiniciar a sessão para aplicar
```

### 6.2 Verificar Conexão WiFi e MQTT

Após a gravação, observe os logs no terminal serial:

```
[INFO] WiFi: Conectando a SuaRedeWiFi...
[INFO] WiFi: Conectado! IP: 192.168.1.100
[INFO] MQTT: Conectando ao broker mqtt.seu-servidor.com:1883...
[INFO] MQTT: Conexão estabelecida!
```

### 6.3 Verificar Informações do Firmware

```bash
picotool info -a
```

Saída esperada:
```
Program Information
 name:          rack_inteligente
 version:       0.5
 features:      USB stdin / stdout
 binary start:  0x10000000
 binary end:    0x100xxxxx
```

---

## 7. Resolução de Problemas

### 7.1 Erro: "Arquivo env.cmake não encontrado!"

**Causa:** O arquivo `env.cmake` não existe na raiz do projeto.

**Solução:** Crie o arquivo conforme a seção [3.2](#32-criar-o-arquivo-de-configuração-envcmake).

### 7.2 Erro: "Variável MQTT_USERNAME não definida"

**Causa:** Variável obrigatória faltando no `env.cmake`.

**Solução:** Adicione todas as variáveis obrigatórias no `env.cmake`.

### 7.3 Dispositivo RPI-RP2 não aparece

**Causas possíveis:**
1. Botão BOOTSEL não foi pressionado corretamente
2. Cabo USB com defeito ou apenas para carga (sem dados)
3. Firmware corrompido travando o boot

**Soluções:**
1. Tente novamente pressionando BOOTSEL **antes** de conectar
2. Use outro cabo USB de dados
3. Use o comando `picotool reboot -f -u` para forçar modo BOOTSEL

### 7.4 Erro de compilação: "arm-none-eabi-gcc not found"

**Causa:** Toolchain ARM não está instalado ou não está no PATH.

**Solução:**
```bash
# Ubuntu/Debian
sudo apt install gcc-arm-none-eabi

# Ou verifique se a extensão do VS Code instalou em ~/.pico-sdk
export PATH="$HOME/.pico-sdk/toolchain/14_2_Rel1/bin:$PATH"
```

### 7.5 Sem saída no terminal serial

**Verificações:**
1. Confirme que `pico_enable_stdio_usb` está como `1` no CMakeLists.txt
2. Verifique se a porta serial correta está sendo usada
3. Aguarde alguns segundos após a conexão (o USB CDC demora para inicializar)

### 7.6 WiFi não conecta

**Verificações:**
1. Confirme SSID e senha no `env.cmake`
2. Verifique se a rede é 2.4GHz (Pico W não suporta 5GHz)
3. Aproxime o dispositivo do roteador

---

## Referências

- [Raspberry Pi Pico SDK Documentation](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html)
- [Getting Started with Pico W](https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf)
- [FreeRTOS on RP2040](https://www.freertos.org/Documentation/02-Kernel/02-Kernel-porting-guide/01-Supported-devices/11-Raspberry-Pi-Pico)
- [picotool GitHub](https://github.com/raspberrypi/picotool)

---

**Tempo estimado:** 15-30 minutos para primeira configuração; 2-5 minutos para compilação e gravação subsequentes.
