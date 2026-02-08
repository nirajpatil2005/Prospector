"""
LLM client for Groq/OpenAI API
"""
import os
import json
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

class LLMClient:
    """Client for LLM API calls"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.setup_client()
    
    def setup_client(self):
        """Setup HTTP client based on provider"""
        if self.provider == "groq":
            self.api_key = settings.GROQ_API_KEY
            self.base_url = "https://api.groq.com/openai/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "openai":
            self.api_key = settings.OPENAI_API_KEY
            self.base_url = "https://api.openai.com/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def analyze_company(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze scraped company data using LLM
        """
        # If API key or provider not configured, return a simple heuristic fallback
        if not getattr(self, 'api_key', None):
            # Basic heuristic/fallback analysis (no LLM)
            domain = scraped_data.get('domain') or scraped_data.get('original_url', '')
            pages = scraped_data.get('pages_content', {})
            homepage = pages.get('homepage', {}) if isinstance(pages, dict) else {}

            description = homepage.get('key_paragraphs', []) if isinstance(homepage.get('key_paragraphs', None), list) else homepage.get('paragraphs', [])
            description = description[0] if description else 'No description available.'

            products = homepage.get('important_lists', []) if isinstance(homepage.get('important_lists', None), list) else homepage.get('list_items', [])

            # Minimal analysis result matching expected schema
            analysis_result = {
                'company_name': scraped_data.get('company_name') or domain,
                'description': (description[:300] + '...') if len(description) > 300 else description,
                'industry': [],
                'employee_size': 'unknown',
                'founded_year': None,
                'headquarters': 'unknown',
                'revenue_range': 'unknown',
                'business_model': 'Other',
                'target_market': [],
                'products_services': products[:10] if isinstance(products, list) else [],
                'technology_stack': [],
                'certifications': [],
                'key_clients': [],
                'competitive_advantage': [],
                'risks': [],
                'opportunities': [],
                'sentiment_score': 0.0,
                'confidence_score': 0.0,
                'tokens_used': 0
            }

            return analysis_result

        # Prepare optimized prompt with token management
        prompt = self._prepare_analysis_prompt(scraped_data)
        
        messages = [
            {
                "role": "system",
                "content": """You are a company intelligence analyst. Extract and analyze structured information 
                from scraped company data. Be concise, accurate, and focus on key business insights."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 2000,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    tokens_used = result.get("usage", {}).get("total_tokens", 0)
                    
                    # Parse JSON response
                    analysis_result = json.loads(content)
                    analysis_result["tokens_used"] = tokens_used
                    
                    return analysis_result
                else:
                    raise Exception(f"LLM API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            raise Exception(f"LLM analysis failed: {str(e)}")
    
    def _prepare_analysis_prompt(self, scraped_data: Dict[str, Any]) -> str:
        """Prepare optimized prompt for analysis"""
        
        # Extract key content (token optimization)
        company_name = scraped_data.get('company_name', 'Unknown')
        domain = scraped_data.get('domain', '')
        
        # Get page summaries (optimized)
        page_summaries = {}
        for page_type, content in scraped_data.get('pages_content', {}).items():
            page_summaries[page_type] = {
                'title': content.get('title', '')[:100],
                'key_headings': content.get('headings', {}).get('h1', [])[:3] + 
                               content.get('headings', {}).get('h2', [])[:5],
                'key_paragraphs': content.get('paragraphs', [])[:3],
                'list_items': content.get('list_items', [])[:10]
            }
        
        prompt = f"""Analyze this company data and return ONLY a JSON object with the structure below.

Company: {company_name}
Domain: {domain}

Content from website pages:
{json.dumps(page_summaries, indent=2, ensure_ascii=False)}

Extract the following information:

{{
  "company_name": "Full company name (if available, otherwise use domain)",
  "description": "Brief company description (1-2 sentences max)",
  "industry": ["primary industry", "secondary industry (if clear)"],
  "employee_size": "Estimate: 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+, unknown",
  "founded_year": "Year or unknown",
  "headquarters": "City, Country or unknown",
  "revenue_range": "Estimate: <$1M, $1M-$10M, $10M-$50M, $50M-$100M, $100M-$500M, $500M-$1B, $1B+, unknown",
  "business_model": "SaaS, Marketplace, E-commerce, Consulting, Services, Product, Other",
  "target_market": ["B2B", "B2C", "Both"],
  "products_services": ["List main products/services (max 10)"],
  "technology_stack": ["Technologies mentioned (max 8)"],
  "certifications": ["ISO, SOC, HIPAA, etc if mentioned"],
  "key_clients": ["Mentioned clients or partners (max 5)"],
  "competitive_advantage": ["Key differentiators (max 3)"],
  "risks": ["Potential risks/weaknesses (max 3)"],
  "opportunities": ["Growth opportunities (max 3)"],
  "sentiment_score": "Number from -1 (negative) to 1 (positive)",
  "confidence_score": "Number from 0 (low) to 1 (high) based on data availability"
}}

Rules:
1. Only include information you can find in the provided content
2. Use "unknown" if information is not available
3. Be conservative with confidence_score
4. Return ONLY valid JSON, no other text
5. Keep arrays concise (max items as specified)
6. Sentiment: analyze tone of content (positive/neutral/negative)"""
        
        return prompt