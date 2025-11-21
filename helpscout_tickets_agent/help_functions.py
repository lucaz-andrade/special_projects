import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_id = os.getenv('HP_APP_ID')
app_secret = os.getenv('HP_APP_SECRET')

# =============================================================================
# SESSION WITH RETRY
# =============================================================================

def create_session_with_retries():
    """Creates a requests.Session with retry logic for handling transient errors."""
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Global session object to reuse connections and retry logic
session = create_session_with_retries()

# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_oauth_token():
    """Gets OAuth access token using app credentials."""
    token_url = "https://api.helpscout.net/v2/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": api_id,
        "client_secret": app_secret
    }
    try:
        response = session.post(token_url, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting token: {e}")
        return None

# =============================================================================
# DATA RETRIEVAL
# =============================================================================

def get_conversations_by_tag(tag_name):
    """Gets conversations with a specific tag using OAuth."""
    token = get_oauth_token()
    if not token:
        return None

    url = "https://api.helpscout.net/v2/conversations"
    params = {
        "query": f'tag:"{tag_name}" AND createdAt:[2025-10-01T00:00:00Z TO 2025-10-05T00:00:00Z]',
        "status": "closed",
        "pageSize": 50,
        "page": 1
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_conversations = []
    while True:
        try:
            response = session.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            all_conversations.extend(conversations)
            if '_links' in data and 'next' in data['_links']:
                params['page'] += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch conversations for tag '{tag_name}': {e}")
            break
    
    print(f"Retrieved {len(all_conversations)} total conversations for tag '{tag_name}'")
    return all_conversations
def get_conversations_by_tag(tag_name):
    """Gets conversations with a specific tag using OAuth."""
    token = get_oauth_token()
    if not token:
        return None

    url = "https://api.helpscout.net/v2/conversations"
    params = {
        "query": f'tag:"{tag_name}" AND createdAt:[2025-10-01T00:00:00Z TO 2025-10-05T00:00:00Z]',
        "status": "closed",
        "pageSize": 50,
        "page": 1
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_conversations = []
    while True:
        try:
            response = session.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            all_conversations.extend(conversations)
            if '_links' in data and 'next' in data['_links']:
                params['page'] += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch conversations for tag '{tag_name}': {e}")
            break
    
    print(f"Retrieved {len(all_conversations)} total conversations for tag '{tag_name}'")
    return all_conversations

def get_conversations_by_inbox(mailboxId):
    """Gets conversations with a specific tag using OAuth."""
    token = get_oauth_token()
    if not token:
        return None

    url = "https://api.helpscout.net/v2/conversations"
    params = {
        "query": 'createdAt:[2025-01-01T00:00:00Z TO 2025-02-01T00:00:00Z]',
        "mailbox": mailboxId,
        "status": "closed",
        "pageSize": 50,
        "page": 1
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    all_conversations = []
    page = 1
    #max_pages = 100  # Safety limit to prevent infinite loops
    
    #while page <= max_pages:
    while True:
        params['page'] = page
        print(f"Fetching conversations page {page} for mailbox ID {mailboxId}...", end=' ', flush=True)
        try:
            response = session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            all_conversations.extend(conversations)
            print(f"✓ Got {len(conversations)} conversations (total: {len(all_conversations)})")
            
            if '_links' in data and 'next' in data['_links']:
                page += 1
            else:
                print("✓ Reached last page")
                break
        except requests.exceptions.Timeout:
            print(f"\n⚠️  Timeout on page {page}, retrying...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Failed to fetch conversations for mailbox ID '{mailboxId}': {e}")
            break
    
    print(f"Retrieved {len(all_conversations)} total conversations for mailbox ID '{mailboxId}'")
    return all_conversations

def get_threads_by_tag(tag_name):
    """Gets all threads from conversations with a specific tag name."""
    token = get_oauth_token()
    if not token:
        return []

    base_url = "https://api.helpscout.net/v2"
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{base_url}/conversations"
    params = {
       "query": f'tag:"{tag_name}" AND createdAt:[2025-10-01T00:00:00Z TO 2025-10-05T00:00:00Z]',
        "status": "all",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []
    page = 1
    while True:
        params['page'] = page
        try:
            response = session.get(conversations_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            
            for conv in conversations:
                conv_id = conv.get('id')
                conv_number = conv.get('number')
                threads_url = f"{base_url}/conversations/{conv_id}/threads"
                try:
                    thread_resp = session.get(threads_url, headers=headers)
                    thread_resp.raise_for_status()
                    threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                    for thread in threads_data:
                        thread['conversation_id'] = conv_id
                        thread['conversation_number'] = conv_number
                    all_threads.extend(threads_data)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch threads for conversation {conv_id}: {e}")

            if '_links' in data and 'next' in data['_links']:
                page += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch conversations page {page} for tag '{tag_name}': {e}")
            break
    
    print(f"Retrieved {len(all_threads)} total threads for tag '{tag_name}'")
    return all_threads

def get_threads_by_assigned_to_first_name(first_name):
    """
    Gets all threads from conversations assigned to a user with the given first name.
    Since HelpScout API does not filter by first name directly, 
    we fetch conversations with assignments, then filter by assignee first name locally.
    """
    token = get_oauth_token()
    if not token:
        print("Failed to get OAuth token.")
        return []

    base_url = "https://api.helpscout.net/v2"
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{base_url}/conversations"
    
    params = {
        "query": 'assigned_to:[*] TO [*]',
        "status": "all",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []
    page = 1
    while True:
        params['page'] = page
        print(f"Fetching conversations page {page}...")
        try:
            response = session.get(conversations_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            print(f"Page {page}: fetched {len(conversations)} conversations")

            filtered_conversations = [
                conv for conv in conversations 
                if conv.get('assignee') and conv['assignee'].get('firstName', '').lower() == first_name.lower()
            ]
            print(f"Page {page}: found {len(filtered_conversations)} conversations assigned to '{first_name}'")

            for conv in filtered_conversations:
                conv_id = conv.get('id')
                conv_number = conv.get('number')
                threads_url = f"{base_url}/conversations/{conv_id}/threads"
                try:
                    thread_resp = session.get(threads_url, headers=headers)
                    thread_resp.raise_for_status()
                    threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                    for thread in threads_data:
                        thread['conversation_id'] = conv_id
                        thread['conversation_number'] = conv_number
                    all_threads.extend(threads_data)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch threads for conversation {conv_id}: {e}")

            if '_links' in data and 'next' in data['_links']:
                page += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch conversations page {page}: {e}")
            break

    print(f"Retrieved {len(all_threads)} total threads for conversations assigned to '{first_name}'")
    return all_threads

def get_threads_by_assigned_id(assigned_user_id):
    """
    Gets all threads from conversations assigned to a specific user ID.
    """
    token = get_oauth_token()
    if not token:
        print("Failed to get OAuth token.")
        return []

    base_url = "https://api.helpscout.net/v2"
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{base_url}/conversations"
    
    params = {
        "query": 'createdAt:[2025-01-01T00:00:00Z TO *]',
        "assigned_to": assigned_user_id,
        "status": "all",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []
    page = 1
    while True:
        params['page'] = page
        print(f"Fetching conversations page {page} for user ID {assigned_user_id}...")
        try:
            response = session.get(conversations_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            print(f"Page {page}: fetched {len(conversations)} conversations")

            for conv in conversations:
                conv_id = conv.get('id')
                conv_number = conv.get('number')

                threads_url = f"{base_url}/conversations/{conv_id}/threads"
                try:
                    thread_resp = session.get(threads_url, headers=headers)
                    thread_resp.raise_for_status()
                    threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                    for thread in threads_data:
                        thread['conversation_id'] = conv_id
                        thread['conversation_number'] = conv_number
                    all_threads.extend(threads_data)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch threads for conversation {conv_id}: {e}")

            if '_links' in data and 'next' in data['_links']:
                page += 1
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch conversations page {page}: {e}")
            break

    print(f"Retrieved {len(all_threads)} total threads assigned to user ID '{assigned_user_id}'")
    return all_threads

def get_threads_by_inbox(mailboxId):
    """
    Gets all threads from conversations assigned to a specific user ID.
    """
    token = get_oauth_token()
    if not token:
        print("Failed to get OAuth token.")
        return []

    base_url = "https://api.helpscout.net/v2"
    headers = {"Authorization": f"Bearer {token}"}
    conversations_url = f"{base_url}/conversations"
    
    params = {
       "query": 'createdAt:[2025-01-01T00:00:00Z TO 2025-02-01T00:00:00Z]',
        "mailbox": mailboxId,
        "status": "closed",
        "pageSize": 50,
        "page": 1
    }
    
    all_threads = []
    page = 1
    max_pages = 100  # Safety limit
    
    while page <= max_pages:
        params['page'] = page
        print(f"\nFetching conversations page {page} for mailbox ID {mailboxId}...", flush=True)
        try:
            response = session.get(conversations_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            conversations = data.get('_embedded', {}).get('conversations', [])
            print(f"  ✓ Got {len(conversations)} conversations, fetching threads...", flush=True)

            for idx, conv in enumerate(conversations, 1):
                conv_id = conv.get('id')
                conv_number = conv.get('number')
                print(f"    [{idx}/{len(conversations)}] Conv #{conv_number} (ID: {conv_id})...", end=' ', flush=True)

                threads_url = f"{base_url}/conversations/{conv_id}/threads"
                try:
                    thread_resp = session.get(threads_url, headers=headers, timeout=30)
                    thread_resp.raise_for_status()
                    threads_data = thread_resp.json().get('_embedded', {}).get('threads', [])
                    for thread in threads_data:
                        thread['conversation_id'] = conv_id
                        thread['conversation_number'] = conv_number
                    all_threads.extend(threads_data)
                    print(f"✓ {len(threads_data)} threads")
                except requests.exceptions.Timeout:
                    print(f"⚠️  Timeout, skipping")
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error: {e}")

            if '_links' in data and 'next' in data['_links']:
                page += 1
            else:
                print("\n✓ Reached last page")
                break
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout on page {page}, retrying...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Failed to fetch conversations page {page}: {e}")
            break

    print(f"Retrieved {len(all_threads)} total threads assigned to mailbox ID '{mailboxId}'")
    return all_threads

# =============================================================================
# DATA PROCESSING
# =============================================================================

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

def extract_tags(tags_data):
    """
    Extracts tag names from the 'tags' column which contains a list of dicts.
    Example input: [{'id': 123, 'tag': 'example'}]
    Example output: ['example']
    """
    if isinstance(tags_data, list):
        return [tag.get('tag') for tag in tags_data if isinstance(tag, dict) and 'tag' in tag]
    return []