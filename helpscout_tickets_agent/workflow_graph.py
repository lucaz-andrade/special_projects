
#%% 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "helpscout_tickets_agent"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Get API key from environment (make sure to set LANGCHAIN_API_KEY in your .env file)
if "LANGCHAIN_API_KEY" not in os.environ:
    print("⚠️  Warning: LANGCHAIN_API_KEY not found in environment variables.")
    print("   LangSmith tracing will not work without it.")
    print("   Add LANGCHAIN_API_KEY=your_api_key to your .env file")
else:
    print("✓ LangSmith tracing enabled")
    print(f"  Project: {os.environ['LANGCHAIN_PROJECT']}")


#%%
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from IPython.display import Image, display


# Define the state structure
class GraphState(TypedDict):
    # ETL outputs
    conversations_df: object  # pandas DataFrame
    threads_by_convo: dict  # {conversation_id: texto_completo}
    
    # Summarization outputs
    summaries: dict  # {conversation_id: summary}
    
    # Tagging outputs
    tagged_conversations_df: object  # pandas DataFrame with tags
    
    # Metadata
    tag_definitions: dict
    total_conversations: int
    status: str


# Import required modules
import pandas as pd
import sys
import os
from help_functions import (
    threads_prep, group_threads, get_conversations_by_inbox, get_threads_by_inbox, extract_tags
)
from bs4 import BeautifulSoup
import ast
import re
import spacy
from tqdm.auto import tqdm
from lm_studio import llm_call

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# ========================
# Node Functions
# ========================

def etl_node(state: GraphState) -> GraphState:
    """
    ETL Node: Extract, Transform, Load data from HelpScout API.
    Processes conversations and threads, cleans and normalizes text.
    """
    print("\n" + "="*50)
    print("ETL NODE: Starting data extraction and processing")
    print("="*50)
    
    # Get conversations and threads from API
    print("Fetching data from HelpScout API...")
    mailbox_id = '294254'  # Same mailbox ID as etl.py
    conversations = get_conversations_by_inbox(mailbox_id)
    threads = get_threads_by_inbox(mailbox_id)
    
    # Process conversations
    df_conversations = pd.DataFrame(conversations)
    df_conversations['tags_list'] = df_conversations['tags'].apply(
        lambda x: extract_tags(ast.literal_eval(x)) if isinstance(x, str) else extract_tags(x)
    )
    
    # Clean threads HTML
    cleaned_threads = []
    for thread in threads:
        cleaned_thread = thread.copy()
        if 'body' in cleaned_thread and cleaned_thread['body']:
            soup = BeautifulSoup(cleaned_thread['body'], 'html.parser')
            cleaned_thread['body'] = soup.get_text(separator=' ', strip=True)
        cleaned_threads.append(cleaned_thread)
    
    # Filter threads
    filtered_threads = threads_prep(cleaned_threads)
    df_filtered_threads = pd.DataFrame(filtered_threads)
    
    # Normalize text
    print("Normalizing text...")
    df_filtered_threads['normalized'] = df_filtered_threads.apply(
        lambda row: process_message_row(row), axis=1
    )
    
    # Group threads by conversation
    threads_by_convo = group_threads(df_filtered_threads)
    
    print(f"✓ ETL complete: {len(threads_by_convo)} conversations processed")
    
    return {
        **state,
        "conversations_df": df_conversations,
        "threads_by_convo": threads_by_convo,
        "total_conversations": len(threads_by_convo),
        "status": "etl_complete"
    }


def process_message_row(row):
    """Helper function to clean and normalize message text."""
    try:
        body = str(row['body'])
        no_sig = remove_signature(body)
        clean = clean_body(no_sig)
        norm = spacy_normalize(clean)
        return norm
    except Exception:
        return ""


def clean_body(text: str) -> str:
    """Remove URLs, emails, phones, line breaks and extra spaces."""
    text = str(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[\w\.-]+@[\w\.-]+", "", text)
    text = re.sub(r"\(?\d{2,3}\)?[\s-]?\d{3,5}[\s-]?\d{4}", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("\n", " ").replace("\r", "")
    return text.strip()


def remove_signature(text: str) -> str:
    """Remove email signatures using patterns and farewell words."""
    text = str(text)
    farewell_words = (
        r"best|regards|kind regards|warm regards|sincerely|thanks|thank you|cheers|respectfully|"
        r"yours truly|yours sincerely|yours faithfully|take care|atenciosamente|obrigado|agradeço|abs"
    )
    common_titles = (
        r"manager|analyst|engineer|developer|designer|director|ceo|cto|founder|consultant|"
        r"coordinator|president|gerente|assistant|controller|accountant"
    )
    pattern = (
        rf"(?i)(?:^|\n)[ \t]*({farewell_words})[^\n]*\n"
        rf"(?:.*({common_titles}).*\n*){{0,3}}"
    )
    text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    return text.strip()


def spacy_normalize(text: str) -> str:
    """Lemmatize and remove punctuation and stopwords using spaCy."""
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_punct and not token.is_stop]
    return " ".join(tokens)


def summarize_node(state: GraphState) -> GraphState:
    """
    Adaptive Summarization Node.
    Evaluates each conversation individually and applies the appropriate strategy:
    - SHORT: Direct summarization for texts <= 2000 characters
    - LONG: Chunking + recombination for texts > 2000 characters
    """
    print("\n" + "="*50)
    print("SUMMARIZATION NODE: Starting adaptive summarization")
    print("="*50)
    
    threads = state["threads_by_convo"]
    summaries = {}
    threshold = 2000
    
    # Statistics
    short_count = 0
    long_count = 0
    
    for i, (conv_id, texto) in enumerate(threads.items(), 1):
        text_length = len(texto)
        print(f"Processing {i}/{len(threads)} (ID: {conv_id}, length: {text_length} chars)")
        
        # Individual decision per conversation
        if text_length <= threshold:
            # SHORT strategy: direct summarization
            print(f"  → Using SHORT strategy")
            summary = summarize_llm_call(texto)
            summaries[conv_id] = summary
            short_count += 1
        else:
            # LONG strategy: chunking + recombination
            print(f"  → Using LONG strategy")
            chunks = [texto[i:i + threshold] for i in range(0, len(texto), threshold)]
            print(f"  Split into {len(chunks)} chunks")
            
            # Summarize each chunk
            partial_summaries = []
            for j, chunk in enumerate(chunks, 1):
                print(f"    Processing chunk {j}/{len(chunks)}")
                chunk_summary = summarize_llm_call(chunk)
                partial_summaries.append(chunk_summary)
            
            # Combine partial summaries if needed
            if len(partial_summaries) > 1:
                combined_text = "\n\n".join(partial_summaries)
                final_prompt = f"""Create a comprehensive summary by combining these partial summaries:

{combined_text}

Provide a unified summary focusing on:
- Main issue or request
- Key decisions made
- Actions taken or planned
- Current status

Final Summary:"""
                
                summary = llm_call(final_prompt, "You are a helpful assistant that creates comprehensive summaries.")
                summaries[conv_id] = summary.strip() if summary else "Unable to generate summary"
            else:
                summaries[conv_id] = partial_summaries[0]
            
            long_count += 1
        
        print(f"✓ Completed conversation {conv_id}")
    
    print(f"\n✓ Summarization complete: {len(summaries)} summaries generated")
    print(f"  - SHORT strategy: {short_count} conversations")
    print(f"  - LONG strategy: {long_count} conversations")
    
    return {
        **state,
        "summaries": summaries,
        "status": "summarization_complete"
    }


def summarize_llm_call(text, system_prompt="You are a helpful assistant that summarizes customer support conversations."):
    """Summarize text using Ollama LLM."""
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


def tagging_node(state: GraphState) -> GraphState:
    """
    Tagging Node: Assigns tags to conversations based on content and summary.
    """
    print("\n" + "="*50)
    print("TAGGING NODE: Starting tag assignment")
    print("="*50)
    
    # Load tag definitions
    tags_excel_path = 'support_files/Help Scout tags.xlsx'
    tag_definitions = load_tag_definitions(tags_excel_path)
    
    if not tag_definitions:
        print("Warning: No tag definitions found")
        tag_definitions = {}
    
    # Create DataFrame with summaries
    threads = state["threads_by_convo"]
    summaries = state["summaries"]
    
    df_results = pd.DataFrame([
        {
            "conversation_id": conv_id,
            "texto_completo": threads[conv_id],
            "summary": summaries.get(conv_id, "")
        }
        for conv_id in threads.keys()
    ])
    
    # Add suggested tags
    df_results['suggested_tags'] = ''
    
    for i, row in enumerate(df_results.itertuples(), 1):
        print(f"Tagging {i}/{len(df_results)} (ID: {row.conversation_id})")
        
        suggested_tags = suggest_tags_for_conversation(
            row.texto_completo, row.summary, tag_definitions
        )
        
        tag_string = ', '.join(suggested_tags)
        df_results.at[i-1, 'suggested_tags'] = tag_string
        
        print(f"✓ Tags: {tag_string}")
    
    print(f"✓ Tagging complete: {len(df_results)} conversations tagged")
    
    return {
        **state,
        "tagged_conversations_df": df_results,
        "tag_definitions": tag_definitions,
        "status": "complete"
    }


def load_tag_definitions(excel_path):
    """Load tag definitions from Excel file."""
    try:
        df = pd.read_excel(excel_path)
        tag_definitions = dict(zip(df['tag'], df['description']))
        print(f"Loaded {len(tag_definitions)} tag definitions")
        return tag_definitions
    except Exception as e:
        print(f"Error loading tag definitions: {str(e)}")
        return {}


def suggest_tags_for_conversation(conversation_text, summary, tag_definitions, max_tags=3):
    """Use LLM to suggest tags for a conversation."""
    if not tag_definitions:
        return []
    
    formatted_tags = "\n".join([f"- {tag}: {desc}" for tag, desc in tag_definitions.items()])
    
    # Truncate conversation text
    truncated_text = conversation_text[:2000] if len(conversation_text) > 2000 else conversation_text
    
    system_prompt = "You are a helpful assistant that analyzes customer support conversations and assigns the most relevant tags."
    
    user_prompt = f"""Analyze this customer support conversation and suggest up to {max_tags} most relevant tags.

CONVERSATION SUMMARY:
{summary}

CONVERSATION TEXT (may be truncated):
{truncated_text}

AVAILABLE TAGS:
{formatted_tags}

Return ONLY the tag names as a comma-separated list. Example: "tag1, tag2, tag3"""
    
    try:
        response = llm_call(user_prompt, system_prompt)
        suggested_tags = [tag.strip() for tag in response.split(',')]
        valid_tags = [tag for tag in suggested_tags if tag in tag_definitions]
        return valid_tags
    except Exception as e:
        print(f"Error suggesting tags: {str(e)}")
        return []


#%%
# Initialize the graph with the state schema
graph = StateGraph(GraphState) 


# Add nodes with actual functions
graph.add_node("etl", etl_node)
graph.add_node("summarize", summarize_node)
graph.add_node("tagging", tagging_node)

# Add edges - simple linear flow
graph.add_edge(START, "etl")
graph.add_edge("etl", "summarize")
graph.add_edge("summarize", "tagging")
graph.add_edge("tagging", END)

# Compile the graph
app = graph.compile()

# %%
# Display the graph
try:
    display(Image(app.get_graph().draw_mermaid_png()))
except Exception as e:
    print(f"Could not display graph: {e}")

# %%
# Run the workflow
if __name__ == "__main__":
    print("\n" + "="*70)
    print("HELPSCOUT TICKETS AGENT WORKFLOW")
    print("="*70)
    
    # Initialize state
    initial_state = {
        "conversations_df": None,
        "threads_by_convo": {},
        "summaries": {},
        "tagged_conversations_df": None,
        "tag_definitions": {},
        "total_conversations": 0,
        "status": "initialized"
    }
    
    # Run the workflow
    print("\nStarting workflow execution...\n")
    final_state = app.invoke(initial_state)
    
    # Save final results
    if final_state["tagged_conversations_df"] is not None:
        output_path = 'data/final_tagged_conversations.csv'
        final_state["tagged_conversations_df"].to_csv(output_path, index=False)
        print(f"\n" + "="*70)
        print(f"✓ WORKFLOW COMPLETE!")
        print(f"✓ Results saved to: {output_path}")
        print(f"✓ Total conversations processed: {final_state['total_conversations']}")
        print("="*70)
    else:
        print("\n❌ Workflow failed to complete")