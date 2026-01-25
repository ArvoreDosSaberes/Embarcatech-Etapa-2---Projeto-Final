---
title: "Rack Inteligente: Sistema AIoT de Gerenciamento e Segurança Ambiental para Racks em Infraestruturas de Pequeno Porte"
authors:
  - "Carlos Delfino Carvalho Pinheiro"
summary: "Solução AIoT focada em monitorar ambiente e controlar o acesso de racks compactos, integrando sensores, atuadores e IA generativa. - Relatório Final"
language: "pt-BR"
date: "2025-11-06"
tags:
  - "EmbarcaTech"
  - "AIoT"
  - "IoT"
  - "Segurança"
  - "Monitoramento"
  - "Infraestrutura"
  - "Rack Inteligente"
  - "MQTT"
  - "Controle Ambiental"
  - "Relatório Final"

abnt:
  institution: "Instituto Federal de Educação, Ciência e Tecnologia"
  campus: "Campus Fortaleza"
  course: "Embarcatech - Etapa 2 - Residência"
  discipline: "Projeto Integrador"
  nature: "Trabalho de Conclusão de Curso"
  natureDetails: "apresentado ao Instituto Federal como requisito parcial do projeto Embarcatech - Etapa 2 - Residência."
  studentId: "202510110980368"
  city: "Fortaleza"
  state: "CE"
  year: "2026"
---
# Rack Inteligente AIoT

## Sistema de gerenciamento e segurança ambiental para racks em infraestruturas de pequeno porte, com apoio de IA generativa

## 1. Introdução

O **Rack Inteligente AIoT** foi desenvolvido para atender a uma necessidade comum em operações de TI de pequeno e médio porte: o gerenciamento de **múltiplos racks compactos**, frequentemente instalados em ambientes com pouca infraestrutura (salas pequenas, armários técnicos e pontos remotos). Nesse contexto, é comum haver:

- **Risco ambiental**, como temperatura elevada e umidade fora do recomendado.
- **Risco físico**, como acesso indevido ao rack.
- **Dificuldade de gestão remota**, especialmente quando há vários pontos distribuídos.

Com o apoio de IA, o sistema passa a operar de forma contínua (24x7), registrando histórico e apoiando decisões de forma cada vez mais consistente a partir dos dados coletados.

## 2. Objetivos

O objetivo do projeto é reduzir falhas e indisponibilidades em infraestruturas de rede de pequeno porte por meio de:

- Monitoramento ambiental (temperatura e umidade).
- Segurança física (estado da porta e eventos associados).
- Alertas e comandos remotos, utilizando MQTT.

Como resultado esperado, busca-se diminuir a incidência de ocorrências relacionadas ao ambiente e, consequentemente, reduzir chamados e custos de manutenção corretiva.

## 3. Justificativa

Durante **35 anos de experiência em suporte e implantação de redes de computadores**, foi observada uma carência de soluções voltadas a **pequenos racks** que unam segurança física e gestão ambiental em um mesmo sistema. Em geral, as tecnologias existentes são direcionadas a **data centers de grande porte**, deixando lacunas no mercado de **infraestruturas menores**, que muitas vezes operam em condições ambientais inadequadas ou vulneráveis a acessos indevidos. Além disso, é comum que as soluções disponíveis tenham custo incompatível com o porte do ambiente.

O **Rack Inteligente AIoT** surge como resposta a essa necessidade, oferecendo um sistema **autônomo, modular e acessível**, capaz de:

- Monitorar e controlar o ambiente interno do rack (temperatura e umidade).
- Gerenciar o acesso físico com autenticação e travamento automático.
- Enviar alertas e relatórios via rede para administração remota.

Essa abordagem é especialmente útil para organizações que precisam garantir **continuidade operacional** e **segurança de dados** com orçamento limitado e infraestrutura simplificada.

## 4. Problemática

Complementando a justificativa, a demanda por monitoramento de racks de pequeno porte é crescente. Atualmente, praticamente toda empresa depende de uma infraestrutura de rede (mesmo que enxuta), frequentemente instalada em pequenos racks. Sem monitoramento, o risco de falha aumenta por fatores como:

- Temperatura elevada e ventilação insuficiente.
- Umidade em níveis inadequados.
- Acesso indevido ou não rastreado.

O projeto busca reduzir esses riscos ao integrar sensores, atuadores e telemetria, combinando automação local com gestão remota.

## 5. Arquitetura do sistema (hardware + firmware + AIoT)

Diagrama representativo do projeto:

![Diagrama Representativo do Projeto](./imagens/rack_inteligente.png)

Diagrama de blocos do projeto:

![Diagrama de Blocos do Projeto](./imagens/Hardware_do_Rack_Inteligente.png)

## 6. Desenvolvimento do sistema

### 6.1. Estratégia de concorrência: uma task por responsabilidade

Foi adotada a estratégia de **uma task por responsabilidade**. Essa decisão facilita:

- **Diagnóstico** (isolamento de falhas e gargalos).
- **Manutenção** (alterações localizadas).
- **Evolução** (troca de drivers e protocolos com menor impacto).

Um exemplo direto é a publicação via MQTT: existem tasks dedicadas por parâmetro monitorado. Isso permite, se necessário, substituir apenas a camada de transporte (por exemplo, trocar MQTT por outro protocolo) **sem interferir** na coleta, validação e cálculo dos parâmetros ambientais.

### 6.2. Entrada do teclado e controle do menu

As tasks relacionadas ao teclado utilizam **notificações (task notify)** com **flags** para representar as teclas pressionadas. Há duas responsabilidades principais:

- **Task de leitura de GPIOs** do teclado.
- **Task de processamento** das teclas e controle do menu.

O menu é estruturado como uma **máquina de estados**. Embora não esteja totalmente finalizado, ele demonstra uma abordagem orientada a eventos adequada para sistemas embarcados.

Apesar de o algoritmo de leitura das teclas estar funcional, ainda não foram implementadas as rotinas completas de **troca de senha** e entrada do **código do rack** via menu. No estágio atual, esses parâmetros precisam ser definidos no momento da gravação do firmware.

### 6.3. Processamento de comandos: filas (queues) e ACK

Para comandos recebidos (por exemplo, **abrir porta**, **acionar alarme** e **acionar ventilação**), foi adotada a abordagem com **queues**. Com isso:

- Os comandos são enfileirados em ordem **FIFO**.
- A execução ocorre de forma previsível, reduzindo risco de concorrência.
- Ao final, é gerado um **ACK**, confirmando que o comando foi recebido e processado.

### 6.4. Sensores e comunicação com MQTT

Para sensores (movimento, temperatura e umidade), o firmware notifica componentes responsáveis por publicar telemetria. A escolha por múltiplas classes/módulos (mesmo quando seria possível centralizar a lógica) foi intencional para reforçar:

- Modularização.
- Separação de responsabilidades.
- Organização do sistema em um formato mais próximo de um produto evolutivo.

No caso do sensor de temperatura e umidade, foi adotado o padrão de projeto **Gatekeeper (Guardião)**: uma tarefa é responsável por se comunicar com o dispositivo e obter os dados, repassando cada medição para a tarefa responsável por tratá-la e publicá-la.

No caso do barramento I2C, foi utilizado o padrão de projeto **Proxy**, permitindo centralizar e gerenciar o acesso ao barramento em uma única lógica de controle, garantindo **atomicidade** na comunicação: iniciar a transação (obter o barramento), comunicar e finalizar, liberando o barramento para outras threads.

## 7. Hardware

O hardware foi desenvolvido conforme o pré-projeto. O diagrama de blocos abaixo resume a estrutura e o funcionamento:

![Esquema de Blocos do Hardware](./imagens/Hardware_do_Rack_Inteligente.png)

A imagem a seguir mostra o protótipo montado. Nela:

- Adaptador e **servo motor** (acionamento da porta).
- Placa de distribuição **I2C**.
- Sensor de movimento (**MPU6050**).
- Sensor de temperatura e umidade (**AHT10**).
- Teclado.
- A **BitDogLab** ao centro, já integrando LEDs RGB e display OLED.

![Circuito do Rack](./imagens/circuito_prototipo_montado.jpeg)

### 7.1. Esquemático das conexões

No esquemático, o barramento I2C usado pelo sensor de movimento (MPU6050) e pelo sensor de temperatura e umidade (AHT10) está conectado aos pinos GPIO0 e GPIO1 (canal I2C0), externalizado pelo conector indicado.

O PWM para controle do servo motor está no pino GPIO2, externalizado pelo conector identificado como I2C1 (neste caso, apenas como conector físico, sem relação com I2C).

O display OLED utiliza GPIO14 e GPIO15 no canal I2C1, não conflitando com o I2C0.

Os LEDs RGB estão conectados nos pinos GPIO12, GPIO13 e GPIO15.

Os buzzers estão conectados aos pinos GPIO10 e GPIO27, controlados por PWM.

Na BitDogLab, os botões são utilizados como entradas digitais:

- **Botão A**: GPIO5 (entrada com pull-up, lógica invertida).
- **Botão B**: GPIO6 (entrada com pull-up, lógica invertida).

O ventilador foi representado no protótipo pelo LED verde. O LED azul pisca indicando funcionamento do firmware: durante o boot rapidamente e, em operação normal, alterna o estado a cada 1 segundo.

O estado de porta aberta/fechada é simulado pelo **botão A**: quando pressionado, considera-se porta aberta; quando solto, porta fechada.

O **botão B** desativa o alarme até a próxima anomalia detectada.

![Esquemático das Conexões](./imagens/Esquematico_do_Projeto.png)

## 8. Camada IoT (MQTT)

Foi adotado o protocolo **MQTT** para comunicação entre o firmware e o dashboard por ser leve e adequado a telemetria e comandos em tempo real.

O broker foi implantado em um **servidor VPS**, com:

- Regras de **firewall** para reduzir a superfície de ataque.
- Autenticação por **usuário e senha**.

Essa base atende às necessidades de segurança operacional no cenário do projeto.

## 9. AIoT (IA aplicada ao sistema)

### 9.1. Integração com LLM via OpenWebUI/Ollama

Foi adotado o **OpenWebUI** como interface de acoplamento entre o dashboard e a engine de LLMs (via **Ollama**). Essa estratégia viabiliza requisições em formato compatível com a biblioteca OpenAI, facilitando a troca de engine de IA generativa sem mudanças grandes no código (em geral, basta ajustar URL e chave de API).

### 9.2. Tool Calling para decisão e atuação

Foram usados recursos de **Tool Calling** para apoiar decisões relacionadas a:

- Temperaturas em níveis críticos.
- Acionamento de ventilação.
- Disparo de alarmes.

O modelo utilizado como orquestrador de ferramentas é o **Granite 4** (3 bilhões de parâmetros).

### 9.3. Previsão de temperatura e umidade (TTM)

Foi adicionado um mecanismo de previsão com o **Granite TTM (Tiny Time Series Model)**, utilizando dados históricos para estimar valores futuros de temperatura e umidade. Isso auxilia na antecipação de situações de risco (por exemplo, tendência de aquecimento contínuo).

## 10. Treinamento e parametrização da IA

- O prompt principal para o comportamento da IA generativa está na pasta `prompts/`.
- As variáveis de execução do dashboard e parâmetros de treinamento/uso do Granite TTM são configuradas via arquivo `.env` na raiz do projeto.

### 10.1. Broker MQTT

O broker MQTT foi implementado com o **Mosquitto** em um servidor VPS, no endereço `mqtt://mqtt.rapport.tec.br`. Por questões de segurança, foi adotado controle de acesso por usuário e senha.

### 10.2. Dashboard (Python)

O dashboard foi desenvolvido em **Python** para facilitar a integração com a LLM e com o TTM (modelos Granite da IBM) e acelerar os ciclos de teste.

A seguir, a janela principal:

![Dashboard Principal](./imagens/dashboard_rack_inteligente.png)

Componentes principais da interface:

- **Lista de racks (lado esquerdo)**: alimentada dinamicamente conforme as telemetrias são publicadas no MQTT. O nome do rack pisca quando algum parâmetro é atualizado.
- **Painel de telemetria (lado direito)**: temperatura e umidade. O traço contínuo representa o histórico coletado; o traço descontínuo representa a previsão baseada no histórico.
- **Controles manuais**: botões para abrir porta e acionar ventilação, além de sinalização do estado do alarme.

Ao rolar o conteúdo, é exibido o mapa de localização do rack, com dados obtidos pelo parâmetro de GPS enviado pelo Rack Inteligente:

![Dashboard Mapa](./imagens/dashboard_rack_inteligente_mapa.png)

No rodapé, são exibidas as **reflexões e decisões** produzidas pela IA generativa a partir dos parâmetros de telemetria.

## 11. Vídeo de apresentação do projeto

[https://youtu.be/8Clld03a714](https://youtu.be/8Clld03a714 "Vídeo de apresentação do projeto")

## 12. Conclusão

O projeto permanece em evolução. Ainda há itens em desenvolvimento, como a finalização do menu e a inclusão de rotinas completas para entrada de senha e código do rack via interface local. Mesmo com limitações de bancada e com a necessidade de validações adicionais em alguns componentes, foi possível testar o firmware e comprovar o funcionamento do sistema integrado.

O uso de séries temporais para previsão tende a ser mais efetivo após um período maior de coleta contínua. Ainda assim, a implementação e experimentação do TTM representaram um aprendizado relevante e abrem espaço para aplicações futuras.

## 13. Referências

- https://arxiv.org/pdf/2401.03955
- https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2
- https://research.ibm.com/publications/tiny-time-mixers-ttms-fast-pre-trained-models-for-enhanced-zerofew-shot-forecasting-of-multivariate-time-series--1
- https://towardsdatascience.com/tiny-time-mixers-ttm-a-powerful-zero-shot-forecasting-model-by-ibm-576b0e0af583/
- https://groq.com/blog/introducing-llama-3-groq-tool-use-models
- https://huggingface.co/Groq/Llama-3-Groq-8B-Tool-Use

## 14. Apêndices

Link para o projeto no GitHub (workspace com submódulos):

[https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final](https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final "Link direto para o repositório")

Para clonar o repositório:

```
git clone --recurse-submodules https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final.git
```
