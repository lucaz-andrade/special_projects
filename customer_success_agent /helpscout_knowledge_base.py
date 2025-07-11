#%%
import requests

# def get_all_helpscout_articles(api_key):
#     """
#     Retrieve all articles from the HelpScout Knowledge Base (Docs API v1).
#     Returns a list of article objects.
#     """
#     base_url = "https://docsapi.helpscout.net/v1/articles"
#     headers = {
#         "Accept": "application/json"
#     }
#     auth = (api_key, "X")  # API key as username, 'X' as dummy password

#     articles = []
#     page = 1

#     while True:
#         params = {"page": page}
#         response = requests.get(base_url, headers=headers, auth=auth, params=params)
#         if response.status_code != 200:
#             raise Exception(f"API request failed: {response.status_code} {response.text}")

#         data = response.json()
#         articles.extend(data.get("articles", []))

#         if not data.get("page", {}).get("hasNextPage", False):
#             break
#         page += 1

#     return articles

def get_all_collections(api_key):
    """
    Retrieve all collections from the HelpScout Knowledge Base.
    """
    base_url = "https://docsapi.helpscout.net/v1/collections"
    headers = {"Accept": "application/json"}
    auth = (api_key, "X")

    collections = []
    page = 1
    while True:
        params = {"page": page}
        response = requests.get(base_url, headers=headers, auth=auth, params=params)
        if response.status_code != 200:
            raise Exception(f"API request failed to get collections: {response.status_code} {response.text}")
        
        data = response.json()
        collections.extend(data.get("collections", {}).get("items", []))

        if not data.get("collections", {}).get("hasNextPage", False):
            break
        page += 1
    return collections
#%% 
import os
from dotenv import load_dotenv
# Load enviroment variables from .env file 
load_dotenv() 

# Load variables 
api_key = os.getenv('HP_API_KEY')

collections = get_all_collections(api_key)
#%%
#articles_list = get_all_helpscout_articles(api_key)
# %%
