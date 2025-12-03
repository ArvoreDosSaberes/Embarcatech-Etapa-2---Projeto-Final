# 🔮 Instalação do IBM Granite TTM-R2

Guia para instalar o modelo **IBM Granite Time Series TTM-R2** no projeto.

## ⚠️ Importante

O modelo Granite TTM-R2 **não está disponível no PyPI** e deve ser instalado diretamente do GitHub.

## 🚀 Instalação Rápida

### Opção 1: Script Automático (Recomendado)

```bash
# 1. Criar e ativar ambiente virtual
python3.7 -m venv venv
source venv/bin/activate

# 2. Instalar dependências base
pip install -r requirements.txt

# 3. Executar script de instalação do Granite
bash install_granite.sh
```

### Opção 2: Instalação Manual

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Instalar PyTorch
pip install torch==1.13.1 --index-url https://download.pytorch.org/whl/cpu

# 3. Instalar transformers
pip install transformers==4.30.0

# 4. Tentar instalar do repositório oficial IBM
pip install git+https://github.com/ibm-granite/granite-tsfm.git@main

# OU do repositório alternativo
pip install git+https://github.com/IBM/tsfm.git
```

## 🔍 Verificar Instalação

```bash
python3.7 -c "
from tsfm_public import TimeSeriesForecastingPipeline, TinyTimeMixerForPrediction
print('✅ Granite TTM-R2 instalado com sucesso!')
"
```

## 📊 Funcionamento do Sistema

O sistema foi projetado para funcionar em **dois modos**:

### Modo 1: Com Granite TTM-R2 (Preferencial)

Se o Granite estiver instalado:
- ✅ Usa o modelo IBM Granite TTM-R2 para previsões
- ✅ Suporte GPU/CPU automático
- ✅ Zero-shot forecasting de alta qualidade
- ✅ Horizonte de 96 pontos futuros

### Modo 2: Fallback (Exponential Smoothing)

Se o Granite **não** estiver disponível:
- ✅ Sistema continua funcionando normalmente
- ✅ Usa Holt-Winters (Triple Exponential Smoothing)
- ✅ Captura tendência e sazonalidade
- ✅ Previsões de boa qualidade

## 🐛 Problemas Comuns

### Erro: "No module named 'tsfm_public'"

**Solução**: Execute o script de instalação:
```bash
bash install_granite.sh
```

### Erro: "Could not find a version that satisfies..."

**Causa**: Python 3.7 tem limitações de compatibilidade.

**Solução**: Verifique se está usando as versões corretas:
```bash
pip install torch==1.13.1
pip install transformers==4.30.0
```

### Erro ao instalar do GitHub

**Causa**: Repositório pode não estar acessível ou ter mudado.

**Solução**: O sistema funcionará automaticamente em modo fallback.

## 📝 Logs do Sistema

O sistema exibe mensagens claras sobre qual modelo está sendo usado:

```
✅ [ForecastService] IBM Granite TTM-R2 disponivel
🔮 [ForecastService] Using IBM Granite TTM-R2 on cpu
```

Ou em modo fallback:

```
⚠️  [ForecastService] IBM Granite TTM-R2 nao disponivel - usando modelo alternativo
💡 [ForecastService] Execute: bash install_granite.sh
🔮 [ForecastService] Using Exponential Smoothing (fallback)
```

## 🎯 Requisitos Mínimos

- **Python**: 3.7+
- **RAM**: 4GB mínimo (8GB recomendado para Granite)
- **Disco**: ~2GB para modelo e dependências
- **Internet**: Necessário para download inicial do modelo

## 🔗 Referências

- [IBM Granite Models](https://github.com/ibm-granite)
- [Granite Time Series Forecasting](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
- [Paper: Tiny Time Mixers](https://arxiv.org/abs/2401.03955)

## ✅ Próximos Passos

Após instalar:

1. Execute o sistema: `python app.py`
2. Acesse: http://localhost:5000
3. Clique em "▶️ Iniciar"
4. Observe os logs para confirmar qual modelo está sendo usado

---

**💡 Dica**: O sistema funciona perfeitamente mesmo sem o Granite instalado!
