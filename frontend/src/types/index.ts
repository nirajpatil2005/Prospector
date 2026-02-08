export interface SearchConfig {
    included_industries: string[];
    excluded_industries?: string[];
    required_keywords: string[];
    excluded_keywords?: string[];
    min_employees?: number;
    max_employees?: number;
    target_countries: string[];
    excluded_countries?: string[];
    required_certifications?: string[];
    required_product_categories?: string[];
}

export interface CompanyBasicInfo {
    name: string;
    url: string;
    snippet?: string;
    location?: string;
    source: string;
}

export interface CompanyAnalysis {
    company_name: string;
    website: string;
    industry_match: boolean;
    employee_count_estimate?: string;
    locations: string[];
    certifications: string[];
    product_categories: string[];
    summary: string;
    contact_info?: string;
    relevance_score: number;
    // Financials
    estimated_revenue?: string;
    market_cap?: string;
    strategic_goals?: string[];

    // Social & Extra
    linkedin_url?: string;
    follower_count?: number;
    founded_year?: number;
    specialties?: string[];
}

export interface ResearchResponse {
    status: string;
    companies_found: number;
    scraped_sites: number;
    analyzed_count: number;
    results: CompanyAnalysis[];
}
