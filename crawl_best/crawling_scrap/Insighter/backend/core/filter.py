"""
Company filtering system
"""
from typing import List, Dict, Any

class CompanyFilter:
    """Filter companies based on criteria"""
    
    def apply_filters(self, companies: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to companies"""
        if not filters:
            return companies
        
        filtered = []
        
        for company in companies:
            if self._matches_filters(company, filters):
                filtered.append(company)
        
        return filtered
    
    def _matches_filters(self, company: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if company matches all filters"""
        
        # Extract AI data if available
        ai_data = company.get('ai_extracted_data', {})
        
        # Industry filter
        if 'industries' in filters:
            company_industries = set(i.lower() for i in ai_data.get('industry', []))
            required_industries = set(i.lower() for i in filters['industries'])
            
            if not company_industries.intersection(required_industries):
                return False
        
        # Employee size filter
        if 'employee_size' in filters:
            company_size = ai_data.get('employee_size', '').lower()
            required_sizes = [s.lower() for s in filters['employee_size']]
            
            if company_size not in required_sizes and company_size != 'unknown':
                return False
        
        # Technology filter
        if 'technologies' in filters:
            company_tech = set(t.lower() for t in ai_data.get('technology_stack', []))
            required_tech = set(t.lower() for t in filters['technologies'])
            
            if not company_tech.intersection(required_tech):
                return False
        
        # Certification filter
        if 'certifications' in filters:
            company_certs = set(c.lower() for c in ai_data.get('certifications', []))
            required_certs = set(c.lower() for c in filters['certifications'])
            
            if not company_certs.intersection(required_certs):
                return False
        
        # Confidence score filter
        if 'min_confidence' in filters:
            confidence = float(ai_data.get('confidence_score', 0))
            if confidence < filters['min_confidence']:
                return False
        
        return True