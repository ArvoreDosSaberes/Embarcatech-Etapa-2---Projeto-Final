# 📟 Tool Calling no ESP32 — Estrutura em C

## Definição das Estruturas

```c
// Estrutura para uma Tool Call recebida
typedef struct {
    char functionName[32];
    char rackId[16];
    char reason[128];
} ToolCall_t;

// Funções disponíveis
typedef enum {
    TOOL_TURN_ON_VENTILATION,
    TOOL_TURN_OFF_VENTILATION,
    TOOL_ACTIVATE_TEMP_ALERT,
    TOOL_SILENCE_BUZZER,
    TOOL_UNKNOWN
} ToolFunction_e;
```

## Tabela de Dispatch

```c
typedef struct {
    const char* name;
    ToolFunction_e function;
    esp_err_t (*handler)(const char* rackId);
} ToolDispatch_t;

static const ToolDispatch_t toolDispatchTable[] = {
    {"turnOnVentilation", TOOL_TURN_ON_VENTILATION, handleVentOn},
    {"turnOffVentilation", TOOL_TURN_OFF_VENTILATION, handleVentOff},
    {"activateCriticalTemperatureAlert", TOOL_ACTIVATE_TEMP_ALERT, handleTempAlert},
    {NULL, TOOL_UNKNOWN, NULL}
};
```
