# %% #Import libraries
from help_functions import threads_prep, group_threads, extract_tags, get_conversations_by_inbox, get_threads_by_inbox
from bs4 import BeautifulSoup
import pandas as pd
#%% #API call
#conversations = get_conversations_by_assigned_id('831957')
#threads = get_threads_by_assigned_id('831957')

# conversations = get_conversations_by_tag('ts-escalation')
# threads = get_threads_by_tag('ts-escalation')

conversations = get_conversations_by_inbox('294254')
threads = get_threads_by_inbox('294254')
#%% 
df_conversations = pd.DataFrame(conversations)

# with open('data/conversations.csv', 'r') as file:
#     df_conversations = pd.read_csv(file)

import ast

# Apply the functions to create the 'tags_list' column
# ast.literal_eval safely converts the string representation of a list back into a list
df_conversations['tags_list'] = df_conversations['tags'].apply(
    lambda x: extract_tags(ast.literal_eval(x)) if isinstance(x, str) else extract_tags(x)
)

df_conversations.to_csv("data/conversations.csv", index=False)

#%%
cleaned_threads = []
for thread in threads:
    # Make a copy to avoid modifying the original data
    cleaned_thread = thread.copy()
    
    # Check if 'body' exists and is not None
    if 'body' in cleaned_thread and cleaned_thread['body']:
        soup = BeautifulSoup(cleaned_thread['body'], 'html.parser')
        cleaned_thread['body'] = soup.get_text(separator=' ', strip=True)
    
    cleaned_threads.append(cleaned_thread)
df_cleaned_threads = pd.DataFrame(cleaned_threads)
df_cleaned_threads.to_csv("data/cleaned_threads.csv", index=False)

#%% #Filter threads by type 

filtered_threads = threads_prep(cleaned_threads)
df_filtered_threads = pd.DataFrame(filtered_threads)
df_filtered_threads.to_csv("data/filtered_threads.csv", index=False)

#%% 
import re
import pandas as pd
import spacy
from tqdm.auto import tqdm

# Carrega modelo spaCy
nlp = spacy.load("en_core_web_sm")  # Altere se estiver usando outro modelo

# ========================
# Funções de pré-processamento
# ========================

def clean_body(text: str) -> str:
    """
    Remove URLs, e-mails, telefones, quebras de linha e espaços extras.
    """
    text = str(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[\w\.-]+@[\w\.-]+", "", text)
    text = re.sub(r"\(?\d{2,3}\)?[\s-]?\d{3,5}[\s-]?\d{4}", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("\n", " ").replace("\r", "")
    return text.strip()


def remove_signature(text: str) -> str:
    """
    Remove assinaturas de e-mail usando padrões e palavras de despedida.
    """
    text = str(text)

    farewell_words = (
        r"best|regards|kind regards|warm regards|sincerely|thanks|thank you|cheers|respectfully|"
        r"yours truly|yours sincerely|yours faithfully|take care|atenciosamente|obrigado|agradeço|abs"
    )
    common_titles = (
        r"manager|analyst|engineer|developer|designer|director|ceo|cto|founder|consultant|"
        r"coordinator|president|gerente|assistant|controller|accountant"
    )

    # Regex: linha de despedida seguida por cargo e até duas linhas adicionais
    pattern = (
        rf"(?i)(?:^|\n)[ \t]*({farewell_words})[^\n]*\n"
        rf"(?:.*({common_titles}).*\n*){{0,3}}"
    )

    text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    return text.strip()


def spacy_normalize(text: str) -> str:
    """
    Lematiza e remove pontuação e stopwords usando spaCy.
    """
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_punct and not token.is_stop]
    return " ".join(tokens)


# ========================
# Pipeline para DataFrame com mensagens
# ========================

def process_message_row(row):
    """
    Aplica limpeza e normalização para um registro com campo 'body'.
    Retorna apenas a versão normalizada.
    """
    try:
        body = str(row['body'])
        no_sig = remove_signature(body)
        clean = clean_body(no_sig)
        norm = spacy_normalize(clean)
        return norm
    except Exception:
        return ""


def process_df_messages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica o pipeline a todo o DataFrame.
    Retorna DataFrame com nova coluna 'normalized'.
    """
    tqdm.pandas(desc="Normalizando mensagens")
    df['normalized'] = df.progress_apply(process_message_row, axis=1)
    return df

#%%
# Aplica pipeline e armazena apenas o texto normalizado de cada thread
#filtered_threads['thread_normalizada'] = filtered_threads['body'].apply(process_df_messages)

treated_threads = process_df_messages(df_filtered_threads)
treated_threads.to_csv("data/treated_threads.csv", index=True)

#%% #Group threads per conversation 

threads_by_convo = group_threads(treated_threads)
#%%
df_threads_by_convo = pd.DataFrame([
    {"conversation_id": conv_id, "texto_completo": texto}
    for conv_id, texto in threads_by_convo.items()
])
df_threads_by_convo.to_csv("data/threads_by_convo.csv", index=True)
# %%
