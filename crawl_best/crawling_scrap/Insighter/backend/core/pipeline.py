"""
Main pipeline orchestrator
"""
import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime

from models.schemas import CompanyAnalysisRequest, CompanyAnalysisResponse, BatchAnalysisResult
from core.scraper import CompanyScraper
from core.analyzer import CompanyAnalyzer
from core.filter import CompanyFilter

class AnalysisPipeline:
    """Orchestrate the entire analysis pipeline"""
    
    def __init__(self):
        self.scraper = CompanyScraper()
        self.analyzer = CompanyAnalyzer()
        self.filter = CompanyFilter()
        
        # In-memory store for results (use Redis in production)
        self.results_store = {}
    
    async def process_request(self, request: CompanyAnalysisRequest) -> CompanyAnalysisResponse:
        """
        Process a company analysis request
        """
        request_id = str(uuid.uuid4())
        
        # Create response
        response = CompanyAnalysisResponse(
            request_id=request_id,
            status="processing",
            total_companies=len(request.urls),
            successful=0,
            failed=0,
            estimated_completion=None,
            results_url=f"/api/v1/results/{request_id}"
        )
        
        # Store initial state
        self.results_store[request_id] = {
            'request': request.dict(),
            'status': 'processing',
            'created_at': datetime.now(),
            'results': [],
            'summary': {}
        }
        
        # Run pipeline in background
        asyncio.create_task(self._run_pipeline(request_id, request))
        
        return response

    async def process_request_sync(self, request: CompanyAnalysisRequest) -> BatchAnalysisResult:
        """
        Process a company analysis request synchronously and return full results
        """
        request_id = str(uuid.uuid4())

        # Store initial state
        self.results_store[request_id] = {
            'request': request.dict(),
            'status': 'processing',
            'created_at': datetime.now(),
            'results': [],
            'summary': {}
        }

        # Execute the pipeline synchronously (await completion)
        await self._run_pipeline(request_id, request)

        # After completion, return BatchAnalysisResult via get_results
        results = self.get_results(request_id)
        return results
    
    async def _run_pipeline(self, request_id: str, request: CompanyAnalysisRequest):
        """
        Execute the full pipeline
        """
        try:
            # Step 1: Scrape company websites
            print(f"📥 Step 1: Scraping {len(request.urls)} companies")
            scraped_data = await self.scraper.scrape_companies(request.urls)
            
            # Step 2: Apply filters if provided
            if request.filters:
                print(f"🔍 Step 2: Applying filters")
                filtered_data = self.filter.apply_filters(scraped_data, request.filters)
            else:
                filtered_data = scraped_data
            
            # Step 3: Analyze with LLM
            print(f"🤖 Step 3: Analyzing {len(filtered_data)} companies with LLM")
            analysis_results = await self.analyzer.analyze_batch(filtered_data)
            
            # Step 4: Generate summary
            print(f"📊 Step 4: Generating summary")
            summary = self._generate_summary(analysis_results)
            
            # Update results store
            self.results_store[request_id].update({
                'status': 'completed',
                'completed_at': datetime.now(),
                'results': [r.dict() for r in analysis_results],
                'summary': summary
            })
            
            print(f"✅ Pipeline completed for request {request_id}")
            
        except Exception as e:
            print(f"❌ Pipeline failed for request {request_id}: {str(e)}")
            self.results_store[request_id].update({
                'status': 'failed',
                'completed_at': datetime.now(),
                'error': str(e)
            })
    
    def _generate_summary(self, results: List) -> Dict[str, Any]:
        """Generate analysis summary"""
        successful = [r for r in results if r.status == 'success']
        failed = [r for r in results if r.status == 'failed']
        
        if not successful:
            return {'error': 'No successful analyses'}
        
        # Calculate averages
        avg_confidence = sum(r.data.confidence_score for r in successful) / len(successful)
        avg_sentiment = sum(r.data.sentiment_score for r in successful) / len(successful)
        
        # Industry distribution
        industries = {}
        for r in successful:
            for industry in r.data.industry:
                industries[industry] = industries.get(industry, 0) + 1
        
        # Company size distribution
        sizes = {}
        for r in successful:
            size = r.data.employee_size
            sizes[size] = sizes.get(size, 0) + 1
        
        # Business model distribution
        business_models = {}
        for r in successful:
            model = r.data.business_model
            business_models[model] = business_models.get(model, 0) + 1
        
        return {
            'total_companies': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'avg_confidence_score': round(avg_confidence, 2),
            'avg_sentiment_score': round(avg_sentiment, 2),
            'total_tokens_used': sum(r.tokens_used for r in results),
            'avg_processing_time': sum(r.processing_time for r in results) / len(results),
            'industry_distribution': dict(sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]),
            'company_size_distribution': sizes,
            'business_model_distribution': business_models
        }
    
    def get_results(self, request_id: str) -> Dict[str, Any]:
        """Get results by request ID"""
        if request_id not in self.results_store:
            return None
        
        result_data = self.results_store[request_id]
        
        if result_data['status'] == 'processing':
            return {'status': 'processing', 'message': 'Analysis in progress'}
        
        # Create BatchAnalysisResult
        if result_data['status'] == 'completed':
            from models.schemas import AnalysisResult
            
            results = []
            for r in result_data['results']:
                results.append(AnalysisResult(**r))
            
            return BatchAnalysisResult(
                request_id=request_id,
                created_at=result_data['created_at'],
                completed_at=result_data['completed_at'],
                total_companies=len(results),
                successful=sum(1 for r in results if r.status == 'success'),
                failed=sum(1 for r in results if r.status == 'failed'),
                results=results,
                summary=result_data['summary']
            )
        
        return {'status': 'failed', 'error': result_data.get('error')}