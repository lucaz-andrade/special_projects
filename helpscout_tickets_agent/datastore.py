#%%
from helpscout_api import get_conversations_by_tag, get_oauth_token, get_threads_by_tag, flatten_convo, flatten_thread  
import os

# %%
api_id = os.getenv('HP_APP_ID') 
app_secret  = os.getenv('HP_APP_SECRET') 

#%% 
reconciliation_request = get_conversations_by_tag('reconciliation')
threads = get_threads_by_tag('reconciliation')

# %%
def create_conversation_content(convo):
    """
    Generates a descriptive content string for a Help Scout conversation.

    Args:
        convo (dict): A flattened conversation dictionary.

    Returns:
        str: A descriptive string summarizing the conversation.
    """
    content = (
        f"Conversation #{convo.get('number')} is about '{convo.get('subject', 'N/A')}'. "
        f"It was created on {convo.get('created_at', 'N/A')} and last modified on {convo.get('modified_at', 'N/A')}. "
        f"The current status is {convo.get('status', 'N/A')} with a state of {convo.get('state', 'N/A')}. "
        f"It has {convo.get('thread_count', 0)} threads. "
        f"The conversation is with {convo.get('customer_email', 'N/A')} and is assigned to {convo.get('assigned_to_email', 'N/A')}. "
        f"Tags: {convo.get('tags', 'None')}. "
        f"Source: {convo.get('source_type', 'N/A')} via {convo.get('source_via', 'N/A')}."
    )
    return content


def create_thread_content(thread):
    """
    Generates a descriptive content string for a Help Scout thread.

    Args:
        thread (dict): A flattened thread dictionary.

    Returns:
        str: A descriptive string summarizing the thread.
    """
    content = (
        f"Thread ID {thread.get('id')} from conversation #{thread.get('conversation_number')}. "
        f"Type: {thread.get('type', 'N/A')}, Status: {thread.get('status', 'N/A')}. "
        f"Created at: {thread.get('createdAt', 'N/A')}. "
        f"From: {thread.get('customer_email', 'N/A')}, To: {thread.get('to', 'N/A')}. "
        f"Assigned to: {thread.get('assignedTo_email', 'N/A')}. "
        f"Body: {thread.get('body', '')[:200]}... "  # Truncate body for brevity
        f"Source: {thread.get('source_type', 'N/A')} via {thread.get('source_via', 'N/A')}."
    )
    return content 



# %%
# Vector Database

from chromadb import PersistentClient 

client = PersistentClient(path="./chroma")

convo_collection = client.get_or_create_collection(name="convo-helpscout") 
thread_collection = client.get_or_create_collection(name="thread-helpscout") 

# Text Embedding

from sentence_transformers import SentenceTransformer 

model = SentenceTransformer('all-MiniLM-L6-v2')
#%% 
# Vector Embedding Storage 
def clean_metadata(metadata):
    """Replaces None values in a dictionary with empty strings for ChromaDB compatibility."""
    return {k: ('' if v is None else v) for k, v in metadata.items()}

# Conversation collection
for convo in reconciliation_request:
    
   # 1. Flatten the conversation object
    metadata = flatten_convo(convo)
    
    # 2. Clean the metadata to remove None values
    cleaned_metadata = clean_metadata(metadata)
    
    # 3. Use the CLEANED metadata to create content and get the ID
    content = create_conversation_content(cleaned_metadata)
    doc_id = str(cleaned_metadata.get('id', ''))
    
    # 4. Encode the content
    conversation_embedding = model.encode(content).tolist()

    # 5. Add to the collection using the cleaned and consistent data
    convo_collection.add(
        embeddings=[conversation_embedding],
        metadatas=[cleaned_metadata],
        ids=[doc_id],
        documents=[content]
    )
#print(f"Stored {len(reconciliation_request)} conversations.")

#%%
#Threads collection 
for thread in threads:
    # 1. Flatten the conversation object
    metadata = flatten_thread(thread)
    
    # 2. Clean the metadata to remove None values
    cleaned_metadata = clean_metadata(metadata)
    # 3. Use the CLEANED metadata to create content and get the ID
    content = create_thread_content(cleaned_metadata)
    doc_id = str(cleaned_metadata.get('id', ''))
    
    # 4. Encode the content
    thread_embedding = model.encode(content).tolist()

    # 5. Add to the collection using the cleaned and consistent data
    thread_collection.add(
        embeddings=[thread_embedding],
        metadatas=[cleaned_metadata],
        ids=[doc_id],
        documents=[content]
    )

#%%
import json
from chromadb import PersistentClient 

client = PersistentClient(path="./chroma")

convo_collection = client.get_collection(name="convo-helpscout") 
thread_collection = client.get_collection(name="thread-helpscout") 
retrieved_threads = thread_collection.get(limit=1)
print("\nRetrieved threads:")
print(json.dumps(retrieved_threads, indent=1))
# %%
