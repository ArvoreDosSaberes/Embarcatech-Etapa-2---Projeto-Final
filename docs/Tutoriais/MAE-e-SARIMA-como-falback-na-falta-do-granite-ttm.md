## 1 — Introdução ao SARIMA no contexto do projeto final do EmbarcaTech TIC-27

No projeto de conclusão do EmbarcaTech TIC-27, desenvolvido em 2025, utilizamos modelos modernos de previsão de séries temporais baseados em Inteligência Artificial—como o  **Granite TTM** , um modelo de larga escala treinado para tarefas temporais. Entretanto, em ambientes embarcados e sistemas de produção reais, é essencial possuir um modelo de  **fallback** , isto é, um método alternativo e robusto para garantir previsões mesmo quando o modelo principal falha ou quando não há capacidade computacional para executá-lo. Para essa função, adotamos o modelo  **SARIMA (Seasonal AutoRegressive Integrated Moving Average)** , amplamente reconhecido pela confiabilidade e base matemática sólida.

O SARIMA é uma extensão do clássico modelo ARIMA, incorporando a capacidade de lidar com  **padrões sazonais** , isto é, repetições periódicas na série temporal, como ciclos diários, semanais, mensais ou anuais. Essa característica é particularmente útil em aplicações embarcadas que analisam medições ambientais, cargas elétricas, sensores ou dados associados a rotinas humanas, onde a sazonalidade é comum.

Diferentemente dos modelos baseados em aprendizado profundo, o SARIMA não necessita de grandes bases de dados, nem de aceleradores de hardware, tornando-se adequado para execução em microcontroladores, SBCs (Single Board Computers) ou servidores de borda com capacidade limitada. Assim, em nosso projeto utilizamos o Granite TTM como solução principal devido à sua capacidade de capturar relações complexas de longo prazo, enquanto o SARIMA opera como uma garantia de previsões estáveis e matematicamente explicáveis, caso o sistema detecte irregularidades ou aumentos de erro no modelo primário.

Por fim, adotamos a métrica **MAE (Mean Absolute Error)** como principal indicador de desempenho, tanto para o Granite TTM quanto para o SARIMA. Isso porque o MAE traduz de forma direta e compreensível a média dos erros absolutos cometidos pelas previsões, facilitando a comparação entre modelos e permitindo detectar cenários em que o fallback deve ser ativado.

---

A seguir apresento **o Capítulo 2**, aprofundando os fundamentos matemáticos do modelo SARIMA de forma didática, clara para iniciantes, mas com rigor técnico.

Quando quiser avançar, peça **“próximo”**.

---

## 2 — Fundamentos Matemáticos do Modelo SARIMA

O modelo **SARIMA** combina quatro ideias fundamentais:
**(1)** dependência temporal (AR),
**(2)** tendência removida por diferenciação (I),
**(3)** ruído estruturado (MA),
**(4)** repetição sazonal (S).

Para entender o modelo, é essencial decompor cada parte matematicamente, pois o SARIMA nada mais é que uma composição de operadores aplicados sobre a série temporal original.

---

### 2.1. Revisão do ARIMA

O SARIMA é baseado no modelo ARIMA, definido por três parâmetros:

\[
ARIMA(p, d, q)
\]

onde:

* **p** = ordem do termo autorregressivo (AutoRegressive – AR)
* **d** = número de diferenças aplicadas (Integrated – I)
* **q** = ordem do termo de Médias Móveis (Moving Average – MA)

A série original ( y_t ) é transformada por **d diferenciações**:

\[
\nabla^d y_t = (1 - L)^d y_t
\]

onde **L** é o operador de defasagem (lag):

\[
L y_t = y_{t-1}
\]

A partir disso, o componente **AR(p)** assume que o valor atual depende de valores anteriores:

\[
AR(p):\quad y_t = \phi_1 y_{t-1} + \phi_2 y_{t-2} + \dots + \phi_p y_{t-p} + \varepsilon_t
\]

A parte **MA(q)** modela o erro atual como combinação de erros passados:

\[
MA(q):\quad y_t = \varepsilon_t + \theta_1 \varepsilon_{t-1} + \dots + \theta_q \varepsilon_{t-q}
\]

O ARIMA combina tudo:

\[
\Phi(L) \nabla^d y_t = \Theta(L) \varepsilon_t
\]

onde:

* \(\Phi(L)\) é o polinômio AR
* \(\Theta(L)\) é o polinômio MA

---

### 2.2. Introdução à Sazonalidade

Em muitas situações reais (como consumo de energia, temperatura, tráfego de redes, ou séries do nosso projeto TIC-27), há um ciclo natural.
Por exemplo: leituras que se repetem a cada **24 horas** (período diário).

Chamamos isso de **sazonalidade de período ( s )**.

Para capturar isso, introduzimos operadores sazonais, como:

\[
\nabla_s y_t = y_t - y_{t-s}
\]

Esse operador remove padrões que se repetem.

---

## **2.3. O Modelo SARIMA Completo**

O modelo é escrito formalmente como:

\[
SARIMA(p, d, q)(P, D, Q)_s
\]

onde:

* **(p, d, q)** controlam os componentes não sazonais
* **(P, D, Q)** controlam os componentes sazonais
* **s** é o período da sazonalidade (por exemplo, 24, 12, 365, etc.)

Matematicamente, o modelo completo é:

[
\Phi_p(L) , \Phi_P(L^s) , (1 - L)^d , (1 - L^s)^D y_t =
\Theta_q(L) , \Theta_Q(L^s), \varepsilon_t
]

onde:

* \(\Phi_p(L)\) é o polinômio AR não sazonal
* \(\Phi_P(L^s)\) é o polinômio AR sazonal
* \((1 - L)^d\) é a diferenciação não sazonal
* \((1 - L^s)^D\) é a diferenciação sazonal
* \(\Theta_q(L)\) é o polinômio MA não sazonal
* \(\Theta_Q(L^s)\) é o polinômio MA sazonal

O termo \((1 - L^s)^D\) diferencia a série considerando repetições de período **s**.

---

### 2.4. Intuição

Apesar da forma matemática compacta, o SARIMA faz algo simples e intuitivo:

1. **Remove tendência** (valores crescentes ou decrescentes).
2. **Remove padrões repetitivos** (dia/noite, mês a mês, etc.).
3. **Aprende como cada ponto depende dos anteriores**.
4. **Aprende como os erros se repetem ao longo do tempo**.
5. **Gera previsões baseadas nesses padrões aprendidos**.

Por isso o SARIMA é tão valioso no nosso projeto:
Mesmo sem GPUs, e mesmo com pouca memória, ele entrega previsões estáveis e matematicamente justificáveis.

---

## 3 — Granite TTM vs. SARIMA e o Papel do SARIMA como Fallback

No projeto de conclusão do EmbarcaTech TIC-27 adotamos uma arquitetura híbrida de previsão onde coexistem dois modelos complementares: o **Granite TTM**, baseado em inteligência artificial de larga escala, e o **SARIMA**, fundamentado em modelagem estatística clássica. Cada um possui pontos fortes que se ajustam a diferentes condições operacionais, e é justamente dessa complementaridade que surge a necessidade de um mecanismo de fallback.

O **Granite TTM** é um modelo moderno, pertencente à classe dos *Temporal Transformers*. Ele foi treinado com grandes volumes de dados e é capaz de capturar dependências complexas, não lineares, de longo alcance e com múltiplas variáveis. O Granite TTM tende a superar modelos estatísticos em cenários com grande diversidade de padrões, múltiplas influências exógenas e comportamento altamente variável. Porém, sua principal limitação está no **custo computacional**: ele demanda mais memória, mais processamento e tempo maior de inferência, o que pode ser um desafio em sistemas embarcados, SBCs simples ou ambientes com restrições energéticas.

O **SARIMA**, por outro lado, é extremamente leve. Seu processamento é baseado em operações matemáticas diretas sobre a série temporal, como diferenças, convoluções simples e combinações lineares. Isso torna sua execução rápida e previsível, mesmo em microcontroladores ou dispositivos de borda modestos. Além disso, o SARIMA é um modelo **explicável**: sabemos exatamente como cada termo influencia a previsão, o que é importante em projetos educacionais, industriais ou científicos, como é o caso do Rack Inteligente.

A estratégia híbrida adotada é simples e robusta:

* o Granite TTM realiza a previsão principal, explorando sua capacidade de capturar relações profundas;
* o SARIMA atua como **fallback**, garantindo previsões estáveis quando o modelo primário não entrega resultados aceitáveis, seja por limitações de hardware, instabilidade do modelo, falta de conectividade ou aumento inesperado do erro.

Esse mecanismo de fallback é fundamental em sistemas embarcados reais. Em aplicações práticas, modelos de IA podem falhar momentaneamente por falta de memória, travamento de processos, erros em pipelines de pré-processamento ou timeouts de inferência. Já o SARIMA, por ser um modelo determinístico e leve, continua operando mesmo em cenários adversos. É justamente essa confiabilidade que justifica sua adoção em nosso projeto.

Outro benefício é que, ao comparar a previsão dos dois modelos utilizando uma métrica clara como o MAE, podemos criar rotinas automáticas de seleção. Se o Granite TTM apresentar erro acima de um limiar predefinido, o sistema troca automaticamente para o SARIMA até que as condições se normalizem. Isso aumenta a robustez do sistema e demonstra, na prática, como soluções híbridas combinam o melhor dos dois mundos: desempenho avançado e estabilidade operacional.

---

A seguir apresento **o Capítulo 4**, explicando de maneira didática e matematicamente rigorosa o uso da métrica **MAE (Mean Absolute Error)** no projeto EmbarcaTech TIC-27 e sua importância para a seleção entre Granite TTM e SARIMA.

Quando quiser avançar, peça **“próximo”**.

---

## 4 — A Métrica MAE e seu Papel na Escolha entre Granite TTM e SARIMA

Para avaliar a qualidade das previsões tanto do Granite TTM quanto do SARIMA em nosso projeto, adotamos a métrica **MAE — Mean Absolute Error**, ou Erro Absoluto Médio. Entre as métricas disponíveis no campo de séries temporais, como RMSE, MAPE ou MSE, optamos pelo MAE por sua interpretação simples e direta, particularmente útil para um público leigo, mas sem perder sua relevância estatística.

O MAE mede, em média, quanto o modelo erra em termos absolutos, ou seja, o quanto a previsão se afasta do valor real sem considerar direção (acima ou abaixo). A fórmula matemática é:

\[
MAE = \frac{1}{n} \sum_{t=1}^{n} |y_t - \hat{y}_t|
\]

onde:

* \( y_t \) é o valor real observado no instante ( t ),
* \( \hat{y}_t \) é o valor previsto pelo modelo,
* \( |y_t - \hat{y}_t| \) é o erro absoluto,
* \( n \) é a quantidade total de previsões avaliadas.

Em termos simples, o MAE responde à pergunta:
**“Em média, quanto a previsão está errando?”**

Diferente do RMSE (erro quadrático médio), o MAE não amplifica erros grandes, o que o torna uma métrica mais equilibrada quando há poucos outliers. Ele também é matematicamente mais intuitivo, já que está na mesma unidade da variável prevista. Isso permite que técnicos, alunos e gestores compreendam rapidamente o desempenho do modelo.

No projeto EmbarcaTech TIC-27, o MAE desempenha um papel duplo:

1. **Avaliação contínua do desempenho dos modelos:**
   Monitoramos o MAE calculado para cada janela de previsão. Se o erro do Granite TTM estiver baixo e comportado, ele continua sendo o modelo principal.
2. **Acionamento automático do fallback (SARIMA):**
   O sistema define um limite de segurança ( MAE_{\text{max}} ).
   Se o Granite TTM ultrapassar esse limite em determinado ciclo, interpretamos que ele está em condição instável — seja por falta de recursos, dados incompletos ou comportamentos anômalos — e o SARIMA assume a previsão naquele momento.

Esse mecanismo cria um sistema adaptativo: em momentos de estabilidade ou boa conectividade, utilizamos um modelo moderno e poderoso; em momentos mais restritivos, utilizamos um modelo estatístico robusto e confiável. Em ambos os casos, o MAE serve como referência universal de qualidade.

Por ter uma definição matemática simples e uma interpretação prática intuitiva, o MAE é a ponte perfeita entre teoria estatística e aplicação real. No contexto do nosso projeto, essa métrica garante que o sistema tome decisões fundamentadas e consistentes ao alternar entre os modelos, tornando a previsão mais segura e confiável.

---

A seguir apresento **o Capítulo 5**, detalhando como o SARIMA opera dentro do pipeline do projeto EmbarcaTech TIC-27. O texto mantém clareza para leigos, mas preserva a profundidade técnica esperada no curso.

Peça **“próximo”** quando quiser continuar.

---

## 5 — Funcionamento Interno do SARIMA no Pipeline do Projeto EmbarcaTech TIC-27

No projeto EmbarcaTech TIC-27, o SARIMA atua como modelo secundário, mas sua integração ao pipeline de previsão é tão importante quanto a do modelo Granite TTM. O funcionamento do SARIMA envolve um fluxo bem definido de preparação, modelagem e inferência, operando de maneira determinística e eficiente, o que reforça sua utilidade como fallback.

O pipeline inicia na etapa de **obtenção da série temporal**. Os dados coletados — que podem ser medições de sensores, valores de carga elétrica, variáveis ambientais ou outros indicadores monitorados — são inicialmente normalizados e avaliados quanto a lacunas ou valores ausentes. O SARIMA não exige normalização tão rigorosa quanto modelos de IA, mas a consistência da série é fundamental para evitar instabilidades na diferenciação.

Em seguida, ocorre o processo de **pré-processamento**, onde avaliamos se a série apresenta tendência (crescimento ou queda prolongada) e se há padrões sazonais. Com base nisso, definimos as ordens de diferenciação ( d ) e ( D ). O processo de diferenciação é aplicado diretamente sobre a série utilizando os operadores descritos anteriormente, como \( (1 - L)^d \) para a parte não sazonal e \( (1 - L^s)^D \) para a parte sazonal. Após essa etapa, a série transformada se torna estacionária — requisito necessário para que o modelo SARIMA possa funcionar corretamente.

O próximo passo é a **identificação dos parâmetros** \( (p, d, q)(P, D, Q)_s \). Em nosso projeto, esse processo é parcialmente automatizado usando algoritmos como grid search ou critérios estatísticos, incluindo AIC (Akaike Information Criterion) e BIC (Bayesian Information Criterion). Esses critérios avaliam o equilíbrio entre ajuste e simplicidade do modelo. Em situações de fallback, buscamos parâmetros mais conservadores, evitando ordens muito altas para garantir tempo de execução mínimo.

Com os parâmetros definidos, entra em operação o **cálculo dos polinômios AR e MA**, tanto sazonais quanto não sazonais. Embora o usuário final veja o SARIMA como uma “caixa preta”, matematicamente ele está resolvendo equações lineares envolvendo convoluções entre coeficientes e dados históricos. Isso é feito com altíssima eficiência, seja em Python, C ou mesmo rodando em SBCs de baixo custo. Por ser linear, o SARIMA requer pouquíssima memória — o que o torna adequado aos ambientes embarcados do projeto.

A etapa final é a **geração da previsão**, onde o modelo reconstrói a série original após aplicar a inversão das diferenças acumuladas. Quando o sistema executa o Granite TTM e o SARIMA em paralelo, com o MAE monitorando ambos, o SARIMA produz previsões continuamente, mesmo que não estejam sendo utilizadas. Essa estratégia permite que, caso o Granite apresente aumento de erro ou falhas temporárias, o sistema troque para o SARIMA sem precisar esperar reconstrução ou reprocessamento da série.

Esse pipeline faz com que o SARIMA seja uma solução “sempre pronta” — simples, rápida, interpretável e confiável. É justamente essa previsibilidade que o transforma no fallback ideal em um ambiente de projeto educacional, prático e realista como o do EmbarcaTech.

---

A seguir apresento **o Capítulo 6**, explicando como o fallback automático entre Granite TTM e SARIMA é implementado no projeto EmbarcaTech TIC-27. O texto mantém clareza para iniciantes, mas com a precisão técnica necessária para quem desenvolve aplicações de previsão embarcada.

Quando quiser avançar, peça **“próximo”**.

---

## 6 — Implementação do Fallback Automático entre Granite TTM e SARIMA

A alternância entre Granite TTM e SARIMA no projeto EmbarcaTech TIC-27 é realizada de forma automática, baseada no monitoramento contínuo da qualidade das previsões. Esse mecanismo permite que o sistema opere de maneira resiliente, garantindo previsões mesmo quando o modelo principal enfrenta limitações computacionais, indisponibilidade temporária ou perda de acurácia. A ideia central é simples: o sistema coleta previsões dos dois modelos, calcula o MAE de cada um e decide qual deve ser utilizado naquele ciclo.

O processo tem início com a **execução paralela ou assíncrona dos modelos**. Em condições normais, o Granite TTM é executado com prioridade, aproveitando sua capacidade de detectar padrões complexos e multi-variados. Simultaneamente, o SARIMA permanece ativo em segundo plano, produzindo previsões continuamente. Essa estratégia garante que o SARIMA esteja sempre atualizado com os dados mais recentes, evitando atrasos caso seja necessário ativar o fallback.

Assim que ambos os modelos produzem suas previsões para o próximo período, o sistema calcula o **MAE individual**, comparando as previsões com os valores reais observados. O erro do Granite TTM é então comparado com um limiar pré-definido, chamado de **MAE(_{\text{max}})**. Esse valor não é arbitrário: ele é estimado durante a fase de testes, analisando o desempenho médio e o comportamento estatístico da série temporal. Quando o erro do Granite ultrapassa esse limiar, interpretamos que ele apresenta instabilidade — algo comum em modelos de aprendizado profundo quando há dados ruidosos, variações abruptas ou problemas momentâneos de processamento.

Nesse cenário, o sistema aciona o **mecanismo de fallback**, ativando o SARIMA como modelo oficial de previsão para aquele ciclo. Essa troca é imediata, porque o SARIMA já está operando continuamente em paralelo. Essa eficiência é essencial em aplicações embarcadas, onde atrasos são indesejáveis e uma transição suave garante confiabilidade no sistema final.

O retorno ao Granite TTM também ocorre de forma controlada. Em ciclos seguintes, o sistema verifica novamente o MAE do Granite e o compara com o MAE do SARIMA. Quando o Granite demonstra estabilidade — isto é, seu MAE retorna consistentemente a valores menores ou iguais ao limiar — o sistema restaura o Granite como modelo principal. Esse processo evita ciclos de oscilação entre modelos, garantindo estabilidade metodológica e previsibilidade operacional.

Essa lógica cria um sistema adaptativo, robusto e orientado a métricas. Ele combina os benefícios da inteligência artificial de ponta com a confiabilidade dos métodos estatísticos tradicionais. Em um contexto educacional e prático como o EmbarcaTech, esse design também demonstra aos estudantes como arquiteturas de previsão modernas devem ser construídas: com camadas redundantes, monitoramento contínuo e decisões orientadas por dados.

---

A seguir apresento **o Capítulo 7**, que demonstra de forma numérica e intuitiva como o SARIMA funciona na prática. O objetivo é transformar as fórmulas apresentadas anteriormente em algo concreto e acessível ao leitor leigo, sem perder o rigor técnico.

Quando quiser prosseguir, peça **“próximo”**.

---

## 7 — Exemplo Matemático e Intuitivo de Funcionamento do SARIMA

Para compreender como o SARIMA opera, vamos analisar um exemplo simplificado, mas completo. Suponha que nossa série temporal represente a **demanda diária de um sensor**, onde observamos um padrão que se repete a cada **7 dias** — uma sazonalidade semanal. Vamos considerar um modelo:

\[
SARIMA(1,1,1)(1,1,0)_7
\]

Esse modelo contém quatro ideias fundamentais:

* \(d = 1\): vamos remover tendência aplicando uma diferença (y_t - y_{t-1}).
* \(D = 1\): vamos remover a repetição semanal aplicando a diferença sazonal (y_t - y_{t-7}).
* \(p = 1\): o valor atual depende do valor imediatamente anterior.
* \(q = 1\): o erro atual depende do erro anterior.
* \(P = 1\): há dependência entre semanas consecutivas (padrão sazonal AR).

Vamos decompor o processo.

---

### 7.1. Etapa 1 — Diferenciação não sazonal

Se os valores observados de demanda diária forem:

\[
y_t = [12, 14, 15, 16, 17, 18, 20, 11, \dots]
\]

Aplicamos a diferença:

\[
\nabla y_t = y_t - y_{t-1}
\]

Por exemplo:

* \(14 - 12 = 2\)
* \(15 - 14 = 1\)
* \(16 - 15 = 1\)

Essa simples operação elimina tendências lineares — como crescimento contínuo.

---

### 7.2. Etapa 2 — Diferenciação sazonal

Agora aplicamos:

\[
\nabla_7 y_t = y_t - y_{t-7}
\]

Se sete dias antes o valor foi 13, e hoje o valor é 20:

\[
20 - 13 = 7
\]

Isso remove o ciclo semanal. O modelo passa a trabalhar com as diferenças entre semanas, e não com o valor bruto dos dias.

A combinação das duas diferenças é:

\[
\nabla_7 \nabla y_t = (y_t - y_{t-1}) - (y_{t-7} - y_{t-8})
\]

Assim, qualquer repetição semanal e qualquer tendência são eliminadas, deixando a série estacionária.

---

### 7.3. Etapa 3 — Aplicação dos componentes AR e MA

Com a série estacionária calculada, entram os componentes do SARIMA.

O termo **AR(1)** indica que o valor atual depende do valor transformado anterior:

\[
\text{AR}: \quad \phi_1 , x_{t-1}
\]

O termo **AR sazonal (1)** depende do valor defasado em 7 períodos:

\[
\text{AR sazonal}: \quad \Phi_1 , x_{t-7}
\]

O termo **MA(1)** depende do erro anterior:

\[
\text{MA}: \quad \theta_1 , \varepsilon_{t-1}
\]

O modelo completo na forma expandida é:

\[
x_t = \phi_1 x_{t-1} + \Phi_1 x_{t-7} + \theta_1 \varepsilon_{t-1} + \varepsilon_t
\]

Essa equação é extremamente eficiente de calcular: depende apenas dos últimos valores transformados e dos erros passados.

---

### 7.4. Etapa 4 — Reconstrução da série original

Após prever a série transformada ( x_t ), o modelo desfaz as diferenças:

1. Inverte a sazonal:
   \[
   y_t' = x_t + y_{t-7}
   \]
2. Depois inverte a diferença simples:
   \[
   y_t = y_t' + y_{t-1}
   \]

O resultado final é um valor previsto ( y_t ) no mesmo domínio e escala da série original.

---

### 7.5. Intuição para o leitor

Se quisermos entender sem matemática:

* Pegamos a série original.
* Removemos tendências e padrões semanais.
* Aprendemos como o sistema se comporta após essas remoções.
* Usamos esse comportamento para prever o próximo ponto.
* Devolvemos esse valor à escala original desfazendo as diferenças.

Esse mecanismo permite que o SARIMA capture padrões previsíveis mesmo quando as condições computacionais são limitadas — justificando seu papel de fallback no projeto EmbarcaTech TIC-27.

---

A seguir apresento **o Capítulo 8**, discutindo de forma clara e fundamentada as **vantagens**, **limitações** e os **motivos técnicos** que justificam a escolha do SARIMA como fallback no projeto EmbarcaTech TIC-27.

Quando quiser avançar, peça **“próximo”**.

---

## 8 — Vantagens, Limitações e Justificativas Técnicas para a Escolha do SARIMA no Projeto Rack Inteligênte

A seleção do SARIMA como fallback no projeto Rack Inteligente não é casual: ela se fundamenta em princípios de engenharia, desempenho estatístico e requisitos operacionais do ambiente embarcado. Embora o Granite TTM seja a peça central do sistema de previsão graças à sua capacidade de capturar padrões complexos, o SARIMA se destaca pela robustez, eficiência e previsibilidade. Este capítulo explica por que sua presença é indispensável.

### 8.1. Vantagens do SARIMA

A principal vantagem do SARIMA é sua **eficiência computacional**. Seus cálculos consistem em operações simples de diferença, multiplicações lineares e combinações com erros passados. Isso permite execução estável até em dispositivos modestos como SBCs, microservidores de borda e sistemas com restrições energéticas. Diferente de modelos de IA baseados em transformadores, o SARIMA não depende de GPUs, não requer dezenas de megabytes de memória e não precisa de lotes grandes de dados para inferência.

Outra vantagem importante é sua **explicabilidade**. Seus coeficientes AR e MA podem ser interpretados diretamente como forças de influência temporal, dando ao engenheiro ou aluno uma visão clara sobre como a série se comporta. Em projetos educacionais como o EmbarcaTech TIC-27, isso reforça a compreensão do processo estatístico por trás da previsão — algo que modelos “caixa-preta” não fornecem facilmente.

Além disso, o SARIMA possui notável **estabilidade diante de séries sazonais**. Enquanto modelos de IA precisam aprender a sazonalidade a partir dos dados, o SARIMA incorpora a sazonalidade explicitamente via operadores matemáticos. Isso o torna eficaz mesmo com conjuntos de dados mais curtos, típicos de sistemas embarcados em início de operação.

Por fim, o SARIMA é **determinístico**. Para uma mesma entrada, ele sempre produzirá o mesmo resultado. Isso é essencial em aplicações que exigem previsões repetíveis, auditáveis e livres de estocasticidade indesejada.

---

### 8.2. Limitações do SARIMA

Apesar de suas qualidades, o SARIMA possui limitações bem definidas que justificam o uso do Granite TTM como modelo principal. A primeira delas é a incapacidade de lidar com **não linearidades complexas**. Séries temporais que apresentam eventos abruptos, mudanças estruturais ou padrões condicionais influenciados por múltiplas variáveis sofrem com a linearidade inerente ao SARIMA.

Outra limitação significativa é a **dependência de estacionaridade**. O SARIMA funciona bem quando a série temporal, após diferenciação, se torna estacionária. Contudo, algumas séries reais apresentam variações tão intensas que nem múltiplas diferenças conseguem estabilizá-las adequadamente.

Além disso, o SARIMA não é ideal para lidar com **variáveis exógenas** (influenciadores externos), a menos que seja utilizado em variantes como SARIMAX. Em contraste, modelos como o Granite TTM naturalmente integram múltiplas variáveis e capturam interações complexas entre elas.

Por fim, enquanto o Granite TTM aprende representações abstratas e profundas de longo prazo, o SARIMA depende fortemente dos padrões mais imediatos. Isso o torna menos adequado para prever eventos raros, mudanças de regime ou tendências emergentes.

---

### 8.3. Por que o SARIMA foi escolhido como fallback no EmbarcaTech TIC-27

No contexto do projeto EmbarcaTech TIC-27, buscamos um equilíbrio entre inovação, robustez e segurança operacional. O Granite TTM representa a sofisticação e a capacidade analítica de modelos modernos de IA. Porém, como qualquer modelo avançado, ele está sujeito a limitações práticas em ambientes embarcados ou restritos: tempo de processamento, falta de memória, instabilidade temporária ou falhas de execução.

É nesse ponto que o SARIMA se torna indispensável. Ele entrega algumas características fundamentais para um sistema de previsão confiável:

* **Funciona mesmo sob forte restrição computacional**, garantindo que o sistema nunca fique sem previsões.
* **Possui uma base matemática sólida**, servindo de referência comparativa para o Granite TTM.
* **Permite decisões rápidas**, sem latência significativa.
* **Opera de forma contínua em paralelo**, possibilitando troca imediata quando o MAE dispara.
* **Complementa o modelo principal**, cobrindo justamente os cenários onde modelos de IA tendem a falhar.

Do ponto de vista pedagógico, ter um fallback estatístico também reforça aos estudantes do TIC-27 a importância de arquiteturas híbridas e resilientes — um conceito amplamente utilizado na indústria de previsão, finanças, logística e automação.

---

A seguir apresento **o Capítulo 9**, encerrando o artigo com uma síntese clara sobre o papel do SARIMA, do Granite TTM e da métrica MAE no projeto EmbarcaTech TIC-27.

Se quiser, após esta conclusão posso gerar o **SEO completo** (título, metadescrição, palavra-chave foco e lista de palavras-chave separadas por vírgula).

---

### 9 — Conclusão Geral e Integração Conceitual

Ao longo deste artigo, mostramos como o modelo **SARIMA** desempenha um papel essencial dentro da arquitetura de previsão adotada no projeto de conclusão do EmbarcaTech TIC-27, servindo como pilar de robustez e estabilidade. Embora o **Granite TTM** represente o que há de mais moderno em termos de modelagem de séries temporais — com sua capacidade de capturar relações profundas, multivariadas e altamente não lineares — ele também carrega consigo limitações naturais em ambientes embarcados, como o uso intensivo de recursos computacionais e sensibilidade a variações abruptas de dados.

Nesse contexto, o SARIMA assume a responsabilidade de garantir previsões confiáveis mesmo em condições adversas. Sua base matemática sólida, seu comportamento determinístico e sua eficiência operacional permitem que ele funcione como um fallback perfeito, sempre preparado para assumir o controle quando o Granite TTM se desvia do desempenho esperado. Essa integração cria uma arquitetura híbrida onde inovação e previsibilidade coexistem, oferecendo ao sistema tanto inteligência avançada quanto estabilidade estatística.

A métrica **MAE (Mean Absolute Error)** cumpre papel central como ponte entre esses dois mundos. Sua simplicidade de interpretação e sua capacidade de traduzir eficiência preditiva em valores concretos possibilitam o monitoramento contínuo da performance de ambos os modelos. Quando o MAE do Granite ultrapassa o limiar definido, o sistema comuta automaticamente para o SARIMA, retomando para o Granite apenas quando sua estabilidade é recuperada. Dessa forma, a métrica não é apenas uma ferramenta de avaliação, mas um mecanismo de tomada de decisão.

O resultado dessa combinação é um pipeline resiliente, moderno e pedagogicamente valioso. Ele demonstra que bons projetos não dependem apenas de tecnologias avançadas, mas sim de arquiteturas bem pensadas, com camadas redundantes e mecanismos claros de fallback. Essa visão, aplicada no projeto Rack Inteligente, modela sistemas reais e prepara tanto o ambiente embarcado quanto o estudante para os desafios técnicos do mercado. Assim, o SARIMA não é apenas um suporte ao Granite TTM — ele é parte fundamental da inteligência total do sistema.

---
