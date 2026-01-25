# Tool Calling Detalhado: Do Conceito à Implementação

> Guia completo sobre Function Calling / Tool Calling em LLMs, com implementações em Python e C para ESP32.

---

## 1. Fundamentos do Tool Calling

### O Problema que Tool Calling Resolve

Antes do Tool Calling, LLMs eram "ilhas isoladas":
- Geravam texto, mas não podiam **agir**
- Conhecimento congelado na data de treinamento
- Incapazes de acessar dados em tempo real
- Cálculos matemáticos imprecisos

**Tool Calling** transforma LLMs em **orquestradores** que podem invocar funções externas para:
- Consultar APIs e bancos de dados
- Executar ações em dispositivos físicos
- Realizar cálculos precisos
- Interagir com qualquer sistema via API

### Anatomia de uma Tool Definition

```json
{
  "type": "function",
  "function": {
    "name": "turnOnVentilation",
    "description": "Liga a ventilação de um rack específico. Use quando a temperatura estiver alta (>=35°C) ou umidade alta (>=80%). Não use se já estiver ligada.",
    "parameters": {
      "type": "object",
      "properties": {
        "rackId": {
          "type": "string",
          "description": "Identificador único do rack (ex: '001', 'rack-alpha')"
        },
        "reason": {
          "type": "string",
          "description": "Motivo detalhado para ligar a ventilação"
        }
      },
      "required": ["rackId", "reason"]
    }
  }
}
```

**Elementos críticos:**

| Campo | Propósito | Dica |
|-------|-----------|------|
| `name` | Identificador único | Use camelCase, seja específico |
| `description` | Guia o LLM sobre **quando** usar | Quanto mais detalhada, melhor |
| `parameters` | Schema JSON dos argumentos | Descreva cada propriedade |
| `required` | Parâmetros obrigatórios | Minimize para flexibilidade |

### A Importância da Description

A `description` é o **manual de instruções** para o LLM. Compare:

**Ruim:**
```
"description": "Liga ventilação"
```

**Boa:**
```
"description": "Liga a ventilação de um rack específico. Use quando: (1) temperatura >= 35°C, (2) umidade >= 80%, (3) tendência de temperatura subindo. NÃO use se ventilação já estiver ligada."
```

O LLM usa essa descrição para decidir **se** e **quando** chamar a função.

---

## 2. Fluxo Completo de Tool Calling

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. ENTRADA: Usuário ou sistema fornece contexto                  │
│    "Rack 001: temp=38°C, umidade=75%, ventilação=OFF"            │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. ANÁLISE: LLM processa contexto + tools disponíveis            │
│    - Avalia condições vs descrições das tools                    │
│    - Decide quais ações são necessárias                          │
│    - Gera chamadas estruturadas                                  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. RESPOSTA: LLM retorna tool_calls em JSON                      │
│    {                                                             │
│      "tool_calls": [{                                            │
│        "id": "call_abc123",                                      │
│        "function": {                                             │
│          "name": "turnOnVentilation",                            │
│          "arguments": "{\"rackId\":\"001\",\"reason\":\"...\"}"  │
│        }                                                         │
│      }]                                                          │
│    }                                                             │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. EXECUÇÃO: Sistema host processa tool_calls                    │
│    - Valida parâmetros                                           │
│    - Executa função correspondente                               │
│    - Captura resultado ou erro                                   │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. FEEDBACK (opcional): Resultado retorna ao LLM                 │
│    - LLM pode usar resultado para próximas decisões              │
│    - Permite fluxos multi-step                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementação Python Completa

### Estrutura do ToolCallingService

```python
"""
Serviço de Tool Calling para controle de racks via LLM.

Este módulo implementa a integração entre LLMs e o sistema de controle,
permitindo que o modelo tome decisões baseadas em telemetria.
"""

import json
import logging
import threading
from typing import Dict, List, Optional, Callable
from openai import OpenAI

logger = logging.getLogger(__name__)


class ToolCallingService:
    """
    Serviço de chamada de ferramentas orientadas por LLMs.
    
    Responsabilidades:
    - Definir tools disponíveis para o LLM
    - Construir prompts contextualizados
    - Processar respostas e extrair tool calls
    - Executar ações via RackControlService
    """
    
    # Definição completa das tools
    TOOLS_DEFINITION = [
        {
            "type": "function",
            "function": {
                "name": "turnOnVentilation",
                "description": (
                    "Liga a ventilação de um rack específico. "
                    "Use quando: temperatura >= 35°C OU umidade >= 80%. "
                    "Considere também tendências de subida."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rackId": {
                            "type": "string",
                            "description": "ID único do rack"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Justificativa para a ação"
                        }
                    },
                    "required": ["rackId", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "turnOffVentilation",
                "description": (
                    "Desliga a ventilação de um rack. "
                    "Use quando: temperatura <= 25°C E umidade <= 40% "
                    "E ventilação estiver ligada. "
                    "Aplique histerese para evitar oscilações."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rackId": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["rackId", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "activateCriticalTemperatureAlert",
                "description": (
                    "Ativa alerta sonoro de EMERGÊNCIA. "
                    "Use APENAS quando temperatura >= 45°C. "
                    "Este é um alerta crítico!"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rackId": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["rackId", "reason"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "silenceBuzzer",
                "description": "Silencia o alarme sonoro após reconhecimento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rackId": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["rackId", "reason"]
                }
            }
        }
    ]
    
    def __init__(
        self,
        apiKey: str,
        model: str = "gpt-4-turbo",
        baseUrl: str = "https://api.openai.com/v1"
    ):
        """
        Inicializa o serviço de Tool Calling.
        
        Args:
            apiKey: Chave de API do provedor LLM
            model: Modelo a utilizar (deve suportar tool calling)
            baseUrl: URL base da API (permite usar Ollama, etc.)
        """
        self.model = model
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl)
        self.rackControlService = None  # Injetado posteriormente
        self._lock = threading.Lock()
        
        logger.info(f"ToolCallingService inicializado com modelo {model}")
    
    def buildSystemPrompt(self) -> str:
        """
        Constrói o prompt de sistema que define o comportamento do LLM.
        
        Returns:
            String com instruções detalhadas para o modelo
        """
        return """Você é um sistema de controle automático de racks de equipamentos.

REGRAS DE OPERAÇÃO:

1. TEMPERATURA:
   - >= 35°C: Ligar ventilação (prevenção)
   - >= 45°C: Ativar alerta crítico (emergência)
   - <= 25°C com ventilação ON: Desligar (economia)

2. UMIDADE:
   - >= 80%: Ligar ventilação (condensação)
   - <= 40% com ventilação ON: Desligar

3. HISTERESE (evitar oscilações):
   - Diferença de 10°C entre ligar/desligar
   - Aguardar estabilização antes de nova ação

4. TENDÊNCIAS:
   - Se temperatura SUBINDO rapidamente: antecipar ação
   - Se temperatura DESCENDO: aguardar confirmação

5. PRIORIDADES:
   - Segurança > Conforto térmico > Economia

Analise a telemetria e execute as ações apropriadas.
Sempre forneça justificativa clara no campo 'reason'."""
    
    def formatTelemetry(self, telemetryData: Dict) -> str:
        """
        Formata dados de telemetria para o prompt do usuário.
        
        Args:
            telemetryData: Dicionário com dados dos racks
            
        Returns:
            String formatada para o LLM
        """
        lines = ["Status atual dos racks:\n"]
        
        for rackId, data in telemetryData.items():
            lines.append(f"Rack {rackId}:")
            lines.append(f"  Temperatura: {data.get('temperature', 'N/A')}°C")
            lines.append(f"  Umidade: {data.get('humidity', 'N/A')}%")
            lines.append(f"  Ventilação: {'ON' if data.get('ventilation') else 'OFF'}")
            lines.append(f"  Porta: {'ABERTA' if data.get('door') else 'FECHADA'}")
            
            if 'tempTrend' in data:
                trend = data['tempTrend']
                direction = "↑ subindo" if trend > 0 else "↓ descendo" if trend < 0 else "→ estável"
                lines.append(f"  Tendência temp: {direction} ({trend:+.1f}°C/h)")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def analyze(self, telemetryData: Dict) -> List[Dict]:
        """
        Envia telemetria ao LLM e obtém decisões via Tool Calling.
        
        Args:
            telemetryData: Dados de telemetria dos racks
            
        Returns:
            Lista de ações a executar
        """
        with self._lock:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.buildSystemPrompt()},
                        {"role": "user", "content": self.formatTelemetry(telemetryData)}
                    ],
                    tools=self.TOOLS_DEFINITION,
                    tool_choice="auto",
                    temperature=0.1  # Baixa para decisões consistentes
                )
                
                return self._extractToolCalls(response)
                
            except Exception as e:
                logger.error(f"Erro na análise LLM: {e}")
                return []
    
    def _extractToolCalls(self, response) -> List[Dict]:
        """
        Extrai tool calls da resposta do LLM.
        
        Args:
            response: Objeto de resposta da API
            
        Returns:
            Lista de dicionários com ações parseadas
        """
        actions = []
        message = response.choices[0].message
        
        if not message.tool_calls:
            logger.debug("Nenhuma ação necessária")
            return actions
        
        for toolCall in message.tool_calls:
            try:
                args = json.loads(toolCall.function.arguments)
                action = {
                    'id': toolCall.id,
                    'function': toolCall.function.name,
                    'rackId': args.get('rackId'),
                    'reason': args.get('reason', 'Não especificado')
                }
                actions.append(action)
                
                logger.info(
                    f"Tool Call: {action['function']}(rackId={action['rackId']}) "
                    f"- {action['reason']}"
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao parsear arguments: {e}")
        
        return actions
    
    def executeActions(self, actions: List[Dict]) -> None:
        """
        Executa as ações decididas pelo LLM.
        
        Args:
            actions: Lista de ações a executar
        """
        if not self.rackControlService:
            logger.error("RackControlService não configurado!")
            return
        
        for action in actions:
            func = action['function']
            rackId = action['rackId']
            
            try:
                if func == 'turnOnVentilation':
                    self.rackControlService.setVentilation(rackId, True)
                elif func == 'turnOffVentilation':
                    self.rackControlService.setVentilation(rackId, False)
                elif func == 'activateCriticalTemperatureAlert':
                    self.rackControlService.setBuzzer(rackId, 3)  # Modo overheat
                elif func == 'silenceBuzzer':
                    self.rackControlService.setBuzzer(rackId, 0)
                else:
                    logger.warning(f"Função desconhecida: {func}")
                    
            except Exception as e:
                logger.error(f"Erro ao executar {func}: {e}")
```

---

## 4. Implementação C para ESP32

### Estruturas Base

```c
/**
 * @file tool_calling.h
 * @brief Definições para processamento de Tool Calls no ESP32
 */

#ifndef TOOL_CALLING_H
#define TOOL_CALLING_H

#include "esp_err.h"

/** Tamanho máximo do nome da função */
#define TOOL_FUNC_NAME_MAX  32

/** Tamanho máximo do ID do rack */
#define TOOL_RACK_ID_MAX    16

/** Tamanho máximo do motivo */
#define TOOL_REASON_MAX     128

/**
 * @brief Estrutura para uma Tool Call parseada
 */
typedef struct {
    char functionName[TOOL_FUNC_NAME_MAX];
    char rackId[TOOL_RACK_ID_MAX];
    char reason[TOOL_REASON_MAX];
} ToolCall_t;

/**
 * @brief Enumeração das funções suportadas
 */
typedef enum {
    TOOL_FUNC_VENT_ON = 0,
    TOOL_FUNC_VENT_OFF,
    TOOL_FUNC_ALERT_ON,
    TOOL_FUNC_ALERT_OFF,
    TOOL_FUNC_BUZZER_OFF,
    TOOL_FUNC_UNKNOWN = -1
} ToolFunction_e;

/**
 * @brief Tipo de função handler
 */
typedef esp_err_t (*tool_handler_t)(const char* rackId);

/**
 * @brief Parseia JSON de resposta e extrai Tool Call
 * 
 * @param jsonStr String JSON da resposta do LLM
 * @param toolCall Ponteiro para estrutura de saída
 * @return ESP_OK em sucesso, ESP_ERR_* em falha
 */
esp_err_t tool_parse_response(const char* jsonStr, ToolCall_t* toolCall);

/**
 * @brief Executa uma Tool Call parseada
 * 
 * @param toolCall Ponteiro para Tool Call a executar
 * @return ESP_OK em sucesso, ESP_ERR_NOT_FOUND se função desconhecida
 */
esp_err_t tool_execute(const ToolCall_t* toolCall);

#endif // TOOL_CALLING_H
```

### Implementação

```c
/**
 * @file tool_calling.c
 * @brief Implementação do processamento de Tool Calls
 */

#include "tool_calling.h"
#include "cJSON.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include <string.h>

static const char* TAG = "TOOL_CALL";

// Protótipos dos handlers
static esp_err_t handle_vent_on(const char* rackId);
static esp_err_t handle_vent_off(const char* rackId);
static esp_err_t handle_alert_on(const char* rackId);
static esp_err_t handle_buzzer_off(const char* rackId);

/**
 * @brief Tabela de dispatch função→handler
 */
static const struct {
    const char* name;
    ToolFunction_e func;
    tool_handler_t handler;
} dispatch_table[] = {
    {"turnOnVentilation",   TOOL_FUNC_VENT_ON,    handle_vent_on},
    {"turnOffVentilation",  TOOL_FUNC_VENT_OFF,   handle_vent_off},
    {"activateCriticalTemperatureAlert", TOOL_FUNC_ALERT_ON, handle_alert_on},
    {"silenceBuzzer",       TOOL_FUNC_BUZZER_OFF, handle_buzzer_off},
    {NULL, TOOL_FUNC_UNKNOWN, NULL}
};


esp_err_t tool_parse_response(const char* jsonStr, ToolCall_t* toolCall) {
    if (!jsonStr || !toolCall) {
        return ESP_ERR_INVALID_ARG;
    }
    
    memset(toolCall, 0, sizeof(ToolCall_t));
    
    cJSON* root = cJSON_Parse(jsonStr);
    if (!root) {
        ESP_LOGE(TAG, "Falha no parse JSON");
        return ESP_ERR_INVALID_ARG;
    }
    
    esp_err_t ret = ESP_FAIL;
    
    // Navega: choices[0].message.tool_calls[0].function
    cJSON* choices = cJSON_GetObjectItem(root, "choices");
    if (!cJSON_IsArray(choices)) goto cleanup;
    
    cJSON* choice0 = cJSON_GetArrayItem(choices, 0);
    if (!choice0) goto cleanup;
    
    cJSON* message = cJSON_GetObjectItem(choice0, "message");
    if (!message) goto cleanup;
    
    cJSON* toolCalls = cJSON_GetObjectItem(message, "tool_calls");
    if (!cJSON_IsArray(toolCalls) || cJSON_GetArraySize(toolCalls) == 0) {
        ESP_LOGD(TAG, "Sem tool_calls na resposta");
        ret = ESP_ERR_NOT_FOUND;
        goto cleanup;
    }
    
    cJSON* tc0 = cJSON_GetArrayItem(toolCalls, 0);
    cJSON* function = cJSON_GetObjectItem(tc0, "function");
    
    // Nome da função
    cJSON* name = cJSON_GetObjectItem(function, "name");
    if (cJSON_IsString(name)) {
        strncpy(toolCall->functionName, name->valuestring, 
                TOOL_FUNC_NAME_MAX - 1);
    }
    
    // Parse do arguments (string JSON aninhada)
    cJSON* argsStr = cJSON_GetObjectItem(function, "arguments");
    if (cJSON_IsString(argsStr)) {
        cJSON* args = cJSON_Parse(argsStr->valuestring);
        if (args) {
            cJSON* rackId = cJSON_GetObjectItem(args, "rackId");
            if (cJSON_IsString(rackId)) {
                strncpy(toolCall->rackId, rackId->valuestring,
                        TOOL_RACK_ID_MAX - 1);
            }
            
            cJSON* reason = cJSON_GetObjectItem(args, "reason");
            if (cJSON_IsString(reason)) {
                strncpy(toolCall->reason, reason->valuestring,
                        TOOL_REASON_MAX - 1);
            }
            
            cJSON_Delete(args);
        }
    }
    
    ESP_LOGI(TAG, "Parsed: %s(rack=%s)", 
             toolCall->functionName, toolCall->rackId);
    ret = ESP_OK;

cleanup:
    cJSON_Delete(root);
    return ret;
}


esp_err_t tool_execute(const ToolCall_t* toolCall) {
    if (!toolCall || !toolCall->functionName[0]) {
        return ESP_ERR_INVALID_ARG;
    }
    
    ESP_LOGI(TAG, "Executando: %s para rack %s",
             toolCall->functionName, toolCall->rackId);
    ESP_LOGI(TAG, "Motivo: %s", toolCall->reason);
    
    for (int i = 0; dispatch_table[i].name != NULL; i++) {
        if (strcmp(dispatch_table[i].name, toolCall->functionName) == 0) {
            return dispatch_table[i].handler(toolCall->rackId);
        }
    }
    
    ESP_LOGW(TAG, "Função desconhecida: %s", toolCall->functionName);
    return ESP_ERR_NOT_FOUND;
}


// ============ HANDLERS ============

#define GPIO_VENTILATION  GPIO_NUM_21
#define GPIO_BUZZER       GPIO_NUM_10

static esp_err_t handle_vent_on(const char* rackId) {
    gpio_set_level(GPIO_VENTILATION, 1);
    ESP_LOGI(TAG, "Ventilação LIGADA - Rack %s", rackId);
    return ESP_OK;
}

static esp_err_t handle_vent_off(const char* rackId) {
    gpio_set_level(GPIO_VENTILATION, 0);
    ESP_LOGI(TAG, "Ventilação DESLIGADA - Rack %s", rackId);
    return ESP_OK;
}

static esp_err_t handle_alert_on(const char* rackId) {
    // Implementar padrão de beep para alerta crítico
    ESP_LOGW(TAG, "ALERTA CRÍTICO - Rack %s", rackId);
    gpio_set_level(GPIO_BUZZER, 1);
    return ESP_OK;
}

static esp_err_t handle_buzzer_off(const char* rackId) {
    gpio_set_level(GPIO_BUZZER, 0);
    ESP_LOGI(TAG, "Buzzer SILENCIADO - Rack %s", rackId);
    return ESP_OK;
}
```

---

## 5. Boas Práticas

### Descrições Efetivas

| Aspecto | Ruim | Bom |
|---------|------|-----|
| Clareza | "Controla LED" | "Liga LED vermelho de alerta quando temperatura > 50°C" |
| Condições | "Quando necessário" | "Quando temp >= 35°C OU umidade >= 80%" |
| Restrições | (nenhuma) | "NÃO use se já estiver ativo" |

### Validação de Parâmetros

Nunca confie cegamente nos parâmetros do LLM:

```python
def executeAction(action: Dict) -> bool:
    rackId = action.get('rackId', '')
    
    # Validação de formato
    if not re.match(r'^[a-zA-Z0-9-]{1,16}$', rackId):
        logger.error(f"rackId inválido: {rackId}")
        return False
    
    # Verificação de existência
    if rackId not in knownRacks:
        logger.error(f"Rack desconhecido: {rackId}")
        return False
    
    # Executa apenas após validação
    return doExecute(action)
```

### Logging e Auditoria

Registre todas as tool calls para debug e compliance:

```python
logger.info(
    f"TOOL_CALL | "
    f"function={action['function']} | "
    f"rackId={action['rackId']} | "
    f"reason={action['reason']} | "
    f"timestamp={datetime.now().isoformat()}"
)
```

---

## 6. Referências

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [ESP-IDF cJSON](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/cjson.html)
