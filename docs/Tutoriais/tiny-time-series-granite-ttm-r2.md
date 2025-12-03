# Tutorial: Tiny Time Series Model (IBM Granite TTM-R2)

> **Tempo estimado:** 45 minutos

## 1. Objetivo

Apresentar, de forma didática, como o modelo **Tiny Time Mixer (TTM-R2)** da família **Granite Time-Series Model** funciona e como ele foi integrado no serviço `forecastService.py`. Você aprenderá a:

1. Entender os fundamentos do Tiny Time Series Model.
2. Explorar o design do `ForecastService` que abstrai o uso do Granite TTM-R2 com fallback estatístico.
3. Preparar dados com e sem variáveis exógenas (ex.: temperatura e umidade) e comparar os resultados.
4. Operar o serviço com logs padronizados para monitoramento e auditoria.

## 2. Pré-requisitos

| Item            | Descrição                                                                            |
| --------------- | -------------------------------------------------------------------------------------- |
| Linguagem       | Python 3.10+                                                                           |
| Bibliotecas     | `pandas`, `numpy`, `statsmodels`, `torch`, `tsfm_public` (Granite)           |
| Hardware        | CPU ou GPU com suporte a PyTorch (opcional para acelerar o Granite)                    |
| Dados           | Série temporal com histórico suficiente (>= 512 pontos para uso completo do Granite) |
| Segurança      | Variáveis de ambiente configuradas (`WATSONX_API_KEY`, etc.) e dados anonimizados   |
| Observabilidade | Logger configurado conforme padrão `[timeseries/forecasting] Mensagem 😀`           |

## 3. Visão Geral do Tiny Time Mixer (TTM-R2)

O Granite TTM-R2 é um **modelo pré-treinado da IBM** otimizado para previsões rápidas de séries temporais:

- **Arquitetura Tiny Time Mixer:** combina camadas convolucionais e blocos de atenção para capturar padrões locais (ciclos curtos) e globais (tendências de longo prazo).
- **Entrada multivariada:** aceita múltiplos canais (variáveis) simultaneamente, o que facilita incorporar variáveis exógenas.
- **Contexto fixo:** trabalha melhor quando recebe janelas com até `context_length = 512` pontos.
- **Horizonte flexível:** gera previsões para horizontes médios (até 96 passos por padrão) com baixa latência.
- **Robustez:** inclui normalização interna e camadas de mistura que reduzem o impacto de ruídos e outliers.

### 3.1 Vantagens

1. **Eficiência:** arquitetura "tiny" consome menos memória e roda em CPU quando necessário.
2. **Generalização:** pré-treino em milhares de séries permite generalizar padrões sem ajuste fino.
3. **Multivariado nativo:** lida com múltiplas variáveis sincronizadas.
4. **Fallback transparente:** integração fácil com métodos clássicos quando o modelo não está disponível.

### 3.2 Limitações

1. **Dependência de contexto:** precisa de janela mínima (>= 512 pontos) para explorar todo o potencial.
2. **Configuração inicial:** requer instalação específica (`bash install_granite.sh`).
3. **Explainability:** interpretações internas são mais complexas que modelos ARIMA/Holt-Winters.

## 4. Arquitetura do `ForecastService`

O arquivo `Granite-Time-Series-Forecasting-Python/src/services/forecastService.py` encapsula a lógica de previsão seguindo princípios de DDD (camada de serviço) e design pattern **Strategy** para alternar entre modelos.

### 4.1 Fluxo Principal

1. **Inicialização:** define horizonte (`forecast_horizon`), tamanho do contexto (`context_length`) e detecta disponibilidade do Granite.
2. **Pré-processamento:** método `_prepare_series` converte o histórico em `pd.Series` ordenada e limita a 512 pontos.
3. **Modelo Granite:**
   - `_load_granite_model` realiza *lazy loading* do `TinyTimeMixerForPrediction` e configura `TimeSeriesForecastingPipeline` com `freq="S"`.
   - `_granite_forecast` cria `DataFrame` com colunas `timestamp` e `value`, invoca a pipeline e higieniza previsões com `_sanitize_predictions`.
4. **Fallback estatístico:** `_exponential_smoothing_forecast` usa Holt-Winters (`statsmodels`) quando o Granite não está disponível ou falha.
5. **Saída padronizada:** `predict` calcula timestamps futuros, organiza previsões e registra métricas de execução (tempo total, modelo usado).

### 4.2 Observabilidade e Resiliência

- Logs seguem o padrão `[timeseries/forecasting] Mensagem 😀` com emojis para destacar status (`✅`, `⚠️`).
- Sanitização garante que apenas valores numéricos válidos sejam retornados.
- Tratamento de exceções conserva histórico em caso de falhas e ativa fallback automaticamente.

## 5. Preparação dos Dados

### 5.1 Estrutura Esperada

Cada ponto da série deve ter as chaves:

```json
{
  "timestamp": "2024-05-01T00:00:00Z",
  "value": 123.4,
  "features": {
    "temperature": 27.1,
    "humidity": 55.2
  }
}
```

- `value`: variável endógena (alvo principal).
- `features`: dicionário opcional com variáveis exógenas (externas ao sistema), como `humidity`.
- Os valores são ordenados por `timestamp` e convertidos em pandas DataFrame antes de alimentar o modelo.

### 5.2 Limpeza Recomendada

1. Remover/Interpolar valores ausentes.
2. Garantir espaçamento temporal constante (uniforme).
3. Normalizar variáveis exógenas para mesma escala (z-score ou min-max).
4. Documentar decisões em `docs/how-to/setup-dev.md`.

## 6. Exemplo Prático: Sem Variáveis Exógenas

O script abaixo replica o comportamento padrão do serviço (somente canal `value`).

```python
import pandas as pd
from Granite_Time_Series_Forecasting_Python.src.services.forecastService import ForecastService

# 1. Criar histórico simples (energia consumida em Wh a cada minuto)
data_history = [
    {"timestamp": f"2024-10-01T00:{str(i).zfill(2)}:00Z", "value": 100 + i * 0.5}
    for i in range(600)
]

# 2. Instanciar o serviço
service = ForecastService(forecast_horizon=12, context_length=512)

# 3. Gerar previsão (Granite ou fallback)
result = service.predict(data_history)

print("Modelo utilizado:", result["model"])
for item in result["predictions"]:
    print(item["timestamp"], "→", round(item["value"], 2))
```

### O que acontece por baixo dos panos?

1. A lista `data_history` é truncada para os últimos 512 pontos (_janelamento_).
2. `TimeSeriesForecastingPipeline` recebe apenas a coluna `value`.
3. O output convertido em `np.ndarray` alimenta a resposta com timestamps futuros.
4. Caso o Granite não esteja disponível, Holt-Winters gera previsões suavizadas, recalculando tendência e sazonalidade.

## 7. Exemplo Prático: Incluindo Variáveis Exógenas

Para comparar o impacto de variáveis exógenas, adicionamos temperatura (endógena) e umidade (exógena). O Granite aceita múltiplos canais; precisamos adaptar a preparação dos dados.

```python
import pandas as pd
import numpy as np
from Granite_Time_Series_Forecasting_Python.src.services.forecastService import ForecastService

# 1. Gerar histórico com variáveis adicionais
rng = pd.date_range("2024-10-01", periods=600, freq="T")
series = []
for ts in rng:
    minutes = (ts - rng[0]).seconds / 60
    base_value = 120 + np.sin(minutes / 60) * 10  # padrão diário
    temperature = 26 + 0.02 * minutes            # tendência leve
    humidity = 55 + np.cos(minutes / 180) * 5    # variável externa
    series.append({
        "timestamp": ts.isoformat() + "Z",
        "value": base_value,
        "features": {
            "temperature": temperature,
            "humidity": humidity
        }
    })

def flatten_multivariate(history):
    """Transforma o histórico em DataFrame multivariado."""
    df = pd.DataFrame([
        {
            "timestamp": pd.to_datetime(item["timestamp"]),
            "value": item["value"],
            "temperature": item["features"]["temperature"],
            "humidity": item["features"]["humidity"]
        }
        for item in history
    ])
    return df.sort_values("timestamp").reset_index(drop=True)

# 2. Ajustar o serviço para múltiplos canais
service = ForecastService(forecast_horizon=12, context_length=512)
service._load_granite_model()

df = flatten_multivariate(series[-service.context_length:])

# 3. Atualizar pipeline (num_input_channels=3: value, temperature, humidity)
service.granite_model = service.granite_model.from_pretrained(
    service.model_name,
    num_input_channels=3
)
service.granite_pipeline = service.granite_pipeline.__class__(
    service.granite_model,
    timestamp_column="timestamp",
    id_columns=[],
    target_columns=["value", "temperature", "humidity"],
    explode_forecasts=False,
    freq="T",
    device=service.device
)

forecast_df = service.granite_pipeline(df)
print(forecast_df.head(12))
```

### Observações Importantes

1. **num_input_channels:** deve corresponder ao número de variáveis (1 alvo + exógenas).
2. **Target columns:** especifique todas as colunas que o modelo deve prever simultaneamente.
3. **Comparação:** avalie métricas de erro separadamente para `value`, `temperature`, `humidity` conforme o objetivo.
4. **Documentação:** registre a alteração da pipeline e atualize os testes para cobrir o cenário multivariado.

### Resultado Esperado

- Previsões do Granite para cada variável (colunas separadas).
- Quando comparado com o cenário univariado, a série alvo (`value`) tende a capturar melhor oscilações que são explicadas pelo comportamento de `humidity`.

## 8. Comparando Cenários

| Cenário                  | Configuração | Erro Médio (MAPE) | Tempo de Execução (s) | Observações                                          |
| ------------------------- | -------------- | ------------------ | ----------------------- | ------------------------------------------------------ |
| Sem exógenas             | Canal único   | 4,8%               | 0,45                    | Comportamento suavizado; menor complexidade            |
| Com temperatura + umidade | 3 canais       | 3,1%               | 0,62                    | Melhor captura de eventos; exige ajuste de pipeline    |
| Fallback Holt-Winters     | Canal único   | 6,5%               | 0,18                    | Disponível mesmo sem Granite; interpretações claras |

> **Nota:** métricas ilustrativas. Recomenda-se executar *backtesting* próprio com dados reais.

## 9. Boas Práticas Operacionais

1. **Versionamento:** mantenha scripts e parâmetros em repositório Git com tag por versão (`x.y.z`).
2. **Logs:** centralize as mensagens com o padrão `[timeseries/forecasting]` e emojis para facilitar rastreio.
3. **Monitoramento contínuo:** implemente alertas para desvios de erro (MAPE/SMAPE) e uso de fallback.
4. **Gestão de credenciais:** armazene chaves em `.env` (ignorado pelo Git) e siga a precedência de `/etc/<nomedoprojeto>/config.json` em produção.
5. **Documentação:** atualize `docs/CHANGELOG.md` e crie ADRs (`docs/decisions/`) quando mudar o fluxo de previsão.
6. **Tratamento de interrupções:** envolva chamadas longas em blocos `try/except` com captura de sinais (`signal.SIGINT`) para desligamento gracioso do serviço.

## 10. Referências

- Documentação do serviço `ForecastService`: `Granite-Time-Series-Forecasting-Python/src/services/forecastService.py`.
- IBM. *Granite Foundation Models for Time-Series*. Documentação watsonx (2024).
- Hyndman, R. J.; Athanasopoulos, G. *Forecasting: Principles and Practice*. OTexts, 2021.
