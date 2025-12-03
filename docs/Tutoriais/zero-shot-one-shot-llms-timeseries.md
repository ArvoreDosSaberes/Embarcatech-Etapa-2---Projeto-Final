# Tutorial: Zero-shot, Zero Few Shot e One-shot com LLMs e IBM TTMS para Séries Temporais

> **Tempo estimado**: 45 minutos

## 1. Objetivo
Este tutorial apresenta, de forma didática, como abordar problemas de séries temporais utilizando Large Language Models (LLMs) nos modos **zero-shot**, **zero few shot**, **enhanced zero few shot** e **one-shot** em conjunto com o **IBM Time Series Management Service (TTMS)**. O foco é demonstrar como o TTMS dá suporte à orquestração de dados, métricas e governança durante a interação com LLMs.

## 2. Pré-requisitos
| Item | Descrição |
| --- | --- |
| Conhecimentos básicos | Noções de séries temporais (tendência, sazonalidade), fundamentos de aprendizado de máquina. |
| Ferramentas | Ambiente Python 3.10+, bibliotecas `pandas`, `numpy`, `matplotlib`, acesso a um LLM via API (ex.: OpenAI, Anthropic ou serviço interno) **e** SDK/CLI do IBM TTMS. |
| Dados | Séries temporais cadastradas em um workspace do IBM TTMS, com metadados e versionamento habilitados. |
| Segurança | Atentar para compliance de dados sensíveis. Utilize as políticas de mascaramento e de acesso granular do TTMS e nunca exponha dados pessoais diretamente ao LLM sem anonimização. |
| Infraestrutura | Chaves de API válidas para TTMS e para o provedor de LLM; rede com acesso aos endpoints `https://<region>.tsm.cloud.ibm.com`. |

## 3. Configuração Inicial com IBM TTMS
1. **Criar workspace**: utilize o IBM Cloud para provisionar um serviço TTMS e crie um workspace dedicado ao domínio analisado (ex.: energia, varejo, telecom).
2. **Organizar coleções**: importe séries temporais para coleções temáticas, definindo atributos (unidade, frequência, fuso horário) e etiquetas para facilitar recuperação.
3. **Habilitar pipelines**: configure jobs de ingestão automática (ex.: a cada hora) e habilite o cálculo de estatísticas nativas (média, desvio, decomposição sazonal).
4. **Gerar credenciais**: crie uma API Key de serviço com permissões apenas de leitura quando o acesso for compartilhado com LLMs; para gravação, use credenciais distintas.
5. **Conectar ao LLM**: planeje como o LLM consumirá dados do TTMS (ex.: via API REST antes do prompt ou com integração RAG que indexa relatórios e anotações do TTMS).

## 4. Conceitos Fundamentais
1. **IBM TTMS**: plataforma de gerenciamento de séries temporais da IBM que provê ingestão, qualidade de dados, agregações em tempo real e versionamento. Serve como fonte confiável para alimentar LLMs de forma governada.
2. **LLM Zero-shot**: modelo recebe apenas a instrução (prompt) sem exemplos explícitos. Depende do conhecimento prévio do LLM para resolver a tarefa.
3. **LLM Zero Few Shot**: modelo recebe instruções e estruturas de saída desejadas (templates, listas de verificação), porém sem um exemplo completo resolvido. É útil para guiar o modelo com âncoras sem engessá-lo.
4. **LLM One-shot**: modelo recebe o prompt e **um** exemplo resolvido, servindo de guia para padronizar a resposta desejada.
5. **LLM Enhanced Zero Few Shot**: variação do zero few shot com recuperação de contexto (RAG) ou metadados adicionais, injetando insights históricos, estatísticas do TTMS e terminologias específicas do domínio antes da instrução principal.
6. **Time Series Forecasting com LLM**: LLM atua como orquestrador ou analista textual, traduzindo contexto do problema em análises descritivas, recomendações de features, geração de código ou interpretação de resultados.
7. **Prompt Engineering**: processo de estruturar instruções para maximizar a qualidade da resposta. Inclui contexto, objetivo, formato de saída e restrições, além de apontar explicitamente as coleções e métricas extraídas do TTMS.

## 5. Quando usar cada abordagem
| Critério | Zero-shot | Zero Few Shot | One-shot | Enhanced Zero Few Shot |
| --- | --- | --- | --- | --- |
| Disponibilidade de exemplos | Não existem exemplos de referência ou são pouco confiáveis, dados extraídos diretamente do TTMS. | Existem templates e checklists, mas não um caso resolvido. | Há pelo menos um exemplo validado com saída esperada. | Há templates e base histórica remissiva (RAG, dados enriquecidos a partir do TTMS e de relatórios derivados). |
| Tempo de setup | Menor, útil em explorações rápidas utilizando coleções TTMS já disponíveis. | Moderado: demanda montagem de esqueleto de saída alinhado às taxonomias do TTMS. | Maior: exige preparação e validação do exemplo usando dados do TTMS. | Elevado: requer configurar recuperação de conhecimento (RAG) junto ao TTMS e curadoria de contexto. |
| Consistência da saída | Depende da clareza do prompt e da qualidade das estatísticas exportadas do TTMS. | Consistência intermediária, guiada pelas estruturas fornecidas. | Alta, graças ao exemplo fornecido. | Muito alta, com respostas contextualizadas pelo TTMS e aderentes às políticas internas. |
| Adaptação a domínios específicos | Limitada quando jargões não são conhecidos pelo modelo. | Boa para domínios com glossários definidos no TTMS. | Excelente, pois o exemplo reforça o vocabulário esperado. | Excelente e dinâmica, incorporando terminologias e estatísticas atualizadas diretamente do TTMS. |
| Uso típico em séries temporais | Geração de hipóteses, descrição dos dados, sugestão de features. | Padronização de relatórios exploratórios e planos de ação apoiados nas coleções TTMS. | Geração de códigos específicos, padronização de relatórios, ajustes finos em pipelines. | Integração com data lake, recomendações sensíveis ao contexto, auditoria e governança com o catálogo TTMS.

## 6. Fluxo Zero-shot para Séries Temporais
1. **Definir o objetivo**: previsão, detecção de anomalias, contextualização de tendências.
2. **Consultar coleções TTMS**: use o SDK/CLI para extrair estatísticas básicas (média, desvio padrão, autocorrelação, sazonalidade) e metadados oficiais.
3. **Criar o prompt** contendo: objetivo, resumo das estatísticas exportadas do TTMS, granularidade temporal, horizonte de previsão desejado e formato de saída.
4. **Enviar ao LLM** e analisar a resposta, verificando coerência e justificativas fornecidas.
5. **Validar** com métricas quantitativas (ex.: MAPE, RMSE) sempre que o LLM gerar código ou estratégias de modelagem.

### Exemplo de Prompt Zero-shot
```
Você é um especialista em séries temporais. Utilize os metadados exportados do IBM TTMS (workspace `energy_ops`, coleção `load_forecast_v1`):
- Métrica: demanda diária de energia
- Período: jan/2020 a dez/2024 (1826 pontos)
- Tendência: crescente
- Sazonalidade: semanal evidente
- RMSE do modelo atual ARIMA(1,1,1): 235
- Observações do TTMS: alertas de outliers em 15/ago e 22/set/2023

Objetivo: sugira um plano de experimentos para reduzir o RMSE em 15%.
Formato esperado:
1. Hipóteses de melhorias
2. Técnicas sugeridas
3. Métricas para acompanhar
```

## 7. Fluxo Zero Few Shot para Séries Temporais
1. **Mapear estruturas de saída**: defina títulos, listas e tabelas que devem aparecer na resposta.
2. **Preparar metadados**: inclua glossários, políticas internas, thresholds relevantes e IDs de coleções TTMS.
3. **Elaborar o prompt** com objetivo, estatísticas-chave exportadas do TTMS e o template a ser seguido.
4. **Incluir âncoras**: indique pontos de atenção (ex.: sazonalidades específicas ou limites de métricas) usando tags do TTMS.
5. **Executar e revisar** ajustando as estruturas até alcançar estabilidade nas respostas.

### Exemplo de Prompt Zero Few Shot
```
Você é consultor de séries temporais. Utilize o template abaixo para responder.

Template obrigatorio:
1. Diagnóstico rápido (máx. 3 bullets)
2. Métricas que merecem vigilância
3. Ações sugeridas

Contexto atual:
- Workspace TTMS: `manufacturing_ops`
- Coleção: `weekly_lead_time`
- Indicador: lead time de produção semanal
- Período: jan/2021 a set/2024 (195 pontos)
- Observações TTMS: sazonalidade trimestral, picos em mar/jun/set, outliers críticos em ago/2023 com tag `supplier_delay`

Entregue o relatório seguindo exatamente o template.
```

## 8. Fluxo One-shot para Séries Temporais
1. **Selecionar um exemplo** real de tarefa resolvida (prompt + resposta ideal).
2. **Estruturar o prompt** com as mesmas seções do zero-shot, mas adicionando o exemplo como guia.
3. **Explicitar o formato** que deve ser seguido pelo LLM ao responder novos casos.
4. **Aplicar o prompt** em séries semelhantes, ajustando apenas as estatísticas ou metas específicas exportadas do TTMS.

### Exemplo de Prompt One-shot
```
Tarefa: gerar relatório de previsão mensal.

Exemplo resolvido (não repetir, apenas usar como padrão):
[Exemplo]
Workspace TTMS: `retail_sales`
Coleção: `monthly_revenue_main`
Contexto: vendas de varejo (jan/2019 - dez/2023)
Resumo estatístico: média=1200, sazonalidade mensal, tendência leve
Horizonte: 3 meses
Saída ideal:
1. Sumário executivo (2 parágrafos)
2. Tabela com previsão e intervalo de confiança
3. Recomendações de ações
[/Exemplo]

Novo caso:
- Workspace TTMS: `telecom_customer_success`
- Coleção: `premium_plan_churn`
Contexto: churn mensal do plano premium
Resumo estatístico TTMS: média=3,5%, sazonalidade trimestral, pico em mar/jun/set/dez
Horizonte: 6 meses
Formato esperado: replicar a estrutura do exemplo.
```

## 9. Fluxo Enhanced Zero Few Shot para Séries Temporais
1. **Provisionar base de conhecimento**: indexe relatórios anteriores, políticas e estatísticas no sistema de recuperação (RAG).
2. **Montar o prompt estruturado**: inclua template, descrição do caso atual e instruções para citar fontes recuperadas diretamente do TTMS (coleções, snapshots, relatórios anotados).
3. **Configurar parâmetros**: defina limites de tokens, temperatura baixa e filtros de conteúdo sensível, reforçando políticas do TTMS.
4. **Executar com enriquecimento**: garanta que o pipeline recupere datasets e notas do TTMS antes da geração do texto.
5. **Validar e auditar**: registre fontes utilizadas e crie trilhas de auditoria.

### Exemplo de Prompt Enhanced Zero Few Shot
```
Sistema: utilize o contexto fornecido pela busca semântica para preencher o template abaixo.

Contexto recuperado:
- TTMS Snapshot `churn_review_2023Q4`: aumento de churn em períodos promocionais
- Estatística atual TTMS: churn médio 3,2%, pico 4,1% em set/2024
- Política interna: citar recomendações com base em casos anteriores do TTMS e indicar IDs das coleções utilizadas

Template:
1. Sumário executivo (mencione fontes)
2. Drivers principais
3. Plano de mitigação com responsáveis

Caso atual: churn mensal do plano premium, meta reduzir 0,5 p.p. em 3 meses.
```

## 10. Pipeline Referencial com IBM TTMS
1. **Preparação dos dados**
   - Configurar jobs TTMS para tratar valores ausentes, outliers e alinhar granularidade.
   - Gerar features temporais no TTMS (lags, sazonalidade, feriados) ou exportá-las para notebooks Python.
2. **Exploração com LLM**
   - Zero-shot: solicitar insights iniciais, hipóteses de features.
   - Zero Few Shot: padronizar relatórios e planos exploratórios alinhados às coleções TTMS.
   - One-shot: produzir relatórios ou scripts com base em exemplo vinculado ao TTMS.
   - Enhanced Zero Few Shot: gerar recomendações governadas por contexto enriquecido com snapshots TTMS.
3. **Implementação técnica**
   - Traduzir recomendações para código Python (ex.: `statsmodels`, `prophet`, `neuralprophet`) consumindo datasets exportados do TTMS via API.
4. **Validação**
   - Comparar modelos tradicionais com propostas assistidas pelo LLM, registrando resultados de volta no TTMS como artefatos ou tags.
   - Registar métricas e inferências aprovadas no TTMS ou em dashboards conectados.
5. **Governança**
   - Controlar versões de prompts e respostas.
   - Revisar uso de dados sensíveis, auditoria de acessos no TTMS e conformidade com políticas de dados.

## 11. Boas Práticas de Prompt Engineering
- **Clareza**: descreva contexto, objetivo e restrições.
- **Formato**: peça estruturas numeradas ou tabelas para facilitar parsing.
- **Vocabulário**: explicite termos e métricas críticas (RMSE, MAPE, janela de previsão) conforme nomenclatura do TTMS.
- **Validar consistência**: refazer prompts com variações para garantir robustez.
- **Versionamento**: mantenha histórico de prompts em repositório controlado (ex.: `docs/prompts/`) e associe-os aos workspaces TTMS utilizados.
- **Contexto TTMS**: informe explicitamente IDs de coleções, snapshots e filtros aplicados para evitar divergências.

## 12. Testes e Validação
1. **Teste manual**: revise respostas quanto a plausibilidade e coerência com os dados reais.
2. **Teste automatizado**: use scripts que comparam recomendações do LLM versus baseline quantitativo, consumindo datasets exportados automaticamente do TTMS.
3. **Monitoramento**: registre métricas em dashboards conectados ao TTMS e compute estatísticas de erro contínuas.
4. **Feedback loop**: documente ajustes feitos nos prompts e resultados obtidos a cada iteração, atualizando notas dentro do TTMS para preservar rastreabilidade.

## 13. Checklist de Implementação
- [ ] Workspace do IBM TTMS configurado com coleções e permissões adequadas.
- [ ] Dados pré-processados e auditados no TTMS.
- [ ] Prompt zero-shot documentado com referência ao TTMS.
- [ ] Prompt zero few shot e enhanced zero few shot vinculados a templates TTMS.
- [ ] Prompt one-shot com exemplo validado e armazenado no TTMS.
- [ ] Métricas de avaliação definidas (RMSE, MAPE, MAE, etc.) e registradas no TTMS.
- [ ] Rotina de logging das respostas do LLM implementada e integrada ao TTMS/observabilidade.
- [ ] Plano de governança e auditoria aprovado, com revisões de acesso ao TTMS.

## 14. Próximos Passos
1. Criar biblioteca interna com prompts reusáveis para tarefas recorrentes.
2. Integrar LLM a pipelines de MLOps para automação de análises e geração de relatórios alimentados pelo TTMS.
3. Avaliar fine-tuning ou uso de modelos especializados em séries temporais quando houver volume de dados suficiente e persisti-los como modelos registrados no TTMS.

---
**Referências Sugeridas**
- Brown, T. et al. *Language Models are Few-Shot Learners*. NeurIPS, 2020.
- Makridakis, S. et al. *The M4 Competition*. International Journal of Forecasting, 2018.
- IBM. *Time Series Management Service Documentation*. Disponível em: https://cloud.ibm.com/docs/time-series.
- Interpretable AI documentation (serviço interno) – seção de governança de prompts.
