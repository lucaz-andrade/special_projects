#%%  
from typing import List, Dict, Callable 
from lm_studio import llm_call, simple_call
from helpscout_api import get_oauth_token, get_threads_by_tag, get_conversations_by_tag
import requests
import os
from dotenv import load_dotenv
import json

# Load enviroment variables from .env file 
load_dotenv() 

# Load variables 
api_id = os.getenv('HP_APP_ID') 
app_secret  = os.getenv('HP_APP_SECRET')
#%%
# API calls
conversations = get_conversations_by_tag("reconciliation")
threads_list = get_threads_by_tag("reconciliation")
#threads = get_threads_by_tag('reconciliation')
#%%
refine_prompt = (
    """
    Provide the results of doing these two tasks on the chat history provided below for the user {}
    task 1 : assess if the tone is happy = 1 , neutral = 0 or unhappy = -1
    task 2 : summarize the text with a maximum of 512 characters
    Return the answer as a JSON string with fields [sentiment, summary, conversation_id] do NOT explain your answer

    Important: Conversations created by address like '@zamp.com' are not from a customer. 
    You should not consider it in yout sentiment analysis.
    """
    ) 

#%% Conversations 

conversation_response = {"_embedded": {"threads": conversations}}
conversation_list = conversation_response["_embedded"]["threads"] 
formatted_conversation = json.dumps(conversation_response, indent=3)

threads_response = {"_embedded": {"threads": threads_list}}
formatted_threads= json.dumps(threads_response, indent=3)
threads_consolidated = threads_response["_embedded"]["threads"]

# %%
# Access first convo
# first_conversation = conversation_response["_embedded"]["threads"][0]
# formatted_first = json.dumps(first_conversation, indent=3)

# first_convo_summary =  simple_call(formatted_first , refine_prompt)
#%% 
#Filter threads by specific conversation_id
conversation_id = 2965626701
filtered_threads = [thread for thread in threads_consolidated if thread.get('conversation_id') == conversation_id]
# formatted_threads = json.dumps(filtered_threads, indent=2)
# thread_summary = simple_call(formatted_threads, refine_prompt)

#%%
def chunk_conversations(thread: list, max_chars: int = 3500) -> list:
    """Split conversations into smaller chunks"""
    chunks = []
    current_chunk = []
    current_size = 0
    
    for conv in thread:
        conv_str = json.dumps(conv)
        if current_size + len(conv_str) > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [conv]
            current_size = len(conv_str)
        else:
            current_chunk.append(conv)
            current_size += len(conv_str)
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Process in chunks
conversation_chunks = chunk_conversations(filtered_threads, 3500)
results = []

for i, chunk in enumerate(conversation_chunks):
    print(f"Processing chunk {i+1}/{len(conversation_chunks)}")
    chunk_response = {"_embedded": {"threads": chunk}}
    formatted_chunk = json.dumps(chunk_response, indent=3)
    
    result = simple_call(formatted_chunk, refine_prompt)
    if result:
        results.append(result)


# %%
print(results)
# %%
# def summarize_thread_by_id(thread: list, conversation_id: int) -> str:
#     """Summarize conversation threads by processing each thread ID separately"""
    
#     # Filter threads for specific conversation
#     conversation_threads = [
#         thread for thread in threads_list 
#         if thread.get('conversation_id') == conversation_id
#     ]
    
#     # Sort threads by created date to maintain conversation flow
#     conversation_threads.sort(key=lambda x: x.get('createdAt', ''))
    
#     # Process each thread individually
#     thread_summaries = []
#     for thread in conversation_threads:
#         # Extract key information
#         thread_data = {
#             "id": thread.get("id"),
#             "type": thread.get("type"),
#             "createdAt": thread.get("createdAt"),
#             "subject": thread.get("subject"),
#             "body": thread.get("body"),
#             "customer": thread.get("customer"),
#             "status": thread.get("status")
#         }
        
#         # Process individual thread
#         formatted_thread = json.dumps(thread_data, indent=2)
#         summary = simple_call(formatted_thread, refine_prompt)
#         if summary:
#             thread_summaries.append(summary)
    
#     return "\n\n---\n\n".join(thread_summaries)

# # Use the new function
# conversation_id = 2965626701
# thread_summary = summarize_thread_by_id(threads_list, conversation_id)
# print(thread_summary)