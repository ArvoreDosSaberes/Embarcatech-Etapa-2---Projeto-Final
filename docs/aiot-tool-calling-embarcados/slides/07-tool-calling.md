# 🛠️ O que são Tool Callings?

## Function Calling / Tool Calling

Capacidade das LLMs de **invocar funções externas**:

- LLM analisa o contexto
- Decide qual ferramenta usar
- Gera os parâmetros corretos
- Sistema executa a função
- Resultado retorna à LLM

## Fluxo de Tool Calling

```
[Usuário] → "Ligue a ventilação do rack 001"
              ↓
         [LLM analisa]
              ↓
    tool_call: turnOnVentilation(rackId="001")
              ↓
      [Sistema executa]
              ↓
        [ACK retorna]
```

## Por Que É Poderoso?

- **LLM decide, sistema executa** — Separação de responsabilidades
- **Validação de parâmetros** — LLM gera JSON estruturado
- **Múltiplas ações** — Pode chamar várias funções em sequência
- **Contexto semântico** — Entende intenção, não apenas comandos

## APIs que Suportam

- OpenAI, Anthropic, Google, IBM, Mistral, Ollama...
