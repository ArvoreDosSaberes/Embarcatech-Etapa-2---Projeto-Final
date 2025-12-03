# 🏗️ Arquitetura do Sistema

Documentação técnica da arquitetura do **Granite Time Series Forecasting System**.

## 📐 Visão Geral

O sistema segue uma arquitetura **modular e orientada a serviços**, baseada nos princípios de **Domain-Driven Design (DDD)**.

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Web UI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chart.js    │  │  WebSocket   │  │  Controls    │     │
│  │  Visualizer  │  │  Client      │  │  & Stats     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket / REST API
┌────────────────────────┴────────────────────────────────────┐
│                   Backend (Flask Server)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Flask + SocketIO Core                   │  │
│  │  • Routing  • WebSocket Events  • API Endpoints     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Data      │  │   Forecast   │  │   Anomaly    │     │
│  │  Generator   │  │   Service    │  │   Detector   │     │
│  │   Service    │  │   (Granite)  │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                    ┌───────┴────────┐                       │
│                    │  Configuration │                       │
│                    │    Manager     │                       │
│                    └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴─────────┐
                    │  IBM Granite     │
                    │  TTM-R2 Model    │
                    │  (Hugging Face)  │
                    └──────────────────┘
```

## 🔧 Componentes Principais

### 1. Frontend (Web UI)

**Tecnologias**: HTML5, JavaScript (ES6+), Chart.js, Socket.IO Client, Tailwind CSS

**Responsabilidades**:
- Renderização de interface responsiva
- Visualização de gráficos em tempo real
- Comunicação WebSocket com backend
- Gerenciamento de estado local
- Exibição de alertas e estatísticas

**Arquivos**:
- `templates/index.html` - Template HTML principal
- `static/app.js` - Lógica JavaScript do frontend

### 2. Backend (Flask Server)

**Tecnologias**: Python 3.8+, Flask, Flask-SocketIO, Flask-CORS

**Responsabilidades**:
- Servidor HTTP e WebSocket
- Orquestração de serviços
- Gerenciamento de threads
- Roteamento de API REST
- Broadcasting de eventos

**Arquivo Principal**: `app.py`

**Endpoints REST**:
- `GET /` - Interface web
- `GET /api/status` - Status do sistema
- `GET /api/history` - Histórico de dados

**Eventos WebSocket**:
- `connect` / `disconnect` - Gerenciamento de conexões
- `start_processing` - Iniciar geração
- `stop_processing` - Parar geração
- `reset_data` - Limpar dados
- `new_data` - Broadcast de novos dados (servidor → cliente)

### 3. Data Generator Service

**Arquivo**: `src/services/dataGenerator.py`

**Responsabilidades**:
- Geração de séries temporais sintéticas
- Simulação de padrões realistas:
  - Tendência linear
  - Sazonalidade (ciclos)
  - Ruído gaussiano
  - Anomalias ocasionais (5%)

**Algoritmo de Geração**:

```python
valor_final = base_value + tendência + sazonalidade + ruído

# Componentes:
tendência = coeficiente * t
sazonalidade = amplitude * sin(2π * t / período)
ruído = N(0, σ²)  # Distribuição normal
```

**Complexidade**: O(1) por ponto gerado

### 4. Forecast Service

**Arquivo**: `src/services/forecastService.py`

**Responsabilidades**:
- Carregamento do modelo Granite TTM-R2
- Preparação de dados de entrada
- Execução de previsões
- Pós-processamento de resultados

**Modelo**: IBM Granite TTM-R2 (Tiny Time Mixer)
- **Tipo**: Zero-shot time series forecasting
- **Arquitetura**: Transformer-based
- **Parâmetros**: ~5M (otimizado para eficiência)
- **Contexto**: 512 pontos históricos
- **Horizonte**: 96 pontos futuros (configurável)

**Pipeline de Previsão**:

```
1. Receber histórico (mínimo: context_length pontos)
2. Preparar DataFrame com timestamp + value
3. Executar pipeline do modelo
4. Extrair previsões
5. Gerar timestamps futuros
6. Retornar resultados estruturados
```

**Complexidade**: O(n + m) onde n = context_length, m = forecast_horizon

### 5. Anomaly Detector Service

**Arquivo**: `src/services/anomalyDetector.py`

**Responsabilidades**:
- Detecção de valores anômalos
- Cálculo de estatísticas (média, desvio padrão)
- Classificação de severidade
- Manutenção de histórico de anomalias

**Algoritmo**: Z-Score (Statistical Outlier Detection)

```python
z_score = |valor - média| / desvio_padrão

# Classificação:
z > threshold (3σ) → Anomalia
  z > 5σ → Critical
  z > 4σ → High
  z > 3σ → Medium
z ≤ 3σ → Normal
```

**Janela Deslizante**: Usa últimos N pontos (padrão: 50) para calcular estatísticas adaptativas.

**Complexidade**: O(w) onde w = window_size

### 6. Configuration Manager

**Arquivo**: `src/config.py`

**Responsabilidades**:
- Centralização de configurações
- Carregamento de variáveis de ambiente
- Validação de parâmetros
- Defaults seguros

**Fontes de Configuração** (ordem de precedência):
1. Variáveis de ambiente
2. Arquivo `.env`
3. Valores padrão no código

## 🔄 Fluxo de Dados

### Fluxo Principal (Tempo Real)

```
1. Thread Background (loop infinito):
   ├─► Data Generator: gera novo ponto
   ├─► Adiciona ao histórico
   ├─► Forecast Service: prevê próximos valores (se histórico >= context_length)
   ├─► Anomaly Detector: verifica se é anomalia
   └─► WebSocket: emite evento 'new_data' para todos os clientes

2. Frontend (ao receber 'new_data'):
   ├─► Atualiza gráfico (Chart.js)
   ├─► Atualiza estatísticas
   ├─► Exibe alerta (se anomalia)
   └─► Atualiza displays de valor atual e previsão
```

### Fluxo de Inicialização

```
1. Usuário acessa http://localhost:5000
2. Flask renderiza index.html
3. Frontend carrega app.js
4. WebSocket conecta ao servidor
5. Frontend solicita status via REST API
6. Usuário clica "Iniciar"
7. Frontend emite evento 'start_processing'
8. Backend inicia thread de processamento
9. Loop de geração/previsão/detecção começa
```

## 🧵 Threading Model

O sistema usa **threading** para processamento assíncrono:

```
Main Thread (Flask)
├─► HTTP Request Handler
├─► WebSocket Event Handler
└─► SocketIO Background Tasks

Background Thread (daemon)
└─► Data Generation Loop
    ├─► Generate Point
    ├─► Forecast (if enough data)
    ├─► Detect Anomaly
    └─► Emit via WebSocket
```

**Sincronização**: Estado compartilhado via dicionário `app_state` (thread-safe para operações simples).

## 📊 Estrutura de Dados

### Ponto de Dados

```python
{
    'timestamp': '2024-01-01T12:00:00',  # ISO 8601
    'value': 105.23,                      # float
    'index': 42,                          # int (contador)
    'components': {                       # Decomposição
        'base': 100.0,
        'trend': 0.42,
        'seasonality': 3.5,
        'noise': 1.31
    },
    'is_injected_anomaly': False         # bool
}
```

### Previsão

```python
{
    'predictions': [                      # Lista de previsões
        {
            'timestamp': '2024-01-01T12:00:02',
            'value': 106.5,
            'horizon_step': 1             # Passo à frente
        },
        # ... mais 95 pontos
    ],
    'forecast_timestamp': '2024-01-01T12:00:00',
    'context_size': 512,
    'model': 'ibm-granite/granite-timeseries-ttm-r2'
}
```

### Informação de Anomalia

```python
{
    'value': 150.0,                       # Valor anômalo
    'mean': 100.0,                        # Média da janela
    'stdev': 5.0,                         # Desvio padrão
    'zscore': 10.0,                       # Z-score
    'threshold': 3.0,                     # Threshold configurado
    'deviation': 10.0,                    # Número de sigmas
    'window_size': 50,                    # Tamanho da janela
    'is_anomaly': True,                   # Classificação
    'severity': 'critical',               # Severidade
    'severity_emoji': '🔴'                # Emoji visual
}
```

## 🔐 Segurança

### Considerações Implementadas

- ✅ **CORS**: Configurado via Flask-CORS
- ✅ **WebSocket Origin**: Permitido para desenvolvimento
- ✅ **Secret Key**: Configurável via ambiente
- ✅ **Input Validation**: Validação de configurações

### Melhorias Futuras

- [ ] Autenticação de usuários
- [ ] Rate limiting
- [ ] HTTPS/WSS em produção
- [ ] Sanitização de inputs
- [ ] Logging de auditoria

## 📈 Performance

### Otimizações Implementadas

1. **Lazy Loading**: Modelo carregado apenas quando necessário
2. **Memory Management**: Limite de histórico em memória (1000 pontos)
3. **Chart Updates**: Sem animação para melhor performance
4. **Batch Operations**: Suporte a processamento em lote
5. **GPU Acceleration**: Detecção automática de CUDA

### Benchmarks Esperados

| Operação | Tempo (CPU) | Tempo (GPU) |
|----------|-------------|-------------|
| Gerar ponto | ~1ms | N/A |
| Detectar anomalia | ~5ms | N/A |
| Previsão (96 pontos) | ~500ms | ~50ms |
| Update gráfico | ~10ms | N/A |

## 🔧 Extensibilidade

### Pontos de Extensão

1. **Novos Geradores**: Implementar `DataGenerator` customizado
2. **Detectores Alternativos**: Substituir `AnomalyDetector` (ex: Isolation Forest)
3. **Modelos Diferentes**: Trocar Granite por outro modelo Hugging Face
4. **Persistência**: Adicionar camada de banco de dados
5. **Notificações**: Integrar com sistemas externos (email, Slack, etc.)

### Exemplo: Adicionar Novo Detector

```python
# src/services/customDetector.py
class CustomAnomalyDetector:
    def detect(self, value, history):
        # Implementar lógica customizada
        pass

# app.py
from src.services.customDetector import CustomAnomalyDetector
anomaly_detector = CustomAnomalyDetector()
```

## 📚 Referências Técnicas

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [Chart.js](https://www.chartjs.org/)
- [IBM Granite TTM-R2](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
- [PyTorch](https://pytorch.org/)

---

**Última atualização**: 2024-01-01
