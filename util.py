#%% 
import anthropic
import os

# %%
def llm_call(prompt: str, system_prompt: str = "") -> str: 
    """
    Calls the model with the given prompt and returns the response.

    Args:
        prompt (str): The user prompt to send to the model.
        system_prompt (str, optional): The system prompt to send to the model. Defaults to "".
        model (str, optional): The model to use for the call. Defaults to "claude-3-5-sonnet-20241022".

    Returns:
        str: The response from the language model.
    """
    try:
        client = anthropic.Anthropic(
            api_key = 'not-needed',
            base_url = 'http://127.0.0.1:1234'
        )

        messages = [{"role": "user", "content": prompt}]
        response = client.messages.create(
            model = "gemma-3-12b-it",
            max_tokens=4096,
            system = system_prompt,
            messages=messages,
            temperature=0.1
        )
        
        # Safe extraction with None checks
        if response is None:
            print("Error: Response is None")
            return ""
        
        if not hasattr(response, 'content') or response.content is None:
            print("Error: Response has no content")
            return ""
        
        if len(response.content) == 0:
            print("Error: Response content is empty")
            return ""
        
        # Check if first content item has text
        first_content = response.content[0]
        if not hasattr(first_content, 'text'):
            print("Error: Content item has no text attribute")
            return ""
        
        return first_content.text or ""
        
    except TypeError as e:
        print(f"TypeError in LLM call: {e}")
        print("This suggests the response format is unexpected")
        return ""
    except Exception as e:
        print(f"LLM API error: {type(e).__name__}: {e}")
        return ""

#%%
query = "Quanto é 2+2?"
llm_call(query)
# %%
import requests

def call_local_lm(prompt: str, base_url: str = 'http://127.0.0.1:1234') -> str:
    """
    Calls a language model running locally via LM Studio.

    Args:
        prompt (str): The user prompt to send to the model.
        base_url (str, optional): The URL of the local server. Defaults to "http://localhost:5001".

    Returns:
        str: The response from the language model.
    """
    try:
        url = f"{base_url}/v1/completions"
        
        # Define the request data
        data = {
            "prompt": prompt,
            "max_tokens": 4096,  # Adjust as needed
            "temperature": 0.1   # Adjust as needed
        }
        
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("text", "")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return ""
    
    except Exception as e:
        print(f"LLM API error: {type(e).__name__}: {e}")
        return ""

#%%
query = "Quanto é 2+2?"
response = call_local_lm(query)
print(response)

# %%
