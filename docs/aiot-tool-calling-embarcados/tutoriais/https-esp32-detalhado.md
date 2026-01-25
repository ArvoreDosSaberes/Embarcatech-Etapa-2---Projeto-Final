# HTTPS no ESP32: Guia Completo

> Tutorial detalhado sobre implementação de comunicação segura HTTPS em microcontroladores ESP32 usando ESP-IDF.

---

## 1. Por Que HTTPS é Obrigatório?

### APIs de IA Exigem TLS

Todas as APIs comerciais de LLM **rejeitam** conexões HTTP simples:

| Provedor | Endpoint | Requisito |
|----------|----------|-----------|
| OpenAI | api.openai.com | TLS 1.2+ |
| Anthropic | api.anthropic.com | TLS 1.2+ |
| Google AI | generativelanguage.googleapis.com | TLS 1.2+ |
| IBM watsonx | us-south.ml.cloud.ibm.com | TLS 1.2+ |

### Razões de Segurança

1. **Proteção de credenciais** — API keys trafegam no header `Authorization: Bearer sk-xxx`

2. **Privacidade dos dados** — Prompts e respostas podem conter dados sensíveis

3. **Integridade** — Certificados garantem que você fala com o servidor real

4. **Compliance** — Requisitos de segurança corporativa (SOC2, ISO 27001)

### Recursos do ESP32

| Recurso | ESP32 | ESP32-S3 | ESP32-C6 |
|---------|-------|----------|----------|
| RAM total | 520 KB | 512 KB | 512 KB |
| RAM por conexão TLS | ~40-60 KB | ~40-60 KB | ~40-60 KB |
| Flash mínima | 4 MB | 4 MB | 4 MB |
| Conexões TLS simultâneas | ~4-6 | ~4-6 | ~4-6 |

---

## 2. Fundamentos de TLS

### O Que Acontece em uma Conexão HTTPS

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. TCP HANDSHAKE                                                │
│    ESP32 ←──→ Servidor: SYN, SYN-ACK, ACK                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. TLS HANDSHAKE                                                │
│    a) ClientHello: ESP32 → Servidor                             │
│       - Versão TLS suportada (1.2, 1.3)                         │
│       - Cipher suites disponíveis                               │
│       - Random bytes                                            │
│                                                                 │
│    b) ServerHello: Servidor → ESP32                             │
│       - Versão TLS escolhida                                    │
│       - Cipher suite selecionada                                │
│       - Certificado do servidor                                 │
│                                                                 │
│    c) Verificação: ESP32                                        │
│       - Valida certificado contra CA raiz                       │
│       - Verifica hostname                                       │
│       - Verifica validade (datas)                               │
│                                                                 │
│    d) Key Exchange                                              │
│       - Troca de chaves Diffie-Hellman ou RSA                   │
│       - Geração de chave de sessão simétrica                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. COMUNICAÇÃO CRIPTOGRAFADA                                    │
│    - Dados HTTP trafegam criptografados                         │
│    - Cada direção usa chave derivada                            │
│    - MAC garante integridade                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Certificados X.509

O servidor apresenta um **certificado** que contém:
- Nome do servidor (CN/SAN)
- Chave pública
- Período de validade
- Assinatura de uma CA (Certificate Authority)

O cliente (ESP32) precisa de um **certificado raiz** da CA para validar a cadeia.

---

## 3. Configuração no ESP-IDF

### Opção 1: Bundle de Certificados (Recomendado)

O ESP-IDF inclui um bundle com certificados de CAs conhecidas:

```c
#include "esp_http_client.h"
#include "esp_crt_bundle.h"

/**
 * @brief Configura cliente HTTPS com bundle de certificados
 * 
 * O bundle inclui certificados de: Let's Encrypt, DigiCert,
 * GlobalSign, Comodo, etc.
 */
esp_http_client_config_t config = {
    .url = "https://api.openai.com/v1/chat/completions",
    .crt_bundle_attach = esp_crt_bundle_attach,
    .method = HTTP_METHOD_POST,
    .timeout_ms = 30000,
    .buffer_size = 4096,
    .buffer_size_tx = 2048,
};

esp_http_client_handle_t client = esp_http_client_init(&config);
```

**Habilitar no menuconfig:**
```
Component config → mbedTLS → Certificate Bundle
  [*] Enable trusted root certificate bundle
  [*] Add custom certificates to the default bundle
```

**Vantagens:**
- Funciona com qualquer servidor que use CA conhecida
- Atualizado com ESP-IDF
- Não requer manutenção de certificados

**Desvantagens:**
- Consome ~50-100 KB de flash
- Inclui CAs que você pode não precisar

### Opção 2: Certificado Específico

Para economizar flash ou usar CA privada:

```c
// Certificado embutido via CMake
extern const char server_cert_pem_start[] asm("_binary_ca_cert_pem_start");
extern const char server_cert_pem_end[] asm("_binary_ca_cert_pem_end");

esp_http_client_config_t config = {
    .url = "https://api.openai.com/v1/chat/completions",
    .cert_pem = server_cert_pem_start,
    .method = HTTP_METHOD_POST,
    .timeout_ms = 30000,
};
```

**No CMakeLists.txt do componente:**
```cmake
idf_component_register(
    SRCS "main.c"
    EMBED_TXTFILES "certs/isrg_root_x1.pem"
)
```

**Obter certificado raiz:**
```bash
# Para OpenAI (usa Let's Encrypt → ISRG Root X1)
openssl s_client -connect api.openai.com:443 -showcerts </dev/null 2>/dev/null | \
    openssl x509 -outform PEM > certs/openai_ca.pem
```

### Opção 3: Sem Verificação (APENAS PARA TESTES!)

```c
// ⚠️ NUNCA USE EM PRODUÇÃO!
esp_http_client_config_t config = {
    .url = "https://api.openai.com/v1/chat/completions",
    .skip_cert_common_name_check = true,
    .transport_type = HTTP_TRANSPORT_OVER_SSL,
    .method = HTTP_METHOD_POST,
};
```

---

## 4. Implementação Completa

### Estrutura do Módulo

```c
/**
 * @file https_client.h
 * @brief Cliente HTTPS para comunicação com APIs de LLM
 */

#ifndef HTTPS_CLIENT_H
#define HTTPS_CLIENT_H

#include "esp_err.h"

/** Tamanho máximo do buffer de resposta */
#define HTTPS_RESPONSE_BUFFER_SIZE  8192

/** Timeout padrão em ms */
#define HTTPS_DEFAULT_TIMEOUT_MS    30000

/**
 * @brief Configuração do cliente HTTPS
 */
typedef struct {
    const char* baseUrl;      /**< URL base da API */
    const char* apiKey;       /**< Chave de API (Bearer token) */
    uint32_t timeoutMs;       /**< Timeout em milissegundos */
} HttpsClientConfig_t;

/**
 * @brief Inicializa o cliente HTTPS
 * 
 * @param config Configuração do cliente
 * @return ESP_OK em sucesso
 */
esp_err_t https_client_init(const HttpsClientConfig_t* config);

/**
 * @brief Envia request POST e recebe resposta
 * 
 * @param endpoint Caminho do endpoint (ex: "/v1/chat/completions")
 * @param requestBody JSON do corpo do request
 * @param responseBuffer Buffer para resposta (deve ser alocado pelo caller)
 * @param responseBufferSize Tamanho do buffer
 * @param responseLength Tamanho real da resposta (output)
 * @return ESP_OK em sucesso
 */
esp_err_t https_client_post(
    const char* endpoint,
    const char* requestBody,
    char* responseBuffer,
    size_t responseBufferSize,
    size_t* responseLength
);

/**
 * @brief Libera recursos do cliente
 */
void https_client_cleanup(void);

#endif // HTTPS_CLIENT_H
```

### Implementação

```c
/**
 * @file https_client.c
 * @brief Implementação do cliente HTTPS para ESP32
 */

#include "https_client.h"
#include "esp_http_client.h"
#include "esp_crt_bundle.h"
#include "esp_log.h"
#include <string.h>

static const char* TAG = "HTTPS";

static HttpsClientConfig_t s_config;
static char s_fullUrl[256];
static bool s_initialized = false;


esp_err_t https_client_init(const HttpsClientConfig_t* config) {
    if (!config || !config->baseUrl || !config->apiKey) {
        ESP_LOGE(TAG, "Configuração inválida");
        return ESP_ERR_INVALID_ARG;
    }
    
    memcpy(&s_config, config, sizeof(HttpsClientConfig_t));
    
    if (s_config.timeoutMs == 0) {
        s_config.timeoutMs = HTTPS_DEFAULT_TIMEOUT_MS;
    }
    
    s_initialized = true;
    ESP_LOGI(TAG, "Cliente HTTPS inicializado para %s", s_config.baseUrl);
    
    return ESP_OK;
}


/**
 * @brief Handler de eventos HTTP
 */
static esp_err_t http_event_handler(esp_http_client_event_t* evt) {
    static size_t output_len = 0;
    
    switch (evt->event_id) {
        case HTTP_EVENT_ON_CONNECTED:
            ESP_LOGD(TAG, "Conectado");
            output_len = 0;
            break;
            
        case HTTP_EVENT_ON_DATA:
            // Copia dados para buffer do usuário
            if (evt->user_data && !esp_http_client_is_chunked_response(evt->client)) {
                char* buffer = (char*)evt->user_data;
                size_t buffer_size = HTTPS_RESPONSE_BUFFER_SIZE;
                
                if (output_len + evt->data_len < buffer_size) {
                    memcpy(buffer + output_len, evt->data, evt->data_len);
                    output_len += evt->data_len;
                    buffer[output_len] = '\0';
                } else {
                    ESP_LOGW(TAG, "Buffer de resposta cheio");
                }
            }
            break;
            
        case HTTP_EVENT_ON_FINISH:
            ESP_LOGD(TAG, "Request finalizado, %d bytes recebidos", output_len);
            break;
            
        case HTTP_EVENT_DISCONNECTED:
            ESP_LOGD(TAG, "Desconectado");
            break;
            
        default:
            break;
    }
    
    return ESP_OK;
}


esp_err_t https_client_post(
    const char* endpoint,
    const char* requestBody,
    char* responseBuffer,
    size_t responseBufferSize,
    size_t* responseLength
) {
    if (!s_initialized) {
        ESP_LOGE(TAG, "Cliente não inicializado");
        return ESP_ERR_INVALID_STATE;
    }
    
    if (!endpoint || !requestBody || !responseBuffer) {
        return ESP_ERR_INVALID_ARG;
    }
    
    // Monta URL completa
    snprintf(s_fullUrl, sizeof(s_fullUrl), "%s%s", s_config.baseUrl, endpoint);
    
    // Configura cliente
    esp_http_client_config_t httpConfig = {
        .url = s_fullUrl,
        .crt_bundle_attach = esp_crt_bundle_attach,
        .method = HTTP_METHOD_POST,
        .timeout_ms = s_config.timeoutMs,
        .buffer_size = 4096,
        .buffer_size_tx = 2048,
        .event_handler = http_event_handler,
        .user_data = responseBuffer,
    };
    
    esp_http_client_handle_t client = esp_http_client_init(&httpConfig);
    if (!client) {
        ESP_LOGE(TAG, "Falha ao criar cliente HTTP");
        return ESP_FAIL;
    }
    
    esp_err_t ret = ESP_FAIL;
    
    // Configura headers
    char authHeader[128];
    snprintf(authHeader, sizeof(authHeader), "Bearer %s", s_config.apiKey);
    
    esp_http_client_set_header(client, "Content-Type", "application/json");
    esp_http_client_set_header(client, "Authorization", authHeader);
    esp_http_client_set_header(client, "User-Agent", "ESP32-AIoT/1.0");
    
    // Configura body
    esp_http_client_set_post_field(client, requestBody, strlen(requestBody));
    
    ESP_LOGI(TAG, "Enviando POST para %s (%d bytes)", 
             endpoint, strlen(requestBody));
    
    // Executa request
    memset(responseBuffer, 0, responseBufferSize);
    
    esp_err_t err = esp_http_client_perform(client);
    
    if (err == ESP_OK) {
        int statusCode = esp_http_client_get_status_code(client);
        int contentLength = esp_http_client_get_content_length(client);
        
        ESP_LOGI(TAG, "Status: %d, Content-Length: %d", statusCode, contentLength);
        
        if (statusCode >= 200 && statusCode < 300) {
            if (responseLength) {
                *responseLength = strlen(responseBuffer);
            }
            ret = ESP_OK;
        } else {
            ESP_LOGE(TAG, "HTTP Error %d: %s", statusCode, responseBuffer);
            ret = ESP_ERR_HTTP_BASE + statusCode;
        }
    } else {
        ESP_LOGE(TAG, "Request falhou: %s", esp_err_to_name(err));
        ret = err;
    }
    
    esp_http_client_cleanup(client);
    return ret;
}


void https_client_cleanup(void) {
    s_initialized = false;
    ESP_LOGI(TAG, "Cliente HTTPS finalizado");
}
```

### Exemplo de Uso

```c
#include "https_client.h"
#include "cJSON.h"

void app_main(void) {
    // Inicializa WiFi primeiro...
    
    // Configura cliente HTTPS
    HttpsClientConfig_t config = {
        .baseUrl = "https://api.openai.com",
        .apiKey = CONFIG_OPENAI_API_KEY,  // Definido via Kconfig
        .timeoutMs = 30000,
    };
    
    ESP_ERROR_CHECK(https_client_init(&config));
    
    // Monta request body
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "model", "gpt-3.5-turbo");
    
    cJSON* messages = cJSON_CreateArray();
    cJSON* msg = cJSON_CreateObject();
    cJSON_AddStringToObject(msg, "role", "user");
    cJSON_AddStringToObject(msg, "content", "Olá!");
    cJSON_AddItemToArray(messages, msg);
    cJSON_AddItemToObject(root, "messages", messages);
    
    char* requestBody = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    
    // Envia request
    char responseBuffer[8192];
    size_t responseLen;
    
    esp_err_t err = https_client_post(
        "/v1/chat/completions",
        requestBody,
        responseBuffer,
        sizeof(responseBuffer),
        &responseLen
    );
    
    free(requestBody);
    
    if (err == ESP_OK) {
        ESP_LOGI("MAIN", "Resposta: %s", responseBuffer);
    }
    
    https_client_cleanup();
}
```

---

## 5. Troubleshooting

### Erro: "Certificate verify failed"

**Causa:** Certificado raiz não reconhecido ou expirado.

**Solução:**
1. Verifique se o bundle está habilitado no menuconfig
2. Atualize o ESP-IDF para versão mais recente
3. Adicione certificado específico se CA for desconhecida

### Erro: "Connection reset by peer"

**Causa:** Servidor fechou conexão, possivelmente por timeout ou TLS incompatível.

**Solução:**
1. Aumente `timeout_ms` (APIs de IA são lentas)
2. Verifique versão TLS no menuconfig
3. Reduza tamanho do request se muito grande

### Erro: "Out of memory"

**Causa:** RAM insuficiente para buffers TLS.

**Solução:**
1. Reduza `buffer_size` e `buffer_size_tx`
2. Limite conexões simultâneas
3. Use ESP32-S3 se precisar de mais RAM

### Erro: "DNS lookup failed"

**Causa:** Problema de rede ou DNS.

**Solução:**
1. Verifique conectividade WiFi
2. Use DNS público (8.8.8.8) via menuconfig
3. Teste com IP direto para isolar problema

---

## 6. Otimizações

### Reduzir Uso de Flash

```
Component config → mbedTLS → Certificate Bundle
  [ ] Enable trusted root certificate bundle
  
# Use apenas certificado específico no código
```

### Reduzir Uso de RAM

```
Component config → mbedTLS
  (16384) TLS maximum fragment length → 4096
  [ ] Enable hardware RSA
```

### Reusar Conexões

```c
// Não chame esp_http_client_cleanup() entre requests
// para reutilizar a sessão TLS

esp_http_client_set_url(client, newUrl);
esp_http_client_set_post_field(client, newBody, len);
esp_http_client_perform(client);  // Reutiliza conexão
```

---

## 7. Segurança

### Armazenamento de API Keys

**NUNCA** coloque API keys no código fonte:

```c
// ❌ ERRADO - Expõe chave no binário
const char* apiKey = "sk-abc123...";

// ✅ CERTO - Via Kconfig (não commita sdkconfig)
const char* apiKey = CONFIG_OPENAI_API_KEY;

// ✅ MELHOR - Via NVS (configurado em runtime)
char apiKey[64];
nvs_get_str(handle, "api_key", apiKey, &len);
```

**Kconfig.projbuild:**
```
config OPENAI_API_KEY
    string "OpenAI API Key"
    default ""
    help
        Chave de API da OpenAI. NÃO commite este valor!
```

### Validação de Certificados

Sempre valide certificados em produção:

```c
// ✅ CORRETO
.crt_bundle_attach = esp_crt_bundle_attach,

// ❌ NUNCA EM PRODUÇÃO
.skip_cert_common_name_check = true,
```

---

## 8. Referências

- [ESP-IDF HTTPS Client](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html)
- [mbedTLS Configuration](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/mbedtls.html)
- [ESP-IDF Certificate Bundle](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_crt_bundle.html)
