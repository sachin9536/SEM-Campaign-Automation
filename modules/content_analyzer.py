"""
Content Analyzer Module
Uses LLM API to analyze website content and generate business insights for SEM campaigns.
"""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re
from .llm_client import LLMClient


@dataclass
class BusinessAnalysis:
    """Data class for business analysis results."""
    business_type: str
    business_category: str
    main_products_services: List[str]
    seed_keywords: List[str]
    search_intents: List[str]
    target_audience: List[str]
    competitive_advantages: List[str]
    industry_keywords: List[str]
    local_keywords: List[str]
    long_tail_keywords: List[str]
    confidence_score: float


class ContentAnalyzer:
    """AI-powered content analyzer for website data."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the content analyzer with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Setup LLM client (supports OpenAI, Hugging Face, Ollama)
        self.llm_client = LLMClient(provider="auto")
        
        if not self.llm_client.is_available():
            self.logger.warning("No LLM provider available. AI analysis will be disabled.")
        else:
            self.logger.info(f"LLM provider initialized: {self.llm_client.get_provider_name()}")
        
        # Analysis settings
        self.max_retries = 3
        self.retry_delay = 2
        self.max_tokens = 2000
        self.temperature = 0.7
    
    def analyze_website_content(self, scraped_data: Dict[str, Any]) -> Optional[BusinessAnalysis]:
        """
        Analyze website content using LLM API.
        
        Args:
            scraped_data: Dictionary containing scraped website data
            
        Returns:
            BusinessAnalysis object with comprehensive insights
        """
        # Check if AI generation is disabled
        if not self.config.get('content_analyzer', {}).get('use_ai_generation', True):
            self.logger.info("AI analysis disabled by config. Using fallback analysis.")
            return self._create_fallback_analysis(scraped_data)
        
        if not self.llm_client.is_available():
            self.logger.error("No LLM provider available. Cannot perform analysis.")
            return None
        
        try:
            self.logger.info("Starting AI-powered content analysis...")
            
            # Prepare content for analysis
            content_summary = self._prepare_content_summary(scraped_data)
            
            # Perform comprehensive analysis
            analysis_result = self._perform_ai_analysis(content_summary)
            
            if analysis_result:
                self.logger.info("AI analysis completed successfully")
                return analysis_result
            else:
                self.logger.error("AI analysis failed to return results")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during AI analysis: {e}")
            return None
    
    def _prepare_content_summary(self, scraped_data: Dict[str, Any]) -> str:
        """Prepare a comprehensive summary of scraped content for AI analysis."""
        summary_parts = []
        
        # Basic information
        summary_parts.append(f"Website URL: {scraped_data.get('url', 'N/A')}")
        summary_parts.append(f"Page Title: {scraped_data.get('title', 'N/A')}")
        summary_parts.append(f"Meta Description: {scraped_data.get('meta_description', 'N/A')}")
        
        # Main content (truncated for token efficiency)
        main_content = scraped_data.get('main_content', '')
        if main_content:
            # Take first 2000 characters for analysis
            summary_parts.append(f"Main Content: {main_content[:2000]}...")
        
        # Headings
        headings = scraped_data.get('headings', [])
        if headings:
            heading_texts = [h.get('text', '') for h in headings[:10]]  # Limit to first 10 headings
            summary_parts.append(f"Main Headings: {' | '.join(heading_texts)}")
        
        # Products and services
        products_services = scraped_data.get('products_services', {})
        if products_services:
            for category, items in products_services.items():
                if items:
                    summary_parts.append(f"{category.title()}: {', '.join(items[:5])}")  # Limit to 5 items per category
        
        # Contact and location info
        contact_info = scraped_data.get('contact_info', {})
        if contact_info.get('phone'):
            summary_parts.append(f"Phone Numbers: {', '.join(contact_info['phone'][:3])}")
        
        locations = scraped_data.get('locations', [])
        if locations:
            summary_parts.append(f"Locations: {', '.join(locations[:3])}")
        
        # Keywords
        keywords = scraped_data.get('keywords', [])
        if keywords:
            summary_parts.append(f"Extracted Keywords: {', '.join(keywords[:20])}")  # Limit to 20 keywords
        
        return '\n\n'.join(summary_parts)
    
    def _perform_ai_analysis(self, content_summary: str) -> Optional[BusinessAnalysis]:
        """Perform comprehensive AI analysis of the content."""
        try:
            # Create the analysis prompt
            prompt = self._create_analysis_prompt(content_summary)
            
            # Make API call with retry logic
            for attempt in range(self.max_retries):
                try:
                    messages = [
                        {
                            "role": "system",
                            "content": "You are an expert business analyst and SEM specialist. Analyze website content to provide comprehensive business insights for search engine marketing campaigns."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                    
                    response_text = self.llm_client.generate_response(
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature
                    )
                    
                    if response_text:
                        return self._parse_ai_response(response_text)
                    else:
                        self.logger.error("Empty response from LLM")
                        return None
                    
                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < self.max_retries - 1:
                        self.logger.warning(f"Rate limit hit, retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.logger.error(f"LLM API error: {e}")
                        return None
                    
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {e}")
            return None
    
    def _create_analysis_prompt(self, content_summary: str) -> str:
        """Create a comprehensive prompt for AI analysis."""
        return f"""
Please analyze the following website content and provide comprehensive business insights for SEM campaign planning.

Website Content:
{content_summary}

Please provide your analysis in the following JSON format:

{{
    "business_type": "Brief description of what type of business this is",
    "business_category": "One of: e-commerce, SaaS, local_service, consulting, manufacturing, healthcare, education, real_estate, finance, other",
    "main_products_services": [
        "List of 5-8 main products or services offered"
    ],
    "seed_keywords": [
        "List of 10-15 high-value seed keywords for SEM campaigns"
    ],
    "search_intents": [
        "List of 5-8 different search intents (informational, navigational, commercial, transactional)"
    ],
    "target_audience": [
        "List of 3-5 target audience segments"
    ],
    "competitive_advantages": [
        "List of 3-5 potential competitive advantages or unique selling points"
    ],
    "industry_keywords": [
        "List of 5-8 industry-specific keywords"
    ],
    "local_keywords": [
        "List of 5-8 location-based keywords (if applicable)"
    ],
    "long_tail_keywords": [
        "List of 5-8 long-tail keyword opportunities"
    ],
    "confidence_score": 0.85
}}

Guidelines:
- Focus on commercial intent keywords for SEM campaigns
- Include both broad and specific keywords
- Consider local SEO if location information is present
- Identify high-converting keyword opportunities
- Suggest keywords that align with the business's main offerings
- Ensure keywords are relevant to the target audience

Return only the JSON response, no additional text.
"""
    
    def _parse_ai_response(self, response_text: str) -> Optional[BusinessAnalysis]:
        """Parse the AI response and create a BusinessAnalysis object."""
        try:
            # Extract JSON from response (handle cases where there might be extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.error("No JSON found in AI response")
                return None
            
            json_str = json_match.group()
            analysis_data = json.loads(json_str)
            
            # Create BusinessAnalysis object
            return BusinessAnalysis(
                business_type=analysis_data.get('business_type', ''),
                business_category=analysis_data.get('business_category', 'other'),
                main_products_services=analysis_data.get('main_products_services', []),
                seed_keywords=analysis_data.get('seed_keywords', []),
                search_intents=analysis_data.get('search_intents', []),
                target_audience=analysis_data.get('target_audience', []),
                competitive_advantages=analysis_data.get('competitive_advantages', []),
                industry_keywords=analysis_data.get('industry_keywords', []),
                local_keywords=analysis_data.get('local_keywords', []),
                long_tail_keywords=analysis_data.get('long_tail_keywords', []),
                confidence_score=analysis_data.get('confidence_score', 0.0)
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _create_fallback_analysis(self, scraped_data: Dict[str, Any]) -> BusinessAnalysis:
        """Create a fallback analysis when AI is disabled or unavailable."""
        url = scraped_data.get('url', '')
        title = scraped_data.get('title', '')
        content = scraped_data.get('main_content', '')
        
        # Extract basic information
        business_type = "technology company"
        if any(word in title.lower() for word in ['ai', 'artificial intelligence', 'machine learning']):
            business_type = "AI technology company"
        elif any(word in title.lower() for word in ['marketing', 'advertising', 'digital']):
            business_type = "digital marketing company"
        elif any(word in title.lower() for word in ['software', 'app', 'platform']):
            business_type = "software company"
        
        # Extract keywords from content
        keywords = scraped_data.get('keywords', [])
        seed_keywords = keywords[:10] if keywords else ['digital solutions', 'technology', 'business services']
        
        # Generate basic insights
        return BusinessAnalysis(
            business_type=business_type,
            business_category="technology",
            main_products_services=["AI solutions", "Digital services", "Technology consulting"],
            seed_keywords=seed_keywords,
            search_intents=["informational", "commercial", "transactional"],
            target_audience=["small businesses", "startups", "enterprises"],
            competitive_advantages=["innovative technology", "expert support", "affordable pricing"],
            industry_keywords=["digital transformation", "technology solutions", "business automation"],
            local_keywords=["local technology services", "nearby tech support"],
            long_tail_keywords=["best AI solutions for small business", "affordable digital marketing services"],
            confidence_score=0.7
        )
    
    def analyze_multiple_websites(self, scraped_data_list: List[Dict[str, Any]]) -> List[Optional[BusinessAnalysis]]:
        """
        Analyze multiple websites and return analysis for each.
        
        Args:
            scraped_data_list: List of scraped website data dictionaries
            
        Returns:
            List of BusinessAnalysis objects (None for failed analyses)
        """
        analyses = []
        
        for i, scraped_data in enumerate(scraped_data_list):
            self.logger.info(f"Analyzing website {i+1}/{len(scraped_data_list)}: {scraped_data.get('url', 'Unknown')}")
            
            analysis = self.analyze_website_content(scraped_data)
            analyses.append(analysis)
            
            # Add delay between analyses to avoid rate limits
            if i < len(scraped_data_list) - 1:
                time.sleep(2)
        
        return analyses
    
    def generate_keyword_variations(self, seed_keywords: List[str], business_context: str) -> Dict[str, List[str]]:
        """
        Generate keyword variations using AI.
        
        Args:
            seed_keywords: List of seed keywords
            business_context: Business context for better variations
            
        Returns:
            Dictionary with different keyword categories
        """
        if not self.llm_client.is_available():
            self.logger.warning("No LLM provider available. Cannot generate keyword variations.")
            return {}
        
        try:
            prompt = f"""
Based on these seed keywords and business context, generate keyword variations for SEM campaigns:

Seed Keywords: {', '.join(seed_keywords)}
Business Context: {business_context}

Generate variations in this JSON format:
{{
    "broad_keywords": ["5-8 broad match keywords"],
    "phrase_keywords": ["5-8 phrase match keywords"],
    "exact_keywords": ["5-8 exact match keywords"],
    "long_tail_keywords": ["5-8 long-tail keywords"],
    "question_keywords": ["5-8 question-based keywords"],
    "local_keywords": ["5-8 location-based keywords"],
    "negative_keywords": ["5-8 negative keywords to exclude"]
}}

Return only the JSON response.
"""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert SEM specialist who generates high-quality keyword variations for Google Ads campaigns."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response_text = self.llm_client.generate_response(
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            if response_text:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    self.logger.error("Failed to parse keyword variations response")
                    return {}
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error generating keyword variations: {e}")
            return {}
    
    def suggest_ad_copy_ideas(self, business_analysis: BusinessAnalysis) -> Dict[str, List[str]]:
        """
        Suggest ad copy ideas based on business analysis.
        
        Args:
            business_analysis: BusinessAnalysis object
            
        Returns:
            Dictionary with ad copy suggestions
        """
        if not self.llm_client.is_available():
            self.logger.warning("No LLM provider available. Cannot generate ad copy ideas.")
            return {}
        
        try:
            context = f"""
Business Type: {business_analysis.business_type}
Category: {business_analysis.business_category}
Main Services: {', '.join(business_analysis.main_products_services)}
Target Audience: {', '.join(business_analysis.target_audience)}
Competitive Advantages: {', '.join(business_analysis.competitive_advantages)}
"""
            
            prompt = f"""
Based on this business analysis, suggest ad copy ideas for Google Ads:

{context}

Generate ad copy ideas in this JSON format:
{{
    "headlines": ["5-8 compelling headline ideas"],
    "descriptions": ["5-8 description line ideas"],
    "call_to_actions": ["5-8 call-to-action phrases"],
    "unique_selling_propositions": ["5-8 USPs for ad copy"],
    "emotional_triggers": ["5-8 emotional trigger words/phrases"]
}}

Focus on:
- Commercial intent
- Clear value propositions
- Action-oriented language
- Emotional appeal
- Local relevance (if applicable)

Return only the JSON response.
"""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Google Ads copywriter who creates compelling ad copy that converts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response_text = self.llm_client.generate_response(
                messages=messages,
                max_tokens=1500,
                temperature=0.8
            )
            
            if response_text:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    self.logger.error("Failed to parse ad copy suggestions response")
                    return {}
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error generating ad copy ideas: {e}")
            return {}
    
    def save_analysis_results(self, analyses: List[Optional[BusinessAnalysis]], output_dir: str = 'output') -> None:
        """Save analysis results to files."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert analyses to dictionaries for JSON serialization
        analysis_data = []
        for analysis in analyses:
            if analysis:
                analysis_data.append({
                    'business_type': analysis.business_type,
                    'business_category': analysis.business_category,
                    'main_products_services': analysis.main_products_services,
                    'seed_keywords': analysis.seed_keywords,
                    'search_intents': analysis.search_intents,
                    'target_audience': analysis.target_audience,
                    'competitive_advantages': analysis.competitive_advantages,
                    'industry_keywords': analysis.industry_keywords,
                    'local_keywords': analysis.local_keywords,
                    'long_tail_keywords': analysis.long_tail_keywords,
                    'confidence_score': analysis.confidence_score
                })
        
        # Save as JSON
        with open(f'{output_dir}/business_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        import pandas as pd
        if analysis_data:
            df = pd.DataFrame(analysis_data)
            df.to_csv(f'{output_dir}/business_analysis.csv', index=False)
        
        self.logger.info(f"Business analysis results saved to {output_dir}/")
    
    def generate_analysis_summary(self, analyses: List[Optional[BusinessAnalysis]]) -> Dict[str, Any]:
        """Generate a summary of all analyses."""
        successful_analyses = [a for a in analyses if a is not None]
        
        if not successful_analyses:
            return {"error": "No successful analyses to summarize"}
        
        summary = {
            'total_websites_analyzed': len(analyses),
            'successful_analyses': len(successful_analyses),
            'business_categories': {},
            'common_keywords': [],
            'average_confidence_score': 0.0,
            'top_industries': [],
            'analysis_timestamp': time.time()
        }
        
        # Count business categories
        for analysis in successful_analyses:
            category = analysis.business_category
            summary['business_categories'][category] = summary['business_categories'].get(category, 0) + 1
        
        # Collect all keywords
        all_keywords = []
        confidence_scores = []
        
        for analysis in successful_analyses:
            all_keywords.extend(analysis.seed_keywords)
            all_keywords.extend(analysis.industry_keywords)
            confidence_scores.append(analysis.confidence_score)
        
        # Find common keywords
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        summary['common_keywords'] = [kw for kw, count in keyword_counts.most_common(20)]
        
        # Calculate average confidence
        if confidence_scores:
            summary['average_confidence_score'] = sum(confidence_scores) / len(confidence_scores)
        
        # Top industries
        summary['top_industries'] = sorted(
            summary['business_categories'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return summary 