"""
Production-Ready Company Intelligence System with Gemini AI
Crawls multiple pages per company + Uses Google Gemini for structured extraction

Features:
- Multi-page crawling (About, Products, Certifications, Contact, etc.)
- JavaScript rendering support (Playwright)
- Google Gemini AI integration for intelligent data extraction
- Handles 50-100 companies in 15-20 minutes
- Structured output ready for filtering

Installation:
pip install scrapy scrapy-playwright playwright google-generativeai beautifulsoup4
playwright install chromium
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod
import json
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import google.generativeai as genai
import os
from collections import defaultdict

# New lightweight FastAPI interface for direct endpoint usage
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import time

class IntelligentCompanyCrawler(scrapy.Spider):
    name = 'intelligent_company_crawler'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 0.5,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 2,
        'DEPTH_LIMIT': 2,
        'ROBOTSTXT_OBEY': False,
        
        # Playwright for JS sites
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 30000,
        },
        
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'INFO',
        
        'ITEM_PIPELINES': {
            '__main__.CompanyDataAggregator': 100,
            '__main__.GeminiAIExtractor': 200,
            '__main__.JsonExportPipeline': 300,
        },
    }
    
    # Pages to crawl for each company
    TARGET_PAGES = [
        'about', 'about-us', 'about_us', 'aboutus',
        'company', 'who-we-are', 'our-story',
        'products', 'services', 'solutions',
        'certifications', 'compliance', 'quality',
        'contact', 'contact-us', 'locations',
        'team', 'leadership', 'careers',
    ]
    
    def __init__(self, urls=None, output_file=None, use_gemini=True, *args, **kwargs):
        super(IntelligentCompanyCrawler, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = output_file or f'company_intelligence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.use_gemini = use_gemini
        
        # Track visited URLs per domain
        self.domain_pages = defaultdict(set)
    
    def start_requests(self):
        """Start crawling each company"""
        for url in self.start_urls:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            domain = urlparse(url).netloc
            
            # Start with homepage
            yield scrapy.Request(
                url,
                callback=self.parse_page,
                errback=self.handle_error,
                meta={
                    'company_domain': domain,
                    'original_url': url,
                    'page_type': 'homepage',
                    'playwright': False,
                    'company_data': {
                        'domain': domain,
                        'original_url': url,
                        'pages_content': {},
                    }
                },
                dont_filter=True
            )
    
    def parse_page(self, response):
        """Parse any page and extract content"""
        
        company_data = response.meta['company_data']
        page_type = response.meta['page_type']
        domain = response.meta['company_domain']
        
        # Check if JS rendering needed
        if not response.meta.get('playwright') and self.needs_js_rendering(response):
            self.logger.info(f"🔄 JS detected on {page_type}, using Playwright: {response.url}")
            
            yield scrapy.Request(
                response.url,
                callback=self.parse_page,
                errback=self.handle_error,
                meta={
                    **response.meta,
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'networkidle'),
                        PageMethod('wait_for_timeout', 2000),
                    ],
                },
                dont_filter=True
            )
            return
        
        # Extract page content
        page_content = self.extract_page_content(response, page_type)
        company_data['pages_content'][page_type] = page_content
        
        self.logger.info(f"✓ Scraped {page_type} for {domain}")
        
        # On homepage, find and crawl important pages
        if page_type == 'homepage':
            # Find target pages
            for next_page in self.find_target_pages(response, domain):
                if next_page not in self.domain_pages[domain]:
                    self.domain_pages[domain].add(next_page)
                    
                    # Determine page type
                    detected_type = self.detect_page_type(next_page)
                    
                    yield scrapy.Request(
                        next_page,
                        callback=self.parse_page,
                        errback=self.handle_error,
                        meta={
                            'company_domain': domain,
                            'original_url': response.meta['original_url'],
                            'page_type': detected_type,
                            'playwright': False,
                            'company_data': company_data,
                        },
                        dont_filter=True
                    )
        
        # If this is the last page or we have enough content, yield the data
        # We'll aggregate in the pipeline
        yield company_data
    
    def extract_page_content(self, response, page_type):
        """Extract meaningful content from a page"""
        
        content = {
            'url': response.url,
            'page_type': page_type,
            'scraped_at': datetime.now().isoformat(),
        }
        
        # Extract title
        content['title'] = response.css('title::text').get()
        
        # Extract meta description
        content['meta_description'] = response.css('meta[name="description"]::attr(content)').get()
        
        # Extract all headings
        content['headings'] = {
            'h1': response.css('h1 ::text').getall(),
            'h2': response.css('h2 ::text').getall(),
            'h3': response.css('h3 ::text').getall(),
        }
        
        # Extract all paragraph text
        paragraphs = response.css('p ::text').getall()
        content['paragraphs'] = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]
        
        # Extract list items (often used for features, certifications, etc.)
        list_items = response.css('ul li ::text, ol li ::text').getall()
        content['list_items'] = [li.strip() for li in list_items if li.strip() and len(li.strip()) > 5]
        
        # Extract specific data based on page type
        if page_type in ['about', 'about-us', 'company']:
            content['specific_data'] = self.extract_about_data(response)
        
        elif page_type in ['products', 'services', 'solutions']:
            content['specific_data'] = self.extract_products_data(response)
        
        elif page_type in ['certifications', 'compliance', 'quality']:
            content['specific_data'] = self.extract_certifications_data(response)
        
        elif page_type in ['contact', 'locations']:
            content['specific_data'] = self.extract_contact_data(response)
        
        # Extract full text content (for Gemini processing)
        all_text = ' '.join(response.css('body ::text').getall())
        # Clean and limit text
        all_text = re.sub(r'\s+', ' ', all_text).strip()
        content['full_text'] = all_text[:10000]  # Limit to 10k chars per page
        
        return content
    
    def extract_about_data(self, response):
        """Extract company info from About page"""
        data = {}
        
        text = ' '.join(response.css('body ::text').getall()).lower()
        
        # Look for employee count
        employee_patterns = [
            r'(\d+[\+]?)\s*employees',
            r'team of (\d+)',
            r'(\d+[\+]?)\s*people',
            r'over (\d+)\s*employees',
        ]
        for pattern in employee_patterns:
            match = re.search(pattern, text)
            if match:
                data['employee_count_mentioned'] = match.group(1)
                break
        
        # Look for founding year
        year_match = re.search(r'founded in (\d{4})|established (\d{4})|since (\d{4})', text)
        if year_match:
            data['founded_year'] = year_match.group(1) or year_match.group(2) or year_match.group(3)
        
        return data
    
    def extract_products_data(self, response):
        """Extract products/services info"""
        data = {}
        
        # Extract product names (usually in h2, h3 headings)
        product_headings = response.css('h2 ::text, h3 ::text').getall()
        data['product_headings'] = [h.strip() for h in product_headings if h.strip()][:20]
        
        return data
    
    def extract_certifications_data(self, response):
        """Extract certifications"""
        data = {}
        
        text = ' '.join(response.css('body ::text').getall())
        
        # Common certifications
        cert_keywords = ['ISO', 'SOC', 'HIPAA', 'GDPR', 'PCI', 'CMMI', 'certified']
        data['certifications_mentioned'] = [kw for kw in cert_keywords if kw in text]
        
        # Extract all text that might be certifications
        list_items = response.css('ul li ::text, ol li ::text').getall()
        data['certification_items'] = [item.strip() for item in list_items if item.strip()][:15]
        
        return data
    
    def extract_contact_data(self, response):
        """Extract contact information"""
        data = {}
        
        # Extract emails
        emails = set()
        mailto_links = response.css('a[href^="mailto:"]::attr(href)').getall()
        for link in mailto_links:
            email = link.replace('mailto:', '').split('?')[0].strip()
            emails.add(email)
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, response.text, re.IGNORECASE)
        emails.update(found_emails)
        
        blacklist = ['example.com', 'test.com', 'wixpress.com']
        data['emails'] = [e for e in emails if not any(bl in e.lower() for bl in blacklist)][:5]
        
        # Extract phones
        phones = set()
        tel_links = response.css('a[href^="tel:"]::attr(href)').getall()
        for link in tel_links:
            phone = link.replace('tel:', '').strip()
            phones.add(phone)
        
        data['phones'] = list(phones)[:3]
        
        # Extract address
        address = response.css('[itemprop="address"] ::text').getall()
        if address:
            data['address'] = ' '.join([a.strip() for a in address if a.strip()])
        
        return data
    
    def find_target_pages(self, response, domain):
        """Find important pages to crawl"""
        found_urls = set()
        
        # Extract all links
        all_links = response.css('a::attr(href)').getall()
        
        for link in all_links:
            # Make absolute URL
            absolute_url = urljoin(response.url, link)
            
            # Check if same domain
            if urlparse(absolute_url).netloc != domain:
                continue
            
            # Clean URL (remove fragments and queries)
            clean_url = absolute_url.split('#')[0].split('?')[0]
            
            # Check if it matches our target pages
            url_path = urlparse(clean_url).path.lower()
            if any(target in url_path for target in self.TARGET_PAGES):
                found_urls.add(clean_url)
                
                # Limit to max 10 pages per company
                if len(found_urls) >= 10:
                    break
        
        return list(found_urls)
    
    def detect_page_type(self, url):
        """Detect what type of page this is"""
        url_lower = url.lower()
        
        for target in self.TARGET_PAGES:
            if target in url_lower:
                # Return the base type (e.g., 'about' for 'about-us')
                if 'about' in target:
                    return 'about'
                elif 'product' in target or 'service' in target or 'solution' in target:
                    return 'products'
                elif 'cert' in target or 'compliance' in target or 'quality' in target:
                    return 'certifications'
                elif 'contact' in target or 'location' in target:
                    return 'contact'
                elif 'team' in target or 'leadership' in target or 'career' in target:
                    return 'team'
        
        return 'other'
    
    def needs_js_rendering(self, response):
        """Check if page needs JavaScript rendering"""
        indicators = 0
        
        text = response.css('body ::text').getall()
        text_length = sum(len(t.strip()) for t in text)
        if text_length < 500:
            indicators += 1
        
        body_html = response.css('body').get() or ''
        js_frameworks = ['data-react', '__NEXT_DATA__', 'ng-app', 'data-v-']
        
        for framework in js_frameworks:
            if framework in body_html:
                indicators += 1
                break
        
        return indicators >= 2
    
    def handle_error(self, failure):
        """Handle errors gracefully"""
        self.logger.error(f"✗ Error: {failure.request.url} - {failure.value}")
        
        company_data = failure.request.meta.get('company_data', {})
        company_data['error'] = str(failure.value)
        
        yield company_data


class CompanyDataAggregator:
    """Aggregate all pages for each company"""
    
    def __init__(self):
        self.companies = {}
    
    def process_item(self, item, spider):
        domain = item.get('domain')
        
        if domain not in self.companies:
            self.companies[domain] = item
        else:
            # Merge pages_content
            existing_pages = self.companies[domain].get('pages_content', {})
            new_pages = item.get('pages_content', {})
            existing_pages.update(new_pages)
            self.companies[domain]['pages_content'] = existing_pages
        
        return item
    
    def close_spider(self, spider):
        # Convert to list for next pipeline
        for domain, data in self.companies.items():
            spider.crawler.engine.slot.scheduler.mqs['default'].push(data)


class GeminiAIExtractor:
    """Use Google Gemini AI to extract structured data from scraped content"""
    
    def __init__(self):
        # Initialize Gemini
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.use_gemini = True
            print("✓ Gemini AI initialized successfully")
        else:
            self.use_gemini = False
            print("⚠️  GOOGLE_API_KEY or GEMINI_API_KEY not found - skipping Gemini AI extraction")
    
    def process_item(self, item, spider):
        if not spider.use_gemini or not self.use_gemini:
            return item
        
        # Skip if error
        if item.get('error'):
            return item
        
        domain = item.get('domain')
        pages_content = item.get('pages_content', {})
        
        if not pages_content:
            return item
        
        print(f"\n🤖 Processing {domain} with Gemini AI...")
        
        # Prepare content for Gemini
        content_summary = self.prepare_content_for_gemini(pages_content)
        
        # Call Gemini API
        try:
            structured_data = self.extract_with_gemini(content_summary, domain)
            item['ai_extracted_data'] = structured_data
            print(f"✓ Gemini extraction complete for {domain}")
            
        except Exception as e:
            print(f"✗ Gemini extraction failed for {domain}: {str(e)}")
            item['ai_extraction_error'] = str(e)
        
        return item
    
    def prepare_content_for_gemini(self, pages_content):
        """Prepare scraped content for Gemini"""
        summary = {}
        
        for page_type, content in pages_content.items():
            page_summary = {
                'title': content.get('title'),
                'headings': content.get('headings'),
                'key_paragraphs': content.get('paragraphs', [])[:10],
                'list_items': content.get('list_items', [])[:20],
                'specific_data': content.get('specific_data', {}),
            }
            summary[page_type] = page_summary
        
        return summary
    
    def extract_with_gemini(self, content_summary, domain):
        """Call Gemini API to extract structured data"""
        
        prompt = f"""You are a company intelligence analyst. I've scraped multiple pages from {domain}'s website.

Here's the content from different pages:

{json.dumps(content_summary, indent=2)}

Please analyze this content and extract the following information in JSON format:

{{
  "company_name": "Full company name",
  "description": "Brief company description (1-2 sentences)",
  "industry": ["primary industry", "secondary industry"],
  "employee_size": "Estimate: 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+, or unknown",
  "founded_year": "Year or unknown",
  "headquarters_location": "City, Country or unknown",
  "products_services": ["product/service 1", "product/service 2", ...],
  "certifications": ["certification 1", "certification 2", ...],
  "target_market": "B2B, B2C, or Both",
  "technology_stack": ["tech 1", "tech 2", ...] (if mentioned),
  "key_clients": ["client 1", "client 2", ...] (if mentioned),
  "has_careers_page": true/false,
  "confidence_score": "0.0 to 1.0 based on data availability"
}}

Rules:
- Only include information you can find in the provided content
- Use "unknown" if information is not available
- For employee_size, make an educated guess based on context clues
- Be conservative with confidence_score - only give high scores when data is clear
- Extract certifications carefully (ISO, SOC, HIPAA, etc.)
- Return ONLY valid JSON, no other text or markdown formatting"""

        # Generate content with Gemini
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2000,
            )
        )
        
        # Parse response
        response_text = response.text
        
        # Extract JSON from response (in case Gemini adds markdown)
        # Remove markdown code blocks if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'^```\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        # Find JSON object
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return json.loads(response_text)


class JsonExportPipeline:
    """Export final data to JSON"""
    
    def open_spider(self, spider):
        self.items = []
        self.file_path = spider.output_file
    
    def close_spider(self, spider):
        # Aggregate by domain and write
        companies = {}
        
        for item in self.items:
            domain = item.get('domain')
            if domain:
                if domain not in companies:
                    companies[domain] = item
                else:
                    # Merge pages
                    existing_pages = companies[domain].get('pages_content', {})
                    new_pages = item.get('pages_content', {})
                    existing_pages.update(new_pages)
                    companies[domain]['pages_content'] = existing_pages
                    
                    # Keep AI data if exists
                    if item.get('ai_extracted_data'):
                        companies[domain]['ai_extracted_data'] = item['ai_extracted_data']
        
        # Write to file
        final_data = list(companies.values())
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        successful = sum(1 for c in final_data if not c.get('error'))
        with_ai = sum(1 for c in final_data if c.get('ai_extracted_data'))
        
        print(f"\n{'='*70}")
        print(f"CRAWLING COMPLETE!")
        print(f"{'='*70}")
        print(f"Total companies: {len(final_data)}")
        print(f"✓ Successfully crawled: {successful}")
        print(f"🤖 AI extraction completed: {with_ai}")
        print(f"💾 Data saved to: {self.file_path}")
        print(f"{'='*70}\n")
    
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item


def run_intelligent_crawler(company_urls, output_file=None, use_gemini=True):
    """
    Run the intelligent company crawler with Gemini AI
    
    Args:
        company_urls: List of company websites
        output_file: Output JSON file path
        use_gemini: Whether to use Gemini AI for extraction
    
    Returns:
        Output file path
    """
    
    if output_file is None:
        output_file = f"company_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Check for Gemini API key
    if use_gemini and not (os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')):
        print("\n⚠️  Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable to use Gemini AI extraction")
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        print("Without it, you'll only get raw scraped data\n")
    
    process = CrawlerProcess({'LOG_LEVEL': 'INFO'})
    process.crawl(IntelligentCompanyCrawler, urls=company_urls, output_file=output_file, use_gemini=use_gemini)
    process.start()
    
    return output_file


if __name__ == '__main__':
    # Start FastAPI when run directly to expose a simple scraping endpoint
    # This endpoint is a lightweight alternative to the full Scrapy crawler
    # and is intended for quick integration with other services (like Insighter).

    app = FastAPI(title="Crawler Quick API")

    class ScrapeRequest(BaseModel):
        urls: list[str]
        timeout: int | None = 10
        max_workers: int | None = 4

    def scrape_single(url: str, timeout: int = 10) -> dict:
        """Basic scraping using requests + BeautifulSoup. Returns a structured dict."""
        result = {
            'url': url,
            'domain': urlparse(url).netloc,
            'scraped_at': datetime.now().isoformat(),
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Crawler/1.0)'
        }

        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
        except Exception as e:
            result['error'] = str(e)
            return result

        soup = BeautifulSoup(resp.text, 'lxml')

        # Basic extracts
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        meta_desc = None
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            meta_desc = desc_tag.get('content').strip()

        def texts(sel):
            return [t.strip() for t in sel if t and t.strip()]

        headings = {
            'h1': texts([h.get_text(separator=' ', strip=True) for h in soup.find_all('h1')]),
            'h2': texts([h.get_text(separator=' ', strip=True) for h in soup.find_all('h2')]),
            'h3': texts([h.get_text(separator=' ', strip=True) for h in soup.find_all('h3')]),
        }

        paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]
        paragraphs = [p for p in paragraphs if p and len(p) > 20][:50]

        list_items = [li.get_text(separator=' ', strip=True) for li in soup.find_all(['li'])]
        list_items = [li for li in list_items if li and len(li) > 5][:100]

        full_text = ' '.join(soup.stripped_strings)
        full_text = re.sub(r'\s+', ' ', full_text).strip()[:20000]

        # Contact extraction (basic)
        emails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", resp.text))
        phones = set(re.findall(r"\+?\d[\d\-\s()]{6,}\d", resp.text))

        result.update({
            'title': title,
            'meta_description': meta_desc,
            'headings': headings,
            'paragraphs': paragraphs,
            'list_items': list_items,
            'emails': list(emails)[:5],
            'phones': list(phones)[:3],
            'full_text': full_text,
        })

        return result

    @app.post('/scrape')
    def scrape(request: ScrapeRequest):
        if not request.urls:
            raise HTTPException(status_code=400, detail='Provide at least one URL')

        results = []
        start = time.time()

        with ThreadPoolExecutor(max_workers=request.max_workers or 4) as ex:
            futures = {ex.submit(scrape_single, url, request.timeout or 10): url for url in request.urls}
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as e:
                    results.append({'url': futures[fut], 'error': str(e)})

        # Save results to output folder as JSON
        try:
            out_dir = os.path.join(os.path.dirname(__file__), 'output')
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, f"scrape_{int(time.time())}.json")
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump({'took_seconds': round(time.time() - start, 2), 'count': len(results), 'results': results}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            'took_seconds': round(time.time() - start, 2),
            'count': len(results),
            'results': results,
            'saved_to': out_file if 'out_file' in locals() else None
        }


    @app.get('/')
    def health():
        return {'status': 'healthy', 'service': 'Crawler Quick API'}

    import uvicorn

    print('✅ FastAPI scraping endpoint available at http://127.0.0.1:8001/scrape')
    uvicorn.run(app, host='0.0.0.0', port=8001)