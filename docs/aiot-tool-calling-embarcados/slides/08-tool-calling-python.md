# 🐍 Tool Calling em Python — Referência

## Definição das Tools (OpenAI API)

```python
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "turnOnVentilation",
            "description": "Liga a ventilação do rack",
            "parameters": {
                "type": "object",
                "properties": {
                    "rackId": {
                        "type": "string",
                        "description": "ID do rack"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motivo da ação"
                    }
                },
                "required": ["rackId", "reason"]
            }
        }
    }
]
```

## Chamada à API

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    tools=TOOLS_DEFINITION,
    tool_choice="auto"
)
```
