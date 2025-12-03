
## Seção 1 — Introdução à Detecção de Anomalias

A detecção de anomalias é uma técnica fundamental em sistemas inteligentes, especialmente em aplicações embarcadas, onde a capacidade de identificar comportamentos inesperados pode evitar falhas catastróficas, reduzir custos de manutenção e aumentar a confiabilidade de equipamentos. Em termos simples, uma anomalia é qualquer comportamento que se desvia significativamente do padrão habitual — seja uma vibração fora do normal em um transformador, um ruído inesperado em um motor, um pacote estranho em uma rede, ou mesmo uma leitura de sensor fora do perfil típico em um microcontrolador.

Existem três grandes abordagens estatísticas e de aprendizado de máquina amplamente usadas: **Isolation Forest**, **One-Class SVM** e **PCA (Principal Component Analysis)** aplicado para detecção de anomalias. Cada uma utiliza uma estratégia diferente no processo de modelagem, o que é particularmente útil quando queremos embarcar parte do processamento em microcontroladores ou realizar inferência em sistemas híbridos MCU+edge AI.

No contexto embarcado, a detecção de anomalias precisa de métodos eficientes, com baixo custo computacional e que funcionem bem mesmo quando há poucos dados rotulados. Por isso, os algoritmos apresentados neste artigo são especialmente adequados para aplicações como: predição de falhas, filtragem inteligente de dados, diagnóstico vibroacústico, análise de corrente, segurança cibernética embarcada e controle inteligente em malha fechada.

---

## Seção 3 — One-Class SVM

O One-Class SVM é um método clássico e robusto para detecção de anomalias baseado em fronteiras de decisão. Enquanto um SVM convencional separa duas classes distintas, o One-Class SVM tenta aprender apenas a região onde os dados “normais” se concentram. A ideia central é encontrar uma superfície (hiperplano ou hiperfronteira) que envolva a maior parte do conjunto de dados, deixando pontos distantes dessa região como anômalos.

Matematicamente, ele busca maximizar a margem entre os dados e a origem no espaço transformado pelo kernel. Isso significa que ele depende fortemente da função kernel — normalmente o **RBF (Radial Basis Function)** — para projetar os dados em um espaço onde as fronteiras possam ser bem delimitadas. Essa característica o torna muito poderoso, porém mais custoso computacionalmente que o Isolation Forest, especialmente na fase de inferência, já que envolve cálculos exponenciais e somas ponderadas sobre vetores de suporte.

Em aplicações embarcadas, o One-Class SVM é mais adequado quando:

* o conjunto de dados normal é bem definido;
* há pouco ruído;
* a anomalia possui características sutis;
* os dados têm baixa dimensionalidade.

Treinar o modelo em um computador e exportar um SVM simplificado para microcontroladores é viável, desde que a quantidade de vetores de suporte seja pequena.

---

## **Exemplo em Python — Treinamento e Teste**

```python
from sklearn.svm import OneClassSVM
import numpy as np

# Dados normais
rng = np.random.RandomState(10)
normal = 0.2 * rng.randn(200, 2)

# Anomalias
anom = rng.uniform(low=-3, high=3, size=(10, 2))

# Treina o modelo
model = OneClassSVM(kernel="rbf", gamma=0.1, nu=0.05)
model.fit(normal)

# Testa
test = np.vstack([normal[:5], anom[:2]])
pred = model.predict(test)

print(pred)  # -1 indica anomalia
```

---

## **Exemplo de Inferência Simplificada em C (Kernel RBF)**

Este é um exemplo reduzido da fórmula RBF usada na inferência:

\[
K(x, v_i) = e^{-\gamma |x - v_i|^2}
\]

Onde cada (v_i) é um vetor de suporte.

A soma ponderada dos kernels determina a decisão final.

```c
#include <math.h>

#define GAMMA 0.1f

// Vetor de suporte simplificado (exemplo)
float sv[][2] = {
    {0.1f,  0.2f},
    {-0.1f, 0.0f},
    {0.05f, 0.1f}
};

// Coeficientes alpha do SVM
float alpha[] = {0.5f, -0.3f, 0.8f};

float rbf(float x0, float x1, float v0, float v1) {
    float dx = x0 - v0;
    float dy = x1 - v1;
    float dist2 = dx*dx + dy*dy;
    return expf(-GAMMA * dist2);
}

int oneclass_svm_infer(float x0, float x1) {
    float sum = 0.0f;

    for (int i = 0; i < 3; i++) {
        sum += alpha[i] * rbf(x0, x1, sv[i][0], sv[i][1]);
    }

    return (sum > 0.0f) ? 1 : -1; // -1 = anomalia
}
```

Esse tipo de código é viável em um Cortex-M4F ou M7 com FPU; para microcontroladores mais modestos, é possível pré-computar tabelas ou usar aproximações de exponencial (como fast exp).

---
##  4 — PCA Embarcado para Detecção de Anomalias

A Análise de Componentes Principais (PCA, Principal Component Analysis) é uma técnica matemática poderosa para redução de dimensionalidade e detecção de anomalias. Diferentemente do Isolation Forest e do One-Class SVM, o PCA não cria fronteiras ou árvores, mas transforma os dados originais em novas direções (componentes principais) que retêm a maior variância possível. Isso permite identificar padrões fundamentais e detectar pontos que se desviam significativamente desse padrão.

A ideia básica é decompor os dados em uma combinação linear de componentes ortogonais. Para detectar anomalias, observamos o **erro de reconstrução**: quando projetamos um ponto nos componentes principais e tentamos reconstruí-lo, pontos normais tendem a ter um erro pequeno, enquanto pontos anômalos produzem erros muito maiores. Essa abordagem é extremamente eficiente para sistemas embarcados porque permite pré-calcular toda a estrutura no computador e embarcar apenas duas operações: multiplicação de matrizes e cálculo de erro.

Matematicamente, se ( x ) é o vetor original e ( W ) é a matriz dos autovetores (componentes), o processo é:

1. **Projeção no espaço PCA:**

\[
z = W^T (x - \mu)
\]

2. **Reconstrução aproximada:**

\[
\hat{x} = Wz + \mu
]

3. **Erro de reconstrução:**

\[
e = | x - \hat{x} |^2
\]

Se o erro (e) ultrapassar um limiar definido, classificamos como anomalia.

Essa abordagem é usada em vibração, acústica, qualidade de energia e em sistemas industriais embarcados com pouco poder computacional, pois envolve apenas multiplicações e somas — operações extremamente eficientes em microcontroladores.

---

## **Exemplo em Python — PCA para Identificar Anomalias**

```python
import numpy as np
from sklearn.decomposition import PCA

# Dados normais
rng = np.random.RandomState(1)
normal = rng.normal(0, 0.3, size=(300, 3))

# Anomalias
anom = rng.uniform(-3, 3, size=(10, 3))
dados = np.vstack([normal, anom])

# PCA com 2 componentes
pca = PCA(n_components=2)
pca.fit(normal)

# Função de erro de reconstrução
def reconstruction_error(x):
    z = pca.transform([x])
    x_hat = pca.inverse_transform(z)
    return np.linalg.norm(x - x_hat)

# Testando
for i in range(5):
    print("Erro:", reconstruction_error(dados[i]))
```

Você perceberá que os erros das amostras anômalas são muito maiores.

---

## **Exemplo Embarcado (C) — Inferência PCA Simplificada**

Os autovetores e a média já foram calculados no PC. Agora, usamos apenas matrizes pequenas no microcontrolador:

```c
#include <math.h>

// Matriz de autovetores (2 componentes, 3 dimensões)
float W[2][3] = {
    {0.58f, 0.57f, 0.58f},
    {-0.72f, 0.01f, 0.69f}
};

// Média dos dados (calculada previamente)
float mu[3] = {0.02f, -0.01f, 0.03f};

float reconstruction_error(float x[3]) {
    float x_centered[3];
    for (int i = 0; i < 3; i++)
        x_centered[i] = x[i] - mu[i];

    // Projeção
    float z[2] = {0};
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 3; j++)
            z[i] += W[i][j] * x_centered[j];

    // Reconstrução
    float x_hat[3] = {0};
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 2; j++)
            x_hat[i] += W[j][i] * z[j];

    for (int i = 0; i < 3; i++)
        x_hat[i] += mu[i];

    // Erro
    float e = 0;
    for (int i = 0; i < 3; i++) {
        float d = x[i] - x_hat[i];
        e += d * d;
    }

    return e;
}
```

Essa função pode ser usada diretamente em qualquer microcontrolador, bastando definir um limiar adequado de erro para classificar anomalias.

---
## 5 — Comparação Entre Métodos e Aplicações Práticas

A escolha entre Isolation Forest, One-Class SVM e PCA depende profundamente do tipo de aplicação, da quantidade de dados disponíveis, da complexidade do sinal e principalmente das restrições computacionais típicas de sistemas embarcados. Cada método tem pontos fortes e limitações, e compreender essas nuances permite projetar sistemas mais eficientes e robustos.

O Isolation Forest é, em geral, o mais eficiente para dados de alta dimensionalidade e cenários onde as anomalias tendem a ser valores extremos ou isolados. Sua natureza baseada em árvores o torna leve na etapa de inferência, já que consiste em uma sequência de comparações simples — ideal em MCUs como RP2040, ESP32-C3/S3 e Cortex-M. Entretanto, sua interpretação pode ser menos intuitiva do que a de modelos lineares ou baseados em geometria. Já o One-Class SVM apresenta excelente desempenho em situações onde os dados normais são bem estruturados e a anomalia é sutil, porém o custo computacional do kernel RBF e a dependência da quantidade de vetores de suporte tornam a inferência mais cara. É um candidato natural quando a inferência ocorre em edge devices mais robustos ou quando se usa aceleradores como o NPU do ESP32-P4, HPM6xxx, STM32N6 ou NPUs externos.

O PCA se destaca em contextos embarcados devido à sua simplicidade computacional e capacidade de reduzir drasticamente a dimensionalidade dos dados, mantendo a essência do comportamento normal. Em aplicações industriais, como vibração e acústica, onde há forte redundância entre sinais, o PCA é extremamente eficaz em capturar esse padrão e detectar desvios, principalmente quando se usa o erro de reconstrução como métrica. Seu treinamento é mais pesado, mas a inferência exige apenas multiplicações de matrizes, algo trivial para um Cortex-M7, M33, ESP32-S3 ou mesmo um RP2040.

### **Aplicações práticas em sistemas embarcados**

* **Manutenção preditiva de motores e transformadores**
  PCA e Isolation Forest são largamente utilizados para vibrações e ruídos mecânicos. PCA detecta sutis alterações espectrais, enquanto Isolation Forest identifica comportamentos fora do padrão global.

* **Segurança cibernética embarcada**
  Em gateways IoT e sistemas críticos, One-Class SVM é eficiente para detectar tráfego malicioso que difere levemente do comportamento normal.

* **Sensores de ambiente (temperatura, pressão, corrente, aceleração)**
  Isolation Forest e PCA executam facilmente em MCUs com pouco recurso, monitorando continuamente leituras de sensores.

* **Detecção de falhas em robôs, veículos autônomos e drones**
  PCA pode identificar alterações no perfil de movimento; Isolation Forest detecta leituras inesperadas de IMUs, LiDARs ou encoders.

* **Sistemas embarcados de análise de energia elétrica**
  PCA é excelente para detectar distorções e harmônicos incomuns; SVM é útil quando há pouca variabilidade na rede elétrica monitorada.

---

## 6 — Conclusão e Boas Práticas de Implementação em Sistemas Embarcados

A detecção de anomalias é uma peça central para sistemas embarcados modernos, especialmente aqueles voltados à manutenção preditiva, diagnóstico inteligente, proteção de equipamentos e segurança operacional. Isolation Forest, One-Class SVM e PCA representam três abordagens complementares que oferecem um conjunto sólido de ferramentas para identificar comportamentos inesperados em tempo real.

Quando bem aplicados, esses algoritmos permitem antecipar falhas mecânicas, detectar desvios elétricos, capturar padrões incomuns em vibração/acústica, identificar leituras suspeitas de sensores ou mesmo reforçar a segurança cibernética em ambientes IoT/IIoT — tudo isso com execução eficiente em microcontroladores acessíveis.

Do ponto de vista prático, algumas recomendações ajudam a garantir que o sistema funcione de maneira consistente:

A primeira boa prática é sempre realizar o treinamento dos modelos fora do microcontrolador, preferencialmente em uma estação de trabalho ou servidor dedicado. Os dados coletados devem ser limpos, normalizados e analisados para garantir que representam adequadamente o “comportamento normal” do sistema. Após o treinamento, os parâmetros essenciais — árvores, vetores de suporte ou autovetores — devem ser exportados para o firmware em representações compactas.

Outra recomendação importante é monitorar os limites numéricos. Em MCUs, operações com ponto flutuante podem gerar erros acumulados; por isso, quando possível, considere **quantização**, **uso de ponto fixo**, ou **tabelas de aproximação** para funções como exponencial (no caso do SVM). Em sistemas de baixa potência, evitar funções matemáticas custosas ajuda a manter a latência e o consumo energético sob controle.

A terceira prática consiste em calibrar limiares de detecção dinamicamente. Em vez de usar um limiar fixo, o sistema pode calcular estatísticas ao longo do tempo — como média móvel ou desvio padrão — para adaptar-se a mudanças naturais no ambiente. A detecção de anomalias fica mais robusta em ambientes ruidosos ou sujeitos a variações não controladas.

Por fim, é essencial validar o sistema com dados reais do ambiente final. Testes em bancada podem não refletir ruídos, variações térmicas, jitter dos sensores ou interferências eletromagnéticas típicas de campo. O processo de testes deve incluir cenários-limite para garantir que o sistema responde não apenas ao “anomalo ideal”, mas também a desvios graduais e quase imperceptíveis — aqueles que, na prática, causam a maior parte das falhas industriais.

---

