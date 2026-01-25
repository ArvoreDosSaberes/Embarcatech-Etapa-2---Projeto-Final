# 📟 Tool Calling no ESP32 — Parse JSON

## Usando cJSON (ESP-IDF)

```c
#include "cJSON.h"

esp_err_t parseToolCall(const char* jsonStr, ToolCall_t* toolCall) {
    cJSON* root = cJSON_Parse(jsonStr);
    if (!root) return ESP_ERR_INVALID_ARG;
    
    // Navega até tool_calls[0].function
    cJSON* toolCalls = cJSON_GetObjectItem(root, "tool_calls");
    cJSON* firstCall = cJSON_GetArrayItem(toolCalls, 0);
    cJSON* function = cJSON_GetObjectItem(firstCall, "function");
    
    // Extrai nome da função
    cJSON* name = cJSON_GetObjectItem(function, "name");
    strncpy(toolCall->functionName, name->valuestring, 31);
    
    // Parse dos argumentos (string JSON aninhada)
    cJSON* argsStr = cJSON_GetObjectItem(function, "arguments");
    cJSON* args = cJSON_Parse(argsStr->valuestring);
    
    cJSON* rackId = cJSON_GetObjectItem(args, "rackId");
    strncpy(toolCall->rackId, rackId->valuestring, 15);
    
    cJSON_Delete(args);
    cJSON_Delete(root);
    return ESP_OK;
}
```

> cJSON é leve e já vem no ESP-IDF!
