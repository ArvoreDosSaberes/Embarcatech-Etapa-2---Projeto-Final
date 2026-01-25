# GenAI e LLMs: Fundamentos para Desenvolvedores Embarcados

> Guia didático sobre Inteligência Artificial Generativa e Modelos de Linguagem para quem vem do mundo de sistemas embarcados.

---

## 1. O Que é Inteligência Artificial?

### A Definição Polêmica

O termo "Inteligência Artificial" foi cunhado em **1956** por John McCarthy como estratégia de marketing acadêmico. Desde então, o debate persiste: máquinas realmente "pensam"?

**Perspectiva técnica:**
```
O que chamamos de IA = 
    Álgebra linear em grande escala +
    Estatística avançada +
    Otimização de parâmetros +
    Muitos dados de treinamento +
    Muito poder computacional
```

**Perspectiva funcional:**

Se um sistema produz resultados indistinguíveis do que um humano produziria, ele é funcionalmente "inteligente" — independente de como funciona internamente.

### Por Que Isso Importa para Embarcados?

Como desenvolvedores de sistemas embarcados, precisamos:
1. **Não esperar magia** — IA são ferramentas com limitações claras
2. **Validar outputs** — Nunca confiar cegamente em sistemas críticos
3. **Entender custos** — CPU, RAM, energia, latência
4. **Dimensionar corretamente** — Edge AI vs Cloud AI

---

## 2. GenAI: Inteligência Artificial Generativa

### Definição

**GenAI** são sistemas de IA capazes de **criar conteúdo novo**:
- Texto
- Imagens
- Código
- Áudio/Música
- Vídeo

Diferente de IA classificadora (que categoriza dados existentes), GenAI **gera** novos exemplos que não existiam nos dados de treinamento.

### Como Funciona (Alto Nível)

```
1. TREINAMENTO (offline, caro):
   [Bilhões de exemplos] → [Modelo aprende distribuições] → [Parâmetros salvos]

2. INFERÊNCIA (online, relativamente barato):
   [Prompt do usuário] → [Modelo amostra da distribuição] → [Conteúdo gerado]
```

O modelo aprende a **distribuição de probabilidade** dos dados. Na inferência, ele **amostra** dessa distribuição para gerar novos exemplos estatisticamente plausíveis.

### Tipos de GenAI

| Tipo | Exemplos | Uso em Embarcados |
|------|----------|-------------------|
| Texto (LLMs) | GPT, Claude, Llama | Análise, decisão, NLU |
| Imagem | DALL-E, Midjourney, Stable Diffusion | Geração de assets |
| Código | Copilot, CodeLlama | Assistência ao dev |
| Áudio | Whisper, Bark | STT, TTS |
| Séries Temporais | Granite TTM, TimeGPT | Previsão de sensores |

---

## 3. LLMs: Large Language Models

### O Que São

**Large Language Models** são redes neurais com **bilhões de parâmetros** treinados em **trilhões de tokens** de texto.

| Modelo | Parâmetros | Tokens de Treino | Organização |
|--------|------------|------------------|-------------|
| GPT-4 | ~1.7 trilhões (estimado) | ~13 trilhões | OpenAI |
| Llama 3 70B | 70 bilhões | ~15 trilhões | Meta |
| Claude 3 Opus | Não divulgado | Não divulgado | Anthropic |
| Granite 34B | 34 bilhões | Não divulgado | IBM |

### Arquitetura Transformer

A revolução dos LLMs veio com a arquitetura **Transformer** (2017):

```
ENTRADA: "O rack está com temperatura"
         ↓
[Tokenização]
    "O", "rack", "está", "com", "temperatura"
         ↓
[Embedding]
    Cada token → vetor de 4096+ dimensões
         ↓
[Atenção Multi-Cabeça] ← A "mágica" do Transformer
    Cada token "olha" para todos os outros
    Captura relações de longo alcance
         ↓
[Feed-Forward Networks]
    Processamento não-linear
         ↓
[Camada de Saída]
    Probabilidade de cada token possível
         ↓
SAÍDA: "alta" (token mais provável)
```

### Self-Attention Explicado

O mecanismo de **self-attention** é o coração do Transformer:

```
Frase: "O rack que monitoramos ontem está superaquecendo"

Sem atenção: cada palavra processada isoladamente
Com atenção: "superaquecendo" pode "olhar" para "rack" mesmo distante

Matematicamente:
Attention(Q, K, V) = softmax(QK^T / √d_k) × V

Onde:
- Q (Query): "O que estou procurando?"
- K (Key): "O que cada token oferece?"
- V (Value): "Qual informação extrair?"
```

### Tokenização

LLMs não processam caracteres — processam **tokens**:

```python
# Exemplo com tiktoken (OpenAI)
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")

texto = "ESP32 microcontrolador"
tokens = enc.encode(texto)
# ['ESP', '32', ' micro', 'control', 'ador'] → 5 tokens
```

**Impacto em custos:**
- APIs cobram por token
- Janela de contexto limitada (4K a 128K tokens)
- Mais tokens = mais processamento = mais latência

---

## 4. Limitações Fundamentais dos LLMs

### 1. Alucinações

LLMs podem gerar informações **factualmente incorretas** com alta confiança:

```
Pergunta: "Qual a tensão de operação do ESP32-C6?"
Resposta errada: "O ESP32-C6 opera a 5V"
Resposta correta: 3.3V
```

**Mitigação:**
- Sempre valide informações técnicas
- Use RAG (Retrieval Augmented Generation) para injetar dados corretos
- Implemente verificações no código

### 2. Conhecimento Desatualizado

O conhecimento está "congelado" na data de corte do treinamento:

```
GPT-4 (versão original): conhecimento até setembro 2021
GPT-4 Turbo: conhecimento até abril 2023
Llama 3: conhecimento até dezembro 2023
```

**Mitigação:**
- Tool Calling para consultar APIs atualizadas
- RAG com base de conhecimento atualizada

### 3. Janela de Contexto Limitada

| Modelo | Janela de Contexto |
|--------|-------------------|
| GPT-3.5 | 4K ou 16K tokens |
| GPT-4 Turbo | 128K tokens |
| Claude 3 Opus | 200K tokens |
| Llama 3 | 8K tokens |

**Mitigação:**
- Resumir contextos longos
- Técnicas de chunking
- Memória externa (RAG)

### 4. Raciocínio Limitado

LLMs são excelentes em **padrões linguísticos**, mas fracos em:
- Matemática precisa
- Lógica formal
- Planejamento de longo prazo

**Mitigação:**
- Tool Calling para calculadoras
- Chain-of-thought prompting
- Decomposição de problemas

---

## 5. Modelos Relevantes para Sistemas Embarcados

### Para Rodar Localmente (Edge)

| Modelo | Parâmetros | RAM Necessária | Uso |
|--------|------------|----------------|-----|
| Phi-3 Mini | 3.8B | ~4 GB | Texto geral |
| Llama 3.2 1B | 1B | ~2 GB | Texto simples |
| Gemma 2B | 2B | ~3 GB | Texto geral |
| Whisper Tiny | 39M | ~500 MB | Speech-to-text |

**Viabilidade no ESP32:** Não direta. Esses modelos rodam em:
- Raspberry Pi 5
- Jetson Nano
- PCs com GPU

### Para Uso via API (Cloud)

| Modelo | Custo/1K tokens | Latência | Qualidade |
|--------|-----------------|----------|-----------|
| GPT-3.5 Turbo | ~$0.002 | ~500ms | Boa |
| GPT-4o Mini | ~$0.00015 | ~300ms | Muito boa |
| GPT-4 Turbo | ~$0.01 | ~2-5s | Excelente |
| Claude 3 Haiku | ~$0.00025 | ~500ms | Muito boa |

**Para ESP32:** Chamadas via HTTPS usando APIs cloud.

### Para Séries Temporais (IoT)

| Modelo | Foco | Tamanho |
|--------|------|---------|
| Granite TTM | Previsão temporal | ~1M params |
| TimeGPT | Previsão temporal | API cloud |
| Chronos | Previsão temporal | Vários tamanhos |

---

## 6. Tool Calling: LLMs que Agem

### O Problema

LLMs sozinhos são "ilhas":
- Geram texto, mas não agem
- Conhecimento desatualizado
- Incapazes de acessar sistemas externos

### A Solução: Tool Calling

```
┌─────────────────────────────────────────────────────┐
│ ANTES: LLM como oráculo isolado                     │
│                                                     │
│ [Pergunta] → [LLM] → [Resposta textual]             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ DEPOIS: LLM como orquestrador                       │
│                                                     │
│ [Contexto] → [LLM] → [Tool Calls] → [Sistema] →     │
│                          ↑               │          │
│                          └───────────────┘          │
│                         [Resultado/Feedback]        │
└─────────────────────────────────────────────────────┘
```

### Fluxo com ESP32

```
[ESP32 Sensores] ──MQTT──→ [Dashboard Python]
                                   │
                                   ↓
                          [Formata telemetria]
                                   │
                                   ↓
                          [Chama LLM com Tools]
                                   │
                                   ↓
                          [LLM retorna Tool Calls]
                                   │
                                   ↓
                          [Parseia e valida]
                                   │
                                   ↓
[ESP32 Atuadores] ←─MQTT─ [Envia comandos]
```

O ESP32 não roda o LLM — atua como **sensor/atuador** em um sistema AIoT.

---

## 7. Custos e Trade-offs

### Modelo de Custo de APIs

```
Custo = (tokens_entrada × preço_entrada) + (tokens_saída × preço_saída)

Exemplo GPT-4 Turbo:
- Entrada: $0.01 / 1K tokens
- Saída: $0.03 / 1K tokens

Telemetria de 1 rack (500 tokens entrada, 200 tokens saída):
Custo = (0.5 × $0.01) + (0.2 × $0.03) = $0.011 por análise

100 análises/dia × 30 dias = $33/mês por rack
```

### Alternativas Econômicas

1. **Modelos menores**: gpt-4o-mini custa 1/66 do GPT-4
2. **Ollama local**: Custo zero após setup
3. **Batch processing**: Agregar telemetria antes de enviar
4. **Regras híbridas**: LLM só para casos ambíguos

### Latência

| Cenário | Latência Típica |
|---------|-----------------|
| GPT-3.5 (API) | 0.5-2s |
| GPT-4 (API) | 2-10s |
| Ollama (local) | 0.5-5s (depende do hardware) |
| Edge TinyML | <100ms |

Para sistemas embarcados com requisitos de tempo real, latência de segundos pode ser inaceitável para controle direto — mas aceitável para decisões de alto nível.

---

## 8. Implementação Prática

### Padrão Recomendado para AIoT

```
┌────────────────────────────────────────────────────────────┐
│ CAMADA 1: ESP32 (Tempo Real)                               │
│ - Leitura de sensores                                      │
│ - Controle de atuadores                                    │
│ - Regras de segurança LOCAIS (temp > 60°C → desliga)       │
│ - Comunicação MQTT                                         │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ CAMADA 2: Gateway/Dashboard (Quase Tempo Real)             │
│ - Agregação de telemetria                                  │
│ - Previsão com Granite TTM / SARIMA                        │
│ - Interface de usuário                                     │
│ - Decisões via Tool Calling (LLM)                          │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│ CAMADA 3: Cloud (Decisões Complexas)                       │
│ - LLM para análise semântica                               │
│ - Histórico de longo prazo                                 │
│ - Análise de múltiplos sites                               │
└────────────────────────────────────────────────────────────┘
```

### Código ESP32 para Integração

```c
/**
 * @brief Estrutura de telemetria para envio
 */
typedef struct {
    char rackId[16];
    float temperature;
    float humidity;
    bool doorOpen;
    bool ventilationOn;
    int64_t timestamp;
} RackTelemetry_t;

/**
 * @brief Publica telemetria via MQTT
 */
esp_err_t publish_telemetry(const RackTelemetry_t* data) {
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "rackId", data->rackId);
    cJSON_AddNumberToObject(root, "temperature", data->temperature);
    cJSON_AddNumberToObject(root, "humidity", data->humidity);
    cJSON_AddBoolToObject(root, "doorOpen", data->doorOpen);
    cJSON_AddBoolToObject(root, "ventilationOn", data->ventilationOn);
    cJSON_AddNumberToObject(root, "timestamp", data->timestamp);
    
    char* json = cJSON_PrintUnformatted(root);
    
    char topic[64];
    snprintf(topic, sizeof(topic), "racks/%s/telemetry", data->rackId);
    
    esp_err_t ret = mqtt_publish(topic, json, 0, 1);
    
    free(json);
    cJSON_Delete(root);
    
    return ret;
}

/**
 * @brief Callback para comandos recebidos
 */
void on_command_received(const char* topic, const char* payload) {
    // Parseia comando
    cJSON* root = cJSON_Parse(payload);
    if (!root) return;
    
    cJSON* action = cJSON_GetObjectItem(root, "action");
    cJSON* value = cJSON_GetObjectItem(root, "value");
    
    if (strcmp(action->valuestring, "ventilation") == 0) {
        gpio_set_level(GPIO_VENTILATION, value->valueint);
    } else if (strcmp(action->valuestring, "buzzer") == 0) {
        buzzer_set_mode(value->valueint);
    }
    
    cJSON_Delete(root);
}
```

---

## 9. Recursos para Aprofundamento

### Cursos e Tutoriais
- [Fast.ai](https://www.fast.ai/) — Curso prático de deep learning
- [Hugging Face Course](https://huggingface.co/learn) — NLP e Transformers
- [Andrej Karpathy YouTube](https://www.youtube.com/@AndrejKarpathy) — Explicações profundas

### Documentação
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Docs](https://docs.anthropic.com/)
- [Ollama](https://ollama.ai/) — LLMs locais

### Papers Fundamentais
- "Attention Is All You Need" (2017) — Introduz Transformers
- "Language Models are Few-Shot Learners" (2020) — GPT-3
- "Scaling Laws for Neural Language Models" (2020) — Leis de escala

---

## 10. Conclusão

Para desenvolvedores de sistemas embarcados:

1. **IA não é magia** — São ferramentas matemáticas com limitações claras

2. **ESP32 não roda LLMs** — Mas pode se integrar via APIs

3. **Tool Calling é o caminho** — LLMs decidem, ESP32 executa

4. **Arquitetura híbrida** — Segurança local + inteligência na nuvem

5. **Comece pequeno** — GPT-3.5 ou Ollama local para experimentos

> "O melhor código de IA embarcada é aquele que sabe quando NÃO precisa de IA."
