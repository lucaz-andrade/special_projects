#%% # Import libraries
import pandas as pd
import json
import sys
import os

# Add the path to access lm_studio.py
#sys.path.append('/Users/strider/Zamp/GitHub/special_projects/customer_success_agent')
from lm_studio import llm_call

#%% # Summarization function using LM Studio
def summarize_with_lm_studio(text, system_prompt="You are a helpful assistant that summarizes customer support conversations."):
    """
    Summarize text using LM Studio model
    """
    user_prompt = f"""Please provide a concise summary of the following customer support conversation, focusing on:
- Main issue or request
- Key decisions made
- Actions taken or planned
- Current status 

Conversation:
{text}

Summary:"""
    
    try:
        summary = llm_call(user_prompt, system_prompt)
        return summary.strip() if summary else "Unable to generate summary"
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def summarize_conversations(texto_conversas, max_length=2000):
    """
    Recebe dict {conversation_id: texto_completo}, retorna dict {conversation_id: resumo}
    """
    resumos = {}
    total_conversations = len(texto_conversas)
    
    print(f"Starting summarization of {total_conversations} conversations using LM Studio...")
    
    for i, (conv_id, texto) in enumerate(texto_conversas.items(), 1):
        print(f"Processing conversation {i}/{total_conversations} (ID: {conv_id})")
        
        # Truncate if too long
        input_text = texto[:max_length]
        resumo = summarize_with_lm_studio(input_text)
        resumos[conv_id] = resumo
        
        print(f"✓ Completed conversation {conv_id}")
    
    print(f"Summarization complete! Processed {len(resumos)} conversations.")
    return resumos

def summarize_long_conversations_lm_studio(texto_conversas, max_chunk_length=1500):
    """
    Resume conversas longas usando LM Studio, dividindo em chunks se necessário.
    Args:
        texto_conversas (dict): {conversation_id: texto_completo}
        max_chunk_length (int): Maximum characters per chunk
    Returns:
        dict: {conversation_id: resumo}
    """
    resumos = {}
    total_conversations = len(texto_conversas)
    
    print(f"Starting long conversation summarization of {total_conversations} conversations using LM Studio...")
    
    for i, (conv_id, texto) in enumerate(texto_conversas.items(), 1):
        print(f"Processing long conversation {i}/{total_conversations} (ID: {conv_id})")
        
        # If text is short enough, summarize directly
        if len(texto) <= max_chunk_length:
            resumo = summarize_with_lm_studio(texto)
            resumos[conv_id] = resumo
        else:
            # Split into chunks
            chunks = [texto[i:i + max_chunk_length] for i in range(0, len(texto), max_chunk_length)]
            print(f"  Split into {len(chunks)} chunks")
            
            # Summarize each chunk
            partial_summaries = []
            for j, chunk in enumerate(chunks, 1):
                print(f"    Processing chunk {j}/{len(chunks)}")
                try:
                    chunk_summary = summarize_with_lm_studio(chunk)
                    partial_summaries.append(chunk_summary)
                except Exception as e:
                    partial_summaries.append(f"[Error summarizing chunk {j}]: {str(e)}")
            
            # Combine partial summaries
            if len(partial_summaries) > 1:
                combined_text = "\n\n".join(partial_summaries)
                final_prompt = f"""Please create a comprehensive summary by combining these partial summaries of a customer support conversation:

{combined_text}

Provide a unified summary focusing on:
- Actors involved
- Main issue or request
- Key decisions made
- Actions taken or planned
- Current status

Final Summary:"""
                
                try:
                    resumo_final = llm_call(final_prompt, "You are a helpful assistant that creates comprehensive summaries from partial summaries.")
                    resumos[conv_id] = resumo_final.strip() if resumo_final else "Unable to generate final summary"
                except Exception as e:
                    resumos[conv_id] = f"[Error creating final summary]: {str(e)}"
            else:
                resumos[conv_id] = partial_summaries[0] if partial_summaries else "No summary generated"
        
        print(f"✓ Completed long conversation {conv_id}")
    
    print(f"Long conversation summarization complete! Processed {len(resumos)} conversations.")
    return resumos

#%% # Load and process data
if __name__ == "__main__":
    # Load data
    print("Loading conversation data...")
    with open('data/threads_by_convo.csv', 'r') as file:
        threads_by_convo = pd.read_csv(file)

    sample_threads = threads_by_convo
    #sample_threads = threads_by_convo.head(30)
    print(f"Loaded {len(sample_threads)} conversations for processing")
    
    # Create a dictionary from conversation_id to texto_completo
    texto_dict = dict(zip(sample_threads['conversation_id'], sample_threads['texto_completo']))
    
    # Apply summarization using LM Studio
    print("\n" + "="*50)
    print("STARTING SUMMARIZATION WITH LM STUDIO")
    print("="*50)
    
    # Choose between simple or long conversation summarization
    use_long_summarization = True  # Set to False for simple summarization
    
    if use_long_summarization:
        resumos = summarize_long_conversations_lm_studio(texto_dict)
    else:
        resumos = summarize_conversations(texto_dict)
    
    # Add summaries back to the DataFrame as a new column
    threads_by_convo['summary'] = threads_by_convo['conversation_id'].map(resumos)
    
    # Save results
    output_file = 'data/threads_by_convo_with_lm_studio_summaries.csv'
    threads_by_convo.to_csv(output_file, index=False)
    print(f"\n✓ Results saved to {output_file}")
    
    # Display sample results
    print("\n" + "="*50)
    print("SAMPLE RESULTS")
    print("="*50)
    
    for i, (conv_id, summary) in enumerate(list(resumos.items())[:3]):
        print(f"\nConversation {conv_id}:")
        print(f"Summary: {summary}")
        print("-" * 50)
    
    print(f"\n🎉 Summarization complete! {len(resumos)} conversations processed.")
# %%
