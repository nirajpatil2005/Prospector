"""
Orchestrator API that uses crawler service and Insighter analysis endpoint.
- POST /analyze_sites accepts { "urls": [...] }
- Calls crawler at http://127.0.0.1:8001/scrape to get scraped content
- Calls Insighter at http://127.0.0.1:8000/api/v1/analyze_scraped with scraped content
- Returns the LLM analysis response to the caller

Requires: run crawler (crawler/scrap.py) and Insighter backend (Insighter/backend/app/main.py)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests
import os
import subprocess
import sys
import time
import atexit
from pathlib import Path

app = FastAPI(title="Orchestrator: Crawler -> Insighter")

CRAWLER_URL = os.getenv('CRAWLER_API_URL', 'http://127.0.0.1:8001/scrape')
INSIGHTER_URL = os.getenv('INSIGHTER_ANALYZE_SCRAPED', 'http://127.0.0.1:8000/api/v1/analyze_scraped')
CRAWLER_HEALTH = os.getenv('CRAWLER_HEALTH', 'http://127.0.0.1:8001/')
INSIGHTER_HEALTH = os.getenv('INSIGHTER_HEALTH', 'http://127.0.0.1:8000/')

procs = []

def start_process(cmd, cwd=None):
    # Start process inheriting stdout/stderr so logs are visible
    p = subprocess.Popen(cmd, cwd=cwd)
    procs.append(p)
    return p

def wait_for_health(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def cleanup():
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

atexit.register(cleanup)

class AnalyzeRequest(BaseModel):
    urls: List[str]

@app.post('/analyze_sites')
def analyze_sites(req: AnalyzeRequest):
    if not req.urls:
        raise HTTPException(status_code=400, detail='Provide at least one URL')

    # Call crawler service
    try:
        cr = requests.post(CRAWLER_URL, json={
            'urls': req.urls,
            'timeout': 20,
            'max_workers': min(8, len(req.urls))
        }, timeout=60)
        cr.raise_for_status()
        scraped_payload = cr.json().get('results', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Crawler call failed: {e}')

    # Transform scraped payload into pipeline expected format if needed
    transformed = []
    for r in scraped_payload:
        transformed.append({
            'domain': r.get('domain') or r.get('url', '').split('//')[-1].split('/')[0],
            'original_url': r.get('url'),
            'pages_content': {
                'homepage': {
                    'title': r.get('title'),
                    'headings': r.get('headings', {}),
                    'paragraphs': r.get('paragraphs', []),
                    'list_items': r.get('list_items', []),
                    'specific_data': {
                        'emails': r.get('emails', []),
                        'phones': r.get('phones', [])
                    },
                    'full_text': r.get('full_text', '')
                }
            }
        })

    # Call Insighter analyze_scraped
    try:
        ir = requests.post(INSIGHTER_URL, json=transformed, timeout=120)
        ir.raise_for_status()
        return ir.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Insighter call failed: {e}')

if __name__ == '__main__':
    # Start crawler and insighter services automatically
    print('Starting crawler and insighter services...')

    # Start crawler (run scrap.py) in crawler/ folder
    crawler_dir = Path(__file__).parent / 'crawler'
    start_process([sys.executable, 'scrap.py'], cwd=str(crawler_dir))

    # Start Insighter backend (uvicorn) in Insighter/backend folder
    insighter_dir = Path(__file__).parent / 'Insighter' / 'backend'
    start_process([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], cwd=str(insighter_dir))

    # Wait for health
    print('Waiting for services to be healthy (timeout 60s)...')
    ok1 = wait_for_health(CRAWLER_HEALTH, timeout=60)
    ok2 = wait_for_health(INSIGHTER_HEALTH, timeout=60)

    if not (ok1 and ok2):
        print('One or more services failed to start. Check logs.')
    else:
        print('Services healthy. Starting orchestrator API on http://127.0.0.1:8100')

    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8100)
