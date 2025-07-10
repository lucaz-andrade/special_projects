#%%
from openai import OpenAI
import os
import re

# Configure client for LM Studio (OpenAI-compatible endpoint)
client = OpenAI(
    api_key="not-needed",  # LM Studio doesn't require a real API key
    base_url="http://127.0.0.1:1234/v1"  # Default LM Studio endpoint
)

def llm_call(prompt: str, system_prompt: str = "", model="local-model") -> str:
    """
    Calls the local LM Studio model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The model identifier (can be any string for local models).

    Returns:
        str: The response from the language model.
    """
    try:
        # Build messages array with system prompt if provided
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,  # LM Studio ignores this, uses loaded model
            messages=messages,
            max_tokens=8000,
            temperature=0.1,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"LM Studio API error: {e}")
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