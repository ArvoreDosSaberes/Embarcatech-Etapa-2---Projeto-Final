# AIoT e Tool Calling em Sistemas Embarcados

**Da Inteligência Artificial na Nuvem ao Microcontrolador ESP32**

> Este tutorial aprofundado acompanha a apresentação "AIoT e Tool Calling em Sistemas Embarcados" e expande cada tópico de forma didática para desenvolvedores de sistemas embarcados.

---

## Sumário

1. [Introdução: A Cultura da Barba e Grandes Inovadores](#capítulo-1-introdução)
2. ["Inteligência Artificial" — É Certo Usar Este Nome?](#capítulo-2-inteligência-artificial)
3. [GenAIs e LLMs — O Que São](#capítulo-3-genais-e-llms)
4. [O Que é AIoT?](#capítulo-4-aiot)
5. [Time Series com Granite TTM](#capítulo-5-time-series)
6. [O Que São Tool Callings?](#capítulo-6-tool-calling)
7. [Tool Calling em Python](#capítulo-7-tool-calling-python)
8. [Tool Calling no ESP32 em C](#capítulo-8-tool-calling-esp32)
9. [HTTPS no ESP32](#capítulo-9-https-esp32)
10. [OpenAI para Demonstração](#capítulo-10-openai-demo)
11. [Arquitetura Completa](#capítulo-11-arquitetura)
12. [Conclusões](#capítulo-12-conclusoes)

---

## Capítulo 1: Introdução

### O Movimento Beard Culture / Beard Brotherhood

Antes de mergulharmos no universo técnico, vale uma reflexão sobre os grandes nomes que moldaram a computação moderna. Curiosamente, muitos compartilham uma característica: suas barbas icônicas.

O **Beard Culture** e o **Beard Brotherhood** são movimentos informais online que celebram a barba como símbolo de **maturidade**, **força**, **autenticidade** e **irmandade**.

### Grandes Barbas da História da Tecnologia

- **Dennis Ritchie** — Criador da linguagem C e Unix
- **Ken Thompson** — Co-criador do Unix e Go
- **Richard Stallman** — Fundador do GNU e Software Livre
- **Linus Torvalds** — Criador do kernel Linux

Todo código C que roda em um ESP32 deve algo a esses pioneiros!

---

## Capítulo 2: Inteligência Artificial

### A Origem do Termo

O termo "Inteligência Artificial" foi cunhado em **1956** por **John McCarthy** durante a Conferência de Dartmouth. Foi, em grande parte, **marketing acadêmico** para atrair financiamento.

### O Debate Filosófico

**Argumentos contra o termo:**
- Máquinas não "pensam" — executam operações matemáticas
- Não há consciência ou experiência subjetiva
- Correlação não é compreensão

**Argumentos a favor:**
- Definição funcional — se produz resultados indistinguíveis, é funcionalmente inteligente
- O termo está consolidado há quase 70 anos

### O Que Realmente Temos Hoje

| Chamamos | Tecnicamente é |
|----------|----------------|
| Inteligência Artificial | Álgebra linear + estatística massiva |
| Aprendizado | Otimização de parâmetros |
| Compreensão | Correlação probabilística |

### Implicações para Desenvolvedores Embarcados

- **Não espere magia** — LLMs são ferramentas previsíveis e limitadas
- **Entenda os limites** — Modelos podem "alucinar"
- **Valide sempre** — Nunca confie cegamente para sistemas críticos
- **Use como ferramenta** — IA é assistente, não substituto para engenharia sólida

---

## Capítulo 3: GenAIs e LLMs

### Generative AI (GenAI)

Sistemas capazes de **criar conteúdo novo**: texto, imagens, código, áudio. Aprendem distribuições de probabilidade e **amostram** para gerar novos exemplos.

### Large Language Models (LLMs)

Modelos com **bilhões de parâmetros** focados em linguagem:

| Modelo | Parâmetros | Organização |
|--------|------------|-------------|
| GPT-4 | ~1.7T (estimado) | OpenAI |
| Llama 3 | 8B-405B | Meta |
| Granite | 3B-34B | IBM |
| Claude 3 | Não divulgado | Anthropic |

### Arquitetura Transformer

```
[Entrada] → [Tokenização] → [Embedding] → [Atenção] → [Predição] → [Saída]
```

O mecanismo de **self-attention** permite que cada token "preste atenção" em todos os outros, capturando relações de longo alcance.

### Limitações Fundamentais

1. **Alucinações** — Geram informações incorretas com alta confiança
2. **Janela de contexto limitada** — 4K a 128K tokens
3. **Conhecimento desatualizado** — Congelado na data de treinamento
4. **Custo computacional** — Requerem GPUs ou muita RAM

---

## Capítulo 4: AIoT

### Definição

**AIoT** = AI + IoT — dispositivos que **coletam dados**, **processam com IA** e **executam ações** no mundo físico.

### Arquiteturas

| Modelo | Processamento | Latência | Custo |
|--------|---------------|----------|-------|
| Cloud AI | 100% nuvem | Alta | Baixo/dispositivo |
| Edge AI | No dispositivo | Mínima | Alto/dispositivo |
| Híbrido | Distribuído | Média | Balanceado |

### Nosso Projeto: Rack Inteligente

```
[ESP32] --MQTT--> [Dashboard Python] --HTTPS--> [LLM]
   ↑                                               |
   |                                               ↓
   └──────────── Comandos via MQTT ←── Tool Calls ─┘
```

O ESP32 não roda a LLM — seria inviável com 520KB de SRAM. Ele:
1. Envia telemetria via MQTT
2. Dashboard consulta LLM
3. LLM retorna Tool Calls
4. Dashboard envia comandos MQTT
5. ESP32 executa ações físicas

---

## Capítulo 5: Time Series

### Séries Temporais

Sequência de observações ordenadas no tempo onde a **ordem importa** — cada ponto depende dos anteriores.

### IBM Granite TTM

Modelo de deep learning da IBM para previsão de séries temporais:

| Característica | Valor |
|----------------|-------|
| Arquitetura | MLP-Mixer adaptado |
| Parâmetros | ~1M (leve!) |
| Pré-treinamento | Milhões de séries |
| Sazonalidade | Automática |

### Arquitetura Híbrida com Fallback

```
[Dados] → [Granite TTM] → [Previsão]
              ↓ (se MAE alto)
         [SARIMA Fallback]
```

O **MAE** (Mean Absolute Error) decide quando trocar para SARIMA, modelo estatístico clássico mais leve e determinístico.

---

## Capítulo 6: Tool Calling

### Definição

Capacidade dos LLMs de **invocar funções externas**:
1. LLM analisa contexto
2. Decide qual ferramenta usar
3. Gera chamada estruturada (JSON)
4. Sistema executa função
5. Resultado retorna ao LLM

### Fluxo

```
"Temperatura 38°C" → [LLM] → tool_call: turnOnVentilation(rackId="001")
                                                    ↓
                                            [Sistema executa]
```

### Por Que é Poderoso?

- **LLM decide, sistema executa** — Separação de responsabilidades
- **Validação de schema** — JSON estruturado e validado
- **Contexto semântico** — Entende intenção, não apenas comandos

---

## Capítulo 7: Tool Calling Python

### Definição de Tools

```python
TOOLS_DEFINITION = [{
    "type": "function",
    "function": {
        "name": "turnOnVentilation",
        "description": "Liga ventilação quando temp >=35°C",
        "parameters": {
            "type": "object",
            "properties": {
                "rackId": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["rackId", "reason"]
        }
    }
}]
```

### Chamada à API

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    tools=TOOLS_DEFINITION,
    tool_choice="auto"
)
```

### Processamento

```python
if message.tool_calls:
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        # Executa função correspondente
```

---

## Capítulo 8: Tool Calling ESP32

### Estruturas em C

```c
typedef struct {
    char functionName[32];
    char rackId[16];
    char reason[128];
} ToolCall_t;

typedef esp_err_t (*ToolHandler_t)(const char* rackId);

static const struct {
    const char* name;
    ToolHandler_t handler;
} toolDispatchTable[] = {
    {"turnOnVentilation", handleVentOn},
    {"turnOffVentilation", handleVentOff},
    {NULL, NULL}
};
```

### Parsing com cJSON

```c
esp_err_t parseToolCall(const char* json, ToolCall_t* tc) {
    cJSON* root = cJSON_Parse(json);
    cJSON* func = cJSON_GetObjectItem(..., "function");
    cJSON* name = cJSON_GetObjectItem(func, "name");
    strncpy(tc->functionName, name->valuestring, 31);
    cJSON_Delete(root);
    return ESP_OK;
}
```

### Execução

```c
esp_err_t executeToolCall(const ToolCall_t* tc) {
    for (int i = 0; toolDispatchTable[i].name; i++) {
        if (strcmp(toolDispatchTable[i].name, tc->functionName) == 0) {
            return toolDispatchTable[i].handler(tc->rackId);
        }
    }
    return ESP_ERR_NOT_FOUND;
}
```

---

## Capítulo 9: HTTPS ESP32

### Por Que Obrigatório?

- APIs de IA exigem HTTPS
- Tokens Bearer no header Authorization
- Dados sensíveis na comunicação

### Configuração ESP-IDF

```c
#include "esp_http_client.h"
#include "esp_crt_bundle.h"

esp_http_client_config_t config = {
    .url = "https://api.openai.com/v1/chat/completions",
    .crt_bundle_attach = esp_crt_bundle_attach,
    .method = HTTP_METHOD_POST,
    .timeout_ms = 30000,
};

esp_http_client_handle_t client = esp_http_client_init(&config);
esp_http_client_set_header(client, "Content-Type", "application/json");
esp_http_client_set_header(client, "Authorization", "Bearer sk-xxx");
```

### Recursos Necessários

- **RAM**: ~40-60 KB por conexão TLS
- **Flash**: Bundle de certificados ou cert específico
- **Timeout**: 30s+ (APIs de IA são lentas)

---

## Capítulo 10: OpenAI Demo

### Obtendo Acesso

1. Criar conta em [platform.openai.com](https://platform.openai.com)
2. Créditos iniciais $5-18 para novos usuários
3. Gerar API Key em Settings → API Keys

### Modelos Econômicos

| Modelo | Custo/1K tokens |
|--------|-----------------|
| gpt-3.5-turbo | ~$0.002 |
| gpt-4o-mini | ~$0.00015 |

### Alternativa: Ollama Local

```bash
ollama run llama3
# API compatível em localhost:11434
```

---

## Capítulo 11: Arquitetura

```
┌─────────┐     MQTT      ┌───────────┐
│  ESP32  │ ────────────→ │ Dashboard │
│Firmware │ ←──────────── │  Python   │
└─────────┘   Comandos    └─────┬─────┘
                                │ HTTPS
                          ┌─────▼─────┐
                          │    LLM    │
                          │Tool Call  │
                          └───────────┘
```

**Componentes:**
- **ESP32**: Sensores, atuadores, MQTT
- **Dashboard**: UI, gráficos, orquestração
- **ToolCallingService**: Decisões via LLM
- **ForecastService**: Granite + SARIMA

---

## Capítulo 12: Conclusões

### Aprendizados

- IA é estatística avançada — útil, mas não mágica
- Tool Calling permite decisões semânticas
- ESP32 pode ser "inteligente" via nuvem
- Arquitetura híbrida garante robustez

### Próximos Passos

- **Edge AI**: TinyML no ESP32
- **Latência**: Decisões locais vs nuvem
- **Custo**: Ollama local vs APIs pagas

> "O melhor momento para começar com IA embarcada foi ontem. O segundo melhor é agora!"

---

## Referências

- [IBM Granite TTM](https://ibm.github.io/granite-tsfm)
- [ESP-IDF Documentation](https://docs.espressif.com)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Ollama](https://ollama.ai)
