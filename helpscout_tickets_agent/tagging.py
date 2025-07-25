#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HelpScout Conversation Tagging Module

This module uses LM Studio to assign tags to HelpScout conversations based on their content.
Tags and their descriptions are loaded from an Excel file, and the model suggests appropriate
tags for each conversation based on the conversation content and summary.
"""
#%%
import pandas as pd
import os
import json
from lm_studio import llm_call

def load_tag_definitions(excel_path):
    """
    Load tag definitions from Excel file.
    
    Args:
        excel_path (str): Path to the Excel file containing tag definitions
        
    Returns:
        dict: Dictionary mapping tag names to their descriptions
    """
    try:
        df = pd.read_excel(excel_path)
        # Create a dictionary of tag: description
        tag_definitions = dict(zip(df['tag'], df['description']))
        print(f"Loaded {len(tag_definitions)} tag definitions")
        return tag_definitions
    except Exception as e:
        print(f"Error loading tag definitions: {str(e)}")
        return {}

def format_tag_definitions(tag_definitions):
    """
    Format tag definitions for use in the LM Studio prompt.
    
    Args:
        tag_definitions (dict): Dictionary mapping tag names to their descriptions
        
    Returns:
        str: Formatted string of tag definitions
    """
    formatted_tags = ""
    for tag, description in tag_definitions.items():
        formatted_tags += f"- {tag}: {description}\n"
    return formatted_tags

def suggest_tags_for_conversation(conversation_text, summary, tag_definitions, max_tags=3):
    """
    Use LM Studio to suggest tags for a conversation based on its content and summary.
    
    Args:
        conversation_text (str): The full text of the conversation
        summary (str): The summary of the conversation
        tag_definitions (dict): Dictionary mapping tag names to their descriptions
        max_tags (int): Maximum number of tags to suggest
        
    Returns:
        list: List of suggested tags
    """
    # Format tag definitions for the prompt
    formatted_tags = format_tag_definitions(tag_definitions)
    
    # Truncate conversation text if too long
    max_length = 2000
    truncated_text = conversation_text[:max_length] if len(conversation_text) > max_length else conversation_text
    
    # Create system prompt
    system_prompt = "You are a helpful assistant that analyzes customer support conversations and assigns the most relevant tags."
    
    # Create user prompt
    user_prompt = f"""Please analyze this customer support conversation and suggest up to {max_tags} most relevant tags from the list below.
    
CONVERSATION SUMMARY:
{summary}

CONVERSATION TEXT (may be truncated):
{truncated_text}

AVAILABLE TAGS (tag: description):
{formatted_tags}

Return ONLY the tag names (without descriptions) as a comma-separated list. Do not include any other text in your response.
For example: "tag1, tag2, tag3"
"""
    
    try:
        # Call LM Studio
        response = llm_call(user_prompt, system_prompt)
        
        # Process response to extract tags
        suggested_tags = [tag.strip() for tag in response.split(',')]
        
        # Validate tags against the available tag definitions
        valid_tags = [tag for tag in suggested_tags if tag in tag_definitions]
        
        return valid_tags
    except Exception as e:
        print(f"Error suggesting tags: {str(e)}")
        return []

def tag_conversations(input_csv_path, output_csv_path, tags_excel_path):
    """
    Process conversations in a CSV file and add suggested tags.
    
    Args:
        input_csv_path (str): Path to the input CSV file with conversations
        output_csv_path (str): Path to save the output CSV file with tags
        tags_excel_path (str): Path to the Excel file with tag definitions
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load tag definitions
        tag_definitions = load_tag_definitions(tags_excel_path)
        if not tag_definitions:
            print("No tag definitions found. Exiting.")
            return False
        
        # Load conversations
        print(f"Loading conversations from {input_csv_path}")
        conversations_df = pd.read_csv(input_csv_path)
        total_conversations = len(conversations_df)
        print(f"Loaded {total_conversations} conversations")
        
        # Create a new column for tags
        conversations_df['suggested_tags'] = ''
        
        # Process each conversation
        for i, row in enumerate(conversations_df.itertuples(), 1):
            conversation_id = row.conversation_id
            conversation_text = row.texto_completo
            summary = row.summary
            
            print(f"Processing conversation {i}/{total_conversations} (ID: {conversation_id})")
            
            # Suggest tags
            suggested_tags = suggest_tags_for_conversation(
                conversation_text, summary, tag_definitions
            )
            
            # Join tags into a comma-separated string
            tag_string = ', '.join(suggested_tags)
            
            # Update the dataframe
            conversations_df.at[i-1, 'suggested_tags'] = tag_string
            
            print(f"✓ Suggested tags for conversation {conversation_id}: {tag_string}")
        
        # Save the results
        conversations_df.to_csv(output_csv_path, index=False)
        print(f"\n✓ Results saved to {output_csv_path}")
        
        return True
    except Exception as e:
        print(f"Error processing conversations: {str(e)}")
        return False

if __name__ == "__main__":
    # Define file paths
    input_csv_path = 'data/threads_by_convo_with_lm_studio_summaries.csv'
    output_csv_path = 'data/threads_by_convo_with_tags.csv'
    tags_excel_path = 'support_files/Help Scout tags.xlsx'
    
    print("\n" + "="*50)
    print("STARTING TAG SUGGESTION WITH LM STUDIO")
    print("="*50)
    
    success = tag_conversations(input_csv_path, output_csv_path, tags_excel_path)
    
    if success:
        print(f"\n🎉 Tagging complete! Results saved to {output_csv_path}")
    else:
        print("\n❌ Tagging process failed.")