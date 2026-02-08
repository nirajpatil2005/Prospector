"""
Company Filtering System
Applies 18 requirements to filter companies based on scraped + AI-extracted data

Requirements:
1. Included industries
2. Excluded industries  
3. Required keywords
4. Excluded keywords
5. Min employee size
6. Max employee size
7. Target countries/regions
8. Excluded countries
9. Required certifications
10. Required product categories
11. Technology stack
12. Target market (B2B/B2C)
13. Founded year range
14. Has careers page
15. Has contact info
16. Confidence threshold
17. Social media presence
18. Custom filters
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class CompanyFilter:
    def __init__(self):
        self.filters = {}
    
    def set_filter(self, filter_name, value):
        """Set a filter value"""
        self.filters[filter_name] = value
        return self
    
    # Fluent API for easy configuration
    def included_industries(self, industries: List[str]):
        """Industries to include (e.g., ['SaaS', 'Fintech'])"""
        self.filters['included_industries'] = [i.lower() for i in industries]
        return self
    
    def excluded_industries(self, industries: List[str]):
        """Industries to exclude"""
        self.filters['excluded_industries'] = [i.lower() for i in industries]
        return self
    
    def required_keywords(self, keywords: List[str]):
        """Keywords that MUST appear in description/products"""
        self.filters['required_keywords'] = [k.lower() for k in keywords]
        return self
    
    def excluded_keywords(self, keywords: List[str]):
        """Keywords that MUST NOT appear"""
        self.filters['excluded_keywords'] = [k.lower() for k in keywords]
        return self
    
    def employee_size_range(self, min_size: Optional[str] = None, max_size: Optional[str] = None):
        """
        Employee size range
        Sizes: '1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'
        """
        if min_size:
            self.filters['min_employee_size'] = min_size
        if max_size:
            self.filters['max_employee_size'] = max_size
        return self
    
    def target_countries(self, countries: List[str]):
        """Countries to include"""
        self.filters['target_countries'] = [c.lower() for c in countries]
        return self
    
    def excluded_countries(self, countries: List[str]):
        """Countries to exclude"""
        self.filters['excluded_countries'] = [c.lower() for c in countries]
        return self
    
    def required_certifications(self, certs: List[str]):
        """Certifications required (e.g., ['ISO 9001', 'SOC 2'])"""
        self.filters['required_certifications'] = [c.lower() for c in certs]
        return self
    
    def required_product_categories(self, categories: List[str]):
        """Product categories required"""
        self.filters['required_product_categories'] = [c.lower() for c in categories]
        return self
    
    def required_technologies(self, techs: List[str]):
        """Technologies that must be used"""
        self.filters['required_technologies'] = [t.lower() for t in techs]
        return self
    
    def target_market(self, market: str):
        """Target market: 'B2B', 'B2C', or 'Both'"""
        self.filters['target_market'] = market
        return self
    
    def founded_year_range(self, min_year: Optional[int] = None, max_year: Optional[int] = None):
        """Founded year range"""
        if min_year:
            self.filters['min_founded_year'] = min_year
        if max_year:
            self.filters['max_founded_year'] = max_year
        return self
    
    def requires_careers_page(self, required: bool = True):
        """Must have careers page"""
        self.filters['requires_careers_page'] = required
        return self
    
    def requires_contact_info(self, required: bool = True):
        """Must have email or phone"""
        self.filters['requires_contact_info'] = required
        return self
    
    def min_confidence_score(self, score: float):
        """Minimum confidence score (0.0 to 1.0)"""
        self.filters['min_confidence_score'] = score
        return self
    
    def requires_social_media(self, platforms: List[str]):
        """Required social media platforms (e.g., ['linkedin', 'twitter'])"""
        self.filters['required_social_media'] = [p.lower() for p in platforms]
        return self
    
    def apply_filters(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply all filters to companies
        
        Returns:
            {
                'matched': [list of matched companies],
                'rejected': [list of rejected companies with reasons],
                'stats': {statistics}
            }
        """
        
        matched = []
        rejected = []
        
        for company in companies:
            result = self._evaluate_company(company)
            
            if result['passes']:
                matched.append(company)
            else:
                rejected.append({
                    'company': company,
                    'rejection_reasons': result['reasons']
                })
        
        return {
            'matched': matched,
            'rejected': rejected,
            'stats': {
                'total_companies': len(companies),
                'matched': len(matched),
                'rejected': len(rejected),
                'match_rate': f"{(len(matched)/len(companies)*100):.1f}%" if companies else "0%",
                'filters_applied': len(self.filters),
            }
        }
    
    def _evaluate_company(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single company against all filters"""
        
        reasons = []
        ai_data = company.get('ai_extracted_data', {})
        
        # 1. Included industries
        if 'included_industries' in self.filters:
            company_industries = [i.lower() for i in ai_data.get('industry', [])]
            if not any(ind in company_industries for ind in self.filters['included_industries']):
                reasons.append(f"Industry not in included list. Has: {company_industries}")
        
        # 2. Excluded industries
        if 'excluded_industries' in self.filters:
            company_industries = [i.lower() for i in ai_data.get('industry', [])]
            if any(ind in company_industries for ind in self.filters['excluded_industries']):
                reasons.append(f"Industry in excluded list: {company_industries}")
        
        # 3. Required keywords
        if 'required_keywords' in self.filters:
            searchable_text = ' '.join([
                ai_data.get('description', ''),
                ' '.join(ai_data.get('products_services', [])),
            ]).lower()
            
            missing_keywords = [kw for kw in self.filters['required_keywords'] 
                               if kw not in searchable_text]
            if missing_keywords:
                reasons.append(f"Missing required keywords: {missing_keywords}")
        
        # 4. Excluded keywords
        if 'excluded_keywords' in self.filters:
            searchable_text = ' '.join([
                ai_data.get('description', ''),
                ' '.join(ai_data.get('products_services', [])),
            ]).lower()
            
            found_excluded = [kw for kw in self.filters['excluded_keywords'] 
                             if kw in searchable_text]
            if found_excluded:
                reasons.append(f"Contains excluded keywords: {found_excluded}")
        
        # 5 & 6. Employee size range
        if 'min_employee_size' in self.filters or 'max_employee_size' in self.filters:
            company_size = ai_data.get('employee_size', 'unknown')
            
            size_order = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']
            
            if company_size != 'unknown' and company_size in size_order:
                company_idx = size_order.index(company_size)
                
                if 'min_employee_size' in self.filters:
                    min_idx = size_order.index(self.filters['min_employee_size'])
                    if company_idx < min_idx:
                        reasons.append(f"Employee size {company_size} below minimum {self.filters['min_employee_size']}")
                
                if 'max_employee_size' in self.filters:
                    max_idx = size_order.index(self.filters['max_employee_size'])
                    if company_idx > max_idx:
                        reasons.append(f"Employee size {company_size} above maximum {self.filters['max_employee_size']}")
        
        # 7. Target countries
        if 'target_countries' in self.filters:
            company_location = ai_data.get('headquarters_location', '').lower()
            if not any(country in company_location for country in self.filters['target_countries']):
                reasons.append(f"Location '{company_location}' not in target countries")
        
        # 8. Excluded countries
        if 'excluded_countries' in self.filters:
            company_location = ai_data.get('headquarters_location', '').lower()
            if any(country in company_location for country in self.filters['excluded_countries']):
                reasons.append(f"Location '{company_location}' in excluded countries")
        
        # 9. Required certifications
        if 'required_certifications' in self.filters:
            company_certs = [c.lower() for c in ai_data.get('certifications', [])]
            missing_certs = [cert for cert in self.filters['required_certifications'] 
                           if not any(cert in cc for cc in company_certs)]
            if missing_certs:
                reasons.append(f"Missing certifications: {missing_certs}")
        
        # 10. Required product categories
        if 'required_product_categories' in self.filters:
            company_products = ' '.join(ai_data.get('products_services', [])).lower()
            missing_categories = [cat for cat in self.filters['required_product_categories'] 
                                 if cat not in company_products]
            if missing_categories:
                reasons.append(f"Missing product categories: {missing_categories}")
        
        # 11. Required technologies
        if 'required_technologies' in self.filters:
            company_tech = [t.lower() for t in ai_data.get('technology_stack', [])]
            missing_tech = [tech for tech in self.filters['required_technologies'] 
                          if not any(tech in ct for ct in company_tech)]
            if missing_tech:
                reasons.append(f"Missing technologies: {missing_tech}")
        
        # 12. Target market
        if 'target_market' in self.filters:
            company_market = ai_data.get('target_market', '')
            if self.filters['target_market'] != 'Both' and company_market != self.filters['target_market']:
                reasons.append(f"Target market is '{company_market}', required '{self.filters['target_market']}'")
        
        # 13. Founded year range
        if 'min_founded_year' in self.filters or 'max_founded_year' in self.filters:
            founded_year = ai_data.get('founded_year', 'unknown')
            
            if founded_year != 'unknown':
                try:
                    year = int(founded_year)
                    
                    if 'min_founded_year' in self.filters and year < self.filters['min_founded_year']:
                        reasons.append(f"Founded year {year} before minimum {self.filters['min_founded_year']}")
                    
                    if 'max_founded_year' in self.filters and year > self.filters['max_founded_year']:
                        reasons.append(f"Founded year {year} after maximum {self.filters['max_founded_year']}")
                except ValueError:
                    pass
        
        # 14. Requires careers page
        if self.filters.get('requires_careers_page'):
            if not ai_data.get('has_careers_page'):
                reasons.append("No careers page found")
        
        # 15. Requires contact info
        if self.filters.get('requires_contact_info'):
            # Check in pages_content
            has_contact = False
            pages = company.get('pages_content', {})
            
            for page_content in pages.values():
                specific_data = page_content.get('specific_data', {})
                if specific_data.get('emails') or specific_data.get('phones'):
                    has_contact = True
                    break
            
            if not has_contact:
                reasons.append("No contact information found")
        
        # 16. Confidence score
        if 'min_confidence_score' in self.filters:
            confidence = float(ai_data.get('confidence_score', 0))
            if confidence < self.filters['min_confidence_score']:
                reasons.append(f"Confidence score {confidence} below minimum {self.filters['min_confidence_score']}")
        
        # 17. Social media presence
        if 'required_social_media' in self.filters:
            social_media = company.get('pages_content', {}).get('homepage', {}).get('specific_data', {}).get('social_media', {})
            missing_platforms = [platform for platform in self.filters['required_social_media'] 
                               if platform not in social_media]
            if missing_platforms:
                reasons.append(f"Missing social media: {missing_platforms}")
        
        return {
            'passes': len(reasons) == 0,
            'reasons': reasons
        }


def load_companies(json_file: str) -> List[Dict[str, Any]]:
    """Load companies from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_filtered_results(results: Dict[str, Any], output_file: str):
    """Save filtered results to JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Filtered results saved to: {output_file}")


def print_filter_summary(results: Dict[str, Any]):
    """Print summary of filtering results"""
    stats = results['stats']
    
    print(f"\n{'='*70}")
    print(f"FILTERING RESULTS")
    print(f"{'='*70}")
    print(f"Total companies analyzed: {stats['total_companies']}")
    print(f"✓ Matched: {stats['matched']}")
    print(f"✗ Rejected: {stats['rejected']}")
    print(f"Match rate: {stats['match_rate']}")
    print(f"Filters applied: {stats['filters_applied']}")
    print(f"{'='*70}\n")
    
    # Show sample rejections
    if results['rejected']:
        print("Sample rejection reasons:")
        for i, item in enumerate(results['rejected'][:3]):
            company_name = item['company'].get('ai_extracted_data', {}).get('company_name', 'Unknown')
            print(f"\n{i+1}. {company_name}:")
            for reason in item['rejection_reasons'][:3]:
                print(f"   - {reason}")


# Example usage
if __name__ == '__main__':
    # Example 1: Simple filtering
    filter_config = CompanyFilter() \
        .included_industries(['SaaS', 'Fintech', 'AI']) \
        .excluded_industries(['Gaming', 'Gambling']) \
        .employee_size_range(min_size='51-200', max_size='1000+') \
        .target_countries(['USA', 'India', 'UK']) \
        .required_certifications(['ISO']) \
        .requires_careers_page(True) \
        .min_confidence_score(0.6)
    
    # Load scraped companies
    companies = load_companies('company_intelligence_20260123_185912.json')
    
    # Apply filters
    results = filter_config.apply_filters(companies)
    
    # Print summary
    print_filter_summary(results)
    
    # Save results
    output_file = f"filtered_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_filtered_results(results, output_file)
    
    # Example 2: More complex filtering
    print("\n" + "="*70)
    print("EXAMPLE 2: More Complex Filtering")
    print("="*70)
    
    advanced_filter = CompanyFilter() \
        .included_industries(['SaaS', 'Enterprise Software']) \
        .required_keywords(['API', 'cloud', 'platform']) \
        .excluded_keywords(['consulting', 'agency']) \
        .employee_size_range(min_size='201-500') \
        .target_countries(['USA', 'Canada']) \
        .requires_social_media(['linkedin']) \
        .target_market('B2B') \
        .founded_year_range(min_year=2010, max_year=2020)
    
    advanced_results = advanced_filter.apply_filters(companies)
    print_filter_summary(advanced_results)
