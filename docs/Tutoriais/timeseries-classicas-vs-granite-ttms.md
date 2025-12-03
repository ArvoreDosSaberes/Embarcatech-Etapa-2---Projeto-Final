# Tutorial: Séries Temporais Clássicas e Granite TTMS (IBM)

> **Tempo estimado**: 60 minutos

## 1. Objetivo
Apresentar um fluxo didático para análise e previsão de séries temporais comparando abordagens **clássicas** (ARIMA, ETS, Prophet) com o uso de **modelos baseados em LLM**, destacando a família **Granite Time-Series Model (TTMS)** da IBM. Ao final, você será capaz de configurar ambos os pipelines, interpretar resultados e definir critérios para escolher a estratégia ideal em produção.

## 2. Pré-requisitos
| Item | Descrição |
| --- | --- |
| Conhecimentos prévios | Estatística básica, noções de séries temporais (tendência, sazonalidade, estacionariedade), fundamentos de machine learning. |
| Ferramentas | Python 3.10+, bibliotecas `pandas`, `numpy`, `matplotlib`, `statsmodels`, `prophet`, `scikit-learn`; acesso à plataforma **IBM watsonx** com o modelo Granite TTMS habilitado. |
| Dados | Histórico consolidado da métrica-alvo em CSV ou banco relacional; metadados sobre feriados e eventos de negócio. |
| Segurança | Garantir anonimização de dados sensíveis antes de enviá-los a provedores externos; validar políticas de LGPD e acordos de confidencialidade. |
| Observabilidade | Ferramenta de logging centralizado para registrar métricas, prompts e respostas (ex.: Elastic Stack, Grafana Loki). |

## 3. Visão Geral das Abordagens
| Aspecto | Clássicas (ARIMA/ETS/Prophet) | Granite TTMS (LLM) |
| --- | --- | --- |
| Dependência de dados | Necessitam histórico consistente e pré-processamento rigoroso. | Podem combinar histórico com contexto textual (eventos, planos de marketing) para enriquecer a previsão. |
| Interpretabilidade | Elevada; parâmetros claros (p, d, q, sazonalidade). | Média; fornece explicações textuais, mas baseia-se em embeddings e conhecimento pré-treinado. |
| Tempo de setup | Baixo a médio (scripts locais). | Médio; requer integração com API, gestão de prompts e credenciais. |
| Escalabilidade | Exige tuning manual para cada série. | Suporta múltiplas séries com ajustes via prompt e few-shot. |
| Custos | Infra hospedada localmente ou cloud básica. | Uso sob demanda na plataforma IBM; considerar custos de tokens e latência. |

## 4. Passo a Passo Consolidado

### 4.1 Preparação dos Dados
1. **Ingestão**: carregar CSV ou executar consulta SQL com filtros de período e granularidade.
2. **Limpeza**: tratar valores ausentes (imputação ou forward fill), remover outliers extremos, garantir monotonicidade temporal.
3. **Engenharia de atributos**: criar lags, médias móveis, variáveis sazonais e marcadores de feriados/eventos.
4. **Split temporal**: separar conjuntos de treino, validação e teste respeitando a ordem cronológica (ex.: 70/15/15).
5. **Documentação**: registrar decisões de limpeza em `docs/how-to/` e versionar scripts de preparação.

### 4.2 Pipeline Clássico (ARIMA/ETS/Prophet)
1. **Exploração**: aplicar decomposição STL, autocorrelação (ACF/PACF) e testes de estacionariedade (ADF, KPSS).
2. **Seleção de modelo**:
   - *ARIMA/SARIMA*: testar combinações de (p, d, q) e componentes sazonais (P, D, Q, s).
   - *ETS*: usar `statsmodels.tsa.holtwinters` para captar tendência e sazonalidade suaves.
   - *Prophet*: ideal para séries com feriados e sazonalidades múltiplas.
3. **Treinamento**: ajustar o modelo no conjunto de treino e validar hiperparâmetros usando walk-forward validation.
4. **Avaliação**: calcular RMSE, MAPE, sMAPE, cobertura do intervalo de confiança.
5. **Implantação**: empacotar scripts em um serviço REST (Express.js ou FastAPI) com rotinas de atualização.
6. **Monitoramento**: coletar métricas em dashboards, armazenar previsões e erros para ajuste contínuo.

### 4.3 Pipeline Granite TTMS (LLM da IBM)
1. **Provisionamento**:
   - Criar projeto no **IBM watsonx**.
   - Gerar API key e configurar variáveis de ambiente (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`).
2. **Contextualização**:
   - Resumir dados (estatísticas, eventos, feriados) em texto estruturado.
   - Converter séries para formato aceito (JSON ou CSV) e, se necessário, armazenar em object storage acessível ao modelo.
3. **Prompt Engineering**:
   - Definir objetivo, horizonte de previsão, métricas-alvo e restrições.
   - Incluir *few-shot* com exemplos aprovados para padronizar a saída.
4. **Chamada à API**: enviar prompt e dados para o endpoint Granite TTMS (`/ml/v1-beta/generate_timeseries`).
5. **Pós-processamento**:
   - Converter o output em DataFrame, validar coerência com escalas e sazonalidade histórica.
   - Armazenar logs (prompts, respostas, versões do modelo) para auditoria.
6. **Iteração**: ajustar prompts, fornecer feedback e comparar resultados com baseline clássico.

#### Exemplo de Prompt Estruturado
```
Sistema: Você é um especialista em previsão de demanda energética industrial.
Dados resumidos:
- Período: 2018-01-01 a 2024-06-30 (diário)
- Tendência: crescente
- Sazonalidade: semanal e anual
- Eventos relevantes: manutenção anual em agosto, feriados nacionais (lista em anexo)
- Métrica atual: RMSE=180, MAPE=4,2%
Tarefa: Gere previsões para os próximos 90 dias com intervalo de confiança de 95%.
Formato de saída:
1. Tabela (data, previsão, limite inferior, limite superior)
2. Sumário textual (até 3 parágrafos)
3. Recomendações de ajuste operacional
Restrições: explique como eventos externos influenciam a dinâmica prevista.
```

### 4.4 Comparação e Decisão
1. **Consolidar métricas** em uma tabela comparando RMSE, MAPE, cobertura e custo de execução.
2. **Fatores qualitativos**: interpretabilidade, tempo de resposta, aderência a compliance.
3. **Escolha híbrida**: considerar ensemble (média ponderada) ou uso condicional (clássico para curto prazo, Granite para cenários estratégicos com contexto textual).

## 5. Boas Práticas
- **Versionamento**: manter prompts, scripts e parâmetros em repositório Git separado por ambiente.
- **Governança**: registrar quem alterou prompts e por quê; utilizar checklist de aprovação antes de enviar dados sensíveis.
- **Observabilidade**: centralizar logs com o formato `[timeseries/forecasting] Mensagem 😀` para facilitar auditoria.
- **Resiliência**: implementar tratamento de exceções e retentativas ao chamar a API Granite TTMS (status 429, 5xx).
- **Documentação**: atualizar `docs/` com decisões de modelagem e resultados de experimentos.

## 6. Checklist Operacional
- [ ] Dataset higienizado, com metadados documentados.
- [ ] Baseline clássico treinado e salvo (artefatos versionados).
- [ ] Credenciais do IBM watsonx configuradas com rotação automática.
- [ ] Prompts Granite TTMS revisados por especialista de domínio.
- [ ] Monitoramento de métricas em produção com alertas proativos.
- [ ] Plano de fallback caso a API Granite esteja indisponível.

## 7. Próximos Passos
1. Construir pipeline MLOps que automatize re-treinos e comparações de modelos.
2. Experimentar *prompt chaining* para incorporar análises de anomalias antes da previsão.
3. Avaliar fine-tuning supervisionado do Granite TTMS com dados proprietários (respeitando contratos).
4. Implementar testes automatizados que validem coerência das previsões (faixas aceitáveis, monotonicidade).

## 8. Referências
- Makridakis, S. et al. *The M4 Competition: 100,000 Time Series and 61 Forecasting Methods*. International Journal of Forecasting, 2018.
- Hyndman, R.J., Athanasopoulos, G. *Forecasting: Principles and Practice*. OTexts, 2021.
- IBM. *Granite Foundation Models for Time-Series*. Documentação watsonx (2024).
- Brown, T. et al. *Language Models are Few-Shot Learners*. NeurIPS, 2020.
- Aggarwal, C. *Machine Learning for Time-Series Forecasting*. Springer, 2023.
