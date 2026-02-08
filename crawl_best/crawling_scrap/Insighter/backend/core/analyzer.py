"""
Company data analyzer using LLM
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from utils.llm_client import LLMClient
from utils.token_optimizer import TokenOptimizer
from models.schemas import CompanyData, AnalysisResult

class CompanyAnalyzer:
    """Analyze scraped company data using LLM"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.optimizer = TokenOptimizer()
        # Simple keyword lists for extraction
        self._tech_keywords = set([
            'python','java','javascript','node.js','node','react','angular','vue','django','flask',
            'aws','azure','gcp','docker','kubernetes','k8s','terraform','ansible','postgres','mysql',
            'mongodb','redis','spark','hadoop','pandas','numpy','tensorflow','pytorch','ml','ai','saas',
            'microservice','graphql','rest','api','spark','scala','go','golang'
        ])

        self._industry_keywords = set([
            'finance','health','healthcare','education','retail','ecommerce','manufacturing','automotive',
            'telecom','media','entertainment','gaming','insurance','banking','energy','logistics','transport',
            'real estate','construction','agriculture'
        ])
    
    async def analyze_batch(self, scraped_data: List[Dict[str, Any]]) -> List[AnalysisResult]:
        """
        Analyze a batch of scraped companies
        """
        results = []
        
        # Process companies in batches
        for i in range(0, len(scraped_data), settings.BATCH_SIZE):
            batch = scraped_data[i:i + settings.BATCH_SIZE]
            
            # Create analysis tasks
            tasks = []
            for company_data in batch:
                task = self._analyze_single_company(company_data)
                tasks.append(task)
            
            # Run batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(AnalysisResult(
                        url="unknown",
                        status="failed",
                        error=str(result),
                        processing_time=0,
                        tokens_used=0
                    ))
                else:
                    results.append(result)
            
            # Add delay between batches to avoid rate limiting
            if i + settings.BATCH_SIZE < len(scraped_data):
                await asyncio.sleep(1)
        
        return results

    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Simple keyword extractor: find tech and industry keywords by frequency."""
        if not text:
            return {'technologies': [], 'industries': []}

        txt = text.lower()
        # count occurrences
        tech_counts = {}
        for kw in self._tech_keywords:
            if kw in txt:
                tech_counts[kw] = txt.count(kw)

        industry_counts = {}
        for kw in self._industry_keywords:
            if kw in txt:
                industry_counts[kw] = txt.count(kw)

        # sort by frequency
        techs = [k for k, v in sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)]
        industries = [k for k, v in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)]

        return {'technologies': techs, 'industries': industries}
    
    async def _analyze_single_company(self, company_data: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze a single company
        """
        start_time = datetime.now()
        
        try:
            # Call LLM for analysis
            analysis_result = await self.llm_client.analyze_company(company_data)
            
            # Extract tokens used
            tokens_used = analysis_result.pop('tokens_used', 0)
            
            # Convert to CompanyData schema
            company_data_obj = CompanyData(
                company_name=analysis_result.get('company_name', 'Unknown'),
                domain=company_data.get('domain', ''),
                description=analysis_result.get('description', ''),
                industry=analysis_result.get('industry', []),
                employee_size=analysis_result.get('employee_size', 'unknown'),
                founded_year=analysis_result.get('founded_year'),
                headquarters=analysis_result.get('headquarters', 'unknown'),
                revenue_range=analysis_result.get('revenue_range', 'unknown'),
                business_model=analysis_result.get('business_model', 'Other'),
                target_market=analysis_result.get('target_market', []),
                products_services=analysis_result.get('products_services', []),
                technology_stack=analysis_result.get('technology_stack', []),
                certifications=analysis_result.get('certifications', []),
                key_clients=analysis_result.get('key_clients', []),
                competitive_advantage=analysis_result.get('competitive_advantage', []),
                risks=analysis_result.get('risks', []),
                opportunities=analysis_result.get('opportunities', []),
                sentiment_score=float(analysis_result.get('sentiment_score', 0)),
                confidence_score=float(analysis_result.get('confidence_score', 0)),
                scraped_at=datetime.now(),
                analyzed_at=datetime.now()
            )

            # If LLM returned low-confidence or was a fallback, create a local synthesis
            synthesis = None
            if not analysis_result.get('tokens_used') or float(analysis_result.get('confidence_score', 0)) == 0:
                # Build a concise synthesis from scraped content and extract keywords
                name = company_data.get('company_name') or company_data.get('domain') or company_data.get('original_url','')
                homepage = company_data.get('pages_content', {}).get('homepage', {}) if isinstance(company_data.get('pages_content', {}), dict) else {}
                title = homepage.get('title') or ''
                paragraphs = homepage.get('paragraphs', []) or []
                lists = homepage.get('list_items', []) or []
                full_text = (homepage.get('full_text', '') or '') + ' ' + ' '.join(paragraphs[:5]) + ' ' + ' '.join(lists[:10])

                # Extract technology and industry keywords
                keywords = self._extract_keywords(full_text)
                techs = keywords.get('technologies', [])
                industries = keywords.get('industries', [])

                # Update company_data_obj fields if missing
                if not company_data_obj.technology_stack and techs:
                    company_data_obj.technology_stack = techs[:8]
                if (not company_data_obj.industry or company_data_obj.industry == []) and industries:
                    company_data_obj.industry = industries[:3]

                parts = []
                # Lead: concise description
                if company_data_obj.description and company_data_obj.description != 'No description available.':
                    parts.append(company_data_obj.description.rstrip('.'))
                elif title:
                    parts.append(f"{name}: {title}")
                elif lists:
                    parts.append(f"{name} offers {lists[0] if isinstance(lists[0], str) else 'several services'}")
                else:
                    parts.append(f"{name} provides digital products and services")

                # Tech/Industry highlight
                if techs:
                    parts.append(f"Key technologies mentioned: {', '.join(techs[:6])}.")
                if industries:
                    parts.append(f"Relevant industries: {', '.join(industries[:3])}.")

                # Products/services
                if lists:
                    top = [str(x) for x in lists[:5]]
                    parts.append(f"Notable offerings include: {', '.join(top)}.")

                # Recommendation and confidence note
                parts.append("Recommendation: confirm market focus and add customer case studies to improve confidence in analysis.")

                synthesis = ' '.join(parts)
                company_data_obj.llm_synthesis = synthesis
                company_data_obj.llm_raw = analysis_result
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AnalysisResult(
                url=company_data.get('original_url', ''),
                status="success",
                data=company_data_obj,
                error=None,
                processing_time=processing_time,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AnalysisResult(
                url=company_data.get('original_url', ''),
                status="failed",
                data=None,
                error=str(e),
                processing_time=processing_time,
                tokens_used=0
            )