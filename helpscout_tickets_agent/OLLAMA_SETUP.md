# Configuração do Ollama

## Instalação

1. **Instalar o Ollama:**
   ```bash
   # macOS
   brew install ollama
   
   # Ou baixe de: https://ollama.ai/download
   ```

2. **Instalar a biblioteca Python:**
   ```bash
   pip install ollama
   ```

## Uso

### Iniciar o Ollama
```bash
ollama serve
```

### Baixar um modelo
```bash
# Modelo recomendado (leve e eficiente)
ollama pull llama3.2

# Outros modelos disponíveis:
ollama pull mistral
ollama pull codellama
ollama pull llama2
```

### Listar modelos instalados
```bash
ollama list
```

## Uso no código

O arquivo `lm_studio.py` agora usa Ollama. Para usar um modelo específico:

```python
from lm_studio import llm_call

# Usar o modelo padrão (llama3.2)
response = llm_call("Sua pergunta aqui", system_prompt="Você é um assistente útil")

# Usar um modelo específico
response = llm_call("Sua pergunta aqui", model="mistral")
```

## Modelos disponíveis

- **llama3.2** (padrão) - Rápido e eficiente
- **mistral** - Ótimo para tarefas gerais
- **codellama** - Especializado em código
- **llama2** - Versão anterior, ainda muito capaz

## Diferenças do LM Studio

- **Porta:** Ollama usa `localhost:11434` (LM Studio usava `localhost:1234`)
- **API:** Ollama tem API nativa Python (mais simples que OpenAI-compatible)
- **Modelos:** Gerenciados via CLI do Ollama (não precisa interface gráfica)
- **Performance:** Geralmente mais rápido e eficiente

## Troubleshooting

Se encontrar erro de conexão:
```bash
# Verificar se o Ollama está rodando
ps aux | grep ollama

# Reiniciar o serviço
killall ollama
ollama serve
```
