import os
from google import genai
import json
import asyncio
import time
from app.models import CompanyAnalysis, ScrapedContent, SearchConfig
from typing import List, Optional
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()

# --- Initialize Gemini ---
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# --- Initialize Groq ---
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = None
if groq_api_key and Groq:
    groq_client = Groq(api_key=groq_api_key)

# Global semaphore to limit concurrent Gemini API calls
gemini_semaphore = asyncio.Semaphore(1) 

async def call_llm(prompt: str) -> Optional[str]:
    """
    Robust LLM Caller:
    1. Tries Gemini 2.0 Flash (Primary)
    2. Falls back to Groq Llama 3.3 70B (Secondary)
    3. Returns None if both fail.
    """
    # Attempt 1: Gemini
    if client:
        # Use semaphore only for Gemini as it has strict rate limits
        async with gemini_semaphore:
            try:
                # Slight delay to respect RPM
                await asyncio.sleep(0.5)
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                return response.text
            except Exception as e:
                print(f"WARN: Gemini API Failure ({type(e).__name__}). Switching to Groq fallback...", flush=True)
    
    # Attempt 2: Groq
    if groq_client:
        try:
            print("INFO: Calling Groq (llama-3.3-70b-versatile)...", flush=True)
            chat_completion = await asyncio.to_thread(
                groq_client.chat.completions.create,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"ERROR: Groq API Failure: {e}", flush=True)
            
    print("CRITICAL: Both AI services failed.", flush=True)
    return None

async def analyze_companies(scraped_data: dict[str, ScrapedContent], config: SearchConfig) -> List[CompanyAnalysis]:
    """
    Analyzes scraped data to extract structured company information.
    """
    analyzed_companies = []
    
    # We create tasks but they will be throttled by the semaphore inside the function
    tasks = [analyze_single_company(content, config) for content in scraped_data.values()]
    
    # Run all tasks (they will respect the semaphore)
    results = await asyncio.gather(*tasks)
    
    for analysis in results:
        if analysis:
            analyzed_companies.append(analysis)
            
    return analyzed_companies

async def analyze_single_company(content: ScrapedContent, config: SearchConfig) -> Optional[CompanyAnalysis]:
    # Fallback data if AI fails
    fallback_analysis = CompanyAnalysis(
        company_name=content.page_title or "Unknown Company",
        website=content.url,
        industry_match=False, # Unknown
        employee_count_estimate="Unknown",
        locations=[],
        certifications=[],
        product_categories=[],
        summary=content.meta_description or "No summary available (Analysis Failed).",
        contact_info=None,
        relevance_score=0
    )

    # Ultra-concise context to save tokens
    context_text = f"URL:{content.url}\nT:{content.page_title}\nD:{content.meta_description}\nTXT:{content.text_content[:1500]}..."
    
    for cat, text in content.sub_pages.items():
        context_text += f"\n{cat.upper()}:{text[:500]}..."

    prompt = f"""
    Analyze company vs reqs:
    Reqs: Ind:{config.included_industries}, Loc:{config.target_countries}, Key:{config.required_keywords}
    
    Data:
    {context_text}
    
    Output JSON (no markdown):
    {{
    "company_name": "str",
    "website": "{content.url}",
    "industry_match": bool,
    "employee_count_estimate": "str/Unknown",
    "locations": ["str"],
    "certifications": ["str"],
    "product_categories": ["str"],
    "summary": "Short 1-sentence summary",
    "contact_info": "email/phone/Unknown",
    "relevance_score": int(0-100)
    }}
    """

    text_response = await call_llm(prompt)
    if not text_response:
        print(f"Failed to analyze {content.url} after retries. Using fallback.")
        return fallback_analysis

    try:
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        data = json.loads(text_response)
        
        # Ensure data matches model
        data['website'] = content.url
        
        return CompanyAnalysis(**data)

    except Exception as e:
        print(f"Error analyzing {content.url}: {e}")
        return fallback_analysis


async def extract_candidate_urls(content: ScrapedContent) -> List[dict]:
    """
    Analyzes listicle/directory content to find external company URLs.
    Returns: [{"name": "Company Name", "url": "https://company.com"}, ...]
    """
    # Context specifically for URL extraction
    context_text = f"Title: {content.page_title}\n\nText Content Snippet:\n{content.text_content[:20000]}..." 
    
    prompt = """
    Task: Extract companies and their websites from this text.
    Target: Valid external B2B/company homepages. 
    Ignore: Social media (linkedin, facebook), internal links, news articles, or directories (clutch, yelp).
    
    Output strictly a RAW JSON list of objects:
    [{"name": "Company Name", "url": "https://company-website.com"}]
    
    If no companies are found, return [].
    """
    
    text_response = await call_llm(prompt + "\n\nText:\n" + context_text)

    if text_response:
        try:
            print(f"DEBUG: Extracting from {content.url} (len: {len(context_text)})", flush=True)
            text_response = text_response.replace("```json", "").replace("```", "").strip()
            candidates = json.loads(text_response)
            if isinstance(candidates, list):
                valid_candidates = []
                for c in candidates:
                    url = c.get("url", "").lower()
                    name = c.get("name", "")
                    if "http" in url and name:
                        valid_candidates.append(c)
                
                if valid_candidates:
                    print(f"DEBUG: Found {len(valid_candidates)} valid candidates via LLM from {content.url}", flush=True)
                    return valid_candidates
        except Exception as e:
            print(f"Error extracting URLs from {content.url}: {e}", flush=True)

    # --- Regex Fallback if LLM fails ---
    print(f"DEBUG: LLM failed to extract meaningful URLs from {content.url}. Using Regex fallback...", flush=True)
    import re
    from urllib.parse import urlparse
    
    # Simple regex to find http/https links
    raw_links = re.findall(r'https?://[^\s<>"]+', content.text_content)
    
    unique_links = set()
    fallback_candidates = []
    
    current_domain = urlparse(content.url).netloc
    
    excluded_domains = [
        "linkedin.com", "facebook.com", "twitter.com", "instagram.com", "youtube.com", 
        "google.com", "github.com", "microsoft.com", "apple.com", "adobe.com",
        "cloudflare.com", "googletagmanager.com", "w3.org", "schema.org",
        current_domain # Exclude self
    ]
    
    for link in raw_links:
        # cleanup
        link = link.rstrip('.,;)]}')
        
        try:
            parsed = urlparse(link)
            domain = parsed.netloc.lower()
            
            if not domain or any(ex in domain for ex in excluded_domains):
                continue
                
            # Filter file extensions
            if any(link.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.json', '.xml']):
                continue
                
            if link not in unique_links:
                unique_links.add(link)
                # Create a simple candidate object
                fallback_candidates.append({"name": f"Extracted: {domain}", "url": link})
        except:
            continue
            
    # Limit fallback to top 15 to avoid junk
    print(f"DEBUG: Regex fallback found {len(fallback_candidates)} potential links.", flush=True)
    return fallback_candidates[:15]

async def analyze_linkedin_company(data: dict, config: SearchConfig) -> Optional[CompanyAnalysis]:
    """
    Analyzes structured LinkedIn data using Gemini.
    """
    company_name = data.get("name", "Unknown Company")
    linkedin_url = data.get("url", "")
    website = data.get("website", "") or linkedin_url
    
    # Construct context from LinkedIn data
    about = data.get("about", "") or data.get("description", "")
    tagline = data.get("tagline", "")
    industry = data.get("industry", "")
    specialties = data.get("specialties", [])
    followers = data.get("followerCount", 0)
    confirmed_locations = data.get("locations", [])
    
    context_text = f"""
    Company: {company_name}
    LinkedIn: {linkedin_url}
    Website: {website}
    Tagline: {tagline}
    About: {about[:5000]}
    Industry: {industry}
    Specialties: {', '.join(specialties) if isinstance(specialties, list) else specialties}
    Followers: {followers}
    Locations: {confirmed_locations}
    """
    
    prompt = f"""
    Analyze this LinkedIn profile against requirements:
    Reqs: Ind:{config.included_industries}, Loc:{config.target_countries}, Key:{config.required_keywords}
    
    Data:
    {context_text}
    
    Output JSON (no markdown):
    {{
    "company_name": "str",
    "website": "str (prefer external website if available)",
    "industry_match": bool,
    "employee_count_estimate": "str/Unknown",
    "locations": ["str"],
    "certifications": ["str"],
    "product_categories": ["str"],
    "summary": "Short 1-sentence summary",
    "contact_info": "email/phone/Unknown",
    "linkedin_url": "{linkedin_url}",
    "follower_count": int,
    "founded_year": int or null,
    "specialties": ["str"],
    "relevance_score": int(0-100)
    }}
    """
    
    text_response = await call_llm(prompt)
    if not text_response: return None

    try:
        text_response = text_response.replace("```json", "").replace("```", "").strip()
        result = json.loads(text_response)
        
        # Fill in missing fields from raw data if LLM missed them
        if "linkedin_url" not in result or not result["linkedin_url"]:
            result["linkedin_url"] = linkedin_url
        if "follower_count" not in result:
            result["follower_count"] = followers
        if "specialties" not in result:
                result["specialties"] = specialties if isinstance(specialties, list) else []

        return CompanyAnalysis(**result)

    except Exception as e:
        print(f"Error analyzing LinkedIn data for {company_name}: {e}", flush=True)
    
    return None

async def generate_market_insights(companies: List[CompanyAnalysis]) -> str:
    """
    Generates a high-level market insights report based on the analyzed companies.
    """
    if not companies:
        return "Not enough data to generate insights."

    # Manual Table Construction (Fallback & Data Prep)
    table_header = "| Company Name | Location | EST. Revenue | Est. Employees | Relevance |"
    table_divider = "|---|---|---|---|---|"
    table_rows = []
    
    for c in companies:
        loc = c.locations[0] if c.locations else "Unknown"
        emp = c.employee_count_estimate or "Unknown"
        rev = c.estimated_revenue or "Unknown"
        rel = c.relevance_score
        table_rows.append(f"| {c.company_name} | {loc} | {rev} | {emp} | {rel}/100 |")
    
    manual_table = "\n".join([table_header, table_divider] + table_rows)
    
    # AI Report Generation
    company_summaries = []
    for c in companies:
        goals = ", ".join(c.strategic_goals[:2]) if c.strategic_goals else "None"
        company_summaries.append(f"- {c.company_name}: {c.summary}. Revenue: {c.estimated_revenue}. Goals: {goals}")
    
    context = "\n".join(company_summaries)
    
    prompt = f"""
    Synthesize a Comprehensive Market Research Report based on these analyzed companies:
    
    {context}
    
    Output a professional markdown report in this format:
    # Market Landscape
    [Key trends, commonalities, and financial health of the sector]
    
    # Competitive Analysis
    [Market leaders vs emerging players based on revenue/size]
    
    # Strategic Opportunities
    [Gaps or potential engagement areas based on company goals]
    
    # Financial Benchmarks
    [INSERT MARKDOWN TABLE HERE]
    
    **Benchmark Table Instructions**:
    Create a markdown table comparing all companies on:
    | Company Name | Est. Revenue | Location | Key Strategic Focus | Relevance Score |
    
    Keep it concise.
    """
    
    text_response = await call_llm(prompt)
    
    if text_response:
        return text_response
    
    # If LLM fails, return manual table
    return f"""
    # Market Analysis (Auto-Generated)
    
    The AI could not generate a textual summary at this time. However, here is the comparative data:
    
    ## Financial Benchmark Table
    {manual_table}
    """

async def discover_companies_with_gemini(config: SearchConfig, limit: int = 5) -> List[dict]:
    """
    Uses Gemini to verify/find companies based on its internal knowledge (Fast Mode).
    """
    fallback_data = [
        {"name": "Google (System Fallback)", "url": "https://google.com", "snippet": "Demonstration Data: The AI API failed to respond."},
        {"name": "Microsoft (System Fallback)", "url": "https://microsoft.com", "snippet": "Demonstration Data: The AI API failed to respond."},
        {"name": "OpenAI (System Fallback)", "url": "https://openai.com", "snippet": "Demonstration Data: The AI API failed to respond."}
    ]

    print(f"DEBUG: Discovering with Gemini. Config: Ind={config.included_industries}, Loc={config.target_countries}", flush=True)

    async def get_companies(prompt_text):
        text = await call_llm(prompt_text)
        if not text: return []

        try:
            text = text.replace("```json", "").replace("```", "").strip()
            # Handle potential markdown wrapping or prefixes
            if "[" not in text: 
                print(f"DEBUG: Invalid JSON format: {text[:100]}")
                return []
            
            # Find closest bracket if there's preamble
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end != -1:
                text = text[start:end]

            print(f"DEBUG: Raw response len: {len(text)}", flush=True)
            data = json.loads(text)
            return data
        except Exception as e:
            print(f"DEBUG: Discovery parsing failed: {type(e).__name__}: {e}")
            return []

    # Attempt 1: Strict/Specific Search
    prompt_1 = f"""
    Task: Identify {limit} companies relevant to:
    Industry: {config.included_industries}
    Keywords: {config.required_keywords}
    Location: {config.target_countries}
    
    CRITICAL INSTRUCTION:
    - Return ONLY the official homepage URL for the company.
    - DO NOT return links to news articles, blog posts, definitions, or directories (like Wikipedia, Clutch, LinkedIn, etc.).
    - If the official site is not found, exclude the company.
    
    Output strictly a RAW JSON list of objects:
    [
      {{
        "name": "Company Name",
        "url": "https://company-official-website.com", 
        "snippet": "Brief description."
      }}
    ]
    """
    
    results = await get_companies(prompt_1)
    if results: return results
    
    print("DEBUG: Primary search returned empty. Retrying with broader scope...", flush=True)
    
    # Attempt 2: Industry Broad Search
    prompt_2 = f"""
    Task: List {limit} major companies in the '{config.included_industries}' industry.
    Ignore other constraints if necessary. Return JSON list as above.
    """
    results = await get_companies(prompt_2)
    if results: return results
    
    print("DEBUG: Industry search returned empty. Retrying with generic fallback...", flush=True)

    # Attempt 3: Generic Fallback (Guarantee)
    prompt_3 = f"""
    Task: List {limit} major global technology or service companies.
    Return JSON list as above.
    """
    results = await get_companies(prompt_3)
    if results: return results

    # Attempt 4: Total Failure (Nuclear Option)
    print("CRITICAL: All AI attempts failed. Using Hardcoded Fallback.", flush=True)
    return fallback_data

async def enrich_company_with_gemini(company: dict, config: SearchConfig) -> Optional[CompanyAnalysis]:
    """
    Analyzes a company using Gemini's internal knowledge base (No scraping).
    """
    name = company.get("name", "Unknown")
    url = company.get("url", "")
    snippet = company.get("snippet", "")
    
    prompt = f"""
    Analyze the company "{name}" ({url}).
    Context: {snippet}
    
    Task: Populate the following fields based on your knowledge of this company.
    
    Requirements check:
    - Included Industries: {config.included_industries}
    - Target Locations: {config.target_countries}
    - Required Keywords: {config.required_keywords}

    Output JSON (no markdown):
    {{
    "company_name": "{name}",
    "website": "{url}",
    "industry_match": bool,
    "employee_count_estimate": "str (e.g. 50-200)",
    "locations": ["City, Country"],
    "certifications": ["str"],
    "product_categories": ["str"],
    "summary": "Professional summary",
    "contact_info": "email/phone/Unknown",
    "estimated_revenue": "str (e.g. $10M+)",
    "market_cap": "str (e.g. Private or $1B)",
    "strategic_goals": ["Goal 1", "Goal 2"],
    "linkedin_url": "https://linkedin.com/company/...", 
    "follower_count": int (estimate),
    "founded_year": int,
    "specialties": ["str"],
    "relevance_score": int(0-100)
    }}
    """
    
    text_response = await call_llm(prompt)
    if not text_response: return None

    try:
        text = text_response.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        # Ensure defaults
        if "linkedin_url" not in data: data["linkedin_url"] = ""
        if "follower_count" not in data: data["follower_count"] = 0
        if "specialties" not in data: data["specialties"] = []
        if "strategic_goals" not in data: data["strategic_goals"] = []
        if "estimated_revenue" not in data: data["estimated_revenue"] = "Unknown"
        if "market_cap" not in data: data["market_cap"] = "Unknown"
        
        return CompanyAnalysis(**data)
    except Exception as e:
        print(f"Enrichment Error for {name}: {e}")
        return None
