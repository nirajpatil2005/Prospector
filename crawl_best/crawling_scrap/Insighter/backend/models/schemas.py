"""
Pydantic schemas for data validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CompanyAnalysisRequest(BaseModel):
    """Request model for company analysis"""
    urls: List[str] = Field(..., min_items=1, max_items=50)
    analysis_type: str = Field("comprehensive", pattern="^(comprehensive|financial|technical|market)$")
    filters: Optional[Dict[str, Any]] = None
    
class CompanyAnalysisResponse(BaseModel):
    """Response model for company analysis"""
    request_id: str
    status: str
    total_companies: int
    successful: int
    failed: int
    estimated_completion: Optional[str] = None
    results_url: Optional[str] = None

class CompanyData(BaseModel):
    """Structured company data"""
    company_name: str
    domain: str
    description: str
    industry: List[str]
    employee_size: str
    founded_year: Optional[str]
    headquarters: str
    revenue_range: Optional[str]
    business_model: str
    target_market: List[str]
    products_services: List[str]
    technology_stack: List[str]
    certifications: List[str]
    key_clients: List[str]
    competitive_advantage: List[str]
    risks: List[str]
    opportunities: List[str]
    sentiment_score: float = Field(ge=-1, le=1)
    confidence_score: float = Field(ge=0, le=1)
    scraped_at: datetime
    analyzed_at: datetime
    llm_synthesis: Optional[str] = None
    llm_raw: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Full analysis result"""
    url: str
    status: str
    data: Optional[CompanyData] = None
    error: Optional[str] = None
    processing_time: float
    tokens_used: int

class BatchAnalysisResult(BaseModel):
    """Batch analysis results"""
    request_id: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_companies: int
    successful: int
    failed: int
    results: List[AnalysisResult]
    summary: Dict[str, Any]