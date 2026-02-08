import os
import sys
import json
import asyncio
import logging
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_company_websites(urls: List[str]) -> List[Dict]:
    """
    Orchestrates the internal scraping of company websites using crawl_best logic.
    Since crawl_best is set up as a standalone script/service, we will invoke it 
    or its logic directly.
    """
    if not urls:
        return []
    
    print(f"DEBUG: Internal Scraper requested for: {urls}", flush=True)

    # We will try to hit the local crawler service if it's running (as suggested by crawl_best structure)
    # OR fallback to running the scraper process directly.
    
    CRAWLER_API_URL = "http://127.0.0.1:8001/scrape"
    
    import httpx
    
    results = []
    
    # Attempt 1: Call Microservice
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(CRAWLER_API_URL, json={"urls": urls, "max_workers": 4})
            if resp.status_code == 200:
                data = resp.json()
                print(f"DEBUG: Scraper Service returned {data.get('count')} results.", flush=True)
                return data.get("results", [])
    except Exception as e:
        print(f"DEBUG: Scraper Service call failed ({e}). Attempting direct subprocess execution...", flush=True)

    # Attempt 2: Direct Subprocess (Fallback)
    current_dir = os.getcwd()
    adapter_script = os.path.join(current_dir, "run_internal_scraper.py")
    
    if not os.path.exists(adapter_script):
         print(f"ERROR: Adapter script not found at {adapter_script}", flush=True)
         return []

    import tempfile
    import subprocess
    
    # Create a temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        output_file = tf.name
    
    try:
        cmd = [sys.executable, adapter_script, output_file] + urls
        print(f"DEBUG: Running fallback command: {' '.join(cmd)}", flush=True)
        
        # Run properly
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            print(f"DEBUG: Scraper subprocess failed: {stderr.decode()}", flush=True)
            return []
            
        print(f"DEBUG: Scraper subprocess output: {stdout.decode()}", flush=True)
        
        # Read output
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Crawl_best format is list of dicts.
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and 'results' in data:
                        return data['results']
            except json.JSONDecodeError:
                print("DEBUG: Failed to decode scraper JSON output.", flush=True)
    except Exception as e:
        print(f"DEBUG: Fallback execution error: {e}", flush=True)
    finally:
        # Cleanup
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except:
                pass

    return []
