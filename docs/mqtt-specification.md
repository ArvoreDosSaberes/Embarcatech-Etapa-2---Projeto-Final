# Especificação MQTT - Rack Inteligente

Este documento descreve a estrutura de comunicação MQTT utilizada entre o **firmware** (ESP32/RP2040) e o **dashboard** (Python/PyQt5) do sistema Rack Inteligente.

> **Objetivo**: Servir como referência única para manter consistência entre firmware e dashboard ao implementar ou atualizar funcionalidades MQTT.

---

## 1. Parâmetros de Conexão

### 1.1 Variáveis de Configuração

| Parâmetro | Firmware (C/C++) | Dashboard (Python) | Descrição |
|-----------|------------------|-------------------|-----------|
| Servidor/Broker | `MQTT_BROKER` | `MQTT_SERVER` | Endereço do broker MQTT |
| Porta | `MQTT_PORT` | `MQTT_PORT` | Porta TCP do broker (padrão: 1883) |
| Usuário | `MQTT_USERNAME` | `MQTT_USERNAME` | Nome de usuário para autenticação |
| Senha | `MQTT_PASSWORD` | `MQTT_PASSWORD` | Senha para autenticação |
| Client ID | `MQTT_CLIENT_ID` | (auto-gerado) | Identificador único do cliente |
| Keep Alive | 60s (hardcoded) | `MQTT_KEEPALIVE` | Intervalo de keep-alive em segundos |
| Tópico Base | `MQTT_BASE_TOPIC` | `MQTT_BASE_TOPIC` | Prefixo para todos os tópicos |
| ID do Rack | `MQTT_RACK_NUMBER` | (dinâmico) | Identificador único do rack |

### 1.2 Exemplo de Configuração

**Firmware** (`env.cmake`):
```cmake
set(MQTT_BROKER "mqtt.exemplo.com.br")
set(MQTT_PORT 1883)
set(MQTT_USERNAME "rack")
set(MQTT_PASSWORD "senha_secreta")
set(MQTT_CLIENT_ID "rack_001")
set(MQTT_BASE_TOPIC "racks")
set(MQTT_RACK_NUMBER "001")
```

**Dashboard** (`.env`):
```env
MQTT_SERVER=mqtt.exemplo.com.br
MQTT_PORT=1883
MQTT_USERNAME=rack
MQTT_PASSWORD=senha_secreta
MQTT_KEEPALIVE=60
MQTT_BASE_TOPIC=racks
```

---

## 2. Estrutura de Tópicos

### 2.1 Formato Geral

```
{MQTT_BASE_TOPIC}/{RACK_ID}/{CATEGORIA}/{SUBCATEGORIA}
```

Onde:
- `{MQTT_BASE_TOPIC}`: Prefixo configurável (padrão: `racks`)
- `{RACK_ID}`: Identificador único do rack (ex: `001`, `rack_a`, `datacenter1_rack5`)
- `{CATEGORIA}`: Grupo funcional (`status`, `environment`, `command`, `gps`, `tilt`)
- `{SUBCATEGORIA}`: Especificação adicional quando aplicável

### 2.2 Tópico Base do Rack

O tópico base de cada rack é construído como:

```
{MQTT_BASE_TOPIC}/{RACK_ID}
```

**Exemplo**: `racks/001`

---

## 3. Tópicos de Publicação (Firmware → Dashboard)

Estes tópicos são **publicados pelo firmware** e **assinados pelo dashboard**.

### 3.1 Status da Porta

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/status` |
| **Direção** | Firmware → Dashboard |
| **Payload** | `"0"` ou `"1"` (string) |
| **QoS** | 0 |
| **Retain** | Não |

**Valores do Payload**:
| Valor | Significado |
|-------|-------------|
| `"0"` | Porta fechada |
| `"1"` | Porta aberta |

**Firmware** (`door_state_mqtt_task.c`):
```c
snprintf(topic_door_state, sizeof(topic_door_state), "%s/status", mqtt_rack_topic);
const char *message = pressed ? "1" : "0";
mqtt_publish(mqtt_client, topic_door_state, message, strlen(message), 0, 0, NULL, NULL);
```

**Dashboard** (`app.py`):
```python
if topic.endswith('/status'):
    state['door_status'] = int(payload)
```

---

### 3.2 Temperatura

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/environment/temperature` |
| **Direção** | Firmware → Dashboard |
| **Payload** | Valor float como string (ex: `"25.50"`) |
| **Unidade** | Graus Celsius (°C) |
| **Faixa** | 0 - 100 |
| **QoS** | 0 |

**Firmware** (`temperature_mqtt_task.c`):
```c
snprintf(topic_rack_temperature, sizeof(topic_rack_temperature), 
         "%s/environment/temperature", mqtt_rack_topic);
snprintf(message, sizeof(message), "%.2f", temperature);
mqtt_publish(mqtt_client, topic_rack_temperature, message, strlen(message), 0, 0, NULL, NULL);
```

**Dashboard** (`app.py`):
```python
if topic.endswith('/environment/temperature'):
    temp_value = float(payload)
    state['temperature'] = temp_value
```

---

### 3.3 Umidade

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/environment/humidity` |
| **Direção** | Firmware → Dashboard |
| **Payload** | Valor float como string (ex: `"65.30"`) |
| **Unidade** | Percentual (%) |
| **Faixa** | 0 - 100 |
| **QoS** | 0 |

**Firmware** (`humidity_mqtt_task.c`):
```c
snprintf(topic_rack_humidity, sizeof(topic_rack_humidity), 
         "%s/environment/humidity", mqtt_rack_topic);
snprintf(message, sizeof(message), "%.2f", humidity);
mqtt_publish(mqtt_client, topic_rack_humidity, message, strlen(message), 0, 0, NULL, NULL);
```

**Dashboard** (`app.py`):
```python
if topic.endswith('/environment/humidity'):
    hum_value = float(payload)
    state['humidity'] = hum_value
```

---

### 3.4 Inclinação (Tilt)

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/tilt` |
| **Direção** | Firmware → Dashboard |
| **Payload** | `"0"` ou `"1"` (string) |
| **QoS** | 0 |

**Valores do Payload**:
| Valor | Significado |
|-------|-------------|
| `"0"` | Rack estável (sem inclinação) |
| `"1"` | Inclinação detectada (possível arrombamento) |

**Firmware** (`tilt_mqtt_task.c`):
```c
snprintf(topic_tilt, sizeof(topic_tilt), "%s/tilt", mqtt_rack_topic);
const char *message = tilt ? "1" : "0";
mqtt_publish(mqtt_client, topic_tilt, message, 1, 0, 0, NULL, NULL);
```

---

### 3.5 GPS / Localização

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/gps` |
| **Direção** | Firmware → Dashboard |
| **Payload** | JSON |
| **QoS** | 2 (garantido) |

**Estrutura do Payload JSON**:
```json
{
    "latitude": -23.550520,
    "longitude": -46.633308,
    "altitude": 760.0,
    "time": 1701456789,
    "speed": 0.0
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `latitude` | float | Latitude em graus decimais |
| `longitude` | float | Longitude em graus decimais |
| `altitude` | float | Altitude em metros |
| `time` | int | Timestamp Unix (segundos) |
| `speed` | float | Velocidade em m/s |

**Firmware** (`gps_mqtt_task.c`):
```c
snprintf(mqttTopicMsg, sizeof(mqttTopicMsg), "%s/gps", mqtt_rack_topic);
snprintf(gps_position_json, sizeof(gps_position_json), 
    "{\"latitude\": %f, \"longitude\": %f, \"altitude\": %f, \"time\": %d, \"speed\": %f}",
    environment.gps_position.latitude,
    environment.gps_position.longitude,
    environment.gps_position.altitude,
    environment.gps_position.time,
    environment.gps_position.speed);
mqtt_publish(mqtt_client, mqttTopicMsg, gps_position_json, strlen(gps_position_json), 2, 0, NULL, NULL);
```

---

## 4. Tópicos de Comando (Dashboard → Firmware)

Estes tópicos são **publicados pelo dashboard** e **assinados pelo firmware**.

### 4.1 Comando de Porta

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/command/door` |
| **Alias** | `{base}/{rack_id}/door` (legado) |
| **Direção** | Dashboard → Firmware |
| **Payload** | `"0"` ou `"1"` (string) |
| **QoS** | 0 |

**Valores do Payload**:
| Valor | Ação |
|-------|------|
| `"0"` | Fechar porta |
| `"1"` | Abrir porta |

**Dashboard** (`rackControlService.py`):
```python
def openDoor(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "door", DoorStatus.OPEN)  # valor 1

def closeDoor(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "door", DoorStatus.CLOSED)  # valor 0
```

**Firmware** (`rack_inteligente.cpp`):
```c
// Subscrição ao tópico
snprintf(mqttDoorTopic, sizeof(mqttDoorTopic), "%s/%s/door", MQTT_BASE_TOPIC, rack_name);

// Callback de dados
if (mqttInTopicDoor && len == 1 && memcmp(data, "1", 1) == 0) {
    openDoor();
} else if (mqttInTopicDoor && len == 1 && memcmp(data, "0", 1) == 0) {
    closeDoor();
}
```

---

### 4.2 Comando de Ventilação

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/command/ventilation` |
| **Direção** | Dashboard → Firmware |
| **Payload** | `"0"` ou `"1"` (string) |
| **QoS** | 0 |

**Valores do Payload**:
| Valor | Ação |
|-------|------|
| `"0"` | Desligar ventilação |
| `"1"` | Ligar ventilação |

**Dashboard** (`rackControlService.py`):
```python
def turnOnVentilation(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "ventilation", VentilationStatus.ON)  # valor 1

def turnOffVentilation(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "ventilation", VentilationStatus.OFF)  # valor 0
```

---

### 4.3 Comando de Buzzer/Alarme

| Atributo | Valor |
|----------|-------|
| **Tópico** | `{base}/{rack_id}/command/buzzer` |
| **Alias** | `{base}/{rack_id}/alert` (legado) |
| **Direção** | Dashboard → Firmware |
| **Payload** | `"0"`, `"1"`, `"2"` ou `"3"` (string) |
| **QoS** | 0 |

**Valores do Payload**:
| Valor | Estado | Descrição |
|-------|--------|-----------|
| `"0"` | OFF | Buzzer desligado |
| `"1"` | DOOR_OPEN | Alerta de porta aberta |
| `"2"` | BREAK_IN | Alerta de arrombamento |
| `"3"` | OVERHEAT | Alerta de superaquecimento |

**Dashboard** (`rackControlService.py`):
```python
class BuzzerStatus(IntEnum):
    OFF = 0
    DOOR_OPEN = 1
    BREAK_IN = 2
    OVERHEAT = 3

def activateCriticalTemperatureAlert(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "buzzer", BuzzerStatus.OVERHEAT)

def silenceBuzzer(self, rack: Rack) -> bool:
    return self._publishCommand(rack, "buzzer", BuzzerStatus.OFF)
```

**Firmware** (`rack_inteligente.cpp`):
```c
// Subscrição ao tópico
snprintf(mqttAlertTopic, sizeof(mqttAlertTopic), "%s/%s/alert", MQTT_BASE_TOPIC, rack_name);

// Callback de dados
if (mqttInTopicAlert && len == 1 && memcmp(data, "1", 1) == 0) {
    turnOnAlarm();
} else if (mqttInTopicAlert && len == 1 && memcmp(data, "0", 1) == 0) {
    turnOffAlarm();
}
```

---

## 5. Tabela Resumo de Tópicos

| Tópico | Direção | Payload | Descrição |
|--------|---------|---------|-----------|
| `{base}/{id}/status` | F→D | `0`/`1` | Estado da porta |
| `{base}/{id}/environment/temperature` | F→D | `float` | Temperatura (°C) |
| `{base}/{id}/environment/humidity` | F→D | `float` | Umidade (%) |
| `{base}/{id}/tilt` | F→D | `0`/`1` | Detecção de inclinação |
| `{base}/{id}/gps` | F→D | JSON | Posição GPS |
| `{base}/{id}/command/door` | D→F | `0`/`1` | Comando de porta |
| `{base}/{id}/command/ventilation` | D→F | `0`/`1` | Comando de ventilação |
| `{base}/{id}/command/buzzer` | D→F | `0-3` | Comando de alarme |
| `{base}/{id}/door` | D→F | `0`/`1` | (Legado) Comando de porta |
| `{base}/{id}/alert` | D→F | `0`/`1` | (Legado) Comando de alarme |

**Legenda**: F = Firmware, D = Dashboard

---

## 6. Enumerações Compartilhadas

### 6.1 DoorStatus

```python
# Python (Dashboard)
class DoorStatus(IntEnum):
    CLOSED = 0
    OPEN = 1
```

```c
// C (Firmware)
#define DOOR_CLOSED 0
#define DOOR_OPEN   1
```

### 6.2 VentilationStatus

```python
# Python (Dashboard)
class VentilationStatus(IntEnum):
    OFF = 0
    ON = 1
```

```c
// C (Firmware)
#define VENTILATION_OFF 0
#define VENTILATION_ON  1
```

### 6.3 BuzzerStatus

```python
# Python (Dashboard)
class BuzzerStatus(IntEnum):
    OFF = 0
    DOOR_OPEN = 1
    BREAK_IN = 2
    OVERHEAT = 3
```

```c
// C (Firmware)
typedef enum {
    BUZZER_OFF = 0,
    BUZZER_DOOR_OPEN = 1,
    BUZZER_BREAK_IN = 2,
    BUZZER_OVERHEAT = 3
} buzzer_status_t;
```

---

## 7. Padrões de Implementação

### 7.1 Publicação de Comando (Dashboard)

```python
def _publishCommand(self, rack: Rack, commandType: str, value: int) -> bool:
    topic = f"{self.baseTopic}/{rack.rackId}/command/{commandType}"
    result = self.mqttClient.publish(topic, str(value))
    return result.rc == 0
```

### 7.2 Publicação de Telemetria (Firmware)

```c
void publish_metric(const char* metric_name, const char* value) {
    if (!mqtt_connected) return;
    
    char topic[50];
    snprintf(topic, sizeof(topic), "%s/%s", mqtt_rack_topic, metric_name);
    mqtt_publish(mqtt_client, topic, value, strlen(value), 0, 0, NULL, NULL);
}
```

### 7.3 Subscrição de Tópicos (Dashboard)

```python
topics = [
    f"{base}/+/status",
    f"{base}/+/environment/temperature",
    f"{base}/+/environment/humidity",
    f"{base}/+/command/door",
    f"{base}/+/command/ventilation",
    f"{base}/+/command/buzzer",
]
for topic in topics:
    client.subscribe(topic)
```

---

## 8. Considerações de Implementação

### 8.1 Firmware (C/C++)

1. **Macros obrigatórias** definidas em `env.cmake`:
   - `WIFI_SSID`, `WIFI_PASSWORD`
   - `MQTT_BROKER`, `MQTT_PORT`
   - `MQTT_CLIENT_ID`, `MQTT_USERNAME`, `MQTT_PASSWORD`
   - `MQTT_BASE_TOPIC`, `MQTT_RACK_NUMBER`

2. **Tópico do rack** construído em runtime:
   ```c
   snprintf(mqtt_rack_topic, sizeof(mqtt_rack_topic), "%s/%s", MQTT_BASE_TOPIC, rack_name);
   ```

3. **Verificar conexão** antes de publicar:
   ```c
   if (!mqtt_connected) return;
   ```

### 8.2 Dashboard (Python)

1. **Variáveis de ambiente** carregadas do `.env`:
   - `MQTT_SERVER`, `MQTT_PORT`
   - `MQTT_USERNAME`, `MQTT_PASSWORD`
   - `MQTT_KEEPALIVE`, `MQTT_BASE_TOPIC`

2. **Wildcard `+`** para descoberta de racks:
   ```python
   client.subscribe(f"{base}/+/status")
   ```

3. **Extração do rack_id** do tópico:
   ```python
   remainder = topic[len(prefix):]
   parts = remainder.split('/')
   rack_id = parts[0]
   ```

---

## 9. Checklist de Compatibilidade

Ao adicionar novo tópico ou funcionalidade:

- [ ] Definir formato do tópico seguindo padrão `{base}/{id}/{categoria}/{sub}`
- [ ] Documentar payload (tipo, valores válidos, unidade)
- [ ] Implementar no firmware (publish ou subscribe)
- [ ] Implementar no dashboard (subscribe ou publish)
- [ ] Adicionar à tabela resumo neste documento
- [ ] Testar comunicação bidirecional
- [ ] Atualizar `.env.example` se necessário

---

## 10. Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0.0 | 2025-12-01 | Versão inicial com tópicos básicos |

---

**Autor**: Dashboard Rack Inteligente - EmbarcaTech  
**Última atualização**: 2025-12-01
