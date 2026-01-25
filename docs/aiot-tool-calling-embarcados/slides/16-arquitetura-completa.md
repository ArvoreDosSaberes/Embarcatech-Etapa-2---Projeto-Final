# 🏗️ Arquitetura Completa do Projeto

## Fluxo de Dados

```
┌─────────────────┐     MQTT      ┌─────────────────┐
│     ESP32       │ ────────────→ │   Dashboard     │
│   (Firmware)    │               │    (Python)     │
│                 │ ←──────────── │                 │
└─────────────────┘   Comandos    └────────┬────────┘
        │                                  │
        │ Sensores                         │ HTTPS
        ↓                                  ↓
┌─────────────────┐              ┌─────────────────┐
│  Temperatura    │              │   LLM Server    │
│  Umidade        │              │  (Tool Calling) │
│  Porta (GPIO)   │              │                 │
└─────────────────┘              └─────────────────┘
```

## Componentes do Sistema

- **Firmware ESP32**: Coleta sensores, executa comandos
- **Dashboard Python**: Interface, gráficos, forecast
- **ToolCallingService**: Decisões via LLM
- **ForecastService**: Granite TTM + SARIMA fallback

> O ESP32 não precisa rodar a LLM — apenas executa as decisões!
