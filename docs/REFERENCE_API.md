# Referência Técnica da API

Documentação completa das funções, macros e variáveis do projeto Rack Inteligente - EmbarcaTech TIC-27.

---

## 📁 Estrutura do Projeto

```
Projeto_Final/
├── dashboard/           # Dashboard PyQt5 com IA
│   ├── app.py           # Aplicação principal
│   └── services/        # Serviços de negócio
├── firmware/            # Firmware ESP32/RP2040
│   ├── rack_inteligente.cpp  # Ponto de entrada
│   ├── inc/             # Headers do projeto
│   ├── lib/             # Bibliotecas
│   └── tasks/           # Tasks FreeRTOS
├── simulador/           # Simulador MQTT
└── scripts/             # Scripts auxiliares
```

---

# 🐍 Códigos Python

## Dashboard - `dashboard/app.py`

### Classe `MainWindow`

Janela principal do dashboard com interface moderna PyQt5.

#### Sinais

| Sinal | Parâmetros | Descrição |
|-------|------------|-----------|
| `message_received` | `dict` | Emitido quando uma mensagem MQTT é recebida |
| `action_executed` | `str, str` | Emitido quando uma ação AI é executada (rackId, action) |
| `status_updated` | `str, str, str` | Emitido para atualizar barra de status (rackId, action, reason) |

#### Atributos de Instância

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `current_rack_id` | `str` | ID do rack atualmente selecionado |
| `currentRack` | `Rack` | Instância do rack selecionado |
| `racks` | `dict[str, Rack]` | Dicionário de racks (rackId → Rack) |
| `rack_states` | `dict` | Cache de estados dos racks |
| `rackControlService` | `RackControlService` | Serviço de controle via MQTT |
| `toolCallingService` | `ToolCallingService` | Serviço de IA para decisões |
| `forecastService` | `ForecastService` | Serviço de previsão de séries temporais |
| `history_limit` | `int` | Limite de pontos de histórico (7 dias * 3600s) |
| `forecast_horizon` | `int` | Horizonte de previsão em horas (24h) |
| `base_topic` | `str` | Tópico MQTT base (da variável `MQTT_BASE_TOPIC`) |

#### Métodos Principais

```python
def setup_ui(self) -> None
```
Configura a interface gráfica com design moderno UX.

```python
def setup_mqtt(self) -> None
```
Configura cliente MQTT e inicia conexão com o broker.

```python
def handle_message_update(self, data: dict) -> None
```
Processa mensagens MQTT recebidas e atualiza a UI na thread principal.
- **Parâmetros**:
  - `data`: Dicionário com `topic` e `payload`

```python
def sample_current_state(self) -> None
```
Amostra periodicamente a telemetria para preencher gráficos de histórico.

```python
def update_metric_forecast(self, state: dict, metric: str) -> None
```
Calcula previsão para a métrica usando ForecastService.
- **Parâmetros**:
  - `state`: Estado do rack
  - `metric`: Nome da métrica ('temperature' ou 'humidity')

```python
@pyqtSlot(str)
def selectRackFromMap(self, rack_id: str) -> None
```
Callback JavaScript quando rack é clicado no mapa.

```python
def generate_all_racks_map_html(self, selected_rack_id: str = None) -> str
```
Gera HTML do mapa Leaflet/OpenStreetMap com todos os racks.

---

## Serviço de Controle - `dashboard/services/rackControlService.py`

### Enums

#### `DoorStatus(IntEnum)`
| Valor | Nome | Descrição |
|-------|------|-----------|
| 0 | `CLOSED` | Porta fechada |
| 1 | `OPEN` | Porta aberta |

#### `VentilationStatus(IntEnum)`
| Valor | Nome | Descrição |
|-------|------|-----------|
| 0 | `OFF` | Ventilação desligada |
| 1 | `ON` | Ventilação ligada |

#### `BuzzerStatus(IntEnum)`
| Valor | Nome | Descrição |
|-------|------|-----------|
| 0 | `OFF` | Buzzer desligado |
| 1 | `DOOR_OPEN` | Alerta de porta aberta |
| 2 | `BREAK_IN` | Alerta de arrombamento |
| 3 | `OVERHEAT` | Alerta de superaquecimento |

### Classe `Rack`

Representa um rack físico no sistema.

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rackId` | `str` | Identificador único do rack |
| `temperature` | `Optional[float]` | Temperatura atual em °C |
| `humidity` | `Optional[float]` | Umidade relativa em % |
| `doorStatus` | `DoorStatus` | Status da porta |
| `ventilationStatus` | `VentilationStatus` | Status da ventilação |
| `buzzerStatus` | `BuzzerStatus` | Status do alarme sonoro |
| `latitude` | `Optional[float]` | Coordenada de latitude |
| `longitude` | `Optional[float]` | Coordenada de longitude |

#### Métodos

```python
def isDoorOpen(self) -> bool
```
Retorna `True` se a porta está aberta.

```python
def isVentilationOn(self) -> bool
```
Retorna `True` se a ventilação está ligada.

```python
def isBuzzerActive(self) -> bool
```
Retorna `True` se o buzzer está ativo (qualquer estado exceto OFF).

### Classe `PendingCommand`

Representa um comando pendente aguardando ACK.

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rackId` | `str` | ID do rack alvo |
| `commandType` | `str` | Tipo de comando (door, ventilation, buzzer) |
| `value` | `int` | Valor enviado |
| `timestamp` | `float` | Momento do envio |
| `callback` | `Optional[Callable]` | Callback ao receber ACK |

### Classe `RackControlService`

Serviço de controle de racks via MQTT com confirmação de comandos.

#### Constantes

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `DEFAULT_COMMAND_TIMEOUT` | `5.0` | Timeout para ACK em segundos |

#### Métodos de Controle

```python
def openDoor(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Abre a porta do rack. Estado NÃO é atualizado até receber ACK.

```python
def closeDoor(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Fecha a porta do rack. Estado NÃO é atualizado até receber ACK.

```python
def toggleDoor(self, rack: Rack) -> bool
```
Alterna estado da porta.

```python
def turnOnVentilation(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Liga a ventilação do rack.

```python
def turnOffVentilation(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Desliga a ventilação do rack.

```python
def toggleVentilation(self, rack: Rack) -> bool
```
Alterna estado da ventilação.

```python
def activateCriticalTemperatureAlert(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Ativa alerta de superaquecimento (buzzer = 3).

```python
def deactivateCriticalTemperatureAlert(self, rack: Rack, callback: Optional[Callable[[bool], None]] = None) -> bool
```
Desativa alerta de temperatura crítica.

```python
def processAck(self, rackId: str, commandType: str, value: int) -> bool
```
Processa confirmação (ACK) recebida do firmware.

```python
def getExpiredCommands(self) -> list
```
Retorna lista de comandos que expiraram sem ACK.

---

## Serviço de Previsão - `dashboard/services/forecastService.py`

### Variáveis de Módulo

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `GRANITE_AVAILABLE` | `bool` | Indica se IBM Granite TTM-R2 está disponível |

### Classe `ForecastService`

Serviço de previsão de séries temporais com arquitetura híbrida (Granite + SARIMA).

#### Parâmetros do Construtor

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `model_name` | `str` | `"ibm-granite/granite-timeseries-ttm-r2"` | Nome do modelo |
| `forecast_horizon` | `int` | `24` | Passos de previsão (horas) |
| `context_length` | `int` | `168` | Tamanho do histórico (7 dias) |

#### Atributos

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `sarimaFallback` | `SarimaFallbackService` | Serviço de fallback SARIMA |
| `maeThreshold` | `float` | Limiar de MAE para ativar fallback |
| `currentMae` | `float` | MAE atual do modelo principal |
| `useFallback` | `bool` | Se está usando fallback |
| `sampleInterval` | `int` | Intervalo de agregação (segundos) |
| `enableAnnualSeasonality` | `bool` | Habilita sazonalidade anual |

#### Métodos

```python
def predict(
    self, 
    data_history: List[Dict], 
    aggregateData: bool = True,
    exogenousData: Optional[List[Dict]] = None
) -> Optional[Dict]
```
Realiza previsão de valores futuros para as próximas 24 horas.

- **Parâmetros**:
  - `data_history`: Histórico de dados (mínimo 10 pontos)
  - `aggregateData`: Se True, agrega dados por hora
  - `exogenousData`: Dados exógenos (ex: umidade)
  
- **Retorno**: Dicionário com previsões ou None se erro

```python
def aggregateHourlyData(self, data_history: List[Dict]) -> List[Dict]
```
Converte amostras de alta frequência em médias horárias.

```python
def addAnnualSeasonalComponent(self, predictions: List[float], baseTimestamp: datetime) -> List[float]
```
Adiciona componente de sazonalidade anual às previsões.

```python
def applyHumidityCorrection(
    self, 
    tempPredictions: List[float], 
    humidityHistory: List[Dict],
    baseTimestamp: datetime
) -> List[float]
```
Aplica correção de umidade às previsões de temperatura.

```python
def updateMaeTracking(self, predicted: float, actual: float) -> float
```
Atualiza tracking de MAE e decide sobre fallback.

```python
def stop(self) -> None
```
Para o serviço graciosamente (suporte a Ctrl+C).

```python
def start(self) -> None
```
Inicia/reinicia o serviço.

---

## Serviço SARIMA Fallback - `dashboard/services/sarimaFallbackService.py`

### Classe `SarimaConfig`

Configuração dos parâmetros SARIMA(p, d, q)(P, D, Q)_s.

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `p` | `int` | `1` | Ordem AR não sazonal |
| `d` | `int` | `1` | Diferenciações não sazonais |
| `q` | `int` | `1` | Ordem MA não sazonal |
| `P` | `int` | `1` | Ordem AR sazonal |
| `D` | `int` | `1` | Diferenciações sazonais |
| `Q` | `int` | `0` | Ordem MA sazonal |
| `s` | `int` | `24` | Período da sazonalidade |
| `maeThreshold` | `float` | `5.0` | Limiar de MAE |
| `maeWindowSize` | `int` | `50` | Janela para cálculo de MAE |
| `autoSelectParams` | `bool` | `True` | Detecta parâmetros automaticamente |

### Classe `ForecastResult`

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `predictions` | `List[float]` | Valores previstos |
| `timestamps` | `List[str]` | Timestamps correspondentes |
| `mae` | `Optional[float]` | MAE calculado |
| `modelUsed` | `str` | Nome do modelo |
| `isFromFallback` | `bool` | Se veio do fallback |
| `confidence` | `float` | Nível de confiança (0-1) |

### Classe `SarimaFallbackService`

#### Métodos

```python
def forecast(self, dataHistory: List[Dict], steps: int = 10) -> Optional[ForecastResult]
```
Realiza previsão SARIMA.

```python
def calculateMae(self, predictions: List[float], actuals: List[float]) -> float
```
Calcula Mean Absolute Error (MAE).

```python
def shouldUseFallback(self, graniteMae: Optional[float] = None) -> bool
```
Verifica se fallback deve ser ativado.

```python
def getModelInfo(self) -> Dict
```
Retorna informações do modelo e estado.

---

## Serviço de Tool Calling - `dashboard/services/toolCallingService.py`

### Classe `RackAction`

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rackId` | `str` | ID do rack alvo |
| `function` | `str` | Nome da função a executar |
| `reason` | `str` | Motivo da ação |

### Classe `RackTelemetry`

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rackId` | `str` | Identificador do rack |
| `temperature` | `Optional[float]` | Temperatura atual em °C |
| `humidity` | `Optional[float]` | Umidade em % |
| `doorStatus` | `int` | Status da porta (0=fechada, 1=aberta) |
| `ventilationStatus` | `int` | Status da ventilação |
| `buzzerStatus` | `int` | Status do buzzer (0-3) |
| `tempAvg` | `Optional[float]` | Média de temperatura da última hora |
| `tempTrend` | `Optional[float]` | Tendência de temperatura (°C/min) |
| `humAvg` | `Optional[float]` | Média de umidade da última hora |
| `humTrend` | `Optional[float]` | Tendência de umidade (%/min) |

### Classe `ThresholdConfig`

Configuração de limiares com histerese (Schmitt Trigger).

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `tempHighThreshold` | `float` | `35.0` | Temperatura para ligar ventilação |
| `tempLowThreshold` | `float` | `28.0` | Temperatura para desligar ventilação |
| `tempCriticalThreshold` | `float` | `45.0` | Temperatura crítica |
| `tempCriticalReset` | `float` | `40.0` | Reset de alerta crítico |
| `humHighThreshold` | `float` | `80.0` | Umidade alta |
| `humLowThreshold` | `float` | `60.0` | Umidade baixa |

### Classe `ToolCallingService`

#### Constantes

```python
AVAILABLE_FUNCTIONS = {
    'turnOnVentilation',
    'turnOffVentilation',
    'activateCriticalTemperatureAlert',
    'deactivateCriticalTemperatureAlert',
    'activateDoorOpenAlert',
    'activateBreakInAlert',
    'silenceBuzzer',
    'openDoor',
    'closeDoor'
}
```

#### Métodos

```python
def updateTelemetry(self, rackId: str, telemetry: Dict[str, Any]) -> None
```
Atualiza dados de telemetria no buffer e histórico.

```python
def analyzeAndExecute(self, racksDict: Dict[str, Any]) -> List[RackAction]
```
Analisa telemetria e executa ações via LLM (Tool Calling nativo).

```python
def callLlmWithTools(self, telemetryList: List[RackTelemetry]) -> List[RackAction]
```
Chama LLM usando Tool Calling nativo da OpenAI.

```python
def loadPrompt(self, promptName: str) -> str
```
Carrega prompt do arquivo na pasta `prompts/`.

---

## Detector de Anomalias - `dashboard/services/anomalyDetector.py`

### Classe `AnomalyDetector`

Detecta anomalias em séries temporais usando Z-score.

#### Parâmetros do Construtor

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `threshold_multiplier` | `float` | `3.0` | Múltiplo de σ para anomalia |
| `window_size` | `int` | `50` | Tamanho da janela |
| `rolling_window_seconds` | `int \| None` | `None` | Janela de tempo em segundos |

#### Métodos

```python
def detect(self, current_value: float, data_history: List[Dict]) -> Tuple[bool, Dict]
```
Detecta se o valor atual é uma anomalia.

- **Retorno**: Tupla `(is_anomaly, info)` onde `info` contém:
  - `value`: Valor atual
  - `mean`: Média da janela
  - `stdev`: Desvio padrão
  - `zscore`: Z-score calculado
  - `severity`: 'normal', 'medium', 'high', 'critical'

```python
def get_anomaly_rate(self, recent_count: int = 100) -> float
```
Calcula taxa de anomalias recentes.

```python
def adjust_sensitivity(self, new_threshold: float) -> None
```
Ajusta sensibilidade do detector.

---

## Simulador MQTT - `simulador/mqtt_simulator.py`

### Variáveis de Módulo

```python
FORTALEZA_COORDINATES: list[Tuple[float, float]]
```
Coordenadas fixas de locais em Fortaleza-CE para atribuir aos racks.

### Classe `RackState`

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `rack_id` | `str` | Identificador do rack |
| `status` | `int` | Estado da porta (0=fechada, 1=aberta) |
| `temperature` | `float` | Temperatura simulada |
| `humidity` | `float` | Umidade simulada |
| `latitude` | `float` | Coordenada latitude |
| `longitude` | `float` | Coordenada longitude |
| `ventilation_status` | `int` | Estado da ventilação |
| `temperature_anomaly` | `Optional[Dict]` | Dados de anomalia térmica |
| `humidity_anomaly` | `Optional[Dict]` | Dados de anomalia de umidade |

### Classe `TelemetryPublisher`

Publicador MQTT para envio de leituras.

```python
def publish(self, topic: str, payload: str) -> None
```
Envia leitura para o broker MQTT.

### Classe `RackSimulator`

Gera e publica telemetria de um rack.

#### Métodos

```python
async def run(self) -> None
```
Executa ciclo assíncrono de geração de telemetria.

```python
def enqueue_command(self, command: str, payload: str) -> None
```
Enfileira comandos vindos do broker MQTT.

```python
def publish_location(self) -> None
```
Publica coordenadas GPS do rack.

### Funções de Módulo

```python
def log_message(sector: str, rack_id: str, message: str, emoji: str) -> None
```
Exibe mensagens padronizadas no console.

```python
def load_mqtt_client() -> mqtt.Client
```
Configura e retorna cliente MQTT baseado em variáveis de ambiente.

```python
def generate_rack_ids(amount: int = 10, reset: bool = False) -> list[str]
```
Gera identificadores únicos para racks com persistência SQLite.

```python
async def run_simulation(reset: bool = False) -> None
```
Inicializa recursos e executa simulação.

---

## Script de Conversão PDF - `scripts/convert_md_to_pdf.py`

### Constantes

```python
PDF_STYLES: str       # Estilos CSS para PDF padrão
ABNT_PDF_STYLES: str  # Estilos CSS para PDF formato ABNT
ROOT_DIR: Path        # Diretório raiz do projeto
DEFAULT_SOURCE: Path  # Diretório fonte padrão (docs/)
DEFAULT_OUTPUT: Path  # Diretório de saída padrão (docs.temp/)
```

### Classes

#### `StandardPdfRenderer`
Renderiza PDFs com estilo padrão.

#### `AbntPdfRenderer`
Renderiza PDFs no formato ABNT com capa e metadados.

### Funções

```python
def parse_front_matter(markdown_text: str) -> tuple[dict, str]
```
Extrai front matter YAML e corpo do markdown.

```python
def convert_markdown_file(
    markdown_file: Path,
    output_dir: Path,
    root: Path,
    *,
    renderer: PdfRenderer
) -> Path
```
Converte um arquivo markdown para PDF.

```python
def main(argv: Sequence[str] | None = None) -> int
```
Ponto de entrada com suporte a argumentos de linha de comando.

---

# 🔧 Códigos C/C++ (Firmware)

## Arquivo Principal - `firmware/rack_inteligente.cpp`

### Variáveis Globais

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `i2c` | `I2C` | Objeto I2C para comunicação com sensores |
| `environment` | `environment_t` | Dados ambientais do rack |
| `mqtt_connected` | `bool` | Estado da conexão MQTT |
| `mqtt_client` | `mqtt_client_t*` | Cliente MQTT |
| `mqtt_rack_topic` | `char[50]` | Tópico MQTT do rack |
| `rack_name` | `char[50]` | Nome/ID do rack |

### Funções

```c
int main(void)
```
Função principal: inicializa Wi-Fi, MQTT, cria tasks FreeRTOS e inicia o scheduler.

```c
static void inpub_cb(void *arg, const char *topic, u32_t tot_len)
```
Callback para identificar tópico MQTT recebido.

```c
static void indata_cb(void *arg, const u8_t *data, u16_t len, u8_t flags)
```
Callback para processar dados da mensagem MQTT recebida.

```c
static void subscribeToCommandTopics(mqtt_client_t *client)
```
Subscreve aos tópicos de comando MQTT após conexão.

```c
static void mqtt_connection_callback(mqtt_client_t *client, void *arg, mqtt_connection_status_t status)
```
Callback de conexão MQTT - inicializa módulo de comandos.

```c
void dns_check_callback(const char *name, const ip_addr_t *ipaddr, void *callback_arg)
```
Callback de resolução DNS do broker MQTT.

```c
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
```
Hook FreeRTOS para stack overflow.

### Funções Legadas

```c
static inline void openDoor()
```
Abre porta via servo (delega para `doorServoOpen`).

```c
static inline void closeDoor()
```
Fecha porta via servo (delega para `doorServoClose`).

```c
static inline void turnOnAlarm()
```
Ativa alarme via PWM (delega para `buzzerPwmSetState`).

```c
static inline void turnOffAlarm()
```
Desativa alarme via PWM (delega para `buzzerPwmOff`).

---

## Header Principal - `firmware/inc/rack_inteligente.h`

### Macros

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `RACK_DOOR_OPEN` | `true` | Porta aberta |
| `RACK_DOOR_CLOSED` | `false` | Porta fechada |

### Estruturas

#### `gps_position_t`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `latitude` | `float` | Latitude |
| `longitude` | `float` | Longitude |
| `altitude` | `float` | Altitude |
| `time` | `uint32_t` | Timestamp GPS |
| `speed` | `float` | Velocidade |

#### `environment_t`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `temperature` | `float` | Temperatura em °C |
| `humidity` | `float` | Umidade em % |
| `door` | `bool` | Estado da porta |
| `tilt` | `bool` | Estado de inclinação |
| `gps_position` | `gps_position_t` | Posição GPS |

---

## Parâmetros - `firmware/inc/rack_inteligente_parametros.h`

### Macros Obrigatórias (definidas via CMake)

| Macro | Descrição |
|-------|-----------|
| `WIFI_SSID` | Nome da rede Wi-Fi |
| `WIFI_PASSWORD` | Senha da rede Wi-Fi |
| `MQTT_BROKER` | Endereço do broker MQTT |
| `MQTT_PORT` | Porta do broker MQTT |
| `MQTT_CLIENT_ID` | ID do cliente MQTT |
| `MQTT_USERNAME` | Usuário MQTT |
| `MQTT_PASSWORD` | Senha MQTT |
| `MQTT_BASE_TOPIC` | Tópico base MQTT |
| `MQTT_RACK_NUMBER` | Número/ID do rack |

### Macros de Pinos GPIO

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `LEDG` | `11` | LED verde |
| `LEDB` | `12` | LED azul |
| `LEDR` | `13` | LED vermelho |
| `I2C_SDA_PIN` | `0` | Pino SDA I2C |
| `I2C_SCL_PIN` | `1` | Pino SCL I2C |
| `RACK_DOOR_STATE_PIN` | `5` | Pino de estado da porta (entrada) |
| `RACK_DOOR_LOCK_PIN` | `2` | Pino da trava/servo da porta (saída) |
| `RACK_ALARM_PIN` | `10` | Pino do buzzer |
| `RACK_VENTILATOR_PIN` | `LEDR` | Pino do ventilador |
| `RACK_DOOR_SERVO_PIN` | `RACK_DOOR_LOCK_PIN` | Pino do servo motor |

### Macros de Servo

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `DOOR_SERVO_ANGLE_CLOSED` | `0` | Ângulo porta fechada |
| `DOOR_SERVO_ANGLE_OPEN` | `179` | Ângulo porta aberta |

### Macros de Configuração I2C

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `I2C_PORT` | `i2c0` | Porta I2C |
| `I2C_BAUD_RATE` | `400000` | Frequência I2C (400kHz) |

### Macros de GPS

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `RACK_LATITUDE` | `-3.9012` | Latitude padrão |
| `RACK_LONGITUDE` | `-38.3876` | Longitude padrão |

### Macros de Tasks FreeRTOS

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `RACK_BUZZER_TASK_STACK_SIZE` | `configMINIMAL_STACK_SIZE * 2` | Stack do buzzer |
| `RACK_BUZZER_TASK_PRIORITY` | `tskIDLE_PRIORITY + 4` | Prioridade do buzzer |
| `RACK_MQTT_TASK_STACK_SIZE` | `configMINIMAL_STACK_SIZE * 3` | Stack de tasks MQTT |
| `RACK_MQTT_TASK_PRIORITY` | `tskIDLE_PRIORITY + 5` | Prioridade MQTT |
| `RACK_POLLING_TASK_STACK_SIZE` | `configMINIMAL_STACK_SIZE * 2` | Stack de polling |
| `RACK_POLLING_TASK_DELAY` | `500` | Delay de polling (ms) |
| `RACK_NETWORK_POLL_TASK_PRIORITY` | `tskIDLE_PRIORITY + 2` | Prioridade da rede |
| `RACK_WIFI_TIMEOUT` | `20000` | Timeout Wi-Fi (ms) |

### Macros de Timeouts

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `RACK_DOOR_OPEN_ALERT_TIMEOUT_MS` | `20 * 60 * 1000` | Timeout de alerta de porta (20 min) |
| `RACK_DOOR_CHECK_INTERVAL_MS` | `1000` | Intervalo de verificação (1s) |

---

## Task de Comandos MQTT - `firmware/tasks/command_mqtt_task.h`

### Enums

#### `CommandType`
| Valor | Nome | Descrição |
|-------|------|-----------|
| `0` | `COMMAND_TYPE_NONE` | Nenhum comando |
| `1` | `COMMAND_TYPE_DOOR` | Comando de porta |
| `2` | `COMMAND_TYPE_VENTILATION` | Comando de ventilação |
| `3` | `COMMAND_TYPE_BUZZER` | Comando de buzzer |

#### `BuzzerState`
| Valor | Nome | Descrição |
|-------|------|-----------|
| `0` | `BUZZER_OFF` | Buzzer desligado |
| `1` | `BUZZER_DOOR_OPEN` | Alerta de porta aberta |
| `2` | `BUZZER_BREAK_IN` | Alerta de arrombamento |
| `3` | `BUZZER_OVERHEAT` | Alerta de superaquecimento |

### Estruturas

#### `CommandQueueItem`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | `CommandType` | Tipo do comando |
| `value` | `int` | Valor do comando |

### Funções

```c
bool commandMqttInit(void)
```
Inicializa variáveis, filas e hardware do módulo de comandos.

```c
void commandMqttStartTask(void)
```
Inicia task FreeRTOS de processamento de comandos.

```c
void processCommandDoor(int value)
```
Enfileira comando de porta. **Seguro para callbacks MQTT**.
- `value = 1`: Abrir porta
- `value = 0`: Fechar porta

```c
void processCommandVentilation(int value)
```
Enfileira comando de ventilação. **Seguro para callbacks MQTT**.
- `value = 1`: Ligar
- `value = 0`: Desligar

```c
void processCommandBuzzer(int value)
```
Enfileira comando de buzzer. **Seguro para callbacks MQTT**.
- `value = 0-3`: Estado do buzzer

```c
bool publishCommandAck(CommandType commandType, int value)
```
Publica confirmação (ACK) via MQTT.

```c
bool getDoorState(void)
```
Retorna estado atual da porta.

```c
bool getVentilationState(void)
```
Retorna estado atual da ventilação.

```c
BuzzerState getBuzzerState(void)
```
Retorna estado atual do buzzer.

---

## Task do Servo Motor - `firmware/tasks/door_servo_task.c`

### Macros

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `SERVO_PWM_FREQ` | `50` | Frequência PWM (50Hz) |
| `SERVO_PULSE_MIN_US` | `500` | Pulso mínimo (0°) em µs |
| `SERVO_PULSE_MAX_US` | `2500` | Pulso máximo (180°) em µs |
| `SERVO_SMOOTH_STEP_DELAY` | `15` | Delay entre passos (ms) |
| `SERVO_SMOOTH_STEP_SIZE` | `3` | Incremento por passo (graus) |

### Enums

#### `DoorServoState`
| Valor | Nome | Descrição |
|-------|------|-----------|
| `0` | `DOOR_SERVO_STATE_CLOSED` | Porta fechada |
| `1` | `DOOR_SERVO_STATE_OPEN` | Porta aberta |
| `2` | `DOOR_SERVO_STATE_MOVING` | Porta em movimento |

### Funções

```c
bool doorServoInit(void)
```
Inicializa hardware PWM e posiciona servo em 0° (fechada).

```c
void doorServoSetAngle(uint8_t angle)
```
Define ângulo do servo (0-180°).

```c
uint8_t doorServoGetAngle(void)
```
Retorna ângulo atual do servo.

```c
DoorServoState doorServoGetState(void)
```
Retorna estado atual do servo.

```c
void doorServoOpen(bool smooth)
```
Abre porta. Se `smooth=true`, movimento gradual.

```c
void doorServoClose(bool smooth)
```
Fecha porta. Se `smooth=true`, movimento gradual.

```c
bool doorServoIsOpen(void)
```
Retorna `true` se porta está aberta (≥180°).

```c
bool doorServoIsClosed(void)
```
Retorna `true` se porta está fechada (0°).

```c
void doorServoDisable(void)
```
Desabilita PWM do servo.

```c
void doorServoEnable(void)
```
Habilita PWM do servo.

---

## Task do Buzzer PWM - `firmware/tasks/buzzer_pwm_task.c`

### Macros

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `BUZZER_PWM_PIN` | `RACK_ALARM_PIN` | Pino do buzzer |
| `BUZZER_PWM_DUTY_CYCLE` | `50` | Duty cycle (50%) |
| `BUZZER_MIN_FREQ` | `100` | Frequência mínima (Hz) |
| `BUZZER_MAX_FREQ` | `10000` | Frequência máxima (Hz) |

### Estrutura `BuzzerPattern`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `frequencyHigh` | `uint32_t` | Frequência do tom alto (Hz) |
| `frequencyLow` | `uint32_t` | Frequência do tom baixo (Hz) |
| `durationHigh` | `uint32_t` | Duração do tom alto (ms) |
| `durationLow` | `uint32_t` | Duração do tom baixo (ms) |
| `pauseDuration` | `uint32_t` | Duração da pausa entre sequências |
| `cyclesBeforePause` | `uint8_t` | Ciclos antes da pausa |

### Padrões Sonoros Predefinidos

| Padrão | Frequência | Ritmo | Uso |
|--------|------------|-------|-----|
| `patternDoorOpen` | 1000Hz / silêncio | beep-beep, pausa 1s | Porta aberta |
| `patternBreakIn` | 2500Hz / 1800Hz | alternância rápida | Arrombamento |
| `patternOverheat` | 500Hz / 300Hz | pulsos longos | Superaquecimento |

### Enums

#### `BuzzerPwmState`
| Valor | Nome | Descrição |
|-------|------|-----------|
| `0` | `BUZZER_STATE_OFF` | Desligado |
| `1` | `BUZZER_STATE_DOOR_OPEN` | Padrão porta aberta |
| `2` | `BUZZER_STATE_BREAK_IN` | Padrão arrombamento |
| `3` | `BUZZER_STATE_OVERHEAT` | Padrão superaquecimento |

### Funções

```c
bool buzzerPwmInit(void)
```
Inicializa hardware PWM e cria task do buzzer.

```c
void buzzerPwmSetState(BuzzerPwmState state)
```
Define estado/padrão do buzzer.

```c
BuzzerPwmState buzzerPwmGetState(void)
```
Retorna estado atual.

```c
void buzzerPwmOff(void)
```
Desliga buzzer.

```c
void buzzerPwmBeep(uint32_t frequency, uint32_t durationMs)
```
Emite beep único com frequência e duração especificadas.

```c
void buzzerPwmTask(void *pvParameters)
```
Task FreeRTOS que executa padrões sonoros.

---

## Biblioteca de Log - `firmware/lib/log_vt100/log_vt100.h`

### Enums

#### `log_level_t`
| Valor | Nome | Cor VT100 |
|-------|------|-----------|
| `0` | `LOG_LEVEL_TRACE` | Cinza |
| `1` | `LOG_LEVEL_DEBUG` | Azul |
| `2` | `LOG_LEVEL_INFO` | Verde |
| `3` | `LOG_LEVEL_WARN` | Amarelo |

### Macros de Configuração

| Macro | Padrão | Descrição |
|-------|--------|-----------|
| `LOG_DEFAULT_LEVEL` | `LOG_LEVEL_INFO` | Nível padrão |
| `LOG_LEVEL` | `1` | Verbosidade em tempo de compilação |
| `LOG_TAG` | `NULL` | Tag opcional para mensagens |

### Macros de Logging

```c
LOG_TRACE(fmt, ...)  // Disponível se LOG_LEVEL >= 3
LOG_DEBUG(fmt, ...)  // Disponível se LOG_LEVEL >= 2
LOG_INFO(fmt, ...)   // Disponível se LOG_LEVEL >= 1
LOG_WARN(fmt, ...)   // Sempre disponível se LOG_LEVEL >= 0
```

### Funções

```c
void log_set_level(log_level_t level)
```
Define nível de log em runtime.

```c
void log_write(log_level_t level, const char *fmt, ...)
```
Escreve mensagem de log com formatação estilo printf.
Suporta especificador extra `%b` para binário.

---

## FreeRTOS Config - `firmware/FreeRTOSConfig.h`

### Macros de Configuração Principal

| Macro | Valor | Descrição |
|-------|-------|-----------|
| `configUSE_PREEMPTION` | `1` | Preempção habilitada |
| `configTICK_RATE_HZ` | `1000` | 1ms por tick |
| `configMAX_PRIORITIES` | `32` | Níveis de prioridade |
| `configMINIMAL_STACK_SIZE` | `256` | Stack mínima em words |
| `configTOTAL_HEAP_SIZE` | `128*1024` | Heap total (128KB) |
| `configCHECK_FOR_STACK_OVERFLOW` | `2` | Verificação de stack overflow |
| `configUSE_MUTEXES` | `1` | Mutexes habilitados |
| `configUSE_COUNTING_SEMAPHORES` | `1` | Semáforos contadores |
| `configUSE_TIMERS` | `1` | Timers de software |
| `configTIMER_TASK_STACK_DEPTH` | `1024` | Stack da task de timers |

---

# 📡 Tópicos MQTT

## Tópicos de Telemetria (Firmware → Dashboard)

| Tópico | Payload | Descrição |
|--------|---------|-----------|
| `{base}/{rack_id}/environment/door` | `0` ou `1` | Estado da porta |
| `{base}/{rack_id}/environment/temperature` | `float` | Temperatura em °C |
| `{base}/{rack_id}/environment/humidity` | `float` | Umidade em % |
| `{base}/{rack_id}/gps` | JSON | Coordenadas GPS |
| `{base}/{rack_id}/tilt` | `0` ou `1` | Inclinação |

## Tópicos de Comando (Dashboard → Firmware)

| Tópico | Payload | Descrição |
|--------|---------|-----------|
| `{base}/{rack_id}/command/door` | `0` ou `1` | Fechar/Abrir |
| `{base}/{rack_id}/command/ventilation` | `0` ou `1` | Desligar/Ligar |
| `{base}/{rack_id}/command/buzzer` | `0-3` | Estado do buzzer |

## Tópicos de Confirmação (Firmware → Dashboard)

| Tópico | Payload | Descrição |
|--------|---------|-----------|
| `{base}/{rack_id}/ack/door` | `0` ou `1` | ACK de comando de porta |
| `{base}/{rack_id}/ack/ventilation` | `0` ou `1` | ACK de ventilação |
| `{base}/{rack_id}/ack/buzzer` | `0-3` | ACK de buzzer |

---

# 🌍 Variáveis de Ambiente (.env)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MQTT_SERVER` | Endereço do broker MQTT | `broker.mqtt.com` |
| `MQTT_PORT` | Porta do broker | `1883` |
| `MQTT_USERNAME` | Usuário MQTT | `user` |
| `MQTT_PASSWORD` | Senha MQTT | `pass` |
| `MQTT_BASE_TOPIC` | Tópico base | `racks` |
| `FORECAST_CONTEXT_LENGTH` | Histórico em horas | `168` |
| `FORECAST_HORIZON` | Horizonte de previsão | `24` |
| `FORECAST_MAE_THRESHOLD` | Limiar MAE | `5.0` |
| `AI_ANALYSIS_INTERVAL` | Intervalo de análise AI (s) | `10` |
| `TEMP_HIGH_THRESHOLD` | Limiar alto de temperatura | `35` |
| `TEMP_LOW_THRESHOLD` | Limiar baixo de temperatura | `28` |
| `TEMP_CRITICAL_THRESHOLD` | Temperatura crítica | `45` |
| `HUMIDITY_HIGH_THRESHOLD` | Limiar alto de umidade | `80` |
| `HUMIDITY_LOW_THRESHOLD` | Limiar baixo de umidade | `60` |

---

*Documentação gerada automaticamente - Projeto Rack Inteligente EmbarcaTech TIC-27*
