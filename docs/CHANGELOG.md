# Changelog

Histórico de mudanças do projeto Rack Inteligente - EmbarcaTech TIC-27.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

## [Unreleased]

### Added
- **Documentação de Referência API** (`docs/REFERENCE_API.md`): Documentação completa de todas as funções, macros e variáveis dos códigos Python e C/C++.
  - Documentação do dashboard PyQt5 (`app.py`)
  - Documentação dos serviços: `rackControlService.py`, `forecastService.py`, `sarimaFallbackService.py`, `toolCallingService.py`, `anomalyDetector.py`
  - Documentação do simulador MQTT (`mqtt_simulator.py`)
  - Documentação do firmware: `rack_inteligente.cpp`, headers, tasks
  - Documentação das bibliotecas: `log_vt100`, `buzzer_pwm_task`, `door_servo_task`
  - Referência de tópicos MQTT padronizados
  - Referência de variáveis de ambiente

---

## [0.1.0] - 2025-11-16

### Added
- Firmware inicial para Raspberry Pi Pico W com FreeRTOS
- Conexão Wi-Fi e cliente MQTT
- Tasks para leitura de sensores (temperatura, umidade, inclinação)
- Task de GPS simulado
- Task de controle de porta via servo motor PWM
- Task de buzzer PWM com padrões sonoros distintos
- Sistema de comandos MQTT com confirmação (ACK)
- Dashboard PyQt5 com interface moderna
- Serviço de controle de racks via MQTT (`RackControlService`)
- Serviço de previsão com IBM Granite TTM-R2 (`ForecastService`)
- Serviço de fallback SARIMA (`SarimaFallbackService`)
- Serviço de Tool Calling com LLM (`ToolCallingService`)
- Detector de anomalias por Z-score (`AnomalyDetector`)
- Simulador MQTT para testes
- Mapa interativo com Leaflet.js e OpenStreetMap
- Script de conversão Markdown para PDF (padrão e ABNT)

### Technical
- Arquitetura híbrida de previsão (Granite + SARIMA)
- Sistema de histerese (Schmitt Trigger) para limiares
- Comunicação MQTT bidirecional com ACK
- Gráficos de séries temporais com previsão 24h
- Saída graciosa para interrupções (Ctrl+C)
