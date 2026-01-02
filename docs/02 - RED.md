---
title: "Rack Inteligente: Sistema AIoT de Gerenciamento e Segurança Ambiental para Racks em Infraestruturas de Pequeno Porte"
authors:
  - "Carlos Delfino Carvalho Pinheiro"
summary: "Solução AIoT focada em monitorar ambiente e controlar o acesso de racks compactos, integrando sensores, atuadores e IA generativa. - Relatório de Evidência de Desenvolvimento"
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
  year: "2025"
---
# Relatório de Evidência de Desenvolvimento (RED)

## 1. Visão geral do projeto

Este projeto implementa um **Rack Inteligente** voltado para **monitoramento ambiental** e **segurança física** em infraestruturas de pequeno porte. A solução integra:

- **Firmware embarcado** (C/C++ com FreeRTOS), responsável por leitura de sensores, atuação e comunicação.
- **Camada IoT** via **MQTT**, para transporte de telemetria e comandos.
- **Dashboard** (Python), para visualização, controle manual e integração com recursos de IA.
- **AIoT**, com uso de **LLM** e **modelos de séries temporais** para apoiar decisões e previsões.

A ideia principal é separar bem as responsabilidades para facilitar manutenção, testes e evolução do sistema.

## 2. Estado atual (marcos e estabilidade)

O projeto está em **estágio avançado**, com os marcos principais **praticamente entregues**. Nesta etapa eu estou focado em:

- **Revisão geral do código** (refatorações pontuais e padronização).
- **Correção de bugs menores**.
- **Reatividade do sistema**, onde testo resposta a comandos e simulação de múltiplos Racks.
- **Testes de resiliência e estabilidade** (execução contínua por longos períodos).

Evidências observadas até aqui:

- **Firmware**: executando por dias com boa estabilidade.
- **Dashboard**: responde bem ao monitoramento simultâneo de **dezenas a centenas de racks**.
- **Broker MQTT (Mosquitto)** em VPS: serviço estável há **mais de 3 meses**, sem incidentes relevantes.

## 3. Arquitetura do firmware (C/C++ com FreeRTOS)

### 3.1. Estratégia de concorrência: uma task por responsabilidade

Foi adotada a tática de **uma task por responsabilidade**. Essa decisão melhora:

- **Diagnóstico** (fica mais fácil isolar gargalos e falhas).
- **Manutenção** (alterações ficam localizadas).
- **Evolução** (troca de protocolos ou drivers sem reescrever o sistema inteiro).

Um exemplo importante: para publicação de dados via MQTT, há tasks dedicadas por parâmetro monitorado. Isso permite, se necessário, substituir apenas a parte de transporte (por exemplo, trocar MQTT por outro protocolo) **sem interferir** na coleta e no cálculo dos parâmetros ambientais.

### 3.2. Entrada do teclado e controle do menu

As tasks relacionadas ao teclado utilizam **notificações (task notify)** com **flags** para representar as teclas pressionadas. Há duas responsabilidades principais:

- **Task de leitura de GPIOs** do teclado.
- **Task de processamento** das teclas e controle do menu.

O menu é estruturado como uma **máquina de estados**. Embora ainda não esteja totalmente finalizado, ele demonstra uma abordagem orientada a eventos, típica de sistemas embarcados robustos.

### 3.3. Processamento de comandos: filas (queues) e ACK

Para comandos recebidos (por exemplo, **abrir porta**, **acionar alarme** e **acionar ventilação**), foi adotada a abordagem com **queues**. Com isso:

- Os comandos são enfileirados em ordem **FIFO**.
- A execução ocorre de forma previsível, reduzindo risco de concorrência.
- Ao final, é gerado um **ACK** confirmando que o comando foi recebido e processado.

### 3.4. Sensores e comunicação com MQTT

Para sensores (movimento, temperatura e umidade), o firmware notifica componentes responsáveis por publicar telemetria. A escolha de múltiplas classes/módulos, mesmo quando seria possível concentrar lógica em um único ponto, foi intencional para reforçar:

- Modularização.
- Separação de responsabilidades.
- Organização do sistema em um formato mais próximo de um produto evolutivo.

## 4. Hardware

O hardware foi desenvolvido conforme o pré-projeto. O diagrama de blocos abaixo resume a estrutura e o funcionamento:

![Esquema de Blocos do Hardware](./imagens/Hardware_do_Rack_Inteligente.png)

A imagem a seguir mostra o protótipo montado. Nela:

- Adaptador e **servo motor** (acionamento da porta).
- Placa de distribuição **I2C**.
- Sensor de movimento (**MPU5060**).
- Sensor de temperatura e umidade (**AHT10**).
- Teclado.
- A **BitDogLab** ao centro, já integrando LEDs RGB e display OLED.

![Circuito do Rack](./imagens/circuito_prototipo_montado.jpeg)

### Esquemático das Conexões

No esquemático vemos o I2C usado pelo sensor de movimento (MPU6050) e sensor de temperatura e umidade (AHT10) conectado aos pinos GPIO0 e GPIO1 para o canal I2C0 do I2C externalizado através do conector de mesmo nome .

Já o PWM para controle do servo motor está no pino GPIO2, externalizado pelo conector de nome I2C1, mas neste uso não tem relação alguma com o I2C.

Os pinos de conexão do Display OLED são GPIO14 e GPIO15 conectados ao canal I2C1, como usam outros pinos não conflitam com o conector de mesmo nome.

Os LEDs RGB estão conectados nos pinos GPIO12, GPIO13 e GPIO15, respectivamente.

Os buzzer estão conectados ao GPIO10 e GPIO27, sendo controladores por PWM.

Os botões, botão A está conectado ao pino GPIO4 e o botão B GPIO5.

O Ventilador está representado pelo LED Verde, O LED Azul pisca indicando funcionamento do firmware corretamente, durante o boot rápidamente e durante o funcionamento normal muda de estado a cada 1 segundo.

A detecção de porta aberta está sendo feita pelo botão A, ao ser apertado a porta está aberta. em posição normal está fechada.

O botão B, desativa o alarme até a próxima anomalia alertada.

![Esquemático das Conexões](./imagens/Esquematico_do_Projeto.png)

## 5. Camada IoT (MQTT)

Foi adotado o protocolo **MQTT** para comunicação entre o firmware e o dashboard, por ser leve e adequado a telemetria e comandos em tempo real.

O broker foi implantado em um **servidor VPS**, com:

- Regras de **firewall** para reduzir superfície de ataque.
- Autenticação por **usuário/senha**.

Isso fornece uma base adequada para segurança operacional no cenário do projeto.

## 6. AIoT (IA aplicada ao sistema)

### 6.1. Integração com LLM via OpenWebUI/Ollama

Foi adotado o **OpenWebUI** como interface de acoplamento entre o dashboard e a engine de LLMs (via **Ollama**). Essa estratégia permite realizar requisições usando compatibilidade com a biblioteca OpenAI, facilitando a troca de engine GenAI sem mudanças grandes no código (normalmente basta alterar URL e chave de API).

### 6.2. Tool Calling para decisão e atuação

Foram usados recursos de **Tool Calling** para apoiar decisões relacionadas a:

- Temperaturas em níveis críticos.
- Acionamento de ventilação.
- Disparo de alarmes.

O modelo utilizado como orquestrador de ferramentas é o **Granite 4** (3 bilhões de parâmetros).

### 6.3. Previsão de temperatura e umidade (TTM)

Foi adicionado um mecanismo de previsão com o **Granite TTM (Tiny Time Series Model)**, utilizando dados históricos para estimar valores futuros de temperatura e umidade. Isso ajuda a antecipar situações de risco (por exemplo, tendência de aquecimento contínuo).

## 7. Treinamento e parametrização da IA

- O prompt principal para o comportamento da GenAI está na pasta `prompts/`.
- As variáveis de execução do dashboard e parâmetros de treinamento/uso do Granite TTM são configuradas via arquivo `.env` na raiz do projeto.

## 8. Dashboard (Python)

O dashboard foi desenvolvido em **Python** para facilitar a integração com a LLM e com o TTM (ambos modelos Granite da IBM) e acelerar os ciclos de teste.

A seguir, a janela principal:

![Dashboard Principal](./imagens/dashboard_rack_inteligente.png)

Componentes principais da interface:

- **Lista de racks (lado esquerdo)**: alimentada dinamicamente conforme as telemetrias são publicadas no MQTT. O nome do rack pisca quando algum parâmetro é atualizado.
- **Painel de telemetria (lado direito)**: temperatura e umidade, traço contínuo valor histórico coletado, traço descontinuo previsão com baseno histórico.
- **Controles manuais**: botões para abrir porta e acionar ventilação, além de sinalização do estado do alarme.

Ao rolar o conteúdo, é exibido o mapa de localização do rack, com dados obtidos pelo parâmetro de GPS enviado pelo Rack Inteligente:

![Dashboard Mapa](./imagens/dashboard_rack_inteligente_mapa.png)

No rodapé, são exibidas as **reflexões e decisões** produzidas pela GenAI a partir dos parâmetros de telemetria.

## 9. Testes realizados (evidências)

Além do uso com o hardware disponível, foram feitos testes para validar escala e estabilidade:

- Teste de **execução contínua** (firmware + dashboard ligados por dias).
- Teste de **carga lógica** no dashboard usando um script Python que simula racks extras publicando dados aleatórios (telemetria e localização), permitindo avaliar:
  - Desempenho da interface.
  - Estabilidade do broker MQTT.
  - Comportamento do sistema sob múltiplas fontes de dados.

### 9.1. Medições e Análise do circuito

Foram feitas medições e analises do circuito para identificar ponto de falhas. Apesar da deformação do sinal no barramento I2C (deveria ser uma onda quadrada mais retilinea) a comunicação funciona perfeitamente bem.

![Medição da Sinalização I2C](./imagens/coleta_de_sinal_i2c.jpg)

## 10. Problemas encontrados e soluções adotadas

- **Limitação de bancada (ausência de um rack real)**

  - Para simular cenários, foram usados métodos práticos para elevar temperatura/umidade, permitindo observar respostas do sistema.
- **Necessidade de testar vários racks com apenas um kit**

  - Foi criado um simulador que injeta dados de múltiplos racks (com geolocalizações variadas e grande variação de temperatura/umidade), viabilizando testes mais completos do dashboard.
- **Sensor de movimento aparentemente não funcional**

  - Está em avaliação a possibilidade de troca do componente junto ao EmbarcaTech.
- **Falha no envio de umidade (intermitente)**

  - Próxima ação: revisar sincronismo entre a task de coleta e a task de publicação MQTT, garantindo consistência na atualização do valor.

## 11. Próximos passos

- Adicionar um **watchdog timer** para detectar travamentos e reiniciar o hardware quando necessário.
- Finalizar o **menu local** para troca de senha.
- Implementar armazenamento dinâmico e seguro de configurações (por exemplo, senha e dados de rede Wi-Fi).
- Evoluir a coleta e uso de geolocalização do rack, incluindo opções de configuração.
- Adicionar no dashboard recursos para **recuperação de senha remota** (com segurança e auditoria).
- Melhorar o treinamento e calibragem dos componentes de IA, tanto do **Granite TTM** quanto do **Granite LLM**.

## 12. Projeto no GitHub

O projeto pode ser clonado, lembre-se de clonar recursivamente, pois o firmware está em outro repositório. Assim poderá ser analisado em seu estágio atual:

* Projeto Geral: [https://github.com/ArvoreDosSaberes/Embacathec-Etapa-2---Projeto-Final.git](https://github.com/ArvoreDosSaberes/Embacathec-Etapa-2---Projeto-Final.git).
* Projeto Firmware: https://github.com/ArvoreDosSaberes/Embarcatech-Etapa-2---Projeto-Final-firmware
* Em breve Dashboard e Simulador estarão em seus repositórios próprios para facilitar minha gerencia do código.
