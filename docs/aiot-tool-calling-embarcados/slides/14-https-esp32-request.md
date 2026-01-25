# 🔒 HTTPS no ESP32 — Enviando Request

## Montando o Payload JSON

```c
char* buildChatRequest(const char* systemPrompt, 
                       const char* userMessage) {
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "model", "gpt-4");
    
    cJSON* messages = cJSON_CreateArray();
    
    // System message
    cJSON* sysMsg = cJSON_CreateObject();
    cJSON_AddStringToObject(sysMsg, "role", "system");
    cJSON_AddStringToObject(sysMsg, "content", systemPrompt);
    cJSON_AddItemToArray(messages, sysMsg);
    
    // User message
    cJSON* usrMsg = cJSON_CreateObject();
    cJSON_AddStringToObject(usrMsg, "role", "user");
    cJSON_AddStringToObject(usrMsg, "content", userMessage);
    cJSON_AddItemToArray(messages, usrMsg);
    
    cJSON_AddItemToObject(root, "messages", messages);
    
    char* jsonStr = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    return jsonStr;  // Caller deve free()
}
```

## Enviando via esp_http_client

```c
esp_http_client_set_post_field(client, jsonStr, strlen(jsonStr));
esp_err_t err = esp_http_client_perform(client);
```
