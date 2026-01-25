# 🔒 HTTPS no ESP32 — Requisito para APIs de IA

## Por Que HTTPS é Obrigatório?

- **OpenAI, IBM, Google** — Todas exigem HTTPS
- **Tokens de API** — Devem trafegar criptografados
- **Dados sensíveis** — Telemetria pode ser confidencial

## Configuração no ESP-IDF

```c
#include "esp_http_client.h"
#include "esp_tls.h"

// Certificado raiz (ex: Let's Encrypt)
extern const char server_cert_pem[] asm("_binary_ca_cert_pem_start");

esp_http_client_config_t config = {
    .url = "https://api.openai.com/v1/chat/completions",
    .cert_pem = server_cert_pem,
    .method = HTTP_METHOD_POST,
    .timeout_ms = 30000,
};

esp_http_client_handle_t client = esp_http_client_init(&config);

// Headers obrigatórios
esp_http_client_set_header(client, "Content-Type", "application/json");
esp_http_client_set_header(client, "Authorization", "Bearer sk-xxx...");
```

## Dicas Importantes

- **Certificados**: Embed no firmware via `component.mk`
- **Memória**: HTTPS consome ~40KB de RAM
- **Timeout**: APIs de IA podem demorar 5-30s
