# 🎮 OpenAI para Demonstração

## Como Obter Acesso Gratuito

1. **Criar conta** em [platform.openai.com](https://platform.openai.com)

2. **Créditos iniciais** — Novos usuários recebem $5-$18 gratuitos

3. **Gerar API Key**:
   - Settings → API Keys → Create new secret key

4. **Testar no Playground**:
   - Menu → Playground → Chat
   - Selecione modelo: `gpt-3.5-turbo` (mais barato)

## Modelos Recomendados para Testes

| Modelo | Custo | Use Case |
|--------|-------|----------|
| gpt-3.5-turbo | ~$0.002/1K tokens | Testes básicos |
| gpt-4-turbo | ~$0.01/1K tokens | Tool Calling avançado |
| gpt-4o-mini | ~$0.00015/1K tokens | Produção econômica |

## Dica: Ollama Local (Gratuito!)

```bash
# Instale Ollama e rode localmente
ollama run llama3
# API compatível com OpenAI em localhost:11434
```

> Para demos, use modelos locais ou gpt-3.5-turbo!
