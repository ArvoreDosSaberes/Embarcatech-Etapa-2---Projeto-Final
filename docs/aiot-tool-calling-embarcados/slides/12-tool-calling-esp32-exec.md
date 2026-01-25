# 📟 Tool Calling no ESP32 — Execução

## Dispatcher de Funções

```c
esp_err_t executeToolCall(const ToolCall_t* toolCall) {
    ESP_LOGI(TAG, "Executando: %s para rack %s", 
             toolCall->functionName, toolCall->rackId);
    
    // Busca na tabela de dispatch
    for (int i = 0; toolDispatchTable[i].name != NULL; i++) {
        if (strcmp(toolDispatchTable[i].name, 
                   toolCall->functionName) == 0) {
            return toolDispatchTable[i].handler(toolCall->rackId);
        }
    }
    
    ESP_LOGW(TAG, "Função desconhecida: %s", toolCall->functionName);
    return ESP_ERR_NOT_FOUND;
}

// Handler de exemplo
esp_err_t handleVentOn(const char* rackId) {
    gpio_set_level(GPIO_VENTILATION, 1);
    ESP_LOGI(TAG, "Ventilação LIGADA - Rack %s", rackId);
    return ESP_OK;
}
```

## Fluxo Completo

```
[MQTT Telemetria] → [Servidor LLM] → [Tool Call JSON]
       ↓                                    ↓
   [ESP32]  ← ←  ← ← ← ← ← ← ← ← ← ← ← ← [Parse + Execute]
```
