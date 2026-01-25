# Chamadas HTTPS à API OpenAI no ESP32

Este tutorial demonstra como fazer requisições HTTPS diretamente à API da OpenAI a partir do ESP32 usando o ESP-IDF, sem depender de bibliotecas de alto nível como a SDK oficial da OpenAI.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração do Projeto](#configuração-do-projeto)
3. [Certificados TLS](#certificados-tls)
4. [Cliente HTTP Básico](#cliente-http-básico)
5. [Requisição Chat Completions](#requisição-chat-completions)
6. [Tool Calling (Function Calling)](#tool-calling-function-calling)
7. [Parsing da Resposta JSON](#parsing-da-resposta-json)
8. [Boas Práticas](#boas-práticas)
9. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- **ESP-IDF v5.x** instalado e configurado
- **ESP32** com conectividade Wi-Fi funcional
- **Chave de API da OpenAI** válida
- Conhecimento básico de C e ESP-IDF

### Dependências do ESP-IDF

O ESP-IDF já inclui todas as bibliotecas necessárias:
- `esp_http_client` - Cliente HTTP/HTTPS
- `esp_tls` - Camada TLS para conexões seguras
- `cJSON` - Parser JSON (incluído no ESP-IDF)

---

## Configuração do Projeto

### 1. Estrutura de Diretórios

```
projeto/
├── main/
│   ├── CMakeLists.txt
│   ├── main.c
│   ├── openai_client.c
│   ├── openai_client.h
│   └── certs/
│       └── openai_root_ca.pem
├── CMakeLists.txt
└── sdkconfig
```

### 2. CMakeLists.txt (main)

```cmake
idf_component_register(
    SRCS "main.c" "openai_client.c"
    INCLUDE_DIRS "."
    EMBED_TXTFILES "certs/openai_root_ca.pem"
)
```

### 3. Configuração do sdkconfig

Certifique-se de habilitar as seguintes opções via `idf.py menuconfig`:

```
Component config → ESP-TLS → 
    [*] Allow potentially insecure options
    [*] Skip server certificate verification (NÃO usar em produção!)
    
Component config → ESP HTTP Client →
    [*] Enable HTTPS
    (16384) HTTP buffer size
```

---

## Certificados TLS

A API da OpenAI usa certificados emitidos por autoridades reconhecidas. Para conexões seguras, você precisa do certificado raiz.

### Obtendo o Certificado

1. Acesse `https://api.openai.com` no navegador
2. Clique no cadeado → Certificado → Detalhes
3. Exporte o certificado raiz (formato PEM)

Ou use o OpenSSL:

```bash
echo | openssl s_client -connect api.openai.com:443 -servername api.openai.com 2>/dev/null | \
    openssl x509 -outform PEM > openai_root_ca.pem
```

### Exemplo de Certificado (Baltimore CyberTrust Root)

Salve em `main/certs/openai_root_ca.pem`:

```
-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIEAgAAuTANBgkqhkiG9w0BAQUFADBaMQswCQYDVQQGEwJJ
RTESMBAGA1UEChMJQmFsdGltb3JlMRMwEQYDVQQLEwpDeWJlclRydXN0MSIwIAYD
VQQDExlCYWx0aW1vcmUgQ3liZXJUcnVzdCBSb290MB4XDTAwMDUxMjE4NDYwMFoX
DTI1MDUxMjIzNTkwMFowWjELMAkGA1UEBhMCSUUxEjAQBgNVBAoTCUJhbHRpbW9y
ZTETMBEGA1UECxMKQ3liZXJUcnVzdDEiMCAGA1UEAxMZQmFsdGltb3JlIEN5YmVy
VHJ1c3QgUm9vdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKMEuyKr
...
-----END CERTIFICATE-----
```

> **Nota:** O certificado exato pode variar. Sempre verifique o certificado atual.

---

## Cliente HTTP Básico

### openai_client.h

```c
/**
 * @file openai_client.h
 * @brief Cliente HTTPS para API OpenAI no ESP32
 * 
 * Este módulo fornece funções para comunicação com a API da OpenAI
 * via HTTPS, incluindo suporte a Chat Completions e Tool Calling.
 */

#ifndef OPENAI_CLIENT_H
#define OPENAI_CLIENT_H

#include <stddef.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Tamanho máximo do buffer de resposta */
#define OPENAI_RESPONSE_BUFFER_SIZE 4096

/** URL base da API OpenAI */
#define OPENAI_API_URL "https://api.openai.com/v1"

/** Endpoint de Chat Completions */
#define OPENAI_CHAT_ENDPOINT "/chat/completions"

/**
 * @brief Estrutura para armazenar a resposta da API
 */
typedef struct {
    char *data;           /**< Buffer com dados da resposta */
    size_t length;        /**< Tamanho dos dados recebidos */
    size_t capacity;      /**< Capacidade total do buffer */
    int status_code;      /**< Código HTTP da resposta */
} openai_response_t;

/**
 * @brief Configuração do cliente OpenAI
 */
typedef struct {
    const char *api_key;          /**< Chave de API (obrigatório) */
    const char *model;            /**< Modelo a usar (ex: "gpt-4o-mini") */
    int timeout_ms;               /**< Timeout em milissegundos */
    const char *cert_pem;         /**< Certificado PEM (opcional) */
} openai_config_t;

/**
 * @brief Inicializa o cliente OpenAI
 * 
 * @param config Configuração do cliente
 * @return ESP_OK em sucesso, código de erro caso contrário
 */
esp_err_t openai_init(const openai_config_t *config);

/**
 * @brief Libera recursos do cliente OpenAI
 */
void openai_cleanup(void);

/**
 * @brief Envia requisição de Chat Completion
 * 
 * @param messages_json JSON com array de mensagens
 * @param tools_json JSON com array de tools (opcional, NULL se não usar)
 * @param response Ponteiro para estrutura de resposta (será alocada)
 * @return ESP_OK em sucesso, código de erro caso contrário
 * 
 * @note O chamador é responsável por liberar response->data com free()
 */
esp_err_t openai_chat_completion(
    const char *messages_json,
    const char *tools_json,
    openai_response_t *response
);

/**
 * @brief Libera memória da resposta
 * 
 * @param response Ponteiro para estrutura de resposta
 */
void openai_response_free(openai_response_t *response);

#ifdef __cplusplus
}
#endif

#endif /* OPENAI_CLIENT_H */
```

### openai_client.c

```c
/**
 * @file openai_client.c
 * @brief Implementação do cliente HTTPS para API OpenAI
 */

#include "openai_client.h"
#include "esp_log.h"
#include "esp_http_client.h"
#include "esp_tls.h"
#include "cJSON.h"
#include <string.h>
#include <stdlib.h>

static const char *TAG = "openai_client";

/** Configuração global do cliente */
static openai_config_t g_config = {0};

/** Buffer temporário para resposta durante callback */
static char *g_response_buffer = NULL;
static size_t g_response_len = 0;

/**
 * @brief Callback para eventos HTTP
 * 
 * Processa eventos do cliente HTTP, acumulando dados da resposta.
 * 
 * @param evt Evento HTTP
 * @return ESP_OK sempre
 */
static esp_err_t http_event_handler(esp_http_client_event_t *evt)
{
    switch (evt->event_id) {
        case HTTP_EVENT_ON_DATA:
            if (!esp_http_client_is_chunked_response(evt->client)) {
                // Realocar buffer se necessário
                size_t new_len = g_response_len + evt->data_len;
                char *new_buffer = realloc(g_response_buffer, new_len + 1);
                if (new_buffer == NULL) {
                    ESP_LOGE(TAG, "Falha ao realocar buffer de resposta");
                    return ESP_ERR_NO_MEM;
                }
                g_response_buffer = new_buffer;
                memcpy(g_response_buffer + g_response_len, evt->data, evt->data_len);
                g_response_len = new_len;
                g_response_buffer[g_response_len] = '\0';
            }
            break;
            
        case HTTP_EVENT_ON_FINISH:
            ESP_LOGD(TAG, "Requisição finalizada, %d bytes recebidos", g_response_len);
            break;
            
        case HTTP_EVENT_DISCONNECTED:
            ESP_LOGD(TAG, "Desconectado");
            break;
            
        default:
            break;
    }
    return ESP_OK;
}

esp_err_t openai_init(const openai_config_t *config)
{
    if (config == NULL || config->api_key == NULL) {
        ESP_LOGE(TAG, "Configuração inválida: api_key é obrigatória");
        return ESP_ERR_INVALID_ARG;
    }
    
    memcpy(&g_config, config, sizeof(openai_config_t));
    
    // Valores padrão
    if (g_config.model == NULL) {
        g_config.model = "gpt-4o-mini";
    }
    if (g_config.timeout_ms == 0) {
        g_config.timeout_ms = 30000; // 30 segundos
    }
    
    ESP_LOGI(TAG, "Cliente OpenAI inicializado (modelo: %s)", g_config.model);
    return ESP_OK;
}

void openai_cleanup(void)
{
    if (g_response_buffer != NULL) {
        free(g_response_buffer);
        g_response_buffer = NULL;
    }
    g_response_len = 0;
    memset(&g_config, 0, sizeof(openai_config_t));
    ESP_LOGI(TAG, "Cliente OpenAI finalizado");
}

esp_err_t openai_chat_completion(
    const char *messages_json,
    const char *tools_json,
    openai_response_t *response)
{
    if (messages_json == NULL || response == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    
    esp_err_t ret = ESP_OK;
    char *post_data = NULL;
    char *auth_header = NULL;
    
    // Limpar resposta anterior
    if (g_response_buffer != NULL) {
        free(g_response_buffer);
        g_response_buffer = NULL;
    }
    g_response_len = 0;
    
    // Construir JSON do body
    cJSON *root = cJSON_CreateObject();
    if (root == NULL) {
        ESP_LOGE(TAG, "Falha ao criar objeto JSON");
        return ESP_ERR_NO_MEM;
    }
    
    cJSON_AddStringToObject(root, "model", g_config.model);
    
    // Parsear e adicionar messages
    cJSON *messages = cJSON_Parse(messages_json);
    if (messages == NULL) {
        ESP_LOGE(TAG, "Falha ao parsear messages JSON");
        cJSON_Delete(root);
        return ESP_ERR_INVALID_ARG;
    }
    cJSON_AddItemToObject(root, "messages", messages);
    
    // Adicionar tools se fornecido
    if (tools_json != NULL) {
        cJSON *tools = cJSON_Parse(tools_json);
        if (tools != NULL) {
            cJSON_AddItemToObject(root, "tools", tools);
            cJSON_AddStringToObject(root, "tool_choice", "auto");
        }
    }
    
    post_data = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    
    if (post_data == NULL) {
        ESP_LOGE(TAG, "Falha ao serializar JSON");
        return ESP_ERR_NO_MEM;
    }
    
    ESP_LOGD(TAG, "Request body: %s", post_data);
    
    // Construir header de autorização
    size_t auth_len = strlen("Bearer ") + strlen(g_config.api_key) + 1;
    auth_header = malloc(auth_len);
    if (auth_header == NULL) {
        free(post_data);
        return ESP_ERR_NO_MEM;
    }
    snprintf(auth_header, auth_len, "Bearer %s", g_config.api_key);
    
    // Configurar cliente HTTP
    char url[128];
    snprintf(url, sizeof(url), "%s%s", OPENAI_API_URL, OPENAI_CHAT_ENDPOINT);
    
    esp_http_client_config_t http_config = {
        .url = url,
        .method = HTTP_METHOD_POST,
        .event_handler = http_event_handler,
        .timeout_ms = g_config.timeout_ms,
        .cert_pem = g_config.cert_pem,
        .skip_cert_common_name_check = false,
    };
    
    esp_http_client_handle_t client = esp_http_client_init(&http_config);
    if (client == NULL) {
        ESP_LOGE(TAG, "Falha ao inicializar cliente HTTP");
        free(post_data);
        free(auth_header);
        return ESP_FAIL;
    }
    
    // Configurar headers
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_header(client, "Authorization", auth_header);
    esp_http_client_set_post_field(client, post_data, strlen(post_data));
    
    // Executar requisição
    ESP_LOGI(TAG, "Enviando requisição para %s", url);
    ret = esp_http_client_perform(client);
    
    if (ret == ESP_OK) {
        response->status_code = esp_http_client_get_status_code(client);
        response->length = g_response_len;
        response->data = g_response_buffer;
        response->capacity = g_response_len + 1;
        
        // Transferir ownership do buffer
        g_response_buffer = NULL;
        g_response_len = 0;
        
        ESP_LOGI(TAG, "Resposta recebida: HTTP %d, %d bytes",
                 response->status_code, response->length);
                 
        if (response->status_code != 200) {
            ESP_LOGW(TAG, "Resposta de erro: %s", response->data);
        }
    } else {
        ESP_LOGE(TAG, "Falha na requisição HTTP: %s", esp_err_to_name(ret));
    }
    
    // Cleanup
    esp_http_client_cleanup(client);
    free(post_data);
    free(auth_header);
    
    return ret;
}

void openai_response_free(openai_response_t *response)
{
    if (response != NULL && response->data != NULL) {
        free(response->data);
        response->data = NULL;
        response->length = 0;
        response->capacity = 0;
    }
}
```

---

## Requisição Chat Completions

### Exemplo Básico

```c
#include "openai_client.h"
#include "esp_log.h"
#include "cJSON.h"

static const char *TAG = "main";

// Certificado embarcado (definido em CMakeLists.txt)
extern const char openai_root_ca_pem_start[] asm("_binary_openai_root_ca_pem_start");
extern const char openai_root_ca_pem_end[] asm("_binary_openai_root_ca_pem_end");

void chat_example(void)
{
    // Inicializar cliente
    openai_config_t config = {
        .api_key = CONFIG_OPENAI_API_KEY,  // Definido no Kconfig
        .model = "gpt-4o-mini",
        .timeout_ms = 30000,
        .cert_pem = openai_root_ca_pem_start,
    };
    
    esp_err_t ret = openai_init(&config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Falha ao inicializar cliente OpenAI");
        return;
    }
    
    // Construir mensagens
    const char *messages = "["
        "{\"role\": \"system\", \"content\": \"Você é um assistente para IoT.\"},"
        "{\"role\": \"user\", \"content\": \"Qual a temperatura ideal para um rack de servidores?\"}"
    "]";
    
    openai_response_t response = {0};
    
    ret = openai_chat_completion(messages, NULL, &response);
    if (ret == ESP_OK && response.status_code == 200) {
        // Parsear resposta
        cJSON *json = cJSON_Parse(response.data);
        if (json != NULL) {
            cJSON *choices = cJSON_GetObjectItem(json, "choices");
            if (cJSON_IsArray(choices) && cJSON_GetArraySize(choices) > 0) {
                cJSON *first_choice = cJSON_GetArrayItem(choices, 0);
                cJSON *message = cJSON_GetObjectItem(first_choice, "message");
                cJSON *content = cJSON_GetObjectItem(message, "content");
                
                if (cJSON_IsString(content)) {
                    ESP_LOGI(TAG, "Resposta: %s", content->valuestring);
                }
            }
            cJSON_Delete(json);
        }
    }
    
    openai_response_free(&response);
    openai_cleanup();
}
```

---

## Tool Calling (Function Calling)

O Tool Calling permite que o modelo solicite a execução de funções locais no ESP32.

### Definindo Tools

```c
/**
 * @brief Definição de tools para controle do rack
 */
const char *RACK_TOOLS = "["
    "{"
        "\"type\": \"function\","
        "\"function\": {"
            "\"name\": \"get_temperature\","
            "\"description\": \"Obtém a temperatura atual do sensor DHT22\","
            "\"parameters\": {"
                "\"type\": \"object\","
                "\"properties\": {},"
                "\"required\": []"
            "}"
        "}"
    "},"
    "{"
        "\"type\": \"function\","
        "\"function\": {"
            "\"name\": \"set_ventilation\","
            "\"description\": \"Controla o sistema de ventilação do rack\","
            "\"parameters\": {"
                "\"type\": \"object\","
                "\"properties\": {"
                    "\"enabled\": {"
                        "\"type\": \"boolean\","
                        "\"description\": \"true para ligar, false para desligar\""
                    "}"
                "},"
                "\"required\": [\"enabled\"]"
            "}"
        "}"
    "},"
    "{"
        "\"type\": \"function\","
        "\"function\": {"
            "\"name\": \"get_door_status\","
            "\"description\": \"Verifica se a porta do rack está aberta ou fechada\","
            "\"parameters\": {"
                "\"type\": \"object\","
                "\"properties\": {},"
                "\"required\": []"
            "}"
        "}"
    "}"
"]";
```

### Fluxo Completo de Tool Calling

```c
#include "openai_client.h"
#include "esp_log.h"
#include "cJSON.h"

static const char *TAG = "tool_calling";

/**
 * @brief Executa uma função local baseada na chamada do modelo
 * 
 * @param function_name Nome da função a executar
 * @param arguments JSON com argumentos
 * @return String JSON com resultado (deve ser liberada pelo chamador)
 */
static char* execute_tool(const char *function_name, const char *arguments)
{
    cJSON *result = cJSON_CreateObject();
    
    if (strcmp(function_name, "get_temperature") == 0) {
        // Simular leitura do sensor (substituir por código real)
        float temp = 23.5;
        float humidity = 45.0;
        cJSON_AddNumberToObject(result, "temperature", temp);
        cJSON_AddNumberToObject(result, "humidity", humidity);
        cJSON_AddStringToObject(result, "unit", "celsius");
        
    } else if (strcmp(function_name, "set_ventilation") == 0) {
        cJSON *args = cJSON_Parse(arguments);
        if (args != NULL) {
            cJSON *enabled = cJSON_GetObjectItem(args, "enabled");
            if (cJSON_IsBool(enabled)) {
                bool state = cJSON_IsTrue(enabled);
                // Aqui você controlaria o GPIO da ventilação
                ESP_LOGI(TAG, "Ventilação %s", state ? "LIGADA" : "DESLIGADA");
                cJSON_AddBoolToObject(result, "success", true);
                cJSON_AddBoolToObject(result, "ventilation_on", state);
            }
            cJSON_Delete(args);
        }
        
    } else if (strcmp(function_name, "get_door_status") == 0) {
        // Simular leitura do sensor de porta
        bool door_open = false;  // GPIO read
        cJSON_AddBoolToObject(result, "door_open", door_open);
        cJSON_AddStringToObject(result, "status", door_open ? "aberta" : "fechada");
        
    } else {
        cJSON_AddBoolToObject(result, "error", true);
        cJSON_AddStringToObject(result, "message", "Função desconhecida");
    }
    
    char *result_str = cJSON_PrintUnformatted(result);
    cJSON_Delete(result);
    return result_str;
}

/**
 * @brief Processa tool calls na resposta do modelo
 * 
 * @param response Resposta da API
 * @param messages_array Array JSON de mensagens (será modificado)
 * @return true se há tool calls para processar
 */
static bool process_tool_calls(openai_response_t *response, cJSON *messages_array)
{
    cJSON *json = cJSON_Parse(response->data);
    if (json == NULL) return false;
    
    cJSON *choices = cJSON_GetObjectItem(json, "choices");
    if (!cJSON_IsArray(choices) || cJSON_GetArraySize(choices) == 0) {
        cJSON_Delete(json);
        return false;
    }
    
    cJSON *first_choice = cJSON_GetArrayItem(choices, 0);
    cJSON *message = cJSON_GetObjectItem(first_choice, "message");
    cJSON *finish_reason = cJSON_GetObjectItem(first_choice, "finish_reason");
    
    // Verificar se é uma chamada de tool
    if (!cJSON_IsString(finish_reason) || 
        strcmp(finish_reason->valuestring, "tool_calls") != 0) {
        cJSON_Delete(json);
        return false;
    }
    
    cJSON *tool_calls = cJSON_GetObjectItem(message, "tool_calls");
    if (!cJSON_IsArray(tool_calls)) {
        cJSON_Delete(json);
        return false;
    }
    
    // Adicionar mensagem do assistente com tool_calls ao histórico
    cJSON *assistant_msg = cJSON_Duplicate(message, true);
    cJSON_AddItemToArray(messages_array, assistant_msg);
    
    // Processar cada tool call
    cJSON *tool_call;
    cJSON_ArrayForEach(tool_call, tool_calls) {
        cJSON *id = cJSON_GetObjectItem(tool_call, "id");
        cJSON *function = cJSON_GetObjectItem(tool_call, "function");
        cJSON *name = cJSON_GetObjectItem(function, "name");
        cJSON *arguments = cJSON_GetObjectItem(function, "arguments");
        
        if (!cJSON_IsString(id) || !cJSON_IsString(name)) {
            continue;
        }
        
        ESP_LOGI(TAG, "Executando tool: %s(%s)", 
                 name->valuestring, 
                 arguments ? arguments->valuestring : "");
        
        // Executar a função
        char *result = execute_tool(
            name->valuestring,
            arguments ? arguments->valuestring : "{}"
        );
        
        // Adicionar resposta da tool ao histórico
        cJSON *tool_response = cJSON_CreateObject();
        cJSON_AddStringToObject(tool_response, "role", "tool");
        cJSON_AddStringToObject(tool_response, "tool_call_id", id->valuestring);
        cJSON_AddStringToObject(tool_response, "content", result);
        cJSON_AddItemToArray(messages_array, tool_response);
        
        free(result);
    }
    
    cJSON_Delete(json);
    return true;
}

/**
 * @brief Exemplo completo de conversa com tool calling
 */
void tool_calling_example(void)
{
    // Inicializar cliente (igual ao exemplo anterior)
    openai_config_t config = {
        .api_key = CONFIG_OPENAI_API_KEY,
        .model = "gpt-4o-mini",
        .timeout_ms = 30000,
    };
    openai_init(&config);
    
    // Criar array de mensagens
    cJSON *messages = cJSON_CreateArray();
    
    // Mensagem de sistema
    cJSON *system_msg = cJSON_CreateObject();
    cJSON_AddStringToObject(system_msg, "role", "system");
    cJSON_AddStringToObject(system_msg, "content", 
        "Você é um assistente de controle de rack de servidores. "
        "Use as tools disponíveis para obter informações e executar comandos.");
    cJSON_AddItemToArray(messages, system_msg);
    
    // Mensagem do usuário
    cJSON *user_msg = cJSON_CreateObject();
    cJSON_AddStringToObject(user_msg, "role", "user");
    cJSON_AddStringToObject(user_msg, "content", 
        "Verifique a temperatura do rack. Se estiver acima de 25°C, ligue a ventilação.");
    cJSON_AddItemToArray(messages, user_msg);
    
    openai_response_t response = {0};
    bool has_tool_calls = true;
    int max_iterations = 5;  // Limite de segurança
    
    while (has_tool_calls && max_iterations-- > 0) {
        char *messages_str = cJSON_PrintUnformatted(messages);
        
        esp_err_t ret = openai_chat_completion(messages_str, RACK_TOOLS, &response);
        free(messages_str);
        
        if (ret != ESP_OK || response.status_code != 200) {
            ESP_LOGE(TAG, "Erro na requisição");
            break;
        }
        
        has_tool_calls = process_tool_calls(&response, messages);
        
        if (!has_tool_calls) {
            // Resposta final do modelo
            cJSON *json = cJSON_Parse(response.data);
            if (json != NULL) {
                cJSON *choices = cJSON_GetObjectItem(json, "choices");
                cJSON *first = cJSON_GetArrayItem(choices, 0);
                cJSON *msg = cJSON_GetObjectItem(first, "message");
                cJSON *content = cJSON_GetObjectItem(msg, "content");
                
                if (cJSON_IsString(content)) {
                    ESP_LOGI(TAG, "Resposta final: %s", content->valuestring);
                }
                cJSON_Delete(json);
            }
        }
        
        openai_response_free(&response);
    }
    
    cJSON_Delete(messages);
    openai_cleanup();
}
```

---

## Parsing da Resposta JSON

### Estrutura da Resposta

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Resposta do modelo..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  }
}
```

### Resposta com Tool Calls

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_temperature",
              "arguments": "{}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### Helper para Extrair Conteúdo

```c
/**
 * @brief Extrai o conteúdo da resposta de chat
 * 
 * @param response Resposta da API
 * @return String com conteúdo (deve ser liberada) ou NULL
 */
char* extract_chat_content(openai_response_t *response)
{
    if (response == NULL || response->data == NULL) {
        return NULL;
    }
    
    cJSON *json = cJSON_Parse(response->data);
    if (json == NULL) {
        return NULL;
    }
    
    char *content = NULL;
    cJSON *choices = cJSON_GetObjectItem(json, "choices");
    
    if (cJSON_IsArray(choices) && cJSON_GetArraySize(choices) > 0) {
        cJSON *first = cJSON_GetArrayItem(choices, 0);
        cJSON *message = cJSON_GetObjectItem(first, "message");
        cJSON *content_json = cJSON_GetObjectItem(message, "content");
        
        if (cJSON_IsString(content_json) && content_json->valuestring != NULL) {
            content = strdup(content_json->valuestring);
        }
    }
    
    cJSON_Delete(json);
    return content;
}
```

---

## Boas Práticas

### 1. Segurança da API Key

Nunca hardcode a API key no código. Use Kconfig:

```kconfig
# Kconfig.projbuild
menu "OpenAI Configuration"
    config OPENAI_API_KEY
        string "OpenAI API Key"
        default ""
        help
            Chave de API da OpenAI. NÃO commite este valor!
endmenu
```

### 2. Gerenciamento de Memória

```c
// Sempre verifique alocações
char *buffer = malloc(size);
if (buffer == NULL) {
    ESP_LOGE(TAG, "Falha de alocação");
    return ESP_ERR_NO_MEM;
}

// Use heap_caps para buffers grandes
char *large_buffer = heap_caps_malloc(16384, MALLOC_CAP_SPIRAM);
if (large_buffer == NULL) {
    // Fallback para RAM interna
    large_buffer = heap_caps_malloc(8192, MALLOC_CAP_DEFAULT);
}

// Sempre libere memória
free(buffer);
```

### 3. Timeouts e Retries

```c
#define MAX_RETRIES 3
#define RETRY_DELAY_MS 2000

esp_err_t send_with_retry(const char *messages, openai_response_t *response)
{
    esp_err_t ret = ESP_FAIL;
    
    for (int i = 0; i < MAX_RETRIES; i++) {
        ret = openai_chat_completion(messages, NULL, response);
        
        if (ret == ESP_OK && response->status_code == 200) {
            return ESP_OK;
        }
        
        // Verificar erro recuperável
        if (response->status_code == 429) {  // Rate limit
            ESP_LOGW(TAG, "Rate limit, aguardando...");
            vTaskDelay(pdMS_TO_TICKS(RETRY_DELAY_MS * (i + 1)));
            openai_response_free(response);
            continue;
        }
        
        if (response->status_code >= 500) {  // Erro do servidor
            ESP_LOGW(TAG, "Erro do servidor, tentando novamente...");
            vTaskDelay(pdMS_TO_TICKS(RETRY_DELAY_MS));
            openai_response_free(response);
            continue;
        }
        
        // Erro não recuperável
        break;
    }
    
    return ret;
}
```

### 4. Controle de Tokens

```c
/**
 * @brief Estima tokens de uma string (aproximação)
 * 
 * Regra geral: ~4 caracteres = 1 token para inglês
 *              ~3 caracteres = 1 token para português
 */
int estimate_tokens(const char *text)
{
    if (text == NULL) return 0;
    return strlen(text) / 3;
}

// Limitar contexto para evitar custos excessivos
#define MAX_CONTEXT_TOKENS 2000

void trim_context(cJSON *messages)
{
    int total_tokens = 0;
    int count = cJSON_GetArraySize(messages);
    
    // Manter system message + últimas mensagens
    // Remover mensagens antigas se exceder limite
    // ...
}
```

---

## Troubleshooting

### Erros Comuns

| Código HTTP | Causa | Solução |
|-------------|-------|---------|
| 401 | API key inválida | Verificar chave no Kconfig |
| 429 | Rate limit excedido | Implementar backoff exponencial |
| 500 | Erro do servidor OpenAI | Retry com delay |
| -1 | Erro de conexão | Verificar Wi-Fi e certificados |

### Debug de TLS

```c
// Habilitar logs detalhados de TLS
esp_log_level_set("esp-tls", ESP_LOG_DEBUG);
esp_log_level_set("esp_http_client", ESP_LOG_DEBUG);
```

### Verificar Heap

```c
ESP_LOGI(TAG, "Free heap: %lu bytes", esp_get_free_heap_size());
ESP_LOGI(TAG, "Min free heap: %lu bytes", esp_get_minimum_free_heap_size());
```

### Problemas de Certificado

```c
// Para testes (NÃO usar em produção!)
esp_http_client_config_t config = {
    // ...
    .skip_cert_common_name_check = true,
    .cert_pem = NULL,  // Desabilita verificação
};
```

---

## Referências

- [ESP-IDF HTTP Client](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [OpenAI Tool Calling](https://platform.openai.com/docs/guides/function-calling)
- [cJSON Library](https://github.com/DaveGamble/cJSON)

---

*Última atualização: Dezembro 2024*
