#%%
from typing import List, Dict, Callable 
from lm_studio import llm_call, simple_call
#from helpscout_api import get_oauth_token, get_threads_by_tag, get_conversations_by_tag
import requests
import os
#from dotenv import load_dotenv
import json

#%% 
recon_prompt = """
    Você é um assistente de análise de dados responsável por gerar relatórios executivos claros, objetivos e bem resumidos. Receberá como entrada os seguintes dados de duas fontes:
        •	Número de linhas em cada fonte
        •	Número de transações em comum
        •	Número de transações ausentes (missing) em cada fonte
        •	Total de uma variável específica em cada fonte
    Sua tarefa é criar um texto sumarizando os principais resultados da análise comparativa, destacando similaridades, diferenças e possíveis implicações, em linguagem clara e acessível para gestores. Não inclua detalhes técnicos ou cálculos intermediários, apenas os resultados mais relevantes.
    
    Exemplo de Prompt:
    Você receberá um input como este:
        "file_details": 
            "zamp_rows": 3479,
            "shopify_rows": 13058,
            "zamp_order_level_rows": 3162,
            "shopify_order_level_rows": 2971,
            "zamp_order_level_tax_total": 34434.15,
            "shopify_order_level_tax_total": 17948.36,
            "zamp_order_level_transaction_total": 539106.16,
            "shopify_order_level_transaction_total": 0.0,
            "tax_difference": 16485.79,
            "matching_orders": 3125,
            "missing_from_shopify": 37,
            "missing_from_zamp": 4,
            "matching_shopify_tax": 17813.06,
            "matching_zamp_tax": 34818.36,
            "matching_tax_difference": 17005.3
        "state_differences": 
                {
            "state": "AZ",
            "zamp_tax": 1253.47,
            "shopify_tax": 802.63,
            "absolute_difference": 450.8,
            "percentage_difference": 36.0
            },
            {
            "state": "CA",
            "zamp_tax": 11570.04,
            "shopify_tax": 8323.81,
            "absolute_difference": 3246.2,
            "percentage_difference": 28.1
            },
            {
            "state": "CO",
            "zamp_tax": 1593.19,
            "shopify_tax": 988.07,
            "absolute_difference": 605.1,
            "percentage_difference": 38.0
            {
            "state": "AR",
            "zamp_tax": 0.0,
            "shopify_tax": 0.0,
            "absolute_difference": 0.0,
            "percentage_difference": null
            },
        "loop_transactions_state_diff": [
            {
            "state": "AL",
            "zamp_tax": 0.0,
            "shopify_tax": 0.0,
            "absolute_difference": 0.0,
            "percentage_difference": null
            },
            {
            "state": "AZ",
            "zamp_tax": 0.0,
            "shopify_tax": 89.17,
            "absolute_difference": 0.0,
            "percentage_difference": null
            },
            {
            "state": "CA",
            "zamp_tax": 0.0,
            "shopify_tax": 451.89,
            "absolute_difference": 0.0,
            "percentage_difference": null
            },
        "order_edited_df": null
    Gere um texto como este:
		“A análise compara duas fontes de dados e revela alta similaridade, com 3.125 transações em comum. 
        Foram identificadas 37 transações presentes apenas na Zamp e 4 apenas na Shopify.
        O valor total de impostos na Zamp é de $34.434,15 e, na Shopify, $17.948,36, resultando em uma diferença de 
        $16.485,79. Os estados com maior impacto nessa diferença são:
            •	CA: diferença de $3.246,20
            •	CO: diferença de $605,10
            •	AZ: diferença de $450,80
        A diferença pode estar relacionada ao uso de um aplicativo de terceiros que afeta a comunicação entre Shopify 
        e Zamp. Transações impactadas pelo Loop Exchange, por exemplo, geraram diferenças nos valores de impostos 
        reportados. Em CA e AZ, essas diferenças foram de $451,89 e $89,17, respectivamente.
        Não encontrei evidencias do uso de Order Editing app ou qualquer outra forma de edição de transacoes que pudesse 
        causar outras diferenças no valor de taxas reportadas"

    Instruções
        •	Seja conciso e objetivo (máximo de 4 frases).
        •	Destaque sempre: similaridade, diferenças e possíveis implicações.
        •	Não utilize linguagem técnica ou termos estatísticos avançados.
        •	O texto deve ser adequado para um relatório executivo.
"""
#%% 
with open('/Users/strider/Zamp/GitHub/special_projects/reduced-reconciliation.json', 'r') as file:
    recon_file = json.load(file)

# Or Method 2: Using json.loads() if you need to load from string
# with open('/Users/strider/Zamp/GitHub/special_projects/reconciliation.json', 'r') as file:
#     recon_file = json.loads(file.read())

recon_formated = json.dumps(recon_file)
#%%
result = simple_call(recon_formated, recon_prompt)

# %%
print(result)

# %%
