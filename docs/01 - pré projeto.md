---
title: "Rack Inteligente: Sistema de Gerenciamento e Segurança Ambiental para Infraestruturas de Pequeno Porte"
authors:
  - "Carlos Delfino"
summary: "Solução IoT focada em monitorar ambiente e controlar o acesso de racks compactos, integrando sensores, atuadores e IA generativa."
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
  natureDetails: "apresentado ao Instituto Federal como requisito parcial para obtenção do título."
  studentId: "202510110980368"
  city: "Fortaleza"
  state: "CE"
  year: "2025"
---
## Título do Projeto

**Rack Inteligente AIoT:
Sistema de Gerenciamento e Segurança Ambiental para Infraestruturas de Pequeno Porte controlado por IA Generativa**

---

## Resumo

O projeto **Rack Inteligente** tem como objetivo desenvolver uma solução de **Internet das Coisas com Inteligência Artificial (AIoT)** para o monitoramento e controle de pequenos racks de servidores, switches, gateways e firewalls. A proposta visa integrar  **segurança física** , **controle ambiental** e **acesso remoto** em um sistema compacto e de baixo custo. O sistema permitirá o **gerenciamento de temperatura, umidade, segurança e acesso físico** por meio de sensores, atuadores e um microcontrolador RP2040, utilizando o protocolo MQTT para comunicação com um servidor remoto e orquestrado com freeRTOS, Além de um Dashboard integrado com Inteligência Artificial Generativa. A solução contribuirá para a prevenção de falhas por superaquecimento e acesso não autorizado, promovendo maior segurança e confiabilidade nas infraestruturas de rede de pequeno porte.

---

## Justificativa

Durante **35 anos de experiência em suporte e implantação de redes de computadores** , foi observada uma carência de soluções dedicadas a **pequenos racks** que unam segurança física e gestão ambiental em um mesmo sistema. Em geral, as tecnologias existentes são voltadas a  **data centers de grande porte** , deixando lacunas no mercado de  **infraestruturas menores** , que muitas vezes operam em condições ambientais inadequadas ou vulneráveis a acessos indevidos. Além do mais, faltam soluções com preços compátiveis a infraestrutura em questão.

O **Rack Inteligente AIoT** surge como uma resposta a essa necessidade, proporcionando um **sistema autônomo, modular, acessível e Inteligênte** que permite:

* Monitorar e controlar o ambiente interno do rack (temperatura e umidade);
* Gerenciar o acesso físico com autenticação e travamento automático;
* Enviar alertas e relatórios via rede para administração remota.

Essa solução é essencial para empresas que necessitam garantir a **continuidade operacional** e  **segurança de dados** , mesmo com orçamentos reduzidos e infraestrutura simplificada.

---

## Requisitos do Sistema

O sistema deverá contemplar os seguintes requisitos funcionais e não funcionais:

### Requisitos Funcionais

1. Monitorar temperatura e umidade do ambiente interno do rack.
2. Controlar o acesso físico à porta do rack via senha e autenticação digital.
3. Acionar mecanismos de abertura e travamento automático (servo motor ou solenóide).
4. Enviar dados ambientais e de estado (aberto/fechado) via protocolo MQTT.
5. Exibir indicadores luminosos de estado e condição do rack (LEDs RGB).
6. Gerar alertas em caso de tentativa de abertura não autorizada.
7. Permitir controle e visualização remota via aplicativo em Python (Dashboard).
8. Emitir relatórios textuais produzidos por Inteligência Artificial Generativa

### Requisitos Não Funcionais

1. O sistema deve ser  **modular e escalável** , permitindo adicionar novos racks facilmente.
2. O tempo de resposta aos comandos MQTT deve ser inferior a  **1000 ms** .
3. Deve operar de forma estável em  **tensões de 5V ou 12V** .
4. O sistema deve possuir  **resiliência a falhas de comunicação** , com reconexão automática.
5. Dados sensíveis como senhas devem ser trafegados de forma cifrada.

---

## Problemática a Ser Resolvida

Atualmente, a maioria dos pequenos racks de servidores e redes de distribuição carece de  **monitoramento ambiental e controle de acesso** . Isso resulta em situações como:

* Superaquecimento devido à falta de ventilação ou excesso de calor acumulado;
* Invasões físicas não detectadas, comprometendo equipamentos sensíveis;
* Falta de rastreabilidade sobre quem acessou e quando;
* Ausência de integração com sistemas remotos de gestão.

Essas deficiências podem resultar em  **interrupções de serviço, danos a equipamentos e riscos à segurança dos dados corporativos** . O **Rack Inteligente** propõe eliminar essas vulnerabilidades por meio de uma abordagem integrada e inteligente baseada em IoT.

---

## Solução Proposta em AIoT

A solução adota a arquitetura **AIoT em quatro camadas** (dispositivo IoT, broker MQTT, camada de Inteligência AIoT e dashboard) para oferecer segurança, controle e comunicação eficiente.

### Diagrama de Blocos de Hardware

* **Microcontrolador** : RP2040 (BitDogLab)
* **Sensores** :
* AHT10: temperatura e umidade interna;
* Sensor magnético: detecção de abertura da porta.
* Sensor de movimento: detecção de tentativa de Arrombamento
* **Atuadores** :
* Solenoide para travamento mecânico;
* LEDs RGB para indicação de status (operacional, alerta, falha).
* Buser: para alertas de porta aberta por longo periodo
* **Broacker**:
* Brocker MQTT protegido por senha
* **Interface de Acesso**:
* Teclado de membrana (senha local);
* Dasboard remota para autenticação e controle.
* **IA Generativa**:
* IA Generativa para aprendizado de máquina e predição de comportamento do rack.

![Diagrama de Blocos de Hardware](./rack_inteligente.png)

### Protocolos de Comunicação

O sistema utilizará o protocolo  **MQTT (Message Queuing Telemetry Transport)** , adequado para IoT devido à sua leveza e confiabilidade. Cada rack possuirá um  **tópico hierarquizado** , por exemplo:

```
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/status (1=aberto/0=fechado)
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/command/door (1=abrir/0=fechar)
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/command/ventilation (1=ligar/0=desligar)
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/command/buzzer (0=desligado/1=porta aberta/2=arrombamento/3=superaquecimento)
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/environment/temperature (0-100)
mqtt://mqtt.rapport.tec.br/racks/<rack_id>/environment/humidity (0-100)
```

A comunicação será autenticada com  **usuário e senha** , e os dados trafegarão via **broker MQTT** hospedado em  **VPS** .

### Aplicativo de Monitoramento

O aplicativo desenvolvido em **Python** permitirá:

* Exibir o status de cada rack (aberto/fechado, temperatura, umidade);
* Visualizar o histórico de alertas e eventos;
* Comandar abertura e fechamento remotamente;
* Apresentar mensagens amigáveis que expliquem as decisões e ações executadas pela IA generativa;
* Gerar relatórios e logs para auditoria.

### Camada de Inteligência AIoT

A camada de Inteligência AIoT introduz uma **IA generativa** responsável por aprender o comportamento térmico do rack, prever riscos de aquecimento e recomendar ações preventivas. Essa IA analisa continuamente **temperatura, umidade e padrões de abertura** para decidir quando **acionar ventilação, enviar alertas ou solicitar intervenção remota**.

Para executar as ações necessárias, a IA utiliza **Tool Calling** apontando para funções especializadas do backend (por exemplo, acionar ventoinhas, ajustar o tempo de abertura da porta ou reforçar o travamento). Esse mecanismo garante **respostas rápidas e auditáveis**, mantendo um registro de cada decisão tomada. As decisões e justificativas são enviadas ao dashboard em mensagens claras, permitindo que o operador acompanhe, em tempo real, o raciocínio da IA e os comandos disparados.

---

## Cronograma de Execução

| Etapa | Atividade                                                              | Duração | Período                      |
| ----- | ---------------------------------------------------------------------- | --------- | ----------------------------- |
| 0     | **Entrega do Pré-Projeto**                                      | -         | **06/11/2025**          |
| 1     | Levantamento de requisitos e componentes                               | 2 semanas | Novembro/2025                 |
| 2     | Desenvolvimento do protótipo eletrônico                              | 4 semanas | Dezembro/2025                 |
| 3     | Implementação do software embarcado (RP2040) e início dos testes    | 3 semanas | Dezembro/2025 - Janeiro/2026  |
| 4     | **Entrega do Relatório de Evidência de Desenvolvimento (RED)** | 1 dia     | **21/12/2025**          |
| 5     | Ajustes técnicos no hardware e software após entrega do RED          | 2 semanas | Janeiro/2026                  |
| 6     | Desenvolvimento do aplicativo Python                                   | 3 semanas | Janeiro/2026 - Fevereiro/2026 |
| 7     | Treinamento e validação da IA generativa                             | 2 semanas | Janeiro/2026                  |
| 8     | Integração e testes do sistema completo                              | 3 semanas | Fevereiro/2026                |
| 9     | Documentação e apresentação final                                  | 1 semana  | Até**08/02/2026**      |
