"""
Token optimization utilities
"""
import re
from typing import List, Dict, Any
from collections import defaultdict

class TokenOptimizer:
    """Optimize content to reduce token usage"""
    
    @staticmethod
    def compress_text(text: str, max_length: int = 2000) -> str:
        """Compress text while preserving key information"""
        if len(text) <= max_length:
            return text
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML artifacts
        artifacts = [
            r'<[^>]+>',
            r'&[a-z]+;',
            r'\s*[\n\r\t]+\s*',
        ]
        for pattern in artifacts:
            text = re.sub(pattern, ' ', text)
        
        # If still too long, truncate intelligently
        if len(text) > max_length:
            # Try to find sentence boundaries
            sentences = re.split(r'[.!?]+', text)
            compressed = []
            current_length = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                if current_length + len(sentence) + 1 <= max_length:
                    compressed.append(sentence)
                    current_length += len(sentence) + 1
                else:
                    break
            
            text = '. '.join(compressed) + '.'
            
            # Final truncation if needed
            if len(text) > max_length:
                text = text[:max_length-3] + '...'
        
        return text
    
    @staticmethod
    def extract_key_content(scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only the most important content from scraped data"""
        optimized = {}
        
        # Basic company info
        optimized['domain'] = scraped_data.get('domain', '')
        optimized['original_url'] = scraped_data.get('original_url', '')
        
        # Process page content
        pages_content = scraped_data.get('pages_content', {})
        optimized_pages = {}
        
        for page_type, content in pages_content.items():
            # Extract only key elements
            optimized_pages[page_type] = {
                'title': content.get('title', '')[:150],
                'headings': {
                    'h1': content.get('headings', {}).get('h1', [])[:3],
                    'h2': content.get('headings', {}).get('h2', [])[:5],
                    'h3': content.get('headings', {}).get('h3', [])[:5],
                },
                'key_paragraphs': [
                    p[:300] for p in content.get('paragraphs', [])[:5]
                    if len(p.strip()) > 50
                ],
                'important_lists': content.get('list_items', [])[:15],
                'has_contact': bool(content.get('specific_data', {}).get('emails') or 
                                   content.get('specific_data', {}).get('phones'))
            }
        
        optimized['pages_content'] = optimized_pages
        
        # Include AI extracted data if available
        if 'ai_extracted_data' in scraped_data:
            optimized['ai_extracted_data'] = scraped_data['ai_extracted_data']
        
        return optimized
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation"""
        # Simple approximation: 1 token ≈ 4 characters
        return len(text) // 4