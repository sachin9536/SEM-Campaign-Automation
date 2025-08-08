"""
Enhanced Keyword Discovery Module
Handles keyword discovery using multiple sources: WordStream, free keyword tools, Google Autocomplete, and web scraping.
"""

import logging
import requests
import time
import random
import json
import re
import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os
from .llm_client import LLMClient


class KeywordDiscovery:
    """Enhanced keyword discovery using multiple sources and methods."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the keyword discovery module."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting settings
        self.rate_limit_delay = 2  # seconds between requests
        self.max_retries = 3
        self.retry_delay = 5
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Session for requests
        self.session = self._create_session()
        
        # Keyword tool URLs
        self.keyword_tools = {
            'keywordtool': 'https://keywordtool.io/google',
            'ubersuggest': 'https://neilpatel.com/ubersuggest/',
            'answerthepublic': 'https://answerthepublic.com/',
            'keywordshitter': 'https://keywordshitter.com/',
            'keyword_surfer': 'https://keyword-surfer.com/'
        }
        
        # Google Autocomplete API settings
        self.google_autocomplete_url = "http://suggestqueries.google.com/complete/search"
        
        # WordStream API settings (if available)
        self.wordstream_api_key = os.getenv('WORDSTREAM_API_KEY')
        self.wordstream_api_url = "https://api.wordstream.com/keywords"
        
        # LLM client for keyword expansion
        self.llm_client = LLMClient(provider="auto")
        if not self.llm_client.is_available():
            self.logger.warning("No LLM provider available. LLM-powered keyword expansion will be disabled.")
        else:
            self.logger.info(f"LLM provider initialized: {self.llm_client.get_provider_name()}")
        
        # Selenium usage toggle from config (default False to avoid driver issues)
        self.use_selenium = self.config.get('scraping', {}).get('use_selenium', False)
    
    def _create_session(self) -> requests.Session:
        """Create a session with enhanced headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session
    
    def discover_keywords(self, brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Main method to discover keywords from multiple sources."""
        self.logger.info("Starting enhanced keyword discovery process...")
        
        all_keywords = []
        
        # Step 1: Extract seed keywords from scraped data
        seed_keywords = self._extract_seed_keywords(brand_data, competitor_data)
        self.logger.info(f"Extracted {len(seed_keywords)} seed keywords")

        # Optional: Load Google Keyword Planner CSV if available
        try:
            gkp_keywords = self._load_keyword_planner_csv()
            if gkp_keywords:
                self.logger.info(f"Loaded {len(gkp_keywords)} keywords from Google Keyword Planner CSV")
                all_keywords.extend(gkp_keywords)
        except Exception as e:
            self.logger.warning(f"Could not load Keyword Planner CSV: {e}")
        
        # Step 2: LLM-powered keyword expansion
        self.logger.info("Starting LLM-powered keyword expansion...")
        llm_keywords = self._generate_llm_keyword_expansion(seed_keywords, brand_data, competitor_data)
        all_keywords.extend(llm_keywords)
        self.logger.info(f"Generated {len(llm_keywords)} keywords using LLM expansion")
        
        # Step 3: WordStream API keywords
        wordstream_keywords = self._get_wordstream_keywords(seed_keywords)
        all_keywords.extend(wordstream_keywords)
        self.logger.info(f"Retrieved {len(wordstream_keywords)} keywords from WordStream")
        
        # Step 4: Google Autocomplete keywords
        autocomplete_keywords = self._get_google_autocomplete_keywords(seed_keywords)
        all_keywords.extend(autocomplete_keywords)
        self.logger.info(f"Retrieved {len(autocomplete_keywords)} keywords from Google Autocomplete")
        
        # Step 5: Free keyword tools scraping (will skip Selenium-based parts if disabled)
        tool_keywords = self._scrape_keyword_tools(seed_keywords)
        all_keywords.extend(tool_keywords)
        self.logger.info(f"Retrieved {len(tool_keywords)} keywords from free tools")
        
        # Step 6: Google search suggestions scraping (Selenium-based; skip when disabled)
        suggestion_keywords = self._scrape_google_search_suggestions(seed_keywords)
        all_keywords.extend(suggestion_keywords)
        self.logger.info(f"Retrieved {len(suggestion_keywords)} keywords from Google search suggestions")
        
        # Step 7: Keyword Processing & Filtering Pipeline
        self.logger.info("Starting Keyword Processing & Filtering Pipeline")
        processed_keywords = self._process_keywords_pipeline(all_keywords, brand_data, competitor_data)
        
        return processed_keywords
    
    def _extract_seed_keywords(self, brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> List[str]:
        """Extract seed keywords from scraped data."""
        seed_keywords = set()
        
        # Extract from brand data
        if brand_data:
            # From title and meta description
            title = brand_data.get('title', '')
            meta_desc = brand_data.get('meta_description', '')
            
            # Extract meaningful phrases
            seed_keywords.update(self._extract_phrases_from_text(title))
            seed_keywords.update(self._extract_phrases_from_text(meta_desc))
            
            # From products/services
            products_services = brand_data.get('products_services', {})
            for category, items in products_services.items():
                for item in items[:5]:  # Limit to first 5 items
                    seed_keywords.update(self._extract_phrases_from_text(item))
            
            # From headings
            headings = brand_data.get('headings', [])
            for heading in headings[:5]:  # Limit to first 5 headings
                seed_keywords.update(self._extract_phrases_from_text(heading.get('text', '')))
        
        # Extract from competitor data
        for competitor in competitor_data:
            title = competitor.get('title', '')
            meta_desc = competitor.get('meta_description', '')
            
            seed_keywords.update(self._extract_phrases_from_text(title))
            seed_keywords.update(self._extract_phrases_from_text(meta_desc))
            
            # From competitor services
            products_services = competitor.get('products_services', {})
            for category, items in products_services.items():
                for item in items[:3]:  # Limit to first 3 items per competitor
                    seed_keywords.update(self._extract_phrases_from_text(item))
        
        return list(seed_keywords)[:20]  # Limit to top 20 seed keywords
    
    def _extract_phrases_from_text(self, text: str) -> set:
        """Extract meaningful phrases from text."""
        if not text:
            return set()
        
        phrases = set()
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Single words (filtered)
        for word in words:
            if len(word) > 3 and word not in stop_words and not word.isdigit():
                phrases.add(word)
        
        # Bigrams
        for i in range(len(words) - 1):
            if (words[i] not in stop_words and words[i+1] not in stop_words and
                len(words[i]) > 2 and len(words[i+1]) > 2):
                bigram = f"{words[i]} {words[i+1]}"
                if len(bigram) > 5:
                    phrases.add(bigram)
        
        # Trigrams
        for i in range(len(words) - 2):
            if (words[i] not in stop_words and words[i+1] not in stop_words and
                words[i+2] not in stop_words and len(words[i]) > 2 and 
                len(words[i+1]) > 2 and len(words[i+2]) > 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if len(trigram) > 8:
                    phrases.add(trigram)
        
        return phrases
    
    def _generate_llm_keyword_expansion(self, seed_keywords: List[str], brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate comprehensive keyword variations using GPT-4.
        
        Args:
            seed_keywords: List of seed keywords
            brand_data: Brand website data
            competitor_data: Competitor website data
            
        Returns:
            List of keyword dictionaries with metadata
        """
        if not self.llm_client.is_available():
            self.logger.warning("LLM provider not available. Skipping LLM keyword expansion.")
            return []
        
        try:
            self.logger.info("Starting LLM-powered keyword expansion...")
            
            # Prepare business context
            business_context = self._prepare_business_context_for_llm(brand_data, competitor_data)
            
            # Generate different types of keyword variations
            all_keywords = []
            
            # 1. Match type variations
            match_type_keywords = self._generate_match_type_keywords(seed_keywords, business_context)
            all_keywords.extend(match_type_keywords)
            
            # 2. Intent-based keywords
            intent_keywords = self._generate_intent_based_keywords(seed_keywords, business_context)
            all_keywords.extend(intent_keywords)
            
            # 3. Competitor-based keywords
            competitor_keywords = self._generate_competitor_based_keywords(seed_keywords, business_context, competitor_data)
            all_keywords.extend(competitor_keywords)
            
            # 4. Location-based keywords
            location_keywords = self._generate_location_based_keywords(seed_keywords, business_context)
            all_keywords.extend(location_keywords)
            
            # 5. Long-tail variations
            longtail_keywords = self._generate_longtail_keywords(seed_keywords, business_context)
            all_keywords.extend(longtail_keywords)
            
            self.logger.info(f"LLM expansion completed: {len(all_keywords)} keywords generated")
            return all_keywords
            
        except Exception as e:
            self.logger.error(f"Error in LLM keyword expansion: {e}")
            return []
    
    def _prepare_business_context_for_llm(self, brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> str:
        """Prepare comprehensive business context for LLM keyword generation."""
        context_parts = []
        
        # Brand information
        if brand_data:
            context_parts.append(f"Brand Name: {brand_data.get('title', 'N/A')}")
            context_parts.append(f"Brand Description: {brand_data.get('meta_description', 'N/A')}")
            
            # Brand services
            products_services = brand_data.get('products_services', {})
            for category, items in products_services.items():
                if items:
                    context_parts.append(f"Brand {category.title()}: {', '.join(items[:5])}")
            
            # Brand locations
            locations = brand_data.get('locations', [])
            if locations:
                context_parts.append(f"Brand Locations: {', '.join(locations[:3])}")
        
        # Competitor information
        if competitor_data:
            comp_names = [comp.get('title', '') for comp in competitor_data[:3]]
            context_parts.append(f"Main Competitors: {', '.join(comp_names)}")
            
            # Competitor services
            all_comp_services = []
            for comp in competitor_data:
                products_services = comp.get('products_services', {})
                for category, items in products_services.items():
                    all_comp_services.extend(items[:3])
            
            if all_comp_services:
                context_parts.append(f"Competitor Services: {', '.join(set(all_comp_services))}")
        
        # Campaign settings
        locations = self.config.get('locations', [])
        if locations:
            location_names = [loc.get('name', '') for loc in locations]
            context_parts.append(f"Target Locations: {', '.join(location_names)}")
        
        return '\n'.join(context_parts)
    
    def _generate_match_type_keywords(self, seed_keywords: List[str], business_context: str) -> List[Dict[str, Any]]:
        """Generate keywords for different match types."""
        keywords = []
        
        try:
            prompt = f"""
Based on these seed keywords and business context, generate keyword variations for different match types:

Seed Keywords: {', '.join(seed_keywords)}
Business Context: {business_context}

Generate keywords in this JSON format:
{{
    "broad_match": ["5-8 broad match keywords"],
    "phrase_match": ["5-8 phrase match keywords"],
    "exact_match": ["5-8 exact match keywords"],
    "modified_broad": ["5-8 modified broad match keywords"]
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
                max_tokens=2000,
                temperature=0.7
            )
            
            if response_text:
                data = self._parse_llm_response(response_text)
                if data:
                    # Convert to keyword dictionaries
                    for match_type, kw_list in data.items():
                        for keyword in kw_list:
                            keywords.append({
                                'keyword': keyword,
                                'match_type': match_type,
                                'source': 'llm_expansion',
                                'category': 'match_type',
                                'search_volume': self._estimate_search_volume(keyword),
                                'competition': self._estimate_competition(keyword),
                                'cpc': self._estimate_cpc(keyword),
                                'commercial_intent': self._assess_commercial_intent(keyword),
                                'relevance_score': 0.8,
                                'difficulty_score': self._calculate_keyword_difficulty_score(keyword)
                            })
            
        except Exception as e:
            self.logger.error(f"Error generating match type keywords: {e}")
        
        return keywords
    
    def _generate_intent_based_keywords(self, seed_keywords: List[str], business_context: str) -> List[Dict[str, Any]]:
        """Generate keywords based on search intent."""
        keywords = []
        
        try:
            prompt = f"""
Based on these seed keywords and business context, generate keywords for different search intents:

Seed Keywords: {', '.join(seed_keywords)}
Business Context: {business_context}

Generate keywords in this JSON format:
{{
    "informational": ["5-8 informational keywords (how to, what is, etc.)"],
    "navigational": ["5-8 navigational keywords (brand names, specific websites)"],
    "commercial": ["5-8 commercial keywords (best, review, compare, etc.)"],
    "transactional": ["5-8 transactional keywords (buy, purchase, order, etc.)"]
}}

Return only the JSON response.
"""
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert SEM specialist who understands search intent and creates targeted keywords."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response_text = self.llm_client.generate_response(
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            if response_text:
                data = self._parse_llm_response(response_text)
                if data:
                    for intent_type, kw_list in data.items():
                        for keyword in kw_list:
                            keywords.append({
                                'keyword': keyword,
                                'intent': intent_type,
                                'source': 'llm_expansion',
                                'category': 'intent_based',
                                'search_volume': self._estimate_search_volume(keyword),
                                'competition': self._estimate_competition(keyword),
                                'cpc': self._estimate_cpc(keyword),
                                'commercial_intent': self._assess_commercial_intent(keyword),
                                'relevance_score': 0.8,
                                'difficulty_score': self._calculate_keyword_difficulty_score(keyword)
                            })
            
        except Exception as e:
            self.logger.error(f"Error generating intent-based keywords: {e}")
        
        return keywords
    
    def _generate_competitor_based_keywords(self, seed_keywords: List[str], business_context: str, competitor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate competitor-based keywords."""
        keywords = []
        
        try:
            # Extract competitor names and services
            competitor_info = []
            for comp in competitor_data[:5]:  # Limit to top 5 competitors
                comp_name = comp.get('title', '')
                comp_services = []
                products_services = comp.get('products_services', {})
                for category, items in products_services.items():
                    comp_services.extend(items[:3])
                
                if comp_name and comp_services:
                    competitor_info.append(f"{comp_name}: {', '.join(comp_services)}")
            
            competitor_context = '\n'.join(competitor_info) if competitor_info else "No specific competitor information available"
            
            prompt = f"""
            Based on these seed keywords, business context, and competitor information, generate competitor-based keywords:

            Seed Keywords: {', '.join(seed_keywords[:10])}
            Business Context: {business_context}
            Competitor Information: {competitor_context}

            Generate keywords in this JSON format:
            {{
                "competitor_brand_keywords": ["5-8 keywords targeting competitor brand names"],
                "competitor_service_keywords": ["5-8 keywords targeting competitor services"],
                "alternative_keywords": ["5-8 keywords for alternatives to competitors"],
                "comparison_keywords": ["5-8 keywords for comparing with competitors"],
                "better_than_keywords": ["5-8 keywords positioning as better than competitors"]
            }}

            Guidelines:
            - Competitor brand keywords should include competitor names
            - Competitor service keywords should target competitor offerings
            - Alternative keywords should offer alternatives to competitors
            - Comparison keywords should enable comparison searches
            - Better than keywords should position superiority

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
            
            response_text = self.llm_client.generate_response(messages=messages, max_tokens=1500, temperature=0.7)
            
            if response_text:
                response = self._parse_llm_response(response_text)
                if response:
                    for comp_type, kw_list in response.items():
                        for keyword in kw_list:
                            keywords.append({
                                'keyword': keyword,
                                'competitor_type': comp_type,
                                'search_volume': self._estimate_search_volume(keyword),
                                'competition': self._estimate_competition(keyword),
                                'cpc': self._estimate_cpc(keyword),
                                'source': 'llm_competitor_based'
                            })
            
        except Exception as e:
            self.logger.error(f"Error generating competitor-based keywords: {e}")
        
        return keywords
    
    def _generate_location_based_keywords(self, seed_keywords: List[str], business_context: str) -> List[Dict[str, Any]]:
        """Generate location-based keyword variations."""
        keywords = []
        
        try:
            # Extract target locations from config
            locations = self.config.get('locations', [])
            location_names = [loc.get('name', '') for loc in locations] if locations else ['local', 'near me']
            
            prompt = f"""
            Based on these seed keywords, business context, and target locations, generate location-based keywords:

            Seed Keywords: {', '.join(seed_keywords[:10])}
            Business Context: {business_context}
            Target Locations: {', '.join(location_names)}

            Generate keywords in this JSON format:
            {{
                "location_specific_keywords": ["5-8 keywords with specific location names"],
                "near_me_keywords": ["5-8 keywords with 'near me' variations"],
                "local_service_keywords": ["5-8 keywords emphasizing local service"],
                "city_based_keywords": ["5-8 keywords with city/location modifiers"],
                "regional_keywords": ["5-8 keywords for broader regional targeting"]
            }}

            Guidelines:
            - Location specific: Include actual location names
            - Near me: Use 'near me', 'close to me', 'nearby' variations
            - Local service: Emphasize local, nearby, in your area
            - City based: Include city names, neighborhoods, areas
            - Regional: Broader regional terms, state names, regions

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
            
            response_text = self.llm_client.generate_response(messages=messages, max_tokens=1500, temperature=0.7)
            
            if response_text:
                response = self._parse_llm_response(response_text)
                if response:
                    for loc_type, kw_list in response.items():
                        for keyword in kw_list:
                            keywords.append({
                                'keyword': keyword,
                                'location_type': loc_type,
                                'search_volume': self._estimate_search_volume(keyword),
                                'competition': self._estimate_competition(keyword),
                                'cpc': self._estimate_cpc(keyword),
                                'source': 'llm_location_based'
                            })
            
        except Exception as e:
            self.logger.error(f"Error generating location-based keywords: {e}")
        
        return keywords
    
    def _generate_longtail_keywords(self, seed_keywords: List[str], business_context: str) -> List[Dict[str, Any]]:
        """Generate long-tail keyword variations."""
        keywords = []
        try:
            prompt = f"""
            Based on these seed keywords and business context, generate long-tail keyword variations:

            Seed Keywords: {', '.join(seed_keywords[:10])}
            Business Context: {business_context}

            Generate keywords in this JSON format:
            {{
                "question_keywords": ["5-8 question-based long-tail keywords"],
                "problem_solution_keywords": ["5-8 problem-solution focused keywords"],
                "specific_service_keywords": ["5-8 specific service or product keywords"],
                "benefit_focused_keywords": ["5-8 benefit-focused long-tail keywords"],
                "niche_keywords": ["5-8 niche or specialized keywords"]
            }}

            Guidelines:
            - Question keywords: Start with what, how, why, when, where, which
            - Problem solution: Focus on solving specific problems
            - Specific service: Very specific offerings or features
            - Benefit focused: Emphasize benefits, advantages, results
            - Niche keywords: Specialized, industry-specific terms

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
            response_text = self.llm_client.generate_response(messages=messages, max_tokens=1500, temperature=0.7)
            if response_text:
                response = self._parse_llm_response(response_text)
                if response:
                    for longtail_type, kw_list in response.items():
                        for keyword in kw_list:
                            keywords.append({
                                'keyword': keyword,
                                'longtail_type': longtail_type,
                                'search_volume': self._estimate_search_volume(keyword),
                                'competition': self._estimate_competition(keyword),
                                'cpc': self._estimate_cpc(keyword),
                                'source': 'llm_longtail'
                            })
        except Exception as e:
            self.logger.error(f"Error generating long-tail keywords: {e}")
        return keywords
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response and extract JSON data."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.error("No JSON found in LLM response")
                return None
            
            json_str = json_match.group()
            data = json.loads(json_str)
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def _get_wordstream_keywords(self, seed_keywords: List[str]) -> List[Dict[str, Any]]:
        """Get keywords from WordStream API."""
        if not self.wordstream_api_key:
            return []
        
        keywords = []
        
        for seed_keyword in seed_keywords[:10]:  # Limit to first 10 seed keywords
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                params = {
                    'api_key': self.wordstream_api_key,
                    'keyword': seed_keyword,
                    'country': 'us',
                    'language': 'en',
                    'max_results': 50
                }
                
                response = self.session.get(self.wordstream_api_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'keywords' in data:
                    for kw_data in data['keywords']:
                        keyword_info = {
                            'keyword': kw_data.get('keyword', ''),
                            'search_volume': kw_data.get('search_volume', 0),
                            'competition': kw_data.get('competition', 0.0),
                            'cpc': kw_data.get('cpc', 0.0),
                            'source': 'wordstream'
                        }
                        keywords.append(keyword_info)
                
            except Exception as e:
                self.logger.error(f"Error getting WordStream keywords for '{seed_keyword}': {e}")
                continue
        
        return keywords
    
    def _get_google_autocomplete_keywords(self, seed_keywords: List[str]) -> List[Dict[str, Any]]:
        """Get keyword suggestions from Google Autocomplete API."""
        keywords = []
        
        for seed_keyword in seed_keywords[:15]:  # Limit to first 15 seed keywords
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                params = {
                    'client': 'firefox',
                    'q': seed_keyword,
                    'hl': 'en',
                    'gl': 'us'
                }
                
                response = self.session.get(self.google_autocomplete_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if len(data) > 1 and isinstance(data[1], list):
                    suggestions = data[1]
                    
                    for suggestion in suggestions:
                        if isinstance(suggestion, str) and len(suggestion) > len(seed_keyword):
                            keyword_info = {
                                'keyword': suggestion,
                                'search_volume': self._estimate_search_volume(suggestion),
                                'competition': self._estimate_competition(suggestion),
                                'cpc': self._estimate_cpc(suggestion),
                                'source': 'google_autocomplete'
                            }
                            keywords.append(keyword_info)
                
            except Exception as e:
                self.logger.error(f"Error getting Google Autocomplete for '{seed_keyword}': {e}")
                continue
        
        return keywords
    
    def _scrape_keyword_tools(self, seed_keywords: List[str]) -> List[Dict[str, Any]]:
        """Scrape keywords from free keyword tools."""
        keywords = []
        
        # Early check for Selenium - log once instead of per keyword
        if not self.use_selenium:
            self.logger.info("Selenium disabled by config; skipping KeywordTool.io scraping")
            # Still try Ubersuggest (non-Selenium) if available
            for seed_keyword in seed_keywords[:5]:  # Reduced limit when Selenium disabled
                try:
                    time.sleep(self.rate_limit_delay)
                    tool_keywords = self._scrape_ubersuggest(seed_keyword)
                    keywords.extend(tool_keywords)
                except Exception as e:
                    self.logger.error(f"Error scraping Ubersuggest for '{seed_keyword}': {e}")
                    continue
            return keywords
        
        for seed_keyword in seed_keywords[:10]:  # Limit to first 10 seed keywords
            try:
                # Rate limiting
                time.sleep(self.rate_limit_delay * 2)  # Longer delay for scraping
                
                # Try different keyword tools
                tool_keywords = self._scrape_ubersuggest(seed_keyword)
                keywords.extend(tool_keywords)
                
                # KeywordTool.io requires Selenium; skip if disabled
                if self.use_selenium:
                    tool_keywords = self._scrape_keywordtool(seed_keyword)
                    keywords.extend(tool_keywords)
                
            except Exception as e:
                self.logger.error(f"Error scraping keyword tools for '{seed_keyword}': {e}")
                continue
        
        return keywords
    
    def _scrape_ubersuggest(self, seed_keyword: str) -> List[Dict[str, Any]]:
        """Scrape keywords from Ubersuggest."""
        keywords = []
        
        try:
            # Ubersuggest URL structure
            url = f"https://neilpatel.com/ubersuggest/api/suggestions.php"
            
            params = {
                'q': seed_keyword,
                'country': 'us',
                'lang': 'en'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'suggestions' in data:
                    for suggestion in data['suggestions']:
                        keyword_info = {
                            'keyword': suggestion.get('keyword', ''),
                            'search_volume': suggestion.get('search_volume', 0),
                            'competition': suggestion.get('competition', 0.0),
                            'cpc': suggestion.get('cpc', 0.0),
                            'source': 'ubersuggest'
                        }
                        keywords.append(keyword_info)
            
        except Exception as e:
            self.logger.error(f"Error scraping Ubersuggest: {e}")
        
        return keywords
    
    def _scrape_keywordtool(self, seed_keyword: str) -> List[Dict[str, Any]]:
        """Scrape keywords from KeywordTool.io."""
        if not self.use_selenium:
            # Safety check; should already be skipped by caller
            return []
        keywords = []
        
        try:
            # Use Selenium for dynamic content
            driver = self._setup_selenium_driver()
            
            try:
                url = f"https://keywordtool.io/google?q={quote_plus(seed_keyword)}"
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "keyword"))
                )
                
                # Extract keywords
                keyword_elements = driver.find_elements(By.CLASS_NAME, "keyword")
                
                for element in keyword_elements[:20]:  # Limit to first 20
                    keyword_text = element.text.strip()
                    if keyword_text and len(keyword_text) > 2:
                        keyword_info = {
                            'keyword': keyword_text,
                            'search_volume': self._estimate_search_volume(keyword_text),
                            'competition': self._estimate_competition(keyword_text),
                            'cpc': self._estimate_cpc(keyword_text),
                            'source': 'keywordtool'
                        }
                        keywords.append(keyword_info)
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error scraping KeywordTool: {e}")
        
        return keywords
    
    def _scrape_google_search_suggestions(self, seed_keywords: List[str]) -> List[Dict[str, Any]]:
        """Scrape Google search suggestions using Selenium."""
        if not self.use_selenium:
            self.logger.info("Selenium disabled by config; skipping Google search suggestions scraping")
            return []
        
        self.logger.info("Starting Google search suggestions scraping...")
        keywords = []
        
        driver = self._setup_selenium_driver()
        
        try:
            for seed_keyword in seed_keywords[:10]:  # Limit to first 10
                try:
                    # Rate limiting
                    time.sleep(self.rate_limit_delay * 2)
                    
                    # Navigate to Google
                    driver.get("https://www.google.com")
                    
                    # Find search box and enter keyword
                    search_box = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "q"))
                    )
                    
                    # Clear and enter keyword
                    search_box.clear()
                    search_box.send_keys(seed_keyword)
                    
                    # Wait for suggestions
                    time.sleep(2)
                    
                    # Extract suggestions
                    suggestion_elements = driver.find_elements(By.CSS_SELECTOR, "ul[role='listbox'] li")
                    
                    for element in suggestion_elements[:10]:  # Limit to first 10 suggestions
                        suggestion_text = element.text.strip()
                        if suggestion_text and len(suggestion_text) > len(seed_keyword):
                            keyword_info = {
                                'keyword': suggestion_text,
                                'search_volume': self._estimate_search_volume(suggestion_text),
                                'competition': self._estimate_competition(suggestion_text),
                                'cpc': self._estimate_cpc(suggestion_text),
                                'source': 'google_search'
                            }
                            keywords.append(keyword_info)
                
                except Exception as e:
                    self.logger.error(f"Error scraping Google suggestions for '{seed_keyword}': {e}")
                    continue
                    
        finally:
            driver.quit()
        
        return keywords

    def _load_keyword_planner_csv(self, csv_path: str = 'input/keyword_planner.csv') -> List[Dict[str, Any]]:
        """Load Google Keyword Planner export (CSV or TSV, UTF-8/UTF-16) and map to internal schema."""
        try:
            if not os.path.exists(csv_path):
                return []

            # Try multiple encodings and delimiter detection
            df = None
            encodings_to_try = ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16le', 'utf-16be']
            last_error = None
            for enc in encodings_to_try:
                try:
                    # Auto-detect delimiter
                    df = pd.read_csv(csv_path, sep=None, engine='python', encoding=enc)
                    # If single wide column, try tab-separated explicitly
                    if df.shape[1] == 1:
                        df = pd.read_csv(csv_path, sep='\t', encoding=enc)
                    break
                except Exception as e:
                    last_error = e
                    continue

            if df is None:
                raise last_error or Exception('Unable to read Keyword Planner file')

            # Normalize expected column names
            cols = {str(c).lower().strip(): c for c in df.columns}
            def get(col_aliases):
                for alias in col_aliases:
                    if alias in cols:
                        return cols[alias]
                return None

            k_col = get(['keyword', 'search term', 'query'])
            sv_col = get(['avg. monthly searches', 'average monthly searches', 'search volume'])
            comp_col = get(['competition'])
            low_col = get(['top of page bid (low range)', 'top of page bid (low)', 'top of page bid low range'])
            high_col = get(['top of page bid (high range)', 'top of page bid (high)', 'top of page bid high range'])

            if not k_col:
                self.logger.warning('Keyword Planner file missing keyword column; skipping load')
                return []

            def to_int(x) -> int:
                try:
                    return int(str(x).replace(',', '').strip())
                except:
                    return 0

            def to_float(x) -> float:
                try:
                    s = str(x)
                    # Strip currency symbols (e.g., $, INR) and commas
                    for sym in ['$', 'INR', '₹']:
                        s = s.replace(sym, '')
                    return float(s.replace(',', '').strip())
                except:
                    return 0.0

            records: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                keyword = str(row.get(k_col, '')).strip()
                if not keyword:
                    continue

                search_volume = to_int(row.get(sv_col, 0)) if sv_col else 0

                competition_raw = row.get(comp_col, 0.0) if comp_col else 0.0
                if isinstance(competition_raw, str):
                    comp_map = {'low': 0.3, 'medium': 0.6, 'high': 0.8}
                    competition = comp_map.get(competition_raw.lower(), 0.5)
                else:
                    try:
                        competition = float(competition_raw)
                    except:
                        competition = 0.0

                top_of_page_low = to_float(row.get(low_col, 0.0)) if low_col else 0.0
                top_of_page_high = to_float(row.get(high_col, 0.0)) if high_col else 0.0
                cpc = top_of_page_low if top_of_page_low > 0 else top_of_page_high

                records.append({
                    'keyword': keyword,
                    'search_volume': search_volume,
                    'competition': competition,
                    'cpc': cpc,
                    'top_of_page_low': top_of_page_low,
                    'top_of_page_high': top_of_page_high,
                    'source': 'keyword_planner'
                })

            return records
        except Exception as e:
            self.logger.error(f"Error loading Keyword Planner CSV: {e}")
            return []
    
    def _setup_selenium_driver(self) -> webdriver.Chrome:
        """Setup Selenium WebDriver with anti-detection options."""
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium driver: {e}")
            raise
    
    def _process_keywords_pipeline(self, all_keywords: List[Dict[str, Any]], brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Comprehensive keyword processing pipeline that combines, filters, and analyzes keywords.
        
        Args:
            all_keywords: List of keyword dictionaries from all sources
            brand_data: Brand website data for context
            competitor_data: Competitor website data for context
            
        Returns:
            Processed and filtered keyword list
        """
        self.logger.info("Starting keyword processing pipeline...")
        
        # Step 1: Combine keywords from all sources
        combined_keywords = self._combine_keywords_from_sources(all_keywords)
        self.logger.info(f"Combined {len(combined_keywords)} keywords from all sources")
        
        # Step 2: Remove duplicates and variations
        deduplicated_keywords = self._remove_duplicates_and_variations(combined_keywords)
        self.logger.info(f"After deduplication: {len(deduplicated_keywords)} keywords")
        
        # Step 3: Filter by estimated search volume (>500 monthly searches)
        volume_filtered_keywords = self._filter_by_search_volume(deduplicated_keywords, min_volume=500)
        self.logger.info(f"After volume filtering: {len(volume_filtered_keywords)} keywords")
        
        # Step 4: Group keywords by intent and theme
        grouped_keywords = self._group_by_intent_and_theme(volume_filtered_keywords, brand_data)
        self.logger.info(f"Grouped into {len(grouped_keywords)} intent/theme groups")
        
        # Step 5: Assign preliminary match types
        match_type_keywords = self._assign_preliminary_match_types(grouped_keywords)
        self.logger.info("Assigned preliminary match types")
        
        # Step 6: Calculate keyword difficulty scores
        difficulty_scored_keywords = self._calculate_keyword_difficulty_scores(match_type_keywords)
        self.logger.info("Calculated keyword difficulty scores")
        
        # Step 7: Final analysis and ranking
        final_keywords = self._analyze_keywords(difficulty_scored_keywords)
        self.logger.info(f"Final processed keywords: {len(final_keywords)}")
        
        return final_keywords

    def _combine_keywords_from_sources(self, all_keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine keywords from all sources with source tracking.
        
        Args:
            all_keywords: List of keyword dictionaries from all sources
            
        Returns:
            Combined keywords with source information
        """
        combined = []
        source_counts = {}
        
        for keyword_data in all_keywords:
            if isinstance(keyword_data, dict) and 'keyword' in keyword_data:
                # Track source
                source = keyword_data.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                
                # Ensure all required fields exist
                keyword_data.setdefault('search_volume', 0)
                keyword_data.setdefault('competition', 0.0)
                keyword_data.setdefault('cpc', 0.0)
                keyword_data.setdefault('commercial_intent', 0.0)
                keyword_data.setdefault('relevance_score', 0.0)
                
                combined.append(keyword_data)
        
        self.logger.info(f"Source distribution: {source_counts}")
        return combined

    def _remove_duplicates_and_variations(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate keywords and similar variations.
        
        Args:
            keywords: List of keyword dictionaries
            
        Returns:
            Deduplicated keyword list
        """
        seen_keywords = set()
        deduplicated = []
        
        for kw_data in keywords:
            keyword = kw_data.get('keyword', '').lower().strip()
            
            # Skip if exact duplicate
            if keyword in seen_keywords:
                continue
            
            # Check for similar variations
            is_variation = False
            for existing in deduplicated:
                existing_keyword = existing.get('keyword', '').lower().strip()
                
                # Check for plural/singular variations
                if keyword == existing_keyword + 's' or existing_keyword == keyword + 's':
                    is_variation = True
                    break
                
                # Check for common word variations
                if self._are_keywords_similar(keyword, existing_keyword):
                    is_variation = True
                    break
            
            if not is_variation:
                seen_keywords.add(keyword)
                deduplicated.append(kw_data)
        
        return deduplicated

    def _are_keywords_similar(self, kw1: str, kw2: str) -> bool:
        """
        Check if two keywords are similar variations.
        
        Args:
            kw1: First keyword
            kw2: Second keyword
            
        Returns:
            True if keywords are similar
        """
        # Split into words
        words1 = set(kw1.split())
        words2 = set(kw2.split())
        
        # Check for high word overlap
        if len(words1) >= 2 and len(words2) >= 2:
            overlap = len(words1.intersection(words2))
            min_length = min(len(words1), len(words2))
            similarity = overlap / min_length
            
            return similarity >= 0.8  # 80% word overlap threshold
        
        return False

    def _filter_by_search_volume(self, keywords: List[Dict[str, Any]], min_volume: int = 500) -> List[Dict[str, Any]]:
        """
        Filter keywords by minimum search volume.
        
        Args:
            keywords: List of keyword dictionaries
            min_volume: Minimum monthly search volume threshold
            
        Returns:
            Filtered keyword list
        """
        filtered = []
        
        for kw_data in keywords:
            search_volume = kw_data.get('search_volume', 0)
            
            # If we have actual search volume data, use it
            if search_volume >= min_volume:
                filtered.append(kw_data)
            else:
                # Estimate search volume if not available
                estimated_volume = self._estimate_search_volume(kw_data.get('keyword', ''))
                if estimated_volume >= min_volume:
                    kw_data['search_volume'] = estimated_volume
                    filtered.append(kw_data)
        
        return filtered

    def _group_by_intent_and_theme(self, keywords: List[Dict[str, Any]], brand_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Group keywords by search intent and thematic categories.
        
        Args:
            keywords: List of keyword dictionaries
            brand_data: Brand website data for context
            
        Returns:
            Keywords with intent and theme grouping
        """
        # Define intent categories
        intent_categories = {
            'informational': ['what', 'how', 'why', 'when', 'where', 'guide', 'tips', 'learn', 'understand'],
            'navigational': ['brand', 'company', 'website', 'official', 'homepage'],
            'commercial': ['best', 'top', 'compare', 'review', 'vs', 'alternative'],
            'transactional': ['buy', 'purchase', 'order', 'price', 'cost', 'deal', 'discount', 'sale'],
            'local': ['near me', 'local', 'nearby', 'location', 'address', 'city', 'area']
        }
        
        # Define theme categories based on business type
        business_type = brand_data.get('business_type', 'general')
        theme_categories = self._get_theme_categories(business_type)
        
        for kw_data in keywords:
            keyword = kw_data.get('keyword', '').lower()
            
            # Determine intent
            intent = self._classify_search_intent(keyword, intent_categories)
            kw_data['search_intent'] = intent
            
            # Determine theme
            theme = self._classify_keyword_theme(keyword, theme_categories)
            kw_data['keyword_theme'] = theme
            
            # Create intent-theme group
            kw_data['intent_theme_group'] = f"{intent}_{theme}"
        
        return keywords

    def _get_theme_categories(self, business_type: str) -> Dict[str, List[str]]:
        """
        Get theme categories based on business type.
        
        Args:
            business_type: Type of business
            
        Returns:
            Dictionary of theme categories and their keywords
        """
        theme_categories = {
            'general': {
                'products': ['product', 'service', 'item', 'solution'],
                'quality': ['best', 'quality', 'premium', 'professional'],
                'pricing': ['price', 'cost', 'affordable', 'cheap', 'expensive'],
                'location': ['near me', 'local', 'location', 'area'],
                'reviews': ['review', 'rating', 'feedback', 'testimonial']
            }
        }
        
        # Add specific themes for different business types
        if 'ecommerce' in business_type.lower():
            theme_categories['ecommerce'] = {
                'products': ['buy', 'shop', 'store', 'online', 'ecommerce'],
                'categories': ['category', 'type', 'brand', 'model'],
                'shipping': ['shipping', 'delivery', 'fast', 'free shipping'],
                'returns': ['return', 'refund', 'warranty', 'guarantee']
            }
        elif 'saas' in business_type.lower():
            theme_categories['saas'] = {
                'features': ['feature', 'tool', 'software', 'platform'],
                'pricing': ['pricing', 'plan', 'subscription', 'trial'],
                'integration': ['integration', 'api', 'connect', 'sync'],
                'support': ['support', 'help', 'documentation', 'tutorial']
            }
        elif 'service' in business_type.lower():
            theme_categories['service'] = {
                'services': ['service', 'professional', 'expert', 'specialist'],
                'booking': ['book', 'appointment', 'schedule', 'reservation'],
                'pricing': ['price', 'quote', 'estimate', 'cost'],
                'location': ['near me', 'local', 'area', 'location']
            }
        
        return theme_categories.get(business_type.lower(), theme_categories['general'])

    def _classify_search_intent(self, keyword: str, intent_categories: Dict[str, List[str]]) -> str:
        """
        Classify keyword by search intent.
        
        Args:
            keyword: Keyword to classify
            intent_categories: Dictionary of intent categories and keywords
            
        Returns:
            Intent classification
        """
        for intent, indicators in intent_categories.items():
            if any(indicator in keyword for indicator in indicators):
                return intent
        
        # Default to commercial if no specific intent detected
        return 'commercial'

    def _classify_keyword_theme(self, keyword: str, theme_categories: Dict[str, List[str]]) -> str:
        """
        Classify keyword by theme.
        
        Args:
            keyword: Keyword to classify
            theme_categories: Dictionary of theme categories and keywords
            
        Returns:
            Theme classification
        """
        for theme, indicators in theme_categories.items():
            if any(indicator in keyword for indicator in indicators):
                return theme
        
        return 'general'

    def _assign_preliminary_match_types(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign preliminary match types to keywords.
        
        Args:
            keywords: List of keyword dictionaries
            
        Returns:
            Keywords with preliminary match types
        """
        for kw_data in keywords:
            keyword = kw_data.get('keyword', '')
            word_count = len(keyword.split())
            
            # Determine match type based on keyword characteristics
            if word_count == 1:
                match_type = 'broad'
            elif word_count == 2:
                match_type = 'phrase'
            elif word_count >= 3:
                match_type = 'exact'
            else:
                match_type = 'broad'
            
            # Adjust based on commercial intent
            commercial_intent = kw_data.get('commercial_intent', 0.0)
            if commercial_intent > 0.7:
                match_type = 'phrase'  # More specific for high commercial intent
            
            # Adjust based on search volume
            search_volume = kw_data.get('search_volume', 0)
            if search_volume > 10000:
                match_type = 'broad'  # High volume keywords get broad match
            elif search_volume < 1000:
                match_type = 'exact'  # Low volume keywords get exact match
            
            kw_data['preliminary_match_type'] = match_type
        
        return keywords

    def _calculate_keyword_difficulty_score(self, keyword: str) -> int:
        """
        Calculate difficulty score for a single keyword.
        
        Args:
            keyword: Keyword to analyze
            
        Returns:
            Difficulty score (0-100, higher = more difficult)
        """
        # Base difficulty factors
        word_count = len(keyword.split())
        competition = self._estimate_competition(keyword)
        search_volume = self._estimate_search_volume(keyword)
        commercial_intent = self._assess_commercial_intent(keyword)
        
        # Calculate difficulty score (0-100, higher = more difficult)
        difficulty_score = 0
        
        # Word count factor (longer keywords = easier)
        if word_count == 1:
            difficulty_score += 40
        elif word_count == 2:
            difficulty_score += 25
        elif word_count == 3:
            difficulty_score += 15
        else:
            difficulty_score += 10
        
        # Competition factor
        difficulty_score += competition * 30
        
        # Search volume factor (higher volume = more competition)
        if search_volume > 10000:
            difficulty_score += 20
        elif search_volume > 5000:
            difficulty_score += 15
        elif search_volume > 1000:
            difficulty_score += 10
        else:
            difficulty_score += 5
        
        # Commercial intent factor (higher commercial intent = more competition)
        difficulty_score += commercial_intent * 15
        
        # Brand vs non-brand factor
        if self._is_brand_keyword(keyword):
            difficulty_score -= 20  # Brand keywords are easier
        
        # Local vs national factor
        if self._is_local_keyword(keyword):
            difficulty_score -= 10  # Local keywords are easier
        
        # Cap difficulty score at 100
        difficulty_score = min(100, max(0, difficulty_score))
        
        return int(difficulty_score)

    def _calculate_keyword_difficulty_scores(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate keyword difficulty scores using available data.
        
        Args:
            keywords: List of keyword dictionaries
            
        Returns:
            Keywords with difficulty scores
        """
        for kw_data in keywords:
            keyword = kw_data.get('keyword', '')
            
            # Base difficulty factors
            word_count = len(keyword.split())
            competition = kw_data.get('competition', 0.0)
            search_volume = kw_data.get('search_volume', 0)
            commercial_intent = kw_data.get('commercial_intent', 0.0)
            
            # Calculate difficulty score (0-100, higher = more difficult)
            difficulty_score = 0
            
            # Word count factor (longer keywords = easier)
            if word_count == 1:
                difficulty_score += 40
            elif word_count == 2:
                difficulty_score += 25
            elif word_count == 3:
                difficulty_score += 15
            else:
                difficulty_score += 10
            
            # Competition factor
            difficulty_score += competition * 30
            
            # Search volume factor (higher volume = more competition)
            if search_volume > 10000:
                difficulty_score += 20
            elif search_volume > 5000:
                difficulty_score += 15
            elif search_volume > 1000:
                difficulty_score += 10
            else:
                difficulty_score += 5
            
            # Commercial intent factor (higher commercial intent = more competition)
            difficulty_score += commercial_intent * 15
            
            # Brand vs non-brand factor
            if self._is_brand_keyword(keyword):
                difficulty_score -= 20  # Brand keywords are easier
            
            # Local vs national factor
            if self._is_local_keyword(keyword):
                difficulty_score -= 10  # Local keywords are easier
            
            # Cap difficulty score at 100
            difficulty_score = min(100, max(0, difficulty_score))
            
            # Categorize difficulty
            if difficulty_score >= 70:
                difficulty_category = 'high'
            elif difficulty_score >= 40:
                difficulty_category = 'medium'
            else:
                difficulty_category = 'low'
            
            kw_data['difficulty_score'] = difficulty_score
            kw_data['difficulty_category'] = difficulty_category
        
        return keywords

    def _is_brand_keyword(self, keyword: str) -> bool:
        """
        Check if keyword contains brand terms.
        
        Args:
            keyword: Keyword to check
            
        Returns:
            True if keyword contains brand terms
        """
        brand_indicators = ['brand', 'company', 'official', 'homepage', 'website']
        return any(indicator in keyword.lower() for indicator in brand_indicators)

    def _is_local_keyword(self, keyword: str) -> bool:
        """
        Check if keyword is location-specific.
        
        Args:
            keyword: Keyword to check
            
        Returns:
            True if keyword is location-specific
        """
        local_indicators = ['near me', 'local', 'nearby', 'location', 'area', 'city', 'state']
        return any(indicator in keyword.lower() for indicator in local_indicators)

    def _remove_duplicates(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate keywords while preserving the best data."""
        keyword_dict = {}
        
        for kw_data in keywords:
            keyword = kw_data['keyword'].lower().strip()
            
            if keyword not in keyword_dict:
                keyword_dict[keyword] = kw_data
            else:
                # Keep the one with better data (higher search volume, lower competition)
                existing = keyword_dict[keyword]
                if (kw_data.get('search_volume', 0) > existing.get('search_volume', 0) or
                    kw_data.get('competition', 1.0) < existing.get('competition', 1.0)):
                    keyword_dict[keyword] = kw_data
        
        return list(keyword_dict.values())
    
    def _analyze_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze keywords and add metadata."""
        analyzed_keywords = []
        
        for kw_data in keywords:
            keyword = kw_data['keyword']
            
            # Skip if keyword is in negative keywords
            negative_keywords = self.config.get('keywords', {}).get('negative_keywords', [])
            if any(neg in keyword.lower() for neg in negative_keywords):
                continue
            
            # Add analysis
            analysis = {
                'keyword': keyword,
                'length': len(keyword),
                'word_count': len(keyword.split()),
                'type': self._classify_keyword_type(keyword),
                'search_volume': kw_data.get('search_volume', self._estimate_search_volume(keyword)),
                'search_volume_category': self._categorize_search_volume(keyword),
                'competition': kw_data.get('competition', self._estimate_competition(keyword)),
                'cpc': kw_data.get('cpc', self._estimate_cpc(keyword)),
                'commercial_intent': self._assess_commercial_intent(keyword),
                'relevance_score': self._calculate_relevance_score(kw_data),
                'source': kw_data.get('source', 'unknown'),
                'match_type': kw_data.get('match_type', ''),
                'intent_type': kw_data.get('intent_type', ''),
                'competitor_type': kw_data.get('competitor_type', ''),
                'location_type': kw_data.get('location_type', ''),
                'longtail_type': kw_data.get('longtail_type', '')
            }
            
            analyzed_keywords.append(analysis)
        
        return analyzed_keywords
    
    def _classify_keyword_type(self, keyword: str) -> str:
        """Classify keyword type."""
        word_count = len(keyword.split())
        
        if word_count == 1:
            return 'broad'
        elif word_count == 2:
            return 'phrase'
        else:
            return 'long-tail'
    
    def _estimate_search_volume(self, keyword: str) -> int:
        """Estimate search volume for keyword."""
        base_volume = 1000
        word_count = len(keyword.split())
        
        if word_count == 1:
            return base_volume * 10  # Broad keywords have higher volume
        elif word_count == 2:
            return base_volume * 5   # Phrase keywords have medium volume
        else:
            return base_volume       # Long-tail keywords have lower volume
    
    def _categorize_search_volume(self, keyword: str) -> str:
        """Categorize search volume as high/medium/low based on keyword patterns."""
        estimated_volume = self._estimate_search_volume(keyword)
        word_count = len(keyword.split())
        
        # High volume indicators
        high_volume_indicators = [
            'best', 'top', 'cheap', 'free', 'near me', 'local',
            'service', 'professional', 'expert', 'reviews', 'compare'
        ]
        
        # Low volume indicators
        low_volume_indicators = [
            'how to', 'what is', 'why', 'when', 'where', 'which',
            'specific', 'custom', 'specialized', 'niche', 'advanced'
        ]
        
        keyword_lower = keyword.lower()
        
        # Check for high volume indicators
        if any(indicator in keyword_lower for indicator in high_volume_indicators):
            return 'high'
        
        # Check for low volume indicators
        if any(indicator in keyword_lower for indicator in low_volume_indicators):
            return 'low'
        
        # Word count based categorization
        if word_count == 1:
            return 'high'
        elif word_count == 2:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_competition(self, keyword: str) -> float:
        """Estimate competition level for keyword."""
        word_count = len(keyword.split())
        
        if word_count == 1:
            return 0.8  # High competition for broad keywords
        elif word_count == 2:
            return 0.6  # Medium competition for phrase keywords
        else:
            return 0.3  # Low competition for long-tail keywords
    
    def _estimate_cpc(self, keyword: str) -> float:
        """Estimate cost per click for keyword."""
        base_cpc = 2.0
        word_count = len(keyword.split())
        
        if word_count == 1:
            return base_cpc * 1.5  # Higher CPC for broad keywords
        elif word_count == 2:
            return base_cpc         # Medium CPC for phrase keywords
        else:
            return base_cpc * 0.7   # Lower CPC for long-tail keywords
    
    def _assess_commercial_intent(self, keyword: str) -> float:
        """Assess commercial intent of keyword."""
        commercial_indicators = [
            'buy', 'purchase', 'order', 'shop', 'store', 'price', 'cost',
            'cheap', 'affordable', 'discount', 'deal', 'offer', 'sale',
            'near me', 'local', 'service', 'professional', 'expert',
            'best', 'top', 'reviews', 'compare', 'vs', 'versus'
        ]
        
        keyword_lower = keyword.lower()
        score = 0.0
        
        for indicator in commercial_indicators:
            if indicator in keyword_lower:
                score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, kw_data: Dict[str, Any]) -> float:
        """Calculate overall relevance score for keyword."""
        search_volume_score = min(kw_data.get('search_volume', 0) / 10000, 1.0)
        competition_score = 1.0 - kw_data.get('competition', 0.5)  # Lower competition is better
        commercial_intent_score = self._assess_commercial_intent(kw_data['keyword'])
        
        # Weighted average
        relevance_score = (
            search_volume_score * 0.3 +
            competition_score * 0.4 +
            commercial_intent_score * 0.3
        )
        
        return relevance_score
    
    def _filter_keywords(self, analyzed_keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter keywords based on criteria."""
        keyword_settings = self.config.get('keywords', {})
        min_search_volume = keyword_settings.get('min_search_volume', 1000)
        max_competition = keyword_settings.get('max_competition', 0.8)
        
        filtered = []
        
        for keyword_data in analyzed_keywords:
            # Apply filters
            if (keyword_data['search_volume'] >= min_search_volume and
                keyword_data['competition'] <= max_competition and
                keyword_data['relevance_score'] >= 0.4):
                filtered.append(keyword_data)
        
        # Sort by relevance score
        filtered.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return filtered
    
    def _group_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group keywords into ad groups."""
        max_keywords_per_ad_group = self.config.get('keywords', {}).get('max_keywords_per_ad_group', 20)
        
        # Group by first word and type
        groups = {}
        
        for keyword_data in keywords:
            keyword = keyword_data['keyword']
            first_word = keyword.split()[0]
            keyword_type = keyword_data['type']
            
            group_key = f"{first_word}_{keyword_type}"
            
            if group_key not in groups:
                groups[group_key] = {
                    'name': f"Ad Group - {first_word.title()} ({keyword_type})",
                    'keywords': [],
                    'type': keyword_type,
                    'primary_keyword': first_word
                }
            
            groups[group_key]['keywords'].append(keyword_data)
        
        # Limit keywords per group
        for group in groups.values():
            group['keywords'] = group['keywords'][:max_keywords_per_ad_group]
        
        return list(groups.values())
    
    def save_keywords(self, keyword_groups: List[Dict[str, Any]], output_dir: str = 'output') -> None:
        """Save keyword data to files with enhanced processing pipeline data."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save keyword groups with processing pipeline data
        groups_data = []
        for group in keyword_groups:
            for keyword_data in group['keywords']:
                groups_data.append({
                    'ad_group': group['name'],
                    'keyword': keyword_data['keyword'],
                    'type': keyword_data.get('type', 'unknown'),
                    'search_volume': keyword_data.get('search_volume', 0),
                    'search_volume_category': keyword_data.get('search_volume_category', 'unknown'),
                    'competition': keyword_data.get('competition', 0.0),
                    'cpc': keyword_data.get('cpc', 0.0),
                    'commercial_intent': keyword_data.get('commercial_intent', 0.0),
                    'relevance_score': keyword_data.get('relevance_score', 0.0),
                    'source': keyword_data.get('source', 'unknown'),
                    'match_type': keyword_data.get('match_type', 'unknown'),
                    'intent_type': keyword_data.get('intent_type', 'unknown'),
                    'competitor_type': keyword_data.get('competitor_type', 'unknown'),
                    'location_type': keyword_data.get('location_type', 'unknown'),
                    'longtail_type': keyword_data.get('longtail_type', 'unknown'),
                    # New processing pipeline fields
                    'search_intent': keyword_data.get('search_intent', 'unknown'),
                    'keyword_theme': keyword_data.get('keyword_theme', 'unknown'),
                    'intent_theme_group': keyword_data.get('intent_theme_group', 'unknown'),
                    'preliminary_match_type': keyword_data.get('preliminary_match_type', 'unknown'),
                    'difficulty_score': keyword_data.get('difficulty_score', 0),
                    'difficulty_category': keyword_data.get('difficulty_category', 'unknown')
                })
        
        df = pd.DataFrame(groups_data)
        df.to_csv(f'{output_dir}/keywords.csv', index=False)
        self.logger.info(f"Keywords saved to {output_dir}/keywords.csv")
        
        # Save summary by source
        source_summary = df.groupby('source').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'relevance_score': 'mean',
            'difficulty_score': 'mean'
        }).round(2)
        
        # Save summary by search volume category
        volume_summary = df.groupby('search_volume_category').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'cpc': 'mean',
            'relevance_score': 'mean',
            'difficulty_score': 'mean'
        }).round(2)
        
        # Save summary by search intent
        intent_summary = df.groupby('search_intent').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'cpc': 'mean',
            'difficulty_score': 'mean'
        }).round(2)
        
        # Save summary by difficulty category
        difficulty_summary = df.groupby('difficulty_category').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'cpc': 'mean',
            'relevance_score': 'mean'
        }).round(2)
        
        # Save summary by keyword theme
        theme_summary = df.groupby('keyword_theme').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'cpc': 'mean',
            'difficulty_score': 'mean'
        }).round(2)
        
        # Save summary by preliminary match type
        match_type_summary = df.groupby('preliminary_match_type').agg({
            'keyword': 'count',
            'search_volume': 'mean',
            'competition': 'mean',
            'cpc': 'mean',
            'difficulty_score': 'mean'
        }).round(2)
        
        # Save all summaries
        volume_summary.to_csv(f'{output_dir}/keyword_volume_summary.csv')
        self.logger.info(f"Keyword volume summary saved to {output_dir}/keyword_volume_summary.csv")
        
        source_summary.to_csv(f'{output_dir}/keyword_source_summary.csv')
        self.logger.info(f"Keyword source summary saved to {output_dir}/keyword_source_summary.csv")
        
        intent_summary.to_csv(f'{output_dir}/keyword_intent_summary.csv')
        self.logger.info(f"Keyword intent summary saved to {output_dir}/keyword_intent_summary.csv")
        
        difficulty_summary.to_csv(f'{output_dir}/keyword_difficulty_summary.csv')
        self.logger.info(f"Keyword difficulty summary saved to {output_dir}/keyword_difficulty_summary.csv")
        
        theme_summary.to_csv(f'{output_dir}/keyword_theme_summary.csv')
        self.logger.info(f"Keyword theme summary saved to {output_dir}/keyword_theme_summary.csv")
        
        match_type_summary.to_csv(f'{output_dir}/keyword_match_type_summary.csv')
        self.logger.info(f"Keyword match type summary saved to {output_dir}/keyword_match_type_summary.csv")
        
        # Save processing pipeline summary
        pipeline_summary = {
            'total_keywords': len(groups_data),
            'total_ad_groups': len(keyword_groups),
            'avg_search_volume': df['search_volume'].mean(),
            'avg_competition': df['competition'].mean(),
            'avg_cpc': df['cpc'].mean(),
            'avg_relevance_score': df['relevance_score'].mean(),
            'avg_difficulty_score': df['difficulty_score'].mean(),
            'sources_used': df['source'].nunique(),
            'intents_covered': df['search_intent'].nunique(),
            'themes_covered': df['keyword_theme'].nunique(),
            'difficulty_distribution': df['difficulty_category'].value_counts().to_dict(),
            'match_type_distribution': df['preliminary_match_type'].value_counts().to_dict(),
            'volume_distribution': df['search_volume_category'].value_counts().to_dict()
        }
        
        summary_df = pd.DataFrame([pipeline_summary])
        summary_df.to_csv(f'{output_dir}/keyword_processing_summary.csv', index=False)
        self.logger.info(f"Keyword processing summary saved to {output_dir}/keyword_processing_summary.csv")
        
        # Save detailed processing report
        processing_report = {
            'pipeline_steps': [
                'Combined keywords from all sources',
                'Removed duplicates and variations',
                'Filtered by search volume (>500 monthly searches)',
                'Grouped by intent and theme',
                'Assigned preliminary match types',
                'Calculated difficulty scores',
                'Final analysis and ranking'
            ],
            'filtering_criteria': {
                'min_search_volume': 500,
                'similarity_threshold': 0.8,
                'difficulty_categories': ['low', 'medium', 'high'],
                'intent_categories': ['informational', 'navigational', 'commercial', 'transactional', 'local']
            },
            'scoring_methods': {
                'difficulty_score': 'Based on word count, competition, search volume, commercial intent, brand/local factors',
                'relevance_score': 'Based on search volume, competition, and commercial intent',
                'commercial_intent': 'Based on commercial indicator words'
            }
        }
        
        with open(f'{output_dir}/processing_pipeline_report.json', 'w') as f:
            json.dump(processing_report, f, indent=2)
        self.logger.info(f"Processing pipeline report saved to {output_dir}/processing_pipeline_report.json") 