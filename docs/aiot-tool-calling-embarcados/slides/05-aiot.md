# 🌐 O que é AIoT?

## Artificial Intelligence + Internet of Things

A **convergência** entre IA e IoT cria dispositivos que:

- **Coletam dados** do mundo físico (sensores)
- **Processam localmente** ou na nuvem
- **Tomam decisões** baseadas em modelos de IA
- **Executam ações** no mundo real (atuadores)

## Arquiteturas de AIoT

| Modelo | Processamento | Latência | Custo |
|--------|---------------|----------|-------|
| Cloud AI | 100% nuvem | Alta | Baixo/dispositivo |
| Edge AI | No dispositivo | Mínima | Alto/dispositivo |
| Híbrido | Distribuído | Média | Balanceado |

## Exemplos Práticos

- **Rack Inteligente** — Controle térmico preditivo
- **Câmeras de Segurança** — Detecção de intrusão
- **Agricultura** — Irrigação automatizada
- **Indústria 4.0** — Manutenção preditiva

> No nosso projeto: ESP32 envia telemetria → LLM decide → ESP32 executa
