# 🚀 Quick Start Guide

Guia rápido para começar a usar o **Granite Time Series Forecasting** em menos de 5 minutos.

## ⚡ Início Rápido (Linux/Mac)

```bash
# 1. Entre na pasta do projeto
cd Granite-Time-Series-Forecasting-Python

# 2. Torne o script executável
chmod +x run.sh

# 3. Execute o script de inicialização
./run.sh
```

O script `run.sh` irá automaticamente:
- ✅ Verificar Python 3.8+
- ✅ Criar ambiente virtual
- ✅ Instalar dependências
- ✅ Configurar arquivo .env
- ✅ Iniciar o servidor

## 🪟 Início Rápido (Windows)

```powershell
# 1. Entre na pasta do projeto
cd Granite-Time-Series-Forecasting-Python

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente
venv\Scripts\activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure o .env
copy .env.example .env

# 6. Inicie o servidor
python app.py
```

## 🌐 Acessar a Interface

Após iniciar o servidor, abra seu navegador em:

**http://localhost:5000**

## 🎮 Usando a Interface

### 1️⃣ Iniciar Processamento

Clique no botão **"▶️ Iniciar"** para começar a geração de dados e previsões em tempo real.

### 2️⃣ Observar o Gráfico

O gráfico será atualizado automaticamente a cada 2 segundos com:
- **Linha azul**: Dados reais gerados
- **Linha roxa tracejada**: Previsões do modelo
- **Triângulos vermelhos**: Anomalias detectadas

### 3️⃣ Alertas de Anomalias

Quando uma anomalia for detectada, um **alerta vermelho pulsante** aparecerá no topo da página com:
- Valor anômalo detectado
- Desvio em relação ao padrão (σ)
- Severidade (medium, high, critical)

### 4️⃣ Estatísticas

Acompanhe em tempo real:
- **Pontos**: Total de dados gerados
- **Previsões**: Número de previsões realizadas
- **Anomalias**: Quantidade de anomalias detectadas

### 5️⃣ Controles

- **⏸️ Parar**: Pausa a geração de dados
- **🔄 Resetar**: Limpa todos os dados e reinicia

## 🔧 Configuração Rápida

Edite o arquivo `.env` para ajustar:

```env
# Intervalo de geração (segundos)
DATA_GENERATION_INTERVAL=2.0

# Sensibilidade de anomalias (menor = mais sensível)
ANOMALY_THRESHOLD_MULTIPLIER=3.0

# Horizonte de previsão (pontos futuros)
FORECAST_HORIZON=96
```

## 📊 Exemplo de Uso

1. **Inicie o sistema** com `./run.sh`
2. **Acesse** http://localhost:5000
3. **Clique** em "▶️ Iniciar"
4. **Observe** o gráfico sendo preenchido em tempo real
5. **Aguarde** ~30 segundos para ver a primeira previsão
6. **Anomalias** serão injetadas aleatoriamente (5% de probabilidade)

## ❓ Problemas Comuns

### Erro: "Port 5000 already in use"

Mude a porta no `.env`:
```env
PORT=8080
```

### Modelo demora para carregar

Na primeira execução, o modelo Granite (~500MB) será baixado. Aguarde a conclusão.

### GPU não detectada

O sistema funcionará normalmente em CPU, apenas mais lento. Para usar GPU, instale CUDA e PyTorch com suporte GPU.

## 📚 Próximos Passos

- Leia o [README.md](README.md) completo para detalhes técnicos
- Explore a [API REST](#) para integração
- Ajuste parâmetros no `.env` para seu caso de uso
- Experimente diferentes configurações de anomalia

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs no terminal
2. Consulte a seção [Troubleshooting](README.md#-troubleshooting) no README
3. Abra uma issue no repositório

---

**🎉 Pronto! Agora você está usando previsão de séries temporais com IA em tempo real!**
