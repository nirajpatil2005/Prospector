import asyncio
from app.services.scraping_service import scrape_company_websites
import time

async def test_scraping():
    print("Testing scraping service integration...")
    # Test with a known simple site if possible or a safe one.
    # Using example.com or similar might not trigger the internal scraper's interesting parts but verifies connectivity.
    urls = ["https://example.com"] 
    
    try:
        results = await scrape_company_websites(urls)
        print(f"Scraping results: {len(results)}")
        if results:
            print(f"First result title: {results[0].get('title')}")
            print("SUCCESS: Service is reachable and returned data.")
        else:
            print("WARNING: Service reachable but returned no data (might be expected for example.com if filters apply).")
            
    except Exception as e:
        print(f"ERROR: Failed to call scraping service: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraping())
