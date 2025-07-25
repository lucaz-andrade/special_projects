import requests
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
import os

load_dotenv() 
api_id = os.getenv('HP_APP_ID') 
app_secret  = os.getenv('HP_APP_SECRET') 

# Get access to the API
def get_oauth_token():
    """Gets OAuth access token using app credentials"""
    token_url = "https://api.helpscout.net/v2/oauth2/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": api_id,
        "client_secret": app_secret
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error getting token: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Create a fucntion to retrieve conversations info ('metadata') based on tags
def get_conversations_by_tag(tag_name):
    """Gets conversations with specific tag using OAuth"""
    token = get_oauth_token()
    if not token:
        return None
        
    url = "https://api.helpscout.net/v2/conversations"
    
    params = {
        "query": f"tag:\"{tag_name}\"",
        "status": "all",
        "pageSize": 50,  # Get maximum results per page
        "page": 1
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_conversations = []
    
    # Keep fetching until no more 'next' link
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            break
            
        data = response.json()
        conversations = data.get('_embedded', {}).get('conversations', [])
        all_conversations.extend(conversations)
        
        # Move to next page if available
        if '_links' in data and 'next' in data['_links']:
            params['page'] += 1
        else:
            break
    
    print(f"Retrieved {len(all_conversations)} total conversations")
    return all_conversations
  
# Create a fucntion to retrieve conversations based on a tag
def get_threads_by_tag(tag_name):
    """Gets all threads from conversations with a specific tag name."""
    token = get_oauth_token()
    base_url = "https://api.helpscout.net/v2"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # Step 1: List conversations with the tag
    conversations_url = f"{base_url}/conversations"
    params = {
       "query": f"tag:\"{tag_name}\"",
        "status": "all",
        "pageSize": 50,  # Get maximum results per page
        "page": 1
    }
    
    all_threads = []

    # Keep fetching until no more 'next' link
    while True:
        response = requests.get(conversations_url, headers=headers, params=params)
        if response.status_code != 200:
            break
            
        data = response.json()
        conversations = data.get('_embedded', {}).get('conversations', [])
        
        # Process each conversation's threads
        for conv in conversations:
            conv_id = conv.get('id')
            conv_number = conv.get('number')
            
            threads_url = f"{base_url}/conversations/{conv_id}/threads"
            thread_resp = requests.get(threads_url, headers=headers)
            
            if thread_resp.status_code == 200:
                threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                # Add conversation metadata to each thread
                for thread in threads_data:
                    thread['conversation_id'] = conv_id
                    thread['conversation_number'] = conv_number
                all_threads.extend(threads_data)
        
        # Check for next page
        if '_links' in data and 'next' in data['_links']:
            params['page'] += 1
        else:
            break
    
    print(f"Retrieved {len(all_threads)} total threads")
    return all_threads

# 
import requests

def get_threads_by_assigned_to_first_name(first_name):
    """
    Gets all threads from conversations assigned to a user with the given first name.
    Since HelpScout API does not filter by first name directly, 
    we fetch conversations with assignments, then filter by assignee first name locally.
    """
    token = get_oauth_token()
    base_url = "https://api.helpscout.net/v2"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    conversations_url = f"{base_url}/conversations"

    query = 'createdAt:[2024-10-01T00:00:00Z TO *]'

    params = {
        "query": query,
        "status": "all",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []

    while True:
        print(f"Fetching conversations page {params['page']}...") # Log which page is being fetched
        response = requests.get(conversations_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch conversations: {response.status_code} - {response.text}")
            break

        data = response.json()
        conversations = data.get('_embedded', {}).get('conversations', [])

        # Filter conversations by assignedTo.firstName
        filtered_convs = [
            c for c in conversations
            if c.get('assignedTo') and
               c['assignedTo'].get('firstName', '').lower() == first_name.lower()
        ]

        if filtered_convs:
            print(f"  Found {len(filtered_convs)} conversations assigned to '{first_name}' on this page.")

        for conv in filtered_convs:
            conv_id = conv.get('id')
            conv_number = conv.get('number')

            threads_url = f"{base_url}/conversations/{conv_id}/threads"
            thread_resp = requests.get(threads_url, headers=headers)

            if thread_resp.status_code == 200:
                threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                for thread in threads_data:
                    thread['conversation_id'] = conv_id
                    thread['conversation_number'] = conv_number
                all_threads.extend(threads_data)
            else:
                print(f"Failed to fetch threads for conversation {conv_id}: {thread_resp.status_code}")

        # Check for next page
        if '_links' in data and 'next' in data['_links']:
            params['page'] += 1
        else:
            break

    print(f"Retrieved {len(all_threads)} total threads assigned to first name '{first_name}'")
    return all_threads

#

import requests

def get_threads_by_assigned_id(assigned_user_id):
    """
    Gets all threads from conversations assigned to a specific user ID.
    """
    token = get_oauth_token()
    base_url = "https://api.helpscout.net/v2"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    conversations_url = f"{base_url}/conversations"
    query = 'createdAt:[2024-10-01T00:00:00Z TO *]'
    params = {
        "query": query,
        "assigned_to": assigned_user_id,
        "status": "all",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []

    while True:
        response = requests.get(conversations_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch conversations: {response.status_code} - {response.text}")
            break

        data = response.json()
        conversations = data.get('_embedded', {}).get('conversations', [])
        
        print(f"Page {params['page']}: fetched {len(conversations)} conversations")

        for conv in conversations:
            conv_id = conv.get('id')
            conv_number = conv.get('number')

            threads_url = f"{base_url}/conversations/{conv_id}/threads"
            thread_resp = requests.get(threads_url, headers=headers)

            if thread_resp.status_code == 200:
                threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                for thread in threads_data:
                    thread['conversation_id'] = conv_id
                    thread['conversation_number'] = conv_number
                all_threads.extend(threads_data)
            else:
                print(f"Failed to fetch threads for conversation {conv_id}: {thread_resp.status_code}")

        # Check for next page
        if '_links' in data and 'next' in data['_links']:
            params['page'] += 1
        else:
            break

    print(f"Retrieved {len(all_threads)} total threads assigned to user ID '{assigned_user_id}'")
    return all_threads


# Create a fucntion to prepare the threads to use in a NLP model
def threads_prep(raw_threads):
    """
    Filtra e formata threads para uso em modelos NLP.
    Apenas threads do tipo 'message', 'customer', 'note', 'reply' são mantidas.
    Retorna lista de threads limpas e agrupadas por conversa.
    """
    # Lista de tipos desejados
    tipos_permitidos = {"message", "customer", "note", "reply"}

    # Filtrar e selecionar campos necessários
    threads_filtradas = []
    for t in raw_threads:
        if t.get('type') in tipos_permitidos and t.get('body'):
            thread_formatada = {
                "conversation_id": t.get("conversation_id"),
                "conversation_number": t.get("conversation_number"),
                "thread_id": t.get("id"),
                "type": t.get("type"),
                "createdAt": t.get("createdAt"),
                "author": (t.get("createdBy", {}).get("name") or
                           t.get("createdBy", {}).get("email") or
                           "Desconhecido"),
                "body": t.get("body").strip()
            }
            threads_filtradas.append(thread_formatada)
    return threads_filtradas



# Group threads by conversation
from collections import defaultdict

def group_threads(df: pd.DataFrame) -> dict:
    """
    Agrupa mensagens em threads por `conversation_id`, ordenando por data.

    Parâmetros:
        df (pd.DataFrame): DataFrame com colunas 'conversation_id', 'createdAt', 'author', 'normalized'
    
    Retorna:
        dict: {conversation_id: texto_da_conversa_em_ordem_cronológica}
    """
    texto_conversas = {}

    # Verifica se todas as colunas necessárias estão presentes
    required_columns = {'conversation_id', 'createdAt', 'author', 'type', 'normalized'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"DataFrame está faltando colunas: {required_columns - set(df.columns)}")

    # Remove mensagens sem normalização
    df_filtrado = df.dropna(subset=['normalized'])
    df_filtrado = df_filtrado[df_filtrado['normalized'].str.strip() != ""]

    # Agrupa por conversation_id
    grouped = df_filtrado.groupby('conversation_id')

    for conv_id, group in grouped:
        # Ordena por createdAt
        sorted_group = group.sort_values(by='createdAt')

        # Concatena as mensagens normalizadas em ordem cronológica
        msgs = [
            f"{row['author']} em {row['createdAt']} ({row['type']}):\n{row['normalized']}\n"
            for idx, row in sorted_group.iterrows()
        ]
        texto_conversas[conv_id] = "\n".join(msgs).strip()

    return texto_conversas

