# %%
def process_threads_data(api_response: Dict) -> str:
    """Convert API response to a formatted string for LLM processing."""
    # Convert to JSON string for better LLM processing
    return json.dumps(api_response, indent=2)

def process_individual_threads(threads_data: List[Dict]) -> List[str]:
    """Process each thread individually and return results."""
    results = []
    
    for i, thread in enumerate(threads_data, 1):
        print(f"\nProcessing Thread {i}/{len(threads_data)}")
        print("-" * 50)
        
        # Convert single thread to string
        thread_input = json.dumps(thread, indent=2)
        
        # Process with chain function
        result = simple_call(thread_input, [refine_prompt])
        results.append(result)
    
    return results