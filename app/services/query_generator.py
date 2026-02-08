import os
from google import genai
from typing import List
from app.models import SearchConfig
from dotenv import load_dotenv
import json
import asyncio

load_dotenv()

# Configure Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

async def generate_search_queries(config: SearchConfig) -> List[str]:
    """
    Uses Gemini to generate targeted search queries based on the user configuration.
    """
    if not client:
        # Fallback for testing if no key is provided
        return [
            f"{config.included_industries[0]} companies in {config.target_countries[0]}",
            f"top {config.included_industries[0]} suppliers {config.target_countries[0]}",
        ]

    prompt = f"""
    Generate 5 specific Google search queries to find companies matching:
    
    Ind: {', '.join(config.included_industries)}
    Loc: {', '.join(config.target_countries)}
    Key: {', '.join(config.required_keywords)}
    
    Output strictly a RAW JSON array of strings. No markdown.
    Example: ["query 1", "query 2"]
    """

    try:
        # Run sync call in executor to avoid blocking event loop
        response = await asyncio.to_thread(
            client.models.generate_content,
            model='gemini-2.0-flash', 
            contents=prompt
        )
        
        text_response = response.text.strip()
        
        # Clean up if Gemini adds markdown code blocks
        if text_response.startswith("```json"):
            text_response = text_response.replace("```json", "").replace("```", "")
        elif text_response.startswith("```"):
            text_response = text_response.replace("```", "")
            
        queries = json.loads(text_response)
        if isinstance(queries, list):
            return queries
        else:
            return [text_response]
            
    except Exception as e:
        print(f"Error generating queries with Gemini: {e}")
        # Fallback queries
        base_query = f"{config.included_industries[0]} companies in {config.target_countries[0]}"
        return [base_query, base_query + f" {config.required_keywords[0]}"]
