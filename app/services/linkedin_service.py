import os
import asyncio
from apify_client import ApifyClientAsync
from typing import List, Dict, Optional
from app.models import CompanyBasicInfo
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

async def find_linkedin_urls(company_names: List[str]) -> Dict[str, str]:
    """
    Uses Google Search via Apify to find LinkedIn Company Page URLs for a list of company names.
    Returns: {"Company Name": "https://www.linkedin.com/company/..."}
    """
    if not APIFY_API_TOKEN:
        print("Error: APIFY_API_TOKEN missing.")
        return {}

    client = ApifyClientAsync(APIFY_API_TOKEN)
    name_to_url = {}

    # Construct queries: "site:linkedin.com/company [Company Name]"
    queries = [f"site:linkedin.com/company {name}" for name in company_names]
    
    # We can batch these or run them 
    # Apify Google Search Scraper supports multiple queries
    run_input = {
        "queries": "\n".join(queries),
        "resultsPerPage": 1, 
        "maxPagesPerQuery": 1,
        "languageCode": "en",
        "mobileResults": False,
        "includeUnfilteredResults": False,
    }

    print(f"DEBUG: Searching for LinkedIn URLs for {len(company_names)} companies...", flush=True)

    try:
        run = await client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        if not run:
            return {}

        dataset_items = await client.dataset(run["defaultDatasetId"]).list_items()
        
        # We need to map results back to the company name. 
        # Since queries are processed in order (mostly), or we can check the searchQuery in the result item
        
        for item in dataset_items.items:
            search_query = item.get("searchQuery", {}).get("term", "")
            # search_query looks like "site:linkedin.com/company Name"
            
            # Extract company name from query
            if "site:linkedin.com/company " in search_query:
                company_name = search_query.replace("site:linkedin.com/company ", "").strip()
            else:
                continue

            organic_results = item.get("organicResults", [])
            if organic_results:
                # The first result should be the LinkedIn page
                first_url = organic_results[0].get("url", "")
                if "linkedin.com/company" in first_url:
                    name_to_url[company_name] = first_url
                    print(f"DEBUG: Found LinkedIn for '{company_name}': {first_url}", flush=True)

    except Exception as e:
        print(f"Error finding LinkedIn URLs: {e}", flush=True)

    return name_to_url


async def scrape_linkedin_companies(linkedin_urls: List[str]) -> List[Dict]:
    """
    Scrapes LinkedIn company pages using Apify (dev_fusion/linkedin-company-scraper).
    Returns list of company data dicts.
    """
    if not APIFY_API_TOKEN or not linkedin_urls:
        return []

    client = ApifyClientAsync(APIFY_API_TOKEN)
    
    print(f"DEBUG: Scraping {len(linkedin_urls)} LinkedIn profiles...", flush=True)
    
    # input for dev_fusion/linkedin-company-scraper
    run_input = {
        "urls": linkedin_urls,
    }
    
    ACTOR_ID = "dev_fusion/linkedin-company-scraper" 

    try:
        run = await client.actor(ACTOR_ID).call(run_input=run_input)
        
        if not run:
            print("LinkedIn scrape run failed/empty.")
            return []

        dataset_items = await client.dataset(run["defaultDatasetId"]).list_items()
        
        results = []
        for item in dataset_items.items:
            # Clean up Apify metadata: Filter for valid company profiles
            if item.get("companyName") or item.get("name"):
                 # Normalize keys if needed or just pass raw
                 results.append(item)
        
        print(f"DEBUG: Successfully scraped {len(results)} valid LinkedIn profiles.", flush=True)
        print(f"DEBUG: LinkedIn Data Sample: {str(results)[:200]}...", flush=True) # Log for verification
        return results

    except Exception as e:
        print(f"Error scraping LinkedIn: {e}", flush=True)
        return []
