"""
Intelligent Web Scraper with Active Data Discovery & Validation

Features:
- Smart email discovery (contact pages, team pages, footer, etc.)
- Phone number validation and formatting
- Employee name extraction from team/about pages
- Location detection from multiple sources
- Social media profile discovery
- Data validation and confidence scoring
- Multi-strategy search for missing data
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import re
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
import phonenumbers
from email_validator import validate_email, EmailNotValidError

app = FastAPI(title="Intelligent Scraper API")


class IntelligentScraper:
    """Scraper with intelligence to find and validate data"""
    
    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url if base_url.startswith('http') else f'https://{base_url}'
        self.domain = urlparse(self.base_url).netloc
        self.timeout = timeout
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Data storage
        self.emails = set()
        self.phones = set()
        self.employees = []
        self.locations = set()
        self.social_media = {}
        
        # Pages cache
        self.pages_content = {}
    
    def scrape_with_intelligence(self) -> Dict:
        """Main scraping method with intelligent data discovery"""
        
        start_time = time.time()
        result = {
            'domain': self.domain,
            'original_url': self.base_url,
            'scraped_at': datetime.now().isoformat(),
        }
        
        try:
            # Step 1: Scrape homepage
            print(f"Scraping homepage: {self.base_url}")
            homepage = self._fetch_page(self.base_url)
            if not homepage:
                result['error'] = 'Failed to fetch homepage'
                return result
            
            self.pages_content['homepage'] = homepage
            
            # Step 2: Find and scrape important pages
            important_pages = self._discover_important_pages(homepage)
            print(f"Found {len(important_pages)} important pages")
            
            for page_type, url in important_pages.items():
                if url and url not in self.visited_urls:
                    print(f"Scraping {page_type}: {url}")
                    page_content = self._fetch_page(url)
                    if page_content:
                        self.pages_content[page_type] = page_content
            
            # Step 3: Extract basic data from all pages
            self._extract_basic_data()
            
            # Step 4: Intelligent data discovery
            print("Starting intelligent data discovery...")
            self._smart_email_discovery()
            self._smart_phone_discovery()
            self._extract_employee_info()
            self._extract_location_info()
            self._discover_social_media()
            
            # Step 5: Validate and enrich
            print(" Validating and enriching data...")
            validated_emails = self._validate_emails(list(self.emails))
            validated_phones = self._validate_phones(list(self.phones))
            
            # Step 6: Calculate confidence scores
            confidence = self._calculate_confidence()
            
            # Compile results
            result.update({
                'basic_info': {
                    'title': self.pages_content.get('homepage', {}).get('title'),
                    'meta_description': self.pages_content.get('homepage', {}).get('meta_description'),
                },
                'contact_info': {
                    'emails': validated_emails,
                    'phones': validated_phones,
                    'email_count': len(validated_emails),
                    'phone_count': len(validated_phones),
                },
                'location_info': {
                    'detected_locations': list(self.locations),
                    'primary_location': self._get_primary_location(),
                },
                'employees': self.employees[:20],  # Top 20 employees
                'social_media': self.social_media,
                'pages_scraped': list(self.pages_content.keys()),
                'confidence_scores': confidence,
                'processing_time': round(time.time() - start_time, 2),
            })
            
            print(f" Scraping completed in {result['processing_time']}s")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"Error: {e}")
        
        return result
    
    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch and parse a page"""
        
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  Failed to fetch {url}: {e}")
            return None
        
        soup = BeautifulSoup(resp.text, 'lxml')
        
        return {
            'url': url,
            'soup': soup,
            'text': resp.text,
            'title': soup.title.string.strip() if soup.title else None,
            'meta_description': self._get_meta_description(soup),
        }
    
    def _get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '').strip() if meta else None
    
    def _discover_important_pages(self, homepage: Dict) -> Dict[str, str]:
        """Discover important pages like contact, about, team, etc."""
        
        soup = homepage['soup']
        links = soup.find_all('a', href=True)
        
        important_pages = {
            'contact': None,
            'about': None,
            'team': None,
            'careers': None,
            'locations': None,
        }
        
        # Keywords for each page type
        keywords = {
            'contact': ['contact', 'reach-us', 'get-in-touch', 'support'],
            'about': ['about', 'who-we-are', 'our-story', 'company'],
            'team': ['team', 'people', 'leadership', 'our-team'],
            'careers': ['careers', 'jobs', 'join-us', 'work-with-us'],
            'locations': ['locations', 'offices', 'branches', 'where-we-are'],
        }
        
        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            
            # Make absolute URL
            absolute_url = urljoin(self.base_url, href)
            
            # Check if same domain
            if urlparse(absolute_url).netloc != self.domain:
                continue
            
            # Match against keywords
            for page_type, kws in keywords.items():
                if important_pages[page_type]:  # Already found
                    continue
                
                if any(kw in href or kw in text for kw in kws):
                    important_pages[page_type] = absolute_url
                    break
        
        return important_pages
    
    def _extract_basic_data(self):
        """Extract basic data from all scraped pages"""
        
        for page_type, page_data in self.pages_content.items():
            soup = page_data['soup']
            text = page_data['text']
            
            # Extract emails (basic)
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
            self.emails.update(emails)
            
            # Extract phones (basic)
            phones = re.findall(r'[\+]?[(]?\d{1,4}[)]?[-\s\.]?\d{1,4}[-\s\.]?\d{1,9}', text)
            self.phones.update(phones)
    
    def _smart_email_discovery(self):
        """Intelligent email discovery using multiple strategies"""
        
        print("  Smart email discovery...")
        
        strategies_found = []
        
        # Strategy 1: mailto: links
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0].strip()
                self.emails.add(email)
                strategies_found.append('mailto_links')
        
        # Strategy 2: Contact forms (look for hidden emails)
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            
            # Check contact sections
            contact_sections = soup.find_all(['section', 'div'], class_=re.compile(r'contact', re.I))
            for section in contact_sections:
                emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', section.get_text())
                self.emails.update(emails)
                if emails:
                    strategies_found.append('contact_section')
        
        # Strategy 3: Footer emails
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            footer = soup.find('footer')
            if footer:
                emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', footer.get_text())
                self.emails.update(emails)
                if emails:
                    strategies_found.append('footer')
        
        # Strategy 4: Team/employee pages
        if 'team' in self.pages_content:
            soup = self.pages_content['team']['soup']
            
            # Look for email patterns near names
            team_members = soup.find_all(['div', 'section'], class_=re.compile(r'team|member|employee', re.I))
            for member in team_members:
                emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', member.get_text())
                self.emails.update(emails)
                if emails:
                    strategies_found.append('team_page')
        
        # Strategy 5: Obfuscated emails (e.g., "info [at] company [dot] com")
        for page_data in self.pages_content.values():
            text = page_data['text']
            
            # Pattern: something [at] domain [dot] com
            obfuscated = re.findall(r'(\w+)\s*\[at\]\s*(\w+)\s*\[dot\]\s*(\w+)', text, re.I)
            for match in obfuscated:
                email = f"{match[0]}@{match[1]}.{match[2]}"
                self.emails.add(email)
                strategies_found.append('obfuscated')
        
        print(f"    Found emails using: {set(strategies_found)}")
    
    def _smart_phone_discovery(self):
        """Intelligent phone number discovery"""
        
        print("  Smart phone discovery...")
        
        # Strategy 1: tel: links
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            tel_links = soup.find_all('a', href=re.compile(r'^tel:', re.I))
            for link in tel_links:
                phone = link['href'].replace('tel:', '').strip()
                self.phones.add(phone)
        
        # Strategy 2: Contact sections
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            contact_sections = soup.find_all(['section', 'div'], class_=re.compile(r'contact', re.I))
            for section in contact_sections:
                # More sophisticated phone pattern
                phones = re.findall(r'[\+]?[(]?\d{1,4}[)]?[-\s\.\(]?\d{1,4}[-\s\.\)]?\d{1,4}[-\s\.]?\d{1,9}', section.get_text())
                self.phones.update(phones)
        
        # Strategy 3: Look for labels like "Phone:", "Tel:", "Call us:"
        for page_data in self.pages_content.values():
            text = page_data['text']
            
            # Find text near phone labels
            phone_patterns = re.finditer(r'(Phone|Tel|Call|Contact)[\s:]+([+\d\s\-\(\)]{10,})', text, re.I)
            for match in phone_patterns:
                phone = match.group(2).strip()
                if len(re.sub(r'\D', '', phone)) >= 10:  # At least 10 digits
                    self.phones.add(phone)
    
    def _extract_employee_info(self):
        """Extract employee names and roles"""
        
        print(" Extracting employee information...")
        
        # Check team/about pages
        target_pages = ['team', 'about', 'homepage']
        
        for page_type in target_pages:
            if page_type not in self.pages_content:
                continue
            
            soup = self.pages_content[page_type]['soup']
            
            # Strategy 1: Find team member cards/sections
            team_sections = soup.find_all(['div', 'section', 'article'], 
                                         class_=re.compile(r'team|member|employee|staff|person', re.I))
            
            for section in team_sections:
                employee = {}
                
                # Extract name (usually in h2, h3, or strong tags)
                name_tag = section.find(['h2', 'h3', 'h4', 'strong', 'b'])
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    # Filter out likely non-names
                    if len(name.split()) >= 2 and len(name) < 50 and not any(char.isdigit() for char in name):
                        employee['name'] = name
                
                # Extract role/title
                role_keywords = ['role', 'title', 'position', 'job']
                for tag in section.find_all(['p', 'span', 'div']):
                    text = tag.get_text(strip=True)
                    if any(kw in tag.get('class', []) for kw in role_keywords) or \
                       any(kw in str(tag.get('id', '')) for kw in role_keywords):
                        employee['role'] = text
                        break
                
                # Extract email if present
                email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', section.get_text())
                if email_match:
                    employee['email'] = email_match.group(0)
                
                if employee.get('name'):
                    self.employees.append(employee)
            
            # Strategy 2: LinkedIn profile links (indicates employee listing)
            linkedin_links = soup.find_all('a', href=re.compile(r'linkedin\.com/in/', re.I))
            for link in linkedin_links:
                # Try to find associated name
                parent = link.find_parent(['div', 'section', 'article'])
                if parent:
                    name_tag = parent.find(['h2', 'h3', 'h4', 'strong'])
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        if len(name.split()) >= 2:
                            self.employees.append({
                                'name': name,
                                'linkedin': link['href']
                            })
        
        print(f"    Found {len(self.employees)} employees")
    
    def _extract_location_info(self):
        """Extract location information from multiple sources"""
        
        print(" Extracting location information...")
        
        # Strategy 1: Structured data (schema.org)
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            
            # Look for address schema
            addresses = soup.find_all(['div', 'span', 'p'], attrs={'itemprop': 'address'})
            for addr in addresses:
                location = addr.get_text(strip=True)
                self.locations.add(location)
        
        # Strategy 2: Contact/Location pages
        target_pages = ['contact', 'locations', 'about', 'homepage']
        
        for page_type in target_pages:
            if page_type not in self.pages_content:
                continue
            
            soup = self.pages_content[page_type]['soup']
            text = self.pages_content[page_type]['text']
            
            # Look for address patterns
            address_sections = soup.find_all(['div', 'section'], class_=re.compile(r'address|location|office', re.I))
            for section in address_sections:
                location = section.get_text(separator=' ', strip=True)
                if 20 < len(location) < 200:  # Reasonable length
                    self.locations.add(location)
            
            # Pattern: City, State/Country
            location_patterns = re.findall(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*),\s*([A-Z]{2,}|[A-Z][a-z]+)', text)
            for city, state_country in location_patterns:
                self.locations.add(f"{city}, {state_country}")
        
        print(f"    Found {len(self.locations)} locations")
    
    def _discover_social_media(self):
        """Discover social media profiles"""
        
        print(" Discovering social media profiles...")
        
        social_patterns = {
            'linkedin': r'linkedin\.com/(company|in)/([^/\s"\']+)',
            'twitter': r'twitter\.com/([^/\s"\']+)',
            'facebook': r'facebook\.com/([^/\s"\']+)',
            'instagram': r'instagram\.com/([^/\s"\']+)',
            'youtube': r'youtube\.com/(channel|c|user)/([^/\s"\']+)',
        }
        
        for page_data in self.pages_content.values():
            soup = page_data['soup']
            
            # Check all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                for platform, pattern in social_patterns.items():
                    match = re.search(pattern, href, re.I)
                    if match:
                        self.social_media[platform] = href
                        break
        
        print(f"    Found {len(self.social_media)} social media profiles")
    
    def _validate_emails(self, emails: List[str]) -> List[Dict]:
        """Validate and score emails"""
        
        validated = []
        
        # Common spam/invalid patterns
        blacklist = ['example.com', 'test.com', 'domain.com', 'email.com', 
                     'wixpress.com', 'placeholder', 'yourcompany']
        
        for email in emails:
            email = email.lower().strip()
            
            # Skip blacklisted
            if any(bl in email for bl in blacklist):
                continue
            
            # Skip if doesn't match domain
            email_domain = email.split('@')[-1]
            
            # Validate format
            try:
                validate_email(email, check_deliverability=False)
                is_valid = True
            except:
                is_valid = False
            
            if not is_valid:
                continue
            
            # Calculate confidence
            confidence = 0.5
            
            # Higher confidence for domain match
            if self.domain in email_domain or email_domain in self.domain:
                confidence += 0.3
            
            # Higher confidence for common business emails
            if any(prefix in email for prefix in ['info@', 'contact@', 'hello@', 'support@']):
                confidence += 0.1
            
            # Lower confidence for personal emails
            if any(suffix in email_domain for suffix in ['gmail.com', 'yahoo.com', 'hotmail.com']):
                confidence -= 0.2
            
            validated.append({
                'email': email,
                'confidence': round(max(0.1, min(1.0, confidence)), 2),
                'is_company_email': self.domain in email_domain or email_domain in self.domain,
            })
        
        # Sort by confidence
        validated.sort(key=lambda x: x['confidence'], reverse=True)
        
        return validated
    
    def _validate_phones(self, phones: List[str]) -> List[Dict]:
        """Validate and format phone numbers"""
        
        validated = []
        seen = set()
        
        for phone in phones:
            # Clean phone number
            clean = re.sub(r'\D', '', phone)
            
            # Skip if too short or already seen
            if len(clean) < 10 or clean in seen:
                continue
            
            seen.add(clean)
            
            # Try to parse and format
            try:
                parsed = phonenumbers.parse('+' + clean if not phone.startswith('+') else phone, None)
                is_valid = phonenumbers.is_valid_number(parsed)
                formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                
                validated.append({
                    'phone': formatted,
                    'original': phone,
                    'is_valid': is_valid,
                    'confidence': 0.9 if is_valid else 0.5,
                })
            except:
                # Keep original if parsing fails
                validated.append({
                    'phone': phone,
                    'original': phone,
                    'is_valid': False,
                    'confidence': 0.3,
                })
        
        validated.sort(key=lambda x: x['confidence'], reverse=True)
        
        return validated
    
    def _get_primary_location(self) -> Optional[str]:
        """Determine the primary location"""
        
        if not self.locations:
            return None
        
        # Simple heuristic: shortest location is usually the primary one
        return min(self.locations, key=len) if self.locations else None
    
    def _calculate_confidence(self) -> Dict:
        """Calculate confidence scores for different data types"""
        
        return {
            'email_discovery': 'high' if len(self.emails) >= 3 else 'medium' if len(self.emails) >= 1 else 'low',
            'phone_discovery': 'high' if len(self.phones) >= 2 else 'medium' if len(self.phones) >= 1 else 'low',
            'employee_data': 'high' if len(self.employees) >= 5 else 'medium' if len(self.employees) >= 2 else 'low',
            'location_data': 'high' if len(self.locations) >= 2 else 'medium' if len(self.locations) >= 1 else 'low',
            'overall': self._calculate_overall_confidence(),
        }
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence score"""
        
        score = 0.0
        
        # Email score
        if len(self.emails) >= 3:
            score += 0.25
        elif len(self.emails) >= 1:
            score += 0.15
        
        # Phone score
        if len(self.phones) >= 2:
            score += 0.20
        elif len(self.phones) >= 1:
            score += 0.10
        
        # Employee score
        if len(self.employees) >= 5:
            score += 0.25
        elif len(self.employees) >= 2:
            score += 0.15
        
        # Location score
        if len(self.locations) >= 2:
            score += 0.20
        elif len(self.locations) >= 1:
            score += 0.10
        
        # Social media score
        if len(self.social_media) >= 3:
            score += 0.10
        elif len(self.social_media) >= 1:
            score += 0.05
        
        return round(score, 2)


class ScrapeRequest(BaseModel):
    urls: List[str]
    timeout: Optional[int] = 15
    max_workers: Optional[int] = 4


@app.post('/scrape_intelligent')
def scrape_intelligent(request: ScrapeRequest):
    """Intelligent scraping endpoint"""
    
    if not request.urls:
        raise HTTPException(status_code=400, detail='Provide at least one URL')
    
    results = []
    start = time.time()
    
    def scrape_single(url: str):
        scraper = IntelligentScraper(url, timeout=request.timeout)
        return scraper.scrape_with_intelligence()
    
    with ThreadPoolExecutor(max_workers=request.max_workers) as executor:
        futures = {executor.submit(scrape_single, url): url for url in request.urls}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    'url': futures[future],
                    'error': str(e)
                })
    
    return {
        'took_seconds': round(time.time() - start, 2),
        'count': len(results),
        'results': results,
    }


@app.get('/')
def health():
    return {'status': 'healthy', 'service': 'Intelligent Scraper API'}


if __name__ == '__main__':
    import uvicorn
    
    print('Intelligent Scraper API starting...')
    print('Endpoint: http://127.0.0.1:8001/scrape_intelligent')
    print('Features: Smart email/phone discovery, employee extraction, validation')
    
    uvicorn.run(app, host='0.0.0.0', port=8001)