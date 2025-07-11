#%%
import requests
import os
from dotenv import load_dotenv
import pandas as pd


# Load enviroment variables from .env file 
load_dotenv() 

# Load variables 
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


# Create function to convert conversation info result to a dataframe (similar to HP report)
def conversations_to_dataframe(conversations):
    """
    Transforms Help Scout conversations data into a pandas DataFrame
    
    Args:
        conversations (dict): The JSON response from Help Scout API
    """
    if not conversations:
        return pd.DataFrame()
        
    conversation_list = conversations.get('_embedded', {}).get('conversations', [])
    
    if not conversation_list:
        return pd.DataFrame()
    
    data = []
    for conv in conversation_list:
        # Safely extract tags
        tags = conv.get('tags', [])
        tag_names = []
        for tag in tags:
            if isinstance(tag, dict) and 'name' in tag:
                tag_names.append(tag['name'])
        
        row = {
            'id': conv.get('id', ''),
            'subject': conv.get('subject', ''),
            'status': conv.get('status', ''),
            'mailbox_id': conv.get('mailboxId', ''),
            'created_at': conv.get('createdAt', ''),
            'modified_at': conv.get('modifiedAt', ''),
            'tags': ', '.join(tag_names),  # Using the safely extracted tag names
            'assigned_to': conv.get('assignee', {}).get('email', ''),
            'customer_email': conv.get('customer', {}).get('email', '')
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Convert date columns to datetime
    date_columns = ['created_at', 'modified_at']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    
    return df
#%% 
# Create fucntions to convert threads result to dataframe
def flatten_convo(convo):
    """
    Flattens a single Help Scout conversation dictionary into a flat dict.
    """
    # Helper to safely extract nested fields
    def get(d, keys, default=None):
        for key in keys:
            if not isinstance(d, dict):
                return default
            d = d.get(key)
            if d is None:
                return default
        return d or default


    # Safely extract tags
    tags = convo.get('tags', [])
    tag_names = []
    for tag in tags:
        if isinstance(tag, dict) and 'name' in tag:
            tag_names.append(tag['name'])

    return {
        "id": convo.get("id"),
        "number": convo.get("number"),
        "subject": convo.get("subject"),
        "status": convo.get("status"),
        "state": convo.get("state"),
        "mailbox_id": convo.get("mailboxId"),
        "created_at": convo.get("createdAt"),
        "modified_at": convo.get("modifiedAt"),
        "tags": ', '.join(tag_names),
        "customer_id": get(convo, ["customer", "id"]),
        "customer_first": get(convo, ["customer", "first"]),
        "customer_last": get(convo, ["customer", "last"]),
        "customer_email": get(convo, ["customer", "email"]),
        "assigned_to_id": get(convo, ["assignee", "id"]),
        "assigned_to_first": get(convo, ["assignee", "first"]),
        "assigned_to_last": get(convo, ["assignee", "last"]),
        "assigned_to_email": get(convo, ["assignee", "email"]),
        "closed_by_id": get(convo, ["closedBy", "id"]),
        "closed_by_first": get(convo, ["closedBy", "first"]),
        "closed_by_last": get(convo, ["closedBy", "last"]),
        "closed_by_email": get(convo, ["closedBy", "email"]),
        "closed_at": convo.get("closedAt"),
        "source_type": get(convo, ["source", "type"]),
        "source_via": get(convo, ["source", "via"]),
        "thread_count": convo.get("threadCount"),
        "folder_id": convo.get("folderId"),
        "is_draft": convo.get("isDraft"),
        "is_spam": convo.get("isSpam"),
        "is_auto_reply": convo.get("isAutoReply"),
    }
def flatten_thread(thread):
    # Helper to safely extract nested fields
    def get(d, keys, default=None):
        for key in keys:
            if not isinstance(d, dict):
                return default
            d = d.get(key)
            if d is None:
                return default
        return d or default

    return {
        "id": thread.get("id"),
        "conversation_id": thread.get("conversation_id"),  # <-- add this
        "conversation_number": thread.get("conversation_number"),  # <-- add this
        "type": thread.get("type"),
        "status": thread.get("status"),
        "state": thread.get("state"),
        "body": thread.get("body"),
        "source_type": get(thread, ["source", "type"]),
        "source_via": get(thread, ["source", "via"]),
        "customer_id": get(thread, ["customer", "id"]),
        "customer_first": get(thread, ["customer", "first"]),
        "customer_last": get(thread, ["customer", "last"]),
        "customer_email": get(thread, ["customer", "email"]),
        "assignedTo_id": get(thread, ["assignedTo", "id"]),
        "assignedTo_first": get(thread, ["assignedTo", "first"]),
        "assignedTo_last": get(thread, ["assignedTo", "last"]),
        "assignedTo_email": get(thread, ["assignedTo", "email"]),
        "createdAt": thread.get("createdAt"),
        "openedAt": thread.get("openedAt"),
        "savedReplyId": thread.get("savedReplyId"),
        "to": ', '.join(thread.get("to", [])),
        "cc": ', '.join(thread.get("cc", [])),
        "bcc": ', '.join(thread.get("bcc", [])),
        "rating": get(thread, ["rating", "rating"]),
        "rating_comments": get(thread, ["rating", "comments"]),
        "scheduledBy": get(thread, ["scheduled", "scheduledBy"]),
        "scheduled_createdAt": get(thread, ["scheduled", "createdAt"]),
        "scheduled_scheduledFor": get(thread, ["scheduled", "scheduledFor"]),
        "scheduled_unscheduleOnCustomerReply": get(thread, ["scheduled", "unscheduleOnCustomerReply"]),
        # First attachment info if present
        "attachment_id": get(thread, ["_embedded", "attachments"], [{}])[0].get("id") if get(thread, ["_embedded", "attachments"]) else None,
        "attachment_filename": get(thread, ["_embedded", "attachments"], [{}])[0].get("filename") if get(thread, ["_embedded", "attachments"]) else None,
        "attachment_mimeType": get(thread, ["_embedded", "attachments"], [{}])[0].get("mimeType") if get(thread, ["_embedded", "attachments"]) else None,
        "attachment_size": get(thread, ["_embedded", "attachments"], [{}])[0].get("size") if get(thread, ["_embedded", "attachments"]) else None,
    }

def json_to_dataframe(json_data):
    threads = json_data.get("_embedded", {}).get("threads", [])
    records = [flatten_thread(thread) for thread in threads]
    return pd.DataFrame(records)