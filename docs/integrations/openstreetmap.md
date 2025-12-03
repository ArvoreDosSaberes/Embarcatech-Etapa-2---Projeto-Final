# Integração com OpenStreetMap e Leaflet.js

## Resumo

Este documento descreve a integração do dashboard com **OpenStreetMap** (OSM) para exibição de mapas e **Leaflet.js** como biblioteca de renderização. Ambas são soluções **opensource** e **gratuitas** para uso em projetos comerciais e não-comerciais.

---

## 1. Licenciamento

### 1.1 OpenStreetMap (Tiles/Dados)

| Aspecto | Detalhes |
|---------|----------|
| **Licença** | Open Data Commons Open Database License (ODbL) |
| **Custo** | Gratuito |
| **Atribuição obrigatória** | Sim |
| **Uso comercial** | Permitido |
| **Link oficial** | [https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |

#### Requisitos de atribuição

Ao utilizar dados ou tiles do OpenStreetMap, você **deve** incluir a seguinte atribuição visível no mapa:

```
© OpenStreetMap contributors
```

Com link para: `https://www.openstreetmap.org/copyright`

> ⚠️ **Importante**: A atribuição já está implementada automaticamente no código do dashboard através do parâmetro `attribution` do Leaflet.

### 1.2 Leaflet.js (Biblioteca JavaScript)

| Aspecto | Detalhes |
|---------|----------|
| **Licença** | BSD 2-Clause "Simplified" License |
| **Custo** | Gratuito |
| **Uso comercial** | Permitido |
| **Atribuição** | Recomendada (não obrigatória) |
| **Repositório** | [https://github.com/Leaflet/Leaflet](https://github.com/Leaflet/Leaflet) |
| **Documentação** | [https://leafletjs.com/](https://leafletjs.com/) |

---

## 2. Como Funciona no Projeto

### 2.1 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard PyQt5                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              QWebEngineView (Chromium)                 │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │                Leaflet.js                        │  │  │
│  │  │  ┌─────────────────────────────────────────┐    │  │  │
│  │  │  │       OpenStreetMap Tiles (CDN)          │    │  │  │
│  │  │  │   https://tile.openstreetmap.org/...     │    │  │  │
│  │  │  └─────────────────────────────────────────┘    │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Carregamento dos Recursos

Os recursos são carregados via CDN (Content Delivery Network):

- **Leaflet CSS**: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
- **Leaflet JS**: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
- **Tiles OSM**: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`

> 💡 **Nota**: Não é necessário instalar dependências adicionais. Os recursos são carregados diretamente da internet.

---

## 3. Política de Uso (Tile Usage Policy)

### 3.1 Limites do OpenStreetMap

O servidor de tiles público do OpenStreetMap tem políticas de uso:

| Regra | Descrição |
|-------|-----------|
| **User-Agent** | Deve identificar a aplicação (navegador já faz isso) |
| **Rate Limiting** | Não fazer mais de 2 requisições/segundo por usuário |
| **Bulk Download** | Proibido fazer download em massa de tiles |
| **Caching** | Respeitar headers de cache HTTP |

> ⚠️ **Para aplicações de alto tráfego**: Considere usar um servidor de tiles próprio ou serviços pagos como Mapbox, Stadia Maps, ou MapTiler.

### 3.2 Alternativas para Produção em Larga Escala

Se o projeto escalar para muitos usuários simultâneos, considere:

1. **Servidor de tiles próprio** (usando OpenMapTiles)
2. **Serviços pagos**:
   - [Mapbox](https://www.mapbox.com/) - Tier gratuito generoso
   - [Stadia Maps](https://stadiamaps.com/) - Foco em privacidade
   - [MapTiler](https://www.maptiler.com/) - Suporte a self-hosting
   - [Thunderforest](https://www.thunderforest.com/) - Mapas especializados

---

## 4. Implementação no Dashboard

### 4.1 Código Relevante

O mapa é gerado dinamicamente pelo método `generate_leaflet_map_html()` em `dashboard/app.py`:

```python
def generate_leaflet_map_html(self, latitude=None, longitude=None, rack_id=None):
    """
    Gera HTML com mapa Leaflet/OpenStreetMap.
    
    Args:
        latitude: Latitude do rack
        longitude: Longitude do rack
        rack_id: ID do rack para popup
    """
    # ... implementação
```

### 4.2 Coordenadas de Fortaleza-CE

O simulador utiliza coordenadas fixas de locais em Fortaleza-CE, Brasil:

| Local | Latitude | Longitude |
|-------|----------|-----------|
| Centro | -3.7319 | -38.5267 |
| Aldeota | -3.7403 | -38.4993 |
| Iguatemi | -3.7648 | -38.4712 |
| Mucuripe | -3.7271 | -38.4909 |
| Praia de Iracema | -3.7191 | -38.5089 |
| Fátima | -3.7456 | -38.5302 |
| Papicu | -3.7589 | -38.4834 |
| Benfica | -3.7744 | -38.5566 |
| Dionísio Torres | -3.7505 | -38.5124 |
| Meireles | -3.7380 | -38.5189 |

---

## 5. Passo a Passo: Configuração

### 5.1 Requisitos

- **Conexão com internet** para carregar tiles e biblioteca Leaflet
- **PyQt5 com WebEngine** instalado (`pip install PyQtWebEngine`)

### 5.2 Verificação

1. Execute o dashboard:
   ```bash
   cd dashboard
   python app.py
   ```

2. Selecione um rack na lista lateral

3. O mapa deve exibir a localização do rack com um marcador

### 5.3 Troubleshooting

| Problema | Solução |
|----------|---------|
| Mapa não carrega | Verifique conexão com internet |
| Tela em branco | Verifique se PyQtWebEngine está instalado |
| Marcador não aparece | Aguarde o simulador publicar coordenadas |

---

## 6. Conformidade Legal

### 6.1 Checklist de Conformidade

- [x] Atribuição "© OpenStreetMap contributors" visível
- [x] Link para copyright do OSM incluído
- [x] Uso dentro dos limites de rate limiting
- [x] Sem download em massa de tiles
- [x] Licença BSD-2-Clause do Leaflet respeitada

### 6.2 Texto de Atribuição no Código

```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);
```

---

## 7. Referências

1. **OpenStreetMap Copyright**: https://www.openstreetmap.org/copyright
2. **ODbL License**: https://opendatacommons.org/licenses/odbl/
3. **Leaflet License**: https://github.com/Leaflet/Leaflet/blob/main/LICENSE
4. **Tile Usage Policy**: https://operations.osmfoundation.org/policies/tiles/
5. **Leaflet Documentation**: https://leafletjs.com/reference.html

---

## 8. Histórico de Alterações

| Data | Versão | Descrição |
|------|--------|-----------|
| 2024-12-03 | 1.0.0 | Documentação inicial da integração OpenStreetMap/Leaflet |

