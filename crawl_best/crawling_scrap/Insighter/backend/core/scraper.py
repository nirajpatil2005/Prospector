"""
Scraper module using existing IntelligentCompanyCrawler
"""
import asyncio
import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any
from datetime import datetime

from app.config import settings
from utils.token_optimizer import TokenOptimizer
import requests


class CompanyScraper:
    """Wrapper for the existing scraper"""
    
    def __init__(self):
        self.optimizer = TokenOptimizer()
    
    async def scrape_companies(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple companies using existing scraper
        """
        # Prepare URLs
        formatted_urls = []
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            formatted_urls.append(url)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            output_file = tmp.name
        
        try:
            # Run the scraper (using existing code)
            # We'll use subprocess to run the scraper
            # In production, you might want to integrate directly
            
            # For now, we'll use a simplified approach
            # You can integrate the existing scraper code here
            
            # Call the lightweight crawler FastAPI service to scrape pages
            print(f"🔍 Scraping {len(formatted_urls)} companies via crawler service {settings.CRAWLER_API_URL}...")

            try:
                resp = requests.post(
                    settings.CRAWLER_API_URL,
                    json={
                        'urls': formatted_urls,
                        'timeout': settings.SCRAPE_TIMEOUT,
                        'max_workers': min(8, len(formatted_urls))
                    },
                    timeout=settings.SCRAPE_TIMEOUT + 10
                )

                resp.raise_for_status()
                payload = resp.json()
                results = payload.get('results', [])

                # Transform results into expected scraped_data format
                scraped_data = []
                for r in results:
                    company = {
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
                    }
                    if r.get('error'):
                        company['error'] = r.get('error')
                    scraped_data.append(company)

            except Exception as e:
                print(f"✗ Crawler service call failed: {e}")
                # Fallback to mock scrape
                scraped_data = await self._mock_scrape(formatted_urls)
            
            # Optimize scraped data
            optimized_data = []
            for data in scraped_data:
                optimized = self.optimizer.extract_key_content(data)
                optimized_data.append(optimized)
            
            return optimized_data
            
        finally:
            # Cleanup
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    async def _mock_scrape(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Mock scraping for testing"""
        # In production, integrate with your existing scraper
        mock_data = []
        
        for url in urls:
            mock_data.append({
                'domain': url.split('//')[-1].split('/')[0],
                'original_url': url,
                'pages_content': {
                    'homepage': {
                        'title': f'Homepage - {url}',
                        'headings': {'h1': ['Welcome'], 'h2': ['Services', 'Contact']},
                        'paragraphs': ['Company provides excellent services...'],
                        'list_items': ['Service 1', 'Service 2'],
                        'specific_data': {'emails': ['info@example.com']}
                    }
                }
            })
        
        return mock_data