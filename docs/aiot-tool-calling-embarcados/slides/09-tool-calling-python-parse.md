# 🐍 Processando Tool Calls em Python

## Extraindo as Chamadas de Função

```python
message = response.choices[0].message

if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        rack_id = arguments.get('rackId')
        reason = arguments.get('reason')
        
        # Executa a função correspondente
        if function_name == 'turnOnVentilation':
            rackControlService.turnOnVentilation(rack_id)
        elif function_name == 'activateCriticalTemperatureAlert':
            rackControlService.activateBuzzer(rack_id, 3)
```

## Resposta da LLM (JSON)

```json
{
  "tool_calls": [{
    "function": {
      "name": "turnOnVentilation",
      "arguments": "{\"rackId\":\"001\",\"reason\":\"Temp 38°C\"}"
    }
  }]
}
```

> A LLM **decide** qual função chamar com base no contexto!
