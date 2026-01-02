# Tutorial: WCET e McCabe (Complexidade Ciclomática) — o que são e como interpretar os dados

Este tutorial explica, de forma prática, dois conceitos muito usados em sistemas embarcados e tempo real:

- **WCET** (*Worst-Case Execution Time*): o **pior tempo de execução** que um trecho de código pode levar.
- **McCabe** (*Complexidade Ciclomática*): uma **métrica de complexidade** que estima quantos caminhos lógicos independentes existem em uma função.

O objetivo é te ajudar a **ler e interpretar** os relatórios gerados por ferramentas do projeto (ex.: `scripts/mccabe_wcet_report.py`), entender o que é **normal**, o que é **risco**, e o que fazer quando uma métrica “estoura”.

---

## Sumário

1. [O que é WCET?](#1-o-que-é-wcet)
2. [O que é McCabe (Complexidade Ciclomática)?](#2-o-que-é-mccabe-complexidade-ciclomática)
3. [Por que WCET e McCabe se complementam](#3-por-que-wcet-e-mccabe-se-complementam)
4. [Como os dados são gerados no projeto](#4-como-os-dados-são-gerados-no-projeto)
5. [Como interpretar o relatório (seção por seção)](#5-como-interpretar-o-relatório-seção-por-seção)
6. [Como usar as métricas para tomar decisões](#6-como-usar-as-métricas-para-tomar-decisões)
7. [Armadilhas comuns (e como evitar)](#7-armadilhas-comuns-e-como-evitar)
8. [Checklist rápido](#8-checklist-rápido)

---

## 1. O que é WCET?

**WCET** (*Worst-Case Execution Time*) é o **maior tempo de execução possível** para uma função/trecho de código, considerando o **pior cenário**.

Em sistemas **tempo real**, WCET é essencial porque você precisa garantir que:

- Uma **task** termine antes do próximo *deadline*.
- Uma **ISR** (interrupção) não bloqueie o sistema por tempo demais.
- O escalonador não entre em saturação (CPU a 100%) em picos.

### 1.1 WCET não é “tempo médio”

- **Tempo médio** ajuda a entender desempenho típico.
- **WCET** é sobre **garantia**: “mesmo no pior caso, ainda funciona?”.

### 1.2 Exemplo intuitivo

Se uma task roda a cada `10 ms` e, no pior caso, ela leva `7 ms`, você ainda tem folga.
Se ela pode levar `12 ms`, ela **perde o prazo** e começa a acumular atraso.

---

## 2. O que é McCabe (Complexidade Ciclomática)?

A **complexidade ciclomática de McCabe** estima quantos **caminhos de decisão** existem dentro de uma função.

- Funções com muitas condições (`if/else`, `switch`, loops, `break`, etc.) têm mais caminhos.
- Quanto mais caminhos, mais difícil:
  - **testar completamente** (explosão combinatória);
  - **prever comportamento**;
  - **garantir WCET realista**, porque o pior caminho pode ser raro e difícil de reproduzir.

### 2.1 Interpretação rápida

Em geral (regra prática, não absoluta):

- **1 a 5**: simples e fácil de testar
- **6 a 10**: moderado
- **11 a 20**: alto (risco crescente)
- **> 20**: muito alto (tende a pedir refatoração)

> Importante: em embarcados, é comum aceitar funções com McCabe maior em drivers/decodificadores, mas você deve justificar e compensar com testes.

### 2.2 Como a métrica costuma ser calculada

Uma forma comum de aproximar McCabe é:

- `McCabe = 1 + (quantidade de decisões)`

No projeto, a análise offline usa **assembly** e conta **branches condicionais** como “decisões” para estimar McCabe.

---

## 3. Por que WCET e McCabe se complementam

- **McCabe** te diz: “o código tem muitos caminhos possíveis?”
- **WCET** te diz: “no pior caminho, quanto tempo pode levar?”

Cenários típicos:

- **McCabe alto + WCET alto**:
  - risco maior de *deadline miss*, difícil de testar, difícil de garantir.
- **McCabe alto + WCET baixo**:
  - o tempo pode estar ok, mas manutenção/testes são difíceis.
- **McCabe baixo + WCET alto**:
  - código simples, mas pesado (muita cópia, loops longos, IO, etc.).

---

## 4. Como os dados são gerados no projeto

O script `scripts/mccabe_wcet_report.py` gera um relatório em Markdown com duas fontes principais:

### 4.1 Análise **offline** (sem serial)

Analisa um arquivo **ELF** para extrair:

- **Complexidade McCabe** por função (via contagem de branches condicionais no assembly)
- **Estimativa de ciclos** por função (tabela simplificada de ciclos por instrução)
- **Estimativa de tempo (μs)** por função usando o clock do MCU
- **Callgraph** (quem chama quem)

Esse modo é útil para:

- fazer auditoria do código sem rodar no hardware;
- identificar funções com alto risco estrutural (complexidade);
- ter uma estimativa inicial de custo computacional.

### 4.2 Coleta **online** (com serial)

Quando o firmware emite linhas no formato **KV (key=value)** via serial, o relatório agrega:

- **Heap** (ex.: `heap_free`, `heap_min`)
- **Stack por task** (ex.: `stack_used`, `stack_free`, `stack_usage_pct`)
- **CPU por task** (via bloco de *Run Time Stats* ou estimativa por trace)
- **WCET medido** por probes (ex.: `WcetKV name=... dur_us=... task=... isr=...`)

Esse modo é útil para:

- validar hipóteses (a estimativa offline condiz com o real?)
- identificar picos, gargalos e regressões
- encontrar *spikes* de latência (p99/p95 altos)

---

## 5. Como interpretar o relatório (seção por seção)

A seguir, como ler as partes principais geradas por `_renderMarkdown()`.

### 5.1 `## Heap`

Exibe estatísticas incrementais para:

- `heap_free`: heap livre observado
- `heap_min`: menor heap livre observado (pior caso de fragmentação/uso)

Campos típicos:

- `count`: número de amostras
- `min`: menor valor observado
- `max`: maior valor observado
- `mean`: média

**Como interpretar**:

- `heap_min` é normalmente o mais importante: ele indica a **pior folga de heap**.
- Se `heap_min` está caindo com o tempo, pode haver:
  - vazamento;
  - alocação dinâmica crescente;
  - fragmentação.

### 5.2 `## Tasks` (por task)

Para cada task (ex.: `### SensorTask`), aparecem métricas como:

- `stack_used (bytes)`
- `stack_free (bytes)`
- `stack_usage_pct (%)`
- `cpu_pct (%)`

**Como interpretar stack**:

- O mais importante é garantir que o **pior caso** de `stack_used` não chegue perto do limite.
- Uma regra prática é manter margem (por exemplo) de **20% a 30%** (depende do projeto).

**Como interpretar CPU%**:

- CPU% alto constante em uma task pode indicar:
  - loop sem delay;
  - polling;
  - tarefa “faz tudo”.
- CPU% baixo mas com picos de WCET pode indicar:
  - trabalho esporádico pesado;
  - contenda de recursos;
  - picos por condição rara.

### 5.3 `## Escalonamento / CPU (janela)`

Mostra uma tabela com **estimativa de CPU por task em uma janela** (por padrão `5s`) quando há eventos `TraceKV`.

Campos:

- `CPU%`: porcentagem de tempo rodando na janela
- `RunTime(s)`: tempo efetivo rodando na janela

**Como interpretar**:

- Essa tabela é uma “foto” recente: use para entender o **agora**.
- Se o trace estiver incompleto (perdas na serial), a estimativa pode ficar distorcida.

### 5.4 `### Segmentos de escalonamento (resumo)`

Tabela por task com:

- `Segments`: número de vezes que a task entrou/saiu
- `TotalRunTime(s)`: soma de tempo rodando (no log)
- `MeanSegment(s)`: duração média de um “pedaço” de execução
- `MaxSegment(s)`: maior fatia observada

**Como interpretar**:

- `MaxSegment(s)` alto pode indicar:
  - preempção baixa (prioridade alta ou interrupções longas);
  - task “monopolizando” CPU;
  - seções críticas longas.

### 5.5 `## WCET (probes)`

Quando existem amostras de `WcetKV` (ou prefixos equivalentes), o relatório traz:

| Campo | O que significa |
|---|---|
| `Probe` | nome do ponto medido (ex.: `name`) |
| `Task` | task associada à medição |
| `ISR` | `1` se a medição ocorreu em interrupção, `0` caso contrário |
| `Count` | quantas amostras |
| `Min(us)` | menor duração |
| `P95(us)` | percentil 95 (95% das execuções ficam abaixo disso) |
| `P99(us)` | percentil 99 |
| `Mean(us)` | média |
| `Std(us)` | desvio padrão |
| `Max(us)` | maior duração observada |

**Como interpretar percentis (P95/P99)**:

- `Max` é importante, mas pode ser um outlier.
- `P95` e `P99` ajudam a entender “pior caso típico”.

Heurística prática:

- Se `P99` já está próximo do seu *deadline*, você tem risco alto.
- Se `Max` é muito maior que `P99`, investigue:
  - interferência de interrupções;
  - contenção (mutex/queue);
  - cache/memória;
  - log/printf em caminho crítico.

### 5.6 `## Complexidade Ciclomática (McCabe) - análise offline`

Quando a análise offline completa está disponível, aparece:

- Clock do MCU
- Quantidade de funções analisadas
- Tasks identificadas
- Profundidade do callgraph

E uma tabela típica:

| Função | McCabe | Decisões | Instruções | Ciclos Est. | WCET Est. (μs) | Task |
|---|---:|---:|---:|---:|---:|:---:|

**Como interpretar**:

- `McCabe`: quanto maior, mais caminhos e mais difícil de testar.
- `Decisões`: aproxima a contagem de branches condicionais.
- `Instruções`: tamanho/complexidade em assembly (aproxima custo).
- `Ciclos Est.` e `WCET Est. (μs)`: estimativa baseada na tabela de ciclos e no clock.

> Atenção: `WCET Est.` aqui é **estimado**. O WCET “real” pode ser maior por wait-states, cache, preempção, contenção e variação de caminho.

### 5.7 `### Tasks Identificadas`

Lista funções detectadas como tasks (heurística por nome). Ajuda a focar no que impacta diretamente escalonamento.

### 5.8 `### Callgraph (amostra de arestas)`

Exibe relações do tipo:

- `funcA` → `funcB`

**Como interpretar**:

- Ajuda a localizar “funções centrais” (muitas chamadas).
- Um nó muito conectado pode ser um bom alvo para:
  - simplificação;
  - caching;
  - divisão em módulos.

---

## 6. Como usar as métricas para tomar decisões

### 6.1 Quando refatorar por McCabe

Refatore quando:

- McCabe muito alto em função crítica de tempo real.
- Bugs recorrentes na mesma função.
- Testes começam a ficar inviáveis.

Estratégias comuns:

- Extrair funções menores.
- Substituir `if/else` em cascata por tabela/estado.
- Isolar validação/parsing do caminho crítico.

### 6.2 Quando otimizar por WCET

Otimize quando:

- `P99` ou `Max` ameaçam o *deadline*.
- Há jitter grande (desvio padrão alto).

Estratégias comuns:

- Remover `printf/log` do caminho crítico.
- Trocar estruturas de dados por versões com custo previsível.
- Evitar alocação dinâmica.
- Reduzir seções críticas e tempo com lock.

### 6.3 Quando aumentar stack

Aumente stack quando:

- `stack_usage_pct` máximo observado passa de uma margem segura.

Mas antes verifique:

- Recursão acidental.
- Buffers grandes em variáveis locais.
- Uso de `printf`/formatação pesada (pode consumir stack).

---

## 7. Armadilhas comuns (e como evitar)

1. **Confundir “estimativa offline” com “garantia”**
   - A estimativa por ciclos ajuda a comparar funções, mas não substitui medição real.

2. **Usar apenas `Max` para decidir**
   - Use `P95/P99` para entender frequência do pior caso.

3. **Coletar poucas amostras (`Count` baixo)**
   - Poucas amostras podem esconder o pior caso.

4. **Medir com logs habilitados**
   - Logs alteram timing e podem inflar WCET.

5. **Ignorar interferência de ISR**
   - Uma task pode “parecer lenta” porque foi preemptada.

---

## 8. Checklist rápido

- **WCET (probes)**
  - `Count` suficiente?
  - `P99` está dentro do *deadline*?
  - `Max` é um outlier extremo?

- **McCabe**
  - Funções críticas com McCabe alto?
  - Funções “centrais” (muitas chamadas) estão complexas?

- **RTOS**
  - `heap_min` tem folga?
  - `stack_usage_pct` máximo tem margem?
  - Uma task domina CPU de forma inesperada?

---
