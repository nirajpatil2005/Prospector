"""
API endpoints
"""
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.schemas import (
    CompanyAnalysisRequest, 
    CompanyAnalysisResponse,
    BatchAnalysisResult
)
from core.pipeline import AnalysisPipeline
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()
pipeline = AnalysisPipeline()

@router.post("/analyze", response_model=CompanyAnalysisResponse)
async def analyze_companies(
    request: CompanyAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze multiple companies
    """
    try:
        # Limit number of companies
        if len(request.urls) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 companies per request"
            )
        
        response = await pipeline.process_request(request)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_sync", response_model=BatchAnalysisResult)
async def analyze_companies_sync(request: CompanyAnalysisRequest):
    """
    Synchronous endpoint: runs the full pipeline and returns results when finished.
    """
    try:
        # Limit number of companies
        if len(request.urls) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 companies per request"
            )

        # Run pipeline synchronously and return full BatchAnalysisResult
        result = await pipeline.process_request_sync(request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_scraped", response_model=BatchAnalysisResult)
async def analyze_scraped(companies: List[Dict[str, Any]]):
    """
    Accept scraped company data (list of dicts) and return LLM analysis results.
    Expected each item to contain at least: 'domain', 'original_url', 'pages_content'
    """
    try:
        # Basic validation
        if not companies:
            raise HTTPException(status_code=400, detail="Provide at least one scraped company item")

        # Analyze using existing analyzer
        analysis_results = await pipeline.analyzer.analyze_batch(companies)

        # Generate summary using pipeline helper
        summary = pipeline._generate_summary(analysis_results)

        # Build BatchAnalysisResult
        from models.schemas import AnalysisResult

        created = datetime.now()
        completed = datetime.now()

        return BatchAnalysisResult(
            request_id="inline",
            created_at=created,
            completed_at=completed,
            total_companies=len(analysis_results),
            successful=sum(1 for r in analysis_results if r.status == 'success'),
            failed=sum(1 for r in analysis_results if r.status == 'failed'),
            results=analysis_results,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{request_id}", response_model=BatchAnalysisResult)
async def get_results(request_id: str):
    """
    Get analysis results by request ID
    """
    results = pipeline.get_results(request_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if isinstance(results, dict) and results.get('status') == 'processing':
        return JSONResponse(
            content=results,
            status_code=202  # Accepted
        )
    
    return results

@router.get("/status/{request_id}")
async def get_status(request_id: str):
    """
    Get analysis status
    """
    results = pipeline.get_results(request_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if isinstance(results, dict):
        return results
    
    return {
        'status': 'completed',
        'total': results.total_companies,
        'successful': results.successful,
        'failed': results.failed
    }