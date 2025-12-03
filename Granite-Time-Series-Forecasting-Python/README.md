# 🔮 Granite Time Series Forecasting

Sistema de previsão de séries temporais em tempo real usando o modelo **IBM Granite TTM-R2** (Tiny Time Mixer).

> **🔧 Última atualização**: Melhorias de diagnóstico e estabilidade do WebSocket - veja [WEBSOCKET_DIAGNOSTICS.md](docs/WEBSOCKET_DIAGNOSTICS.md)

## 📋 Visão Geral

Este projeto demonstra o uso do modelo Granite TTM-R2 para:

- **Previsão de valores futuros** em séries temporais
- **Detecção de anomalias** em tempo real
- **Identificação de padrões** e tendências
- **Visualização interativa** com gráficos dinâmicos
- **Alertas automáticos** quando valores saem do padrão esperado

## ✨ Funcionalidades

### 🎯 Core Features

- ✅ **Geração contínua de dados sintéticos** com características realistas:
  - Tendência temporal
  - Sazonalidade (padrões cíclicos)
  - Ruído aleatório
  - Anomalias ocasionais (5% de probabilidade)

- ✅ **Previsão em tempo real** usando IBM Granite TTM-R2:
  - Horizonte configurável (padrão: 96 pontos)
  - Contexto histórico de 512 pontos
  - Zero-shot forecasting (sem necessidade de treinamento)

- ✅ **Detecção de anomalias** baseada em análise estatística:
  - Z-score (desvio padrão)
  - Threshold configurável (padrão: 3σ)
  - Classificação de severidade (normal, medium, high, critical)

- ✅ **Interface web moderna e responsiva**:
  - Gráfico de linha dinâmico (Chart.js)
  - Alertas visuais de anomalias
  - Estatísticas em tempo real
  - Controles de start/stop/reset

### 🔄 Arquitetura em Tempo Real

```
┌─────────────────┐
│  Data Generator │ ──► Gera pontos a cada 2s
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Forecast Service│ ──► Prevê próximos 96 pontos
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Anomaly Detector│ ──► Detecta desvios > 3σ
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   WebSocket     │ ──► Envia para frontend
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Interface  │ ──► Visualização interativa
└─────────────────┘
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- pip
- (Opcional) CUDA para aceleração GPU

### Passo a Passo

1. **Clone o repositório** (ou navegue até a pasta do projeto):

```bash
cd Granite-Time-Series-Forecasting-Python
```

2. **Crie um ambiente virtual** (recomendado):

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**:

```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**:

```bash
cp .env.example .env
# Edite o arquivo .env conforme necessário
```

5. **Execute a aplicação**:

```bash
python app.py
```

6. **Acesse a interface web**:

Abra seu navegador em: [http://localhost:5000](http://localhost:5000)

## ⚙️ Configuração

Todas as configurações podem ser ajustadas no arquivo `.env`:

### Servidor

```env
PORT=5000                    # Porta do servidor
DEBUG=False                  # Modo debug
SECRET_KEY=your-secret-key   # Chave secreta Flask
```

### Modelo

```env
MODEL_NAME=ibm-granite/granite-timeseries-ttm-r2
FORECAST_HORIZON=96          # Pontos futuros a prever
CONTEXT_LENGTH=512           # Janela de contexto histórico
```

### Geração de Dados

```env
DATA_GENERATION_INTERVAL=2.0  # Intervalo entre gerações (segundos)
BASE_VALUE=100.0              # Valor base da série
NOISE_LEVEL=5.0               # Amplitude do ruído
TREND_ENABLED=True            # Habilitar tendência
SEASONALITY_ENABLED=True      # Habilitar sazonalidade
```

### Detecção de Anomalias

```env
ANOMALY_THRESHOLD_MULTIPLIER=3.0  # Múltiplo do desvio padrão (3σ = 99.7%)
ANOMALY_WINDOW_SIZE=50            # Janela para calcular estatísticas
```

## 📊 Uso

### Interface Web

1. **Iniciar processamento**: Clique no botão "▶️ Iniciar"
2. **Observar dados**: O gráfico será atualizado em tempo real
3. **Alertas**: Anomalias dispararão alertas visuais automáticos
4. **Parar**: Use o botão "⏸️ Parar" para pausar
5. **Resetar**: Limpe todos os dados com "🔄 Resetar"

### API REST

#### Status do Sistema

```bash
GET /api/status
```

Retorna:
```json
{
  "running": true,
  "data_points": 150,
  "anomaly_count": 5,
  "total_predictions": 148,
  "model_loaded": true,
  "config": {
    "forecast_horizon": 96,
    "context_length": 512,
    "generation_interval": 2.0
  }
}
```

#### Histórico de Dados

```bash
GET /api/history
```

Retorna últimos 100 pontos de dados e 10 previsões.

### WebSocket Events

#### Cliente → Servidor

- `start_processing`: Inicia geração e previsão
- `stop_processing`: Para processamento
- `reset_data`: Limpa todos os dados

#### Servidor → Cliente

- `connected`: Confirmação de conexão
- `new_data`: Novos dados, previsões e anomalias
- `status_changed`: Mudança de estado (running/stopped)
- `data_reset`: Confirmação de reset

## 🏗️ Estrutura do Projeto

```
Granite-Time-Series-Forecasting-Python/
├── app.py                          # Aplicação Flask principal
├── requirements.txt                # Dependências Python
├── .env.example                    # Exemplo de configuração
├── README.md                       # Este arquivo
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # Configurações centralizadas
│   │
│   └── services/
│       ├── __init__.py
│       ├── dataGenerator.py        # Gerador de dados sintéticos
│       ├── forecastService.py      # Serviço de previsão (Granite)
│       └── anomalyDetector.py      # Detector de anomalias
│
├── templates/
│   └── index.html                  # Interface web
│
└── static/
    └── app.js                      # Frontend JavaScript
```

## 🤖 Sobre o Modelo Granite TTM-R2

O **Tiny Time Mixer (TTM)** é um modelo de previsão de séries temporais desenvolvido pela IBM Research:

- **Zero-shot forecasting**: Funciona sem necessidade de treinamento adicional
- **Eficiente**: Otimizado para baixa latência e consumo de recursos
- **Versátil**: Suporta múltiplos domínios e padrões temporais
- **Estado da arte**: Performance competitiva com modelos maiores

### Referências

- 🤗 [Hugging Face Model Card](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
- 📄 [Paper: Tiny Time Mixers](https://arxiv.org/abs/2401.03955)
- 🔗 [IBM Research Blog](https://research.ibm.com/)

## 🔧 Desenvolvimento

### Estrutura de Código

O projeto segue princípios de **Domain-Driven Design (DDD)**:

- **Separação de responsabilidades**: Cada serviço tem uma função específica
- **Modularidade**: Componentes independentes e reutilizáveis
- **Documentação**: Código amplamente documentado com docstrings
- **Logging**: Sistema de logs estruturado para debugging

### Complexidade Algorítmica

- **Geração de dados**: O(1) por ponto
- **Previsão**: O(n + m) onde n = context_length, m = forecast_horizon
- **Detecção de anomalias**: O(w) onde w = window_size
- **Atualização de gráfico**: O(1) amortizado

### Testes

Para executar testes (quando implementados):

```bash
pytest tests/ -v --cov=src
```

## 📈 Performance

### Requisitos de Sistema

- **CPU**: 2+ cores recomendado
- **RAM**: 4GB mínimo, 8GB recomendado
- **GPU**: Opcional (CUDA compatível para aceleração)
- **Disco**: ~2GB para modelo e dependências

### Otimizações

- **Lazy loading**: Modelo carregado apenas quando necessário
- **Batch processing**: Suporte a processamento em lote
- **Memory management**: Limite de histórico em memória
- **WebSocket**: Comunicação eficiente em tempo real

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'tsfm_public'"

```bash
pip install tsfm_public
```

### Erro: "CUDA out of memory"

Ajuste no `.env`:
```env
USE_GPU=False
```

### Gráfico não atualiza

1. Verifique console do navegador (F12)
2. Confirme conexão WebSocket
3. Reinicie o servidor

### Modelo demora para carregar

O primeiro carregamento baixa o modelo (~500MB). Aguarde a conclusão.

## 📝 Licença

Este projeto é fornecido como exemplo educacional. O modelo Granite TTM-R2 possui sua própria licença (consulte Hugging Face).

## 🤝 Contribuições

Contribuições são bem-vindas! Áreas de melhoria:

- [ ] Suporte a múltiplas séries temporais simultâneas
- [ ] Persistência de dados em banco de dados
- [ ] Exportação de relatórios (PDF/CSV)
- [ ] Testes unitários e de integração
- [ ] Docker containerization
- [ ] Autenticação e autorização
- [ ] Dashboard administrativo

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**🚀 Desenvolvido com Flask, Socket.IO, Chart.js e IBM Granite TTM-R2**
