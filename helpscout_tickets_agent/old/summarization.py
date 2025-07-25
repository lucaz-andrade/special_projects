#%% # Import libraries
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import pandas as pd
import json
#%% # Load model
model_name = "google/flan-t5-base"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

#%% # Create pipeline
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

#%% # Summarize
def summarize_conversations(texto_conversas, max_length=512, min_length=20):
    """
    Recebe dict {conversation_id: texto_completo}, retorna dict {conversation_id: resumo}
    """
    resumos = {}
    for conv_id, texto in texto_conversas.items():
        # Tratar possíveis limites de tamanho de texto do modelo
        input_text = texto[:2000]  # Trunca se for muito longo
        resumo = summarizer(
            input_text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )[0]['summary_text']
        resumos[conv_id] = resumo
    return resumos

#%% # Load data
with open('data/threads_by_convo.csv', 'r') as file:
    threads_by_convo = pd.read_csv(file)


threads_by_convo = threads_by_convo.head(30)
#%% # Summarize

# Create a dictionary from conversation_id to texto_completo
texto_dict = dict(zip(threads_by_convo['conversation_id'], threads_by_convo['texto_completo']))
#%% # Split text by tokens
def split_text_by_tokens(texto, tokenizer, max_tokens=512):
    """
    Divide um texto em partes de até max_tokens tokens.
    Retorna uma lista de strings (trechos do texto original).
    """
    tokens = tokenizer.encode(texto)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    texts = [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]
    return texts

SUMMARY_PROMPT = (
    "Summarize the following email thread emphasizing the main decisions, actors, issues raised, root causes or hypothesis, and next action steps:\n\n"
)


def summarize_long_conversations(texto_conversas, tokenizer, summarizer,
                                max_input_tokens=512, max_new_tokens=100, min_length=20):
    """
    Resume conversas longas, dividindo em chunks se necessário.
    Args:
        texto_conversas (dict): {conversation_id: texto_completo}
        tokenizer: tokenizer compatível com o modelo Hugging Face
        summarizer: pipeline de sumarização Hugging Face
    Returns:
        dict: {conversation_id: resumo}
    """
    resumos = {}
    for conv_id, texto in texto_conversas.items():
        # 1. Dividir o texto em chunks de até 512 tokens
        chunks = split_text_by_tokens(texto, tokenizer, max_input_tokens)
        # 2. Resumir cada chunk separadamente
        partial_summaries = []
        for chunk in chunks:
            try:
                prompt_chunk = SUMMARY_PROMPT + chunk
                resumo = summarizer(
                    prompt_chunk,
                    max_new_tokens=max_new_tokens,
                    min_length=min_length,
                    do_sample=False
                )[0]['summary_text']
            except Exception as e:
                resumo = f"[Erro ao resumir chunk]: {str(e)}"
            partial_summaries.append(resumo)
        # 3. Se houver vários resumos parciais, resumir esses resumos
        if len(partial_summaries) > 1:
            combined_summary = " ".join(partial_summaries)
            try:
                resumo_final = summarizer(
                    combined_summary,
                    max_new_tokens=max_new_tokens,
                    min_length=min_length,
                    do_sample=False
                )[0]['summary_text']
            except Exception as e:
                resumo_final = f"[Erro ao resumir resumos parciais]: {str(e)}"
            resumos[conv_id] = resumo_final
        else:
            resumos[conv_id] = partial_summaries[0]
    return resumos


# Apply summarization
resumos = summarize_long_conversations(texto_dict, tokenizer, summarizer)
#%%
# Add summaries back to the DataFrame as a new column
threads_by_convo['summary'] = threads_by_convo['conversation_id'].map(resumos)

# Save the result
threads_by_convo.to_csv('data/threads_with_summaries.csv', index=False)
# %%
threads_by_convo.to_csv("data/threads_by_convo.csv", index=True)
# %%
