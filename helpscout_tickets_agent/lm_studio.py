#%%
import ollama
import os
import re

# Ollama client is automatically configured to use localhost:11434
# No explicit client initialization needed

def llm_call(prompt: str, system_prompt: str = "", model="llama3.1:8b") -> str:
    """
    Calls the local Ollama model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The Ollama model identifier (e.g., "llama3.1:8b", "mistral", "codellama").

    Returns:
        str: The response from the language model.
    """
    try:
        # Build messages array with system prompt if provided
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(
            model=model,
            messages=messages,
            options={
                "num_predict": 8000,  # Equivalent to max_tokens
                "temperature": 0.1,
            }
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"Ollama API error: {e}")
        return ""
    

def simple_call(input: str, prompt: str): 
    """Process the input based on the prompt guidance"""
    try:
        print("Making LLM call...")
        result = llm_call(prompt, input)
        
        # Debug the actual result
        print(f"Raw result type: {type(result)}")
        print(f"Raw result repr: {repr(result[:100]) if result else 'None or empty'}")
        print(f"Result is empty string: {result == ''}")
        print(f"Result is None: {result is None}")
        
        return result if result else None
    except Exception as e:
        print(f"LLM call failed with error: {type(e).__name__}: {e}")
        return None