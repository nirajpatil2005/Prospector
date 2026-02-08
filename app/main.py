import json
import asyncio
import hashlib
import time
import os
import glob
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models import SearchConfig, CompanyAnalysis
from async_lru import alru_cache

# We will import services later as we implement them

app = FastAPI(title="Intelligent Company Researcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://localhost:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Intelligent Company Researcher API is running"}

from app.services.query_generator import generate_search_queries
from app.services.search_service import execute_search
from app.services.crawler_service import crawl_companies
from app.services.analysis_service import analyze_single_company

# --- Cache Management ---

OUTPUT_DIR = "output"
CACHE_DURATION = 1800  # 30 minutes in seconds

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_cache_path(config: SearchConfig) -> str:
    # Generate a stable hash from the configuration
    config_json = config.model_dump_json()
    config_hash = hashlib.md5(config_json.encode()).hexdigest()
    return os.path.join(OUTPUT_DIR, f"{config_hash}.json")

def cleanup_cache():
    """Removes cache files older than CACHE_DURATION."""
    now = time.time()
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*.json")):
        if os.stat(f).st_mtime < now - CACHE_DURATION:
            try:
                os.remove(f)
                print(f"Removed expired cache: {f}")
            except OSError as e:
                print(f"Error removing {f}: {e}")

# --- Cached Wrappers ---

@alru_cache(maxsize=32)
async def cached_generate_queries(config_json: str):
    # wrapper to cache based on JSON string of config
    config = SearchConfig.model_validate_json(config_json)
    return await generate_search_queries(config)

@alru_cache(maxsize=32)
async def cached_search(queries_tuple):
    # wrapper to cache search results
    return await execute_search(list(queries_tuple))

async def research_stream(config: SearchConfig):
    """
    Generator function for SSE with Two-Stage Deep Research.
    """
    try:
        cleanup_cache() 
        cache_path = get_cache_path(config)
        
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting Deep Company Research...'})}\n\n"
        
        from app.services.analysis_service import discover_companies_with_gemini, enrich_company_with_gemini, generate_market_insights, analyze_linkedin_company
        from app.services.linkedin_service import scrape_linkedin_companies, find_linkedin_urls
        from app.services.scraping_service import scrape_company_websites

        # 1. Discovery
        yield f"data: {json.dumps({'type': 'status', 'message': 'Discovering companies (Strict Domain Filter)...'})}\n\n"
        companies = await discover_companies_with_gemini(config, limit=10)
        
        if not companies:
             yield f"data: {json.dumps({'type': 'status', 'message': 'No companies found. Try broader keywords.'})}\n\n"
             yield f"data: {json.dumps({'type': 'done'})}\n\n"
             return

        print(f"DEBUG: Discovered {len(companies)} companies: {[c['name'] for c in companies]}", flush=True)
        yield f"data: {json.dumps({'type': 'status', 'message': f'Identified {len(companies)} candidates. Fetching Data...'})}\n\n"

        # 2. LinkedIn Scraping (Parallel)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Scraping LinkedIn Profiles (Apify)...'})}\n\n"
        
        # Prepare LinkedIn URLs (Use what we have or guess/search if missing - for now assuming discovery might miss them)
        # In a real scenario, we might need a step to find LinkedIn URLs if discovery didn't provide them.
        # But for now, let's assume we proceed with the company list. 
        # User said "get linkedin data from linkedin actor... and use our internal scraper for scraping companies official website".
        
        # We need LinkedIn URLs to use the actor.
        linkedin_urls_to_scrape = []
        company_map = {c['name']: c for c in companies}
        
        # Simple heuristic: If we don't have a linkedIn URL, we might need to search it.
        # For this iteration, we'll try to use the name to find it via Apify or skip.
        # Let's try to find them if missing.
        missing_linkedin = [c['name'] for c in companies if 'linkedin' not in c.get('url', '').lower()]
        
        if missing_linkedin:
             print(f"DEBUG: Finding LinkedIn URLs for {len(missing_linkedin)} companies...", flush=True)
             found_urls = await find_linkedin_urls(missing_linkedin) # This uses Apify Google Search
             for name, url in found_urls.items():
                 if name in company_map:
                     company_map[name]['linkedin_url'] = url
                     linkedin_urls_to_scrape.append(url)
        
        # Also add existing ones
        for c in companies:
            if 'linkedin.com/company' in c.get('url', ''):
                linkedin_urls_to_scrape.append(c['url'])
            elif c.get('linkedin_url'):
                linkedin_urls_to_scrape.append(c['linkedin_url'])
        
        linkedin_data_map = {}
        if linkedin_urls_to_scrape:
            linkedin_results = await scrape_linkedin_companies(list(set(linkedin_urls_to_scrape)))
            # Map back to company
            # heuristic matching or by URL
            for item in linkedin_results:
                # Store by URL or Name
                url = item.get('url') or item.get('linkedinUrl')
                if url: linkedin_data_map[url] = item
                name = item.get('name') or item.get('companyName')
                if name: linkedin_data_map[name] = item

        print(f"DEBUG: LinkedIn Data Count: {len(linkedin_data_map)}", flush=True)

        # 3. Internal Website Scraping (Parallel)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Scraping Official Websites (Internal Crawler)...'})}\n\n"
        
        website_urls = [c['url'] for c in companies if 'linkedin' not in c['url']]
        scraped_content_map = {}
        
        if website_urls:
            raw_scraped_data = await scrape_company_websites(website_urls)
            for item in raw_scraped_data:
                u = item.get('url')
                if u: scraped_content_map[u] = item
        
        print(f"DEBUG: Internal Scraped Pages: {len(scraped_content_map)}", flush=True)

        # 4. Analysis & Synthesis
        completed_count = 0
        final_results = []
        
        for c in companies:
            yield f"data: {json.dumps({'type': 'status', 'message': f'Analyzing {c["name"]}...'})}\n\n"
            
            # Combine Data
            li_data = linkedin_data_map.get(c.get('linkedin_url')) or linkedin_data_map.get(c['name'])
            web_data = scraped_content_map.get(c['url'])
            
            # Pass to Analysis Service
            # We'll need a new method or modify existing to accept this composite data
            # For now, we'll patch it into the existing flow or create a merged context
            
            analysis = None
            
            # Prefer LinkedIn data for "Firmographics" and Web data for "Content"
            if li_data:
                # Use Gemini to analyze LinkedIn Data
                analysis = await analyze_linkedin_company(li_data, config)
            
            if not analysis and web_data:
                 # Fallback to web analysis if no LinkedIn
                 # We need to adapt web_data to ScrapedContent object or similar
                 # For now, bypassing strict type check for speed or assuming adapt
                 pass
            
            if not analysis:
                 # Fallback to Gemini Knowledge
                 analysis = await enrich_company_with_gemini(c, config)
            
            # Enforce "Website" is the official one, not LinkedIn
            if analysis and c.get('url') and 'linkedin' not in c['url']:
                analysis.website = c['url']

            if analysis:
                completed_count += 1
                final_results.append(analysis.model_dump())
                yield f"data: {json.dumps({'type': 'company_result', 'data': analysis.model_dump()})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'current': completed_count, 'total': len(companies)})}\n\n"

        # 5. Market Insights
        if final_results:
             yield f"data: {json.dumps({'type': 'status', 'message': 'Generating Final Market Insights...'})}\n\n"
             # Convert dicts back to objects for the insight generator
             analysis_objects = [CompanyAnalysis(**r) for r in final_results]
             insights = await generate_market_insights(analysis_objects)
             yield f"data: {json.dumps({'type': 'market_insights', 'data': insights})}\n\n"

        yield f"data: {json.dumps({'type': 'status', 'message': 'Research completed.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/research")
async def research_companies(config: SearchConfig):
    return StreamingResponse(research_stream(config), media_type="text/event-stream")

@app.get("/ping")
async def ping():
    return {"pong": True}
