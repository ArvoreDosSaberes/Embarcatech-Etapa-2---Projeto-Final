# 📈 Time Series com Granite TTM

## IBM Granite Time Series Model (TTM)

Modelo **especializado** em séries temporais:

- **Tiny Time Mixer (TTM-R2)** — Leve e eficiente
- Treinado em milhões de séries temporais
- Captura sazonalidades complexas (diária, anual)
- Suporta múltiplas variáveis exógenas

## Vantagens do Granite TTM

| Característica | Benefício |
|----------------|-----------|
| Pré-treinado | Funciona com poucos dados |
| Multivariado | Correlaciona temperatura × umidade |
| Sazonalidade | Detecta padrões de 24h automaticamente |
| Leve | Roda em CPU comum |

## Arquitetura Híbrida com Fallback

```
[Dados] → [Granite TTM] → [Previsão]
              ↓ (se falhar ou MAE alto)
         [SARIMA Fallback] → [Previsão]
```

## No Projeto Rack Inteligente

- **Contexto**: 7 dias de histórico (168 horas)
- **Horizonte**: Previsão de 24 horas à frente
- **Métricas**: MAE para decisão de fallback automático
