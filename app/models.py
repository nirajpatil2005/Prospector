from pydantic import BaseModel, Field
from typing import List, Optional

# --- Configuration Models ---

class SearchConfig(BaseModel):
    included_industries: List[str] = Field(..., description="List of industries to include")
    excluded_industries: Optional[List[str]] = Field(default=[], description="List of industries to exclude")
    required_keywords: List[str] = Field(..., description="Keywords that must be present")
    excluded_keywords: Optional[List[str]] = Field(default=[], description="Keywords to exclude")
    min_employees: Optional[int] = Field(None, description="Minimum number of employees")
    max_employees: Optional[int] = Field(None, description="Maximum number of employees")
    target_countries: List[str] = Field(..., description="Target countries or regions")
    excluded_countries: Optional[List[str]] = Field(default=[], description="Countries to exclude")
    required_certifications: Optional[List[str]] = Field(default=[], description="Required certifications (e.g., ISO 9001)")
    required_product_categories: Optional[List[str]] = Field(default=[], description="Specific product categories required")

# --- Intermediate Data Models ---

class CompanyBasicInfo(BaseModel):
    name: str
    url: str
    snippet: Optional[str] = None
    location: Optional[str] = None
    source: str = "search_result"

class ScrapedContent(BaseModel):
    url: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    meta_description: Optional[str] = None
    page_title: Optional[str] = None
    sub_pages: dict = Field(default_factory=dict, description="Content from sub-pages like About, Contact")

# --- Analysis Models (Output) ---

class CompanyAnalysis(BaseModel):
    company_name: str
    website: str
    industry_match: bool
    employee_count_estimate: Optional[str]
    locations: List[str]
    certifications: List[str]
    product_categories: List[str]
    summary: str
    contact_info: Optional[str]
    # Financials & Strategy
    estimated_revenue: Optional[str] = "Unknown"
    market_cap: Optional[str] = "Unknown"
    strategic_goals: List[str] = []
    # LinkedIn Specific
    linkedin_url: Optional[str] = None
    follower_count: Optional[int] = None
    founded_year: Optional[int] = None
    specialties: List[str] = []
    relevance_score: int = Field(..., description="Score from 0-100 indicating fit with requirements")
