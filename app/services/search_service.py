import os
from apify_client import ApifyClientAsync
from typing import List, Dict
from app.models import CompanyBasicInfo
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

async def execute_search(queries: List[str], limit_per_query: int = 5) -> List[CompanyBasicInfo]:
    """
    Executes search queries using Apify's Google Search Scraper and returns a list of unique companies.
    """
    if not APIFY_API_TOKEN:
        print("Warning: APIFY_API_TOKEN not found in environment variables.")
        return []

    client = ApifyClientAsync(APIFY_API_TOKEN)
    results_map: Dict[str, CompanyBasicInfo] = {}

    for query in queries:
        try:
            # Prepare the Actor input
            run_input = {
                "queries": query,
                "resultsPerPage": limit_per_query,
                "maxPagesPerQuery": 1,
                "languageCode": "en",
                "mobileResults": False,
                "includeUnfilteredResults": False,
                "saveHtml": False,
                "saveHtmlToKeyValueStore": False,
                "includeIcons": False,
            }

            # Run the Actor and wait for it to finish
            run = await client.actor("apify/google-search-scraper").call(run_input=run_input)

            # Fetch and print Actor results from the run's dataset (if there are any)
            dataset_items = await client.dataset(run["defaultDatasetId"]).list_items()
            for item in dataset_items.items:
                organic_results = item.get("organicResults", [])
                
                for result in organic_results:
                    url = result.get("url")
                    if not url:
                        continue
                        
                    # Basic deduplication by URL
                    if url in results_map:
                        continue
                    
                    company = CompanyBasicInfo(
                        name=result.get("title", "Unknown"),
                        url=url,
                        snippet=result.get("description", ""),
                        source="apify"
                    )
                    results_map[url] = company

        except Exception as e:
            print(f"Error searching for query in Apify '{query}': {e}")
            
    return list(results_map.values())
