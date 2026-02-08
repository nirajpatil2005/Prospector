import asyncio
import os
from apify_client import ApifyClientAsync
from app.models import ScrapedContent
from typing import List, Dict

# Ensure APIFY_API_TOKEN is available
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

async def crawl_companies(urls: List[str]) -> Dict[str, ScrapedContent]:
    """
    Crawls a list of company URLs using Apify's Website Content Crawler to extract deep content.
    """
    if not APIFY_API_TOKEN:
        print("Error: APIFY_API_TOKEN not found. Cannot perform crawling.")
        return {}

    client = ApifyClientAsync(APIFY_API_TOKEN)
    results = {}
    
    # We will trigger a single crawl run for all valid URLs
    # Filter valid URLs
    valid_urls = [{"url": url} for url in urls if url.startswith("http")]
    
    if not valid_urls:
        return {}

    try:
        # Prepare the Actor input
        run_input = {
            "startUrls": valid_urls,
            "maxCrawlDepth": 1, # Crawl the landing page and 1 level deep (optional, or just 0)
            "maxCrawlPages": 5, # Limit pages per company to avoid huge costs/time
            "saveHtml": False,
            "saveMarkdown": True, # Get clean text/markdown
            "maxConcurrency": 5,
        }

        print(f"Starting Apify crawl for {len(valid_urls)} companies...")
        
        # Run the Actor and wait for it to finish
        # employing apify/website-content-crawler for robust extraction
        run = await client.actor("apify/website-content-crawler").call(run_input=run_input)

        if not run:
            print("Apify run failed or returned None.")
            return {}

        print(f"Apify run finished. Fetching results from dataset {run['defaultDatasetId']}...")

        # Fetch results
        dataset_items = await client.dataset(run["defaultDatasetId"]).list_items()
        
        # Process results
        # The crawler might return multiple items per domain if it crawled subpages.
        # We need to aggregate them by company/root URL.
        
        url_content_map = {}

        for item in dataset_items.items:
            url = item.get("url", "")
            text = item.get("markdown", "") or item.get("text", "")
            title = item.get("metadata", {}).get("title", "") or item.get("title", "")
            desc = item.get("metadata", {}).get("description", "") or item.get("description", "")
            
            # Robust matching logic
            matched_base_url = None
            
            # 1. Try exact or simple prefix match
            for base in urls:
                if base in url or url in base: # loose check
                    matched_base_url = base
                    break
            
            # 2. If valid match found
            if matched_base_url:
                if matched_base_url not in url_content_map:
                    url_content_map[matched_base_url] = {
                        "url": matched_base_url,
                        "text_content": "",
                        "html_content": "",
                        "page_title": title,
                        "meta_description": desc,
                        "sub_pages": {}
                    }
                
                # Heuristic: Is this the main page or close to it?
                # If the crawled URL is short (close to base) treat as main content
                if len(url) <= len(matched_base_url) + 5: 
                     url_content_map[matched_base_url]["text_content"] += "\n" + text[:15000]
                     if not url_content_map[matched_base_url]["page_title"]:
                         url_content_map[matched_base_url]["page_title"] = title
                else:
                    # Treat as subpage
                    slug = url.split("/")[-1] or "subpage"
                    url_content_map[matched_base_url]["sub_pages"][slug] = text[:5000]
            else:
                print(f"Warning: Could not map crawled URL {url} back to any requested base URL.")

        # Convert to ScrapedContent objects
        for url, data in url_content_map.items():
            results[url] = ScrapedContent(
                url=data["url"],
                text_content=data["text_content"] or "Content crawled from subpages",
                page_title=data["page_title"],
                meta_description=data["meta_description"],
                sub_pages=data["sub_pages"]
            )
            
    except Exception as e:
        print(f"Error during Apify crawl execution: {e}")

    return results

# Remove the local crawl_single_company function as it's no longer needed

