"""
Configuration settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "Company Intelligence API"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # LLM Settings
    LLM_PROVIDER: str = "groq"  # groq or openai
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama-3.3-70b-versatile"  # groq model
    # Alternative models: "mixtral-8x7b-32768", "gemma2-9b-it"
    
    # Scraping Settings
    MAX_PAGES_PER_COMPANY: int = 5
    SCRAPE_TIMEOUT: int = 30
    USER_AGENT: str = "CompanyIntelligenceBot/1.0 (+https://example.com/bot)"
    # Crawler service URL (expects crawler/scrap.py FastAPI running)
    CRAWLER_API_URL: str = "http://127.0.0.1:8001/scrape"
    
    # Pipeline Settings
    MAX_TOKENS_PER_ANALYSIS: int = 4000
    BATCH_SIZE: int = 3
    CACHE_RESULTS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()