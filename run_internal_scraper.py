import sys
import os
import json
import asyncio

# Add the crawler directory to path
current_dir = os.getcwd()
crawler_dir = os.path.join(current_dir, 'crawl_best', 'crawling_scrap', 'crawler')
sys.path.append(crawler_dir)

# Now we can try to import scrap
try:
    from scrap import run_intelligent_crawler
except ImportError:
    # Try alternate path if running from root
    sys.path.append(os.path.join(current_dir, 'crawl_best', 'crawling_scrap'))
    from crawler.scrap import run_intelligent_crawler

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_internal_scraper.py <output_file> <url1> [url2 ...]")
        sys.exit(1)
        
    output_file = sys.argv[1]
    urls = sys.argv[2:]
    
    print(f"Starting scraper for {len(urls)} URLs. Output: {output_file}")
    
    # Run the crawler
    # run_intelligent_crawler(company_urls, output_file=None, use_gemini=True)
    # It returns the output file path.
    
    try:
        # We need to run this in a way that doesn't conflict with any existing reactor
        # Since this script is a standalone process, it's fine.
        
        # We assume use_gemini=False to avoid API key issues if not set, or True if env is set.
        # User has .env, hopefully it's loaded.
        from dotenv import load_dotenv
        load_dotenv()
        
        crawled_file = run_intelligent_crawler(urls, output_file=output_file, use_gemini=True)
        print(f"Scraping finished. File: {crawled_file}")
        
    except Exception as e:
        print(f"Error running crawler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
