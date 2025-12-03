# Diagnóstico de Queda de Conexão WebSocket

## Problema Identificado

Durante a geração de predições pelo modelo Granite TTM-R2, a conexão WebSocket estava caindo. Este documento descreve as melhorias implementadas para diagnóstico e resolução do problema.

---

## Melhorias Implementadas

### 1. **Logs Detalhados no ForecastService** (`src/services/forecastService.py`)

#### Método `_granite_forecast()`

Adicionados logs para monitorar cada etapa da predição:

- **Preparação de dados**: tamanho do DataFrame, shape, primeiras e últimas linhas
- **Tempo de predição**: medição precisa do tempo de execução
- **Resposta do Granite**: 
  - Shape do DataFrame de resposta
  - Colunas disponíveis
  - Tipos de dados (dtypes)
  - Estatísticas descritivas (describe)
  - Primeiras e últimas linhas da resposta
- **Estatísticas das predições**:
  - Valores mínimo, máximo, média e desvio padrão
  - Primeiras 10 predições para inspeção
- **Tratamento de erros**: tipo de exceção, detalhes e stack trace completo

#### Método `predict()`

Logs adicionados para:

- **Início da predição**: quantidade de dados e passos de previsão
- **Tempo de execução**: separado para Granite e fallback
- **Tamanho do resultado**: bytes do objeto JSON resultante
- **Erros detalhados**: tipo de exceção e stack trace

---

### 2. **Logs Detalhados no App Principal** (`app.py`)

#### Função `background_processing()`

Melhorias implementadas:

- **Contador de iterações**: rastreamento de cada ciclo de processamento
- **Logs de forecast**: quando inicia, quando completa, quando falha
- **Tamanho dos dados WebSocket**: medição em bytes antes de emitir
- **Tratamento de erros de emissão**: captura específica de erros do WebSocket
- **Logs de sleep**: confirmação de intervalo entre iterações

#### Handlers WebSocket

- **`handle_connect()`**: 
  - Log do ID do cliente conectado
  - Confirmação de envio da mensagem de conexão
  - Tratamento de erros na emissão inicial

- **`handle_disconnect()`**:
  - Log do ID do cliente desconectado
  - Estatísticas no momento da desconexão

---

### 3. **Configurações de SocketIO Otimizadas**

Parâmetros ajustados para evitar timeouts:

```python
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=120,              # Timeout aumentado para 120s
    ping_interval=25,               # Ping a cada 25s
    max_http_buffer_size=10MB,     # Buffer de 10MB
    logger=True,                    # Logs do SocketIO habilitados
    engineio_logger=True            # Logs do Engine.IO habilitados
)
```

**Justificativa**:
- `ping_timeout=120`: Permite que predições longas do Granite completem sem timeout
- `ping_interval=25`: Mantém conexão ativa com pings regulares
- `max_http_buffer_size=10MB`: Suporta mensagens grandes com muitas predições

---

### 4. **Logs de SocketIO e Engine.IO**

Habilitados logs dos componentes internos:

```python
logging.getLogger('socketio').setLevel(logging.INFO)
logging.getLogger('engineio').setLevel(logging.INFO)
```

---

## Como Usar os Logs para Diagnóstico

### Padrões de Log a Observar

#### ✅ **Funcionamento Normal**

```
[ForecastService/Granite] Preparing data: 512 points
[ForecastService/Granite] DataFrame shape: (512, 2)
[ForecastService/Granite] Starting prediction with 96 steps...
[ForecastService/Granite] Prediction completed in 2.345s
[ForecastService/Granite] Response shape: (96, 1)
[ForecastService/Granite] Extracted 96 predictions from 'value' column
[ForecastService/Granite] Total forecast time: 2.456s
[WebSocket] Emitting data: 15234 bytes (iteration 42)
[WebSocket] Data emitted successfully (iteration 42)
```

#### ⚠️ **Predição Lenta (possível causa de timeout)**

```
[ForecastService/Granite] Starting prediction with 96 steps...
[ForecastService/Granite] Prediction completed in 125.678s  # > 120s = TIMEOUT!
```

**Ação**: Se o tempo de predição exceder `ping_timeout`, aumentar o valor ou otimizar o modelo.

#### ❌ **Erro na Predição**

```
[ForecastService/Granite] Forecast error after 3.456s: CUDA out of memory
[ForecastService/Granite] Exception type: RuntimeError
```

**Ação**: Verificar memória GPU/CPU, reduzir `context_length` ou `forecast_horizon`.

#### ❌ **Erro na Emissão WebSocket**

```
[WebSocket] Emit error (iteration 42): Connection closed
[WebSocket] Exception type: ConnectionError
```

**Ação**: Cliente desconectou ou timeout ocorreu. Verificar logs do cliente.

---

## Checklist de Diagnóstico

Quando a conexão WebSocket cair, verificar na ordem:

1. **Tempo de predição do Granite**
   - [ ] Está abaixo de 120s?
   - [ ] Se não, aumentar `ping_timeout` ou otimizar modelo

2. **Tamanho dos dados emitidos**
   - [ ] Está abaixo de 10MB?
   - [ ] Se não, reduzir `forecast_horizon` ou aumentar `max_http_buffer_size`

3. **Erros de memória**
   - [ ] GPU/CPU tem memória suficiente?
   - [ ] Considerar reduzir `context_length`

4. **Logs do cliente**
   - [ ] Cliente recebeu timeout?
   - [ ] Cliente fechou conexão intencionalmente?

5. **Rede**
   - [ ] Conexão de rede estável?
   - [ ] Firewall bloqueando WebSocket?

---

## Métricas de Performance Esperadas

### Granite TTM-R2

- **Tempo de carregamento**: 5-15s (primeira vez)
- **Tempo de predição (CPU)**: 2-5s para 96 passos
- **Tempo de predição (GPU)**: 0.5-2s para 96 passos
- **Tamanho da resposta**: ~5-20KB por predição

### Exponential Smoothing (Fallback)

- **Tempo de predição**: 0.1-0.5s
- **Tamanho da resposta**: ~5-10KB

---

## Comandos Úteis

### Monitorar logs em tempo real

```bash
cd /home/carlosdelfino/workspace/EmbarcaTech/Projeto\ Final/Granite-Time-Series-Forecasting-Python
python app.py 2>&1 | tee granite_debug.log
```

### Filtrar apenas logs de WebSocket

```bash
grep "WebSocket" granite_debug.log
```

### Filtrar apenas logs do Granite

```bash
grep "Granite" granite_debug.log
```

### Ver tempos de predição

```bash
grep "Prediction completed in" granite_debug.log
```

---

## Próximos Passos

Se o problema persistir após estas melhorias:

1. **Coletar logs completos** de uma sessão com falha
2. **Analisar padrões**: 
   - Falha sempre na mesma iteração?
   - Falha após X predições?
   - Falha em horário específico?
3. **Testar isoladamente**:
   - Rodar predição sem WebSocket
   - Rodar WebSocket sem predição
4. **Considerar alternativas**:
   - Usar REST API ao invés de WebSocket para predições
   - Implementar fila de predições assíncronas
   - Cachear predições recentes

---

## Referências

- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Socket.IO Protocol](https://socket.io/docs/v4/)
- [IBM Granite TTM-R2](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
