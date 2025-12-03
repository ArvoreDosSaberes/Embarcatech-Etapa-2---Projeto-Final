# ⚡ Instalação Rápida - Python 3.12

## 🚀 Passos Rápidos

```bash
# 1. Limpar ambiente anterior (se existir)
rm -rf venv

# 2. Executar script de instalação
bash run.sh
```

O script `run.sh` irá automaticamente:
- ✅ Criar ambiente virtual
- ✅ Instalar todas as dependências
- ✅ Iniciar o servidor

## 🔮 Instalar IBM Granite TTM-R2 (Opcional mas Recomendado)

Após o sistema estar rodando, em outro terminal:

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar Granite
bash install_granite.sh

# Reiniciar o servidor
# (Ctrl+C no terminal anterior e executar novamente)
python app.py
```

## 📊 Verificar Instalação

O sistema mostrará nos logs qual modelo está usando:

**Com Granite:**
```
✅ [ForecastService] IBM Granite TTM-R2 disponivel
🔮 [ForecastService] Using IBM Granite TTM-R2 on cpu
```

**Sem Granite (Fallback):**
```
⚠️  [ForecastService] IBM Granite TTM-R2 nao disponivel
🔮 [ForecastService] Using Exponential Smoothing (fallback)
```

## 🌐 Acessar Interface

Abra seu navegador em: **http://localhost:5000**

## ⚙️ Requisitos

- **Python 3.12** ✅
- **pip** atualizado
- **4GB RAM** mínimo
- **Conexão com internet** (primeira execução)

## 🐛 Problemas?

### Erro de permissão no script
```bash
chmod +x run.sh install_granite.sh
```

### Porta 5000 em uso
Edite `.env` e mude:
```
PORT=8080
```

### Dependências não instalam
```bash
pip install --upgrade pip setuptools wheel
bash run.sh
```

---

**💡 Dica**: O sistema funciona perfeitamente mesmo sem o Granite instalado!
