"""
Campaign Builder Module
Handles building SEM campaigns from discovered keywords and generating ads.
"""

import logging
import pandas as pd
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .llm_client import LLMClient


class CampaignBuilder:
    """Campaign builder for creating SEM campaigns from keywords."""
    
    def __init__(self, config):
        """Initialize the campaign builder with configuration."""
        self.config = config
        self.logger = logging
        
        # Respect config flag to disable AI ad generation (use Hugging Face via LLMClient)
        self.use_ai_ads = self.config.get('ads', {}).get('use_ai_generation', False)
        if self.use_ai_ads:
            self.client = LLMClient(provider="huggingface")
            if not self.client.is_available():
                self.logger.warning("LLM provider not available. Using template ads.")
                self.client = None
        else:
            self.logger.info("AI ad generation disabled by config. Using template ads.")
            self.client = None
        
        # Campaign settings from config
        self.campaign_config = config.get('campaign', {})
        self.budget_config = config.get('budgets', {})
        self.ad_config = config.get('ads', {})
        self.brand_config = config.get('brand', {})
        self.locations = config.get('locations', [])
    
    def build_campaign(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Main method to build a complete SEM campaign with enhanced search campaign structure."""
        self.logger.info("Starting enhanced search campaign building process...")
        
        # Step 1: Create campaign structure
        campaign = self._create_campaign_structure()
        
        # Step 2: Group keywords into logical ad groups
        keyword_groups = self._group_keywords_into_ad_groups(keywords)
        
        # Step 3: Create ad groups with proper naming conventions
        campaign['ad_groups'] = self._create_enhanced_ad_groups(keyword_groups)
        
        # Step 4: Generate ads for each ad group
        campaign['ads'] = self._generate_ads(campaign['ad_groups'])
        
        # Step 5: Set up targeting and budgets
        campaign['targeting'] = self._setup_targeting()
        campaign['budgets'] = self._setup_budgets()
        
        # Step 6: Create negative keywords
        campaign['negative_keywords'] = self._create_negative_keywords()
        
        # Step 7: Calculate campaign metrics
        campaign['metrics'] = self._calculate_campaign_metrics(campaign)
        
        self.logger.info(f"Enhanced search campaign built successfully with {len(campaign['ad_groups'])} ad groups and {len(campaign['ads'])} ads")
        
        return campaign
    
    def _create_campaign_structure(self) -> Dict[str, Any]:
        """Create the basic campaign structure."""
        campaign = {
            'name': self.campaign_config.get('name', 'Brand Campaign'),
            'type': self.campaign_config.get('type', 'search'),
            'status': self.campaign_config.get('status', 'active'),
            'start_date': self.campaign_config.get('start_date', datetime.now().strftime('%Y-%m-%d')),
            'end_date': self.campaign_config.get('end_date', (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')),
            'created_at': datetime.now().isoformat(),
            'ad_groups': [],
            'ads': [],
            'targeting': {},
            'budgets': {},
            'negative_keywords': []
        }
        
        return campaign
    
    def _group_keywords_into_ad_groups(self, keywords: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group keywords into logical ad groups based on type and characteristics.
        
        Args:
            keywords: List of processed keyword dictionaries
            
        Returns:
            Dictionary of keyword groups organized by type
        """
        self.logger.info("Grouping keywords into logical ad groups...")
        
        ad_groups = {
            'brand': [],
            'category': [],
            'competitor': [],
            'location': [],
            'long_tail': [],
            'informational': [],
            'transactional': [],
            'commercial': []
        }
        
        for keyword_data in keywords:
            keyword = keyword_data.get('keyword', '').lower()
            
            # Determine ad group type based on keyword characteristics
            if self._is_brand_keyword(keyword):
                ad_groups['brand'].append(keyword_data)
            elif self._is_competitor_keyword(keyword):
                ad_groups['competitor'].append(keyword_data)
            elif self._is_location_keyword(keyword):
                ad_groups['location'].append(keyword_data)
            elif self._is_long_tail_keyword(keyword):
                ad_groups['long_tail'].append(keyword_data)
            elif keyword_data.get('search_intent') == 'informational':
                ad_groups['informational'].append(keyword_data)
            elif keyword_data.get('search_intent') == 'transactional':
                ad_groups['transactional'].append(keyword_data)
            elif keyword_data.get('search_intent') == 'commercial':
                ad_groups['commercial'].append(keyword_data)
            else:
                ad_groups['category'].append(keyword_data)
        
        # Log grouping results
        for group_type, keywords_list in ad_groups.items():
            self.logger.info(f"{group_type.title()} ad group: {len(keywords_list)} keywords")
        
        return ad_groups
    
    def _is_brand_keyword(self, keyword: str) -> bool:
        """Check if keyword is brand-related."""
        brand_name = self.brand_config.get('name', '').lower()
        if brand_name and brand_name in keyword:
            return True
        
        brand_indicators = ['brand', 'company', 'official', 'homepage', 'website']
        return any(indicator in keyword for indicator in brand_indicators)
    
    def _is_competitor_keyword(self, keyword: str) -> bool:
        """Check if keyword is competitor-related."""
        competitor_names = [comp.get('name', '').lower() for comp in self.config.get('competitors', [])]
        competitor_indicators = ['vs', 'versus', 'alternative', 'competitor', 'compare', 'better than']
        
        return (any(comp_name in keyword for comp_name in competitor_names if comp_name) or
                any(indicator in keyword for indicator in competitor_indicators))
    
    def _is_location_keyword(self, keyword: str) -> bool:
        """Check if keyword is location-related."""
        location_indicators = ['near me', 'local', 'nearby', 'location', 'area', 'city', 'state']
        return any(indicator in keyword for indicator in location_indicators)
    
    def _is_long_tail_keyword(self, keyword: str) -> bool:
        """Check if keyword is long-tail."""
        word_count = len(keyword.split())
        return word_count >= 4
    
    def _create_enhanced_ad_groups(self, keyword_groups: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Create enhanced ad groups with proper naming conventions and bid strategies.
        
        Args:
            keyword_groups: Dictionary of keyword groups organized by type
            
        Returns:
            List of enhanced ad group dictionaries
        """
        self.logger.info("Creating enhanced ad groups with proper naming conventions...")
        
        ad_groups = []
        group_counter = 1
        
        for group_type, keywords in keyword_groups.items():
            if not keywords:
                continue
            
            # Create ad group with proper naming convention
            primary_keyword = keywords[0]['keyword'] if keywords else 'General'
            ad_group = {
                'id': f"ad_group_{group_counter:03d}",
                'name': self._generate_ad_group_name(group_type, keywords),
                'type': group_type,
                'primary_keyword': primary_keyword,
                'keywords': [kw['keyword'] for kw in keywords],
                'keyword_data': keywords,
                'status': 'active',
                'bid_strategy': self._determine_enhanced_bid_strategy(group_type, keywords),
                'max_cpc': self._calculate_enhanced_max_cpc(group_type, keywords),
                'target_cpa': self._calculate_target_cpa(group_type, keywords),
                'daily_budget': self._calculate_ad_group_budget(group_type, keywords),
                'match_types': self._assign_match_types(keywords),
                'priority': self._determine_ad_group_priority(group_type),
                'created_at': datetime.now().isoformat()
            }
            
            ad_groups.append(ad_group)
            group_counter += 1
        
        return ad_groups
    
    def _generate_ad_group_name(self, group_type: str, keywords: List[Dict[str, Any]]) -> str:
        """Generate proper ad group name following Google Ads naming conventions."""
        brand_name = self.brand_config.get('name', 'Brand')
        
        # Get primary keyword for naming
        primary_keyword = keywords[0]['keyword'] if keywords else 'General'
        
        # Clean and format keyword for naming
        clean_keyword = primary_keyword.replace(' ', '_').replace('-', '_')[:20]
        
        # Generate name based on group type
        if group_type == 'brand':
            return f"{brand_name}_Brand_Keywords"
        elif group_type == 'category':
            return f"{brand_name}_{clean_keyword}_Category"
        elif group_type == 'competitor':
            return f"{brand_name}_Competitor_{clean_keyword}"
        elif group_type == 'location':
            return f"{brand_name}_Location_{clean_keyword}"
        elif group_type == 'long_tail':
            return f"{brand_name}_LongTail_{clean_keyword}"
        elif group_type == 'informational':
            return f"{brand_name}_Info_{clean_keyword}"
        elif group_type == 'transactional':
            return f"{brand_name}_Transactional_{clean_keyword}"
        elif group_type == 'commercial':
            return f"{brand_name}_Commercial_{clean_keyword}"
        else:
            return f"{brand_name}_{group_type.title()}_{clean_keyword}"
    
    def _determine_enhanced_bid_strategy(self, group_type: str, keywords: List[Dict[str, Any]]) -> str:
        """Determine optimal bid strategy for ad group type."""
        # Calculate average metrics
        avg_competition = sum(kw.get('competition', 0) for kw in keywords) / len(keywords) if keywords else 0
        avg_search_volume = sum(kw.get('search_volume', 0) for kw in keywords) / len(keywords) if keywords else 0
        avg_commercial_intent = sum(kw.get('commercial_intent', 0) for kw in keywords) / len(keywords) if keywords else 0
        
        # Brand keywords: Manual CPC with higher bids
        if group_type == 'brand':
            return 'manual_cpc'
        
        # High commercial intent: Target CPA
        elif avg_commercial_intent > 0.7:
            return 'target_cpa'
        
        # High competition: Target ROAS
        elif avg_competition > 0.6:
            return 'target_roas'
        
        # High search volume: Enhanced CPC
        elif avg_search_volume > 5000:
            return 'enhanced_cpc'
        
        # Default: Manual CPC
        else:
            return 'manual_cpc'
    
    def _calculate_enhanced_max_cpc(self, group_type: str, keywords: List[Dict[str, Any]]) -> float:
        """Calculate enhanced max CPC based on competition, search volume, and ad group type."""
        if not keywords:
            return self.budget_config.get('max_cpc', 5.0)
        
        # Calculate base metrics
        avg_competition = sum(kw.get('competition', 0) for kw in keywords) / len(keywords)
        avg_search_volume = sum(kw.get('search_volume', 0) for kw in keywords) / len(keywords)
        avg_cpc = sum(kw.get('cpc', 0) for kw in keywords) / len(keywords)
        
        # Base CPC from config
        base_cpc = self.budget_config.get('max_cpc', 5.0)
        
        # Adjust based on ad group type
        type_multiplier = {
            'brand': 1.5,      # Higher bids for brand keywords
            'transactional': 1.3,  # Higher bids for transactional intent
            'commercial': 1.2,     # Higher bids for commercial intent
            'competitor': 1.1,     # Moderate bids for competitor keywords
            'location': 1.0,       # Standard bids for location keywords
            'long_tail': 0.8,      # Lower bids for long-tail keywords
            'informational': 0.7,  # Lower bids for informational keywords
            'category': 1.0        # Standard bids for category keywords
        }
        
        multiplier = type_multiplier.get(group_type, 1.0)
        
        # Adjust based on competition
        competition_adjustment = 1 + (avg_competition * 0.5)
        
        # Adjust based on search volume (higher volume = higher competition)
        volume_adjustment = 1 + (min(avg_search_volume / 10000, 1) * 0.3)
        
        # Calculate final CPC
        final_cpc = base_cpc * multiplier * competition_adjustment * volume_adjustment
        
        # Cap at reasonable maximum
        return min(final_cpc, 50.0)
    
    def _calculate_target_cpa(self, group_type: str, keywords: List[Dict[str, Any]]) -> float:
        """Calculate target CPA using 2% conversion rate assumption."""
        if not keywords:
            return 25.0  # Default target CPA
        
        # Calculate average CPC
        avg_cpc = sum(kw.get('cpc', 0) for kw in keywords) / len(keywords)
        
        # 2% conversion rate assumption
        conversion_rate = 0.02
        
        # Target CPA = CPC / Conversion Rate
        target_cpa = avg_cpc / conversion_rate
        
        # Adjust based on ad group type
        type_adjustment = {
            'brand': 0.8,       # Lower CPA for brand (higher conversion)
            'transactional': 0.9,  # Lower CPA for transactional
            'commercial': 1.0,     # Standard CPA for commercial
            'competitor': 1.2,     # Higher CPA for competitor
            'location': 1.0,       # Standard CPA for location
            'long_tail': 1.1,      # Slightly higher CPA for long-tail
            'informational': 1.5,  # Higher CPA for informational
            'category': 1.0        # Standard CPA for category
        }
        
        adjustment = type_adjustment.get(group_type, 1.0)
        target_cpa *= adjustment
        
        # Cap at reasonable maximum
        return min(target_cpa, 200.0)
    
    def _calculate_ad_group_budget(self, group_type: str, keywords: List[Dict[str, Any]]) -> float:
        """Calculate daily budget allocation for ad group."""
        total_daily_budget = self.budget_config.get('daily_budget', 100)
        
        # Budget allocation by ad group type
        budget_allocation = {
            'brand': 0.25,        # 25% for brand keywords
            'transactional': 0.20, # 20% for transactional
            'commercial': 0.15,    # 15% for commercial
            'category': 0.15,      # 15% for category
            'location': 0.10,      # 10% for location
            'competitor': 0.08,    # 8% for competitor
            'long_tail': 0.05,     # 5% for long-tail
            'informational': 0.02  # 2% for informational
        }
        
        allocation = budget_allocation.get(group_type, 0.05)
        return total_daily_budget * allocation
    
    def _assign_match_types(self, keywords: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Assign appropriate match types to keywords."""
        match_types = {
            'broad': [],
            'phrase': [],
            'exact': [],
            'modified_broad': []
        }
        
        for keyword_data in keywords:
            keyword = keyword_data['keyword']
            word_count = len(keyword.split())
            commercial_intent = keyword_data.get('commercial_intent', 0)
            search_volume = keyword_data.get('search_volume', 0)
            
            # Determine match type based on characteristics
            if word_count == 1:
                match_types['broad'].append(keyword)
            elif word_count == 2:
                if commercial_intent > 0.7:
                    match_types['phrase'].append(keyword)
                else:
                    match_types['broad'].append(keyword)
            elif word_count >= 3:
                if search_volume < 1000:
                    match_types['exact'].append(keyword)
                else:
                    match_types['phrase'].append(keyword)
            else:
                match_types['broad'].append(keyword)
        
        return match_types
    
    def _determine_ad_group_priority(self, group_type: str) -> str:
        """Determine ad group priority for budget allocation."""
        priority_map = {
            'brand': 'high',
            'transactional': 'high',
            'commercial': 'medium',
            'category': 'medium',
            'location': 'medium',
            'competitor': 'low',
            'long_tail': 'low',
            'informational': 'low'
        }
        
        return priority_map.get(group_type, 'medium')
    
    def _calculate_campaign_metrics(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive campaign metrics."""
        total_keywords = sum(len(ag['keywords']) for ag in campaign['ad_groups'])
        total_ads = len(campaign['ads'])
        
        # Calculate average metrics across all keywords
        all_keywords = []
        for ag in campaign['ad_groups']:
            all_keywords.extend(ag['keyword_data'])
        
        if all_keywords:
            avg_search_volume = sum(kw.get('search_volume', 0) for kw in all_keywords) / len(all_keywords)
            avg_competition = sum(kw.get('competition', 0) for kw in all_keywords) / len(all_keywords)
            avg_cpc = sum(kw.get('cpc', 0) for kw in all_keywords) / len(all_keywords)
            avg_difficulty = sum(kw.get('difficulty_score', 0) for kw in all_keywords) / len(all_keywords)
        else:
            avg_search_volume = avg_competition = avg_cpc = avg_difficulty = 0
        
        # Calculate budget metrics
        total_daily_budget = sum(ag.get('daily_budget', 0) for ag in campaign['ad_groups'])
        total_monthly_budget = total_daily_budget * 30
        
        # Calculate estimated performance metrics
        estimated_clicks = sum(kw.get('search_volume', 0) * 0.01 for kw in all_keywords)  # 1% CTR assumption
        estimated_cost = estimated_clicks * avg_cpc
        estimated_conversions = estimated_clicks * 0.02  # 2% conversion rate
        estimated_cpa = estimated_cost / estimated_conversions if estimated_conversions > 0 else 0
        
        return {
            'total_keywords': total_keywords,
            'total_ad_groups': len(campaign['ad_groups']),
            'total_ads': total_ads,
            'avg_search_volume': avg_search_volume,
            'avg_competition': avg_competition,
            'avg_cpc': avg_cpc,
            'avg_difficulty_score': avg_difficulty,
            'total_daily_budget': total_daily_budget,
            'total_monthly_budget': total_monthly_budget,
            'estimated_clicks': estimated_clicks,
            'estimated_cost': estimated_cost,
            'estimated_conversions': estimated_conversions,
            'estimated_cpa': estimated_cpa,
            'estimated_roas': self.budget_config.get('target_roas', 4.0),
            'conversion_rate_assumption': 0.02,
            'click_through_rate_assumption': 0.01
        }
    
    def _create_ad_groups(self, keyword_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create ad groups from keyword groups."""
        ad_groups = []
        
        for i, group in enumerate(keyword_groups):
            ad_group = {
                'id': f"ad_group_{i+1}",
                'name': group['name'],
                'type': group['type'],
                'primary_keyword': group['primary_keyword'],
                'keywords': [kw['keyword'] for kw in group['keywords']],
                'keyword_data': group['keywords'],
                'status': 'active',
                'bid_strategy': self._determine_bid_strategy(group),
                'max_cpc': self._calculate_max_cpc(group),
                'created_at': datetime.now().isoformat()
            }
            
            ad_groups.append(ad_group)
        
        return ad_groups
    
    def _determine_bid_strategy(self, keyword_group: Dict[str, Any]) -> str:
        """Determine bid strategy for ad group based on keyword characteristics."""
        avg_competition = sum(kw['competition'] for kw in keyword_group['keywords']) / len(keyword_group['keywords'])
        avg_search_volume = sum(kw['search_volume'] for kw in keyword_group['keywords']) / len(keyword_group['keywords'])
        
        if avg_competition > 0.7:
            return 'manual_cpc'  # High competition - manual control
        elif avg_search_volume > 5000:
            return 'target_cpa'  # High volume - automated bidding
        else:
            return 'manual_cpc'  # Default to manual control
    
    def _calculate_max_cpc(self, keyword_group: Dict[str, Any]) -> float:
        """Calculate max CPC for ad group."""
        base_cpc = self.budget_config.get('max_cpc', 5.00)
        avg_competition = sum(kw['competition'] for kw in keyword_group['keywords']) / len(keyword_group['keywords'])
        
        # Adjust CPC based on competition
        if avg_competition > 0.7:
            return base_cpc * 1.5  # High competition - higher bids
        elif avg_competition < 0.3:
            return base_cpc * 0.8  # Low competition - lower bids
        else:
            return base_cpc
    
    def _generate_ads(self, ad_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ads for each ad group."""
        all_ads = []
        
        for ad_group in ad_groups:
            self.logger.info(f"Generating ads for ad group: {ad_group['name']}")
            
            # Generate multiple ads per ad group
            num_ads = min(3, self.ad_config.get('max_headlines', 3))  # Generate up to 3 ads per group
            
            for i in range(num_ads):
                ad = self._create_ad(ad_group, i+1)
                all_ads.append(ad)
        
        return all_ads
    
    def _create_ad(self, ad_group: Dict[str, Any], ad_number: int) -> Dict[str, Any]:
        """Create a single ad for an ad group."""
        # Generate ad content using AI if available
        if self.client and self.use_ai_ads:
            ad_content = self._generate_ai_ad_content(ad_group)
        else:
            ad_content = self._generate_template_ad_content(ad_group)
        
        ad = {
            'id': f"ad_{ad_group['id']}_{ad_number}",
            'ad_group_id': ad_group['id'],
            'ad_group_name': ad_group['name'],
            'headlines': ad_content['headlines'],
            'descriptions': ad_content['descriptions'],
            'final_url': self.brand_config.get('website', ''),
            'display_url': self._create_display_url(),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        return ad
    
    def _generate_ai_ad_content(self, ad_group: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ad content using AI."""
        try:
            # Prepare context for AI
            context = self._prepare_ad_context(ad_group)
            
            prompt = f"""
            Create Google Ads ad content for the following ad group:
            
            Ad Group: {ad_group['name']}
            Primary Keyword: {ad_group['primary_keyword']}
            Keywords: {', '.join(ad_group['keywords'][:5])}
            
            Business Information:
            {context}
            
            Requirements:
            - Create 3 compelling headlines (max 30 characters each)
            - Create 2 descriptions (max 90 characters each)
            - Include the primary keyword in at least one headline
            - Make it compelling and action-oriented
            - Include a call-to-action
            
            Return the content in this format:
            Headlines:
            1. [headline 1]
            2. [headline 2]
            3. [headline 3]
            
            Descriptions:
            1. [description 1]
            2. [description 2]
            """
            
            messages = [
                {"role": "system", "content": "You are an expert Google Ads copywriter who creates compelling ad content."},
                {"role": "user", "content": prompt}
            ]
            content_text = self.client.generate_response(messages=messages, max_tokens=500, temperature=0.7) or ""
            
            # Parse the response
            headlines = []
            descriptions = []
            
            lines = content_text.split('\n')
            in_headlines = False
            in_descriptions = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('Headlines:'):
                    in_headlines = True
                    in_descriptions = False
                elif line.startswith('Descriptions:'):
                    in_headlines = False
                    in_descriptions = True
                elif line and in_headlines and line[0].isdigit():
                    headline = line.split('.', 1)[1].strip()
                    if headline and len(headline) <= 30:
                        headlines.append(headline)
                elif line and in_descriptions and line[0].isdigit():
                    description = line.split('.', 1)[1].strip()
                    if description and len(description) <= 90:
                        descriptions.append(description)
            
            return {
                'headlines': headlines[:3],  # Ensure max 3 headlines
                'descriptions': descriptions[:2]  # Ensure max 2 descriptions
            }
            
        except Exception as e:
            self.logger.error(f"Error generating AI ad content: {e}")
            return self._generate_template_ad_content(ad_group)
    
    def _generate_template_ad_content(self, ad_group: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template ad content when AI is not available."""
        primary_keyword = ad_group['primary_keyword']
        brand_name = self.brand_config.get('name', 'Our Business')
        
        # Template headlines
        headlines = [
            f"{primary_keyword.title()} Services",
            f"Best {primary_keyword.title()} Near You",
            f"Professional {primary_keyword.title()}"
        ]
        
        # Template descriptions
        descriptions = [
            f"Get professional {primary_keyword} services. Fast, reliable, and affordable. Contact us today!",
            f"Expert {primary_keyword} solutions. Free consultation available. Call now for best rates."
        ]
        
        return {
            'headlines': headlines,
            'descriptions': descriptions
        }
    
    def _prepare_ad_context(self, ad_group: Dict[str, Any]) -> str:
        """Prepare context for AI ad generation."""
        context_parts = []
        
        # Brand information
        context_parts.append(f"Brand: {self.brand_config.get('name', 'N/A')}")
        context_parts.append(f"Brand Description: {self.brand_config.get('description', 'N/A')}")
        context_parts.append(f"Website: {self.brand_config.get('website', 'N/A')}")
        
        # Services
        services = self.brand_config.get('services', [])
        if services:
            context_parts.append(f"Services: {', '.join(services)}")
        
        # Locations
        if self.locations:
            location_names = [loc.get('name', '') for loc in self.locations]
            context_parts.append(f"Service Areas: {', '.join(location_names)}")
        
        # Budget information
        context_parts.append(f"Target ROAS: {self.budget_config.get('target_roas', 'N/A')}")
        
        return '\n'.join(context_parts)
    
    def _create_display_url(self) -> str:
        """Create display URL for ads."""
        website = self.brand_config.get('website', '')
        if website:
            # Extract domain from website
            from urllib.parse import urlparse
            parsed = urlparse(website)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return f"{domain}/services"
        else:
            return "yourbusiness.com/services"
    
    def _setup_targeting(self) -> Dict[str, Any]:
        """Setup targeting for the campaign."""
        targeting = {
            'locations': [],
            'languages': ['en'],
            'devices': ['desktop', 'mobile', 'tablet'],
            'audience_targeting': [],
            'demographics': {}
        }
        
        # Add location targeting
        for location in self.locations:
            targeting['locations'].append({
                'name': location.get('name', ''),
                'radius_miles': location.get('radius_miles', 25),
                'priority': location.get('priority', 'medium')
            })
        
        return targeting
    
    def _setup_budgets(self) -> Dict[str, Any]:
        """Setup budget configuration."""
        budgets = {
            'daily_budget': self.budget_config.get('daily_budget', 100),
            'monthly_budget': self.budget_config.get('monthly_budget', 3000),
            'max_cpc': self.budget_config.get('max_cpc', 5.00),
            'target_roas': self.budget_config.get('target_roas', 4.0),
            'bid_strategy': 'manual_cpc'
        }
        
        return budgets
    
    def _create_negative_keywords(self) -> List[str]:
        """Create negative keywords list."""
        negative_keywords = self.config.get('keywords', {}).get('negative_keywords', [])
        
        # Add common negative keywords
        common_negatives = [
            'free', 'cheap', 'discount', 'coupon', 'deal',
            'how to', 'what is', 'why', 'when', 'where',
            'job', 'career', 'employment', 'hire', 'hiring'
        ]
        
        all_negatives = list(set(negative_keywords + common_negatives))
        return all_negatives
    
    def save_campaign(self, campaign: Dict[str, Any], output_dir: str = 'output'):
        """Save campaign data to files with Google Ads compatible format."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save enhanced campaign structure
        campaign_df = pd.DataFrame([{
            'campaign_name': campaign['name'],
            'campaign_type': campaign['type'],
            'status': campaign['status'],
            'start_date': campaign['start_date'],
            'end_date': campaign['end_date'],
            'total_ad_groups': len(campaign['ad_groups']),
            'total_ads': len(campaign['ads']),
            'total_daily_budget': campaign['metrics']['total_daily_budget'],
            'total_monthly_budget': campaign['metrics']['total_monthly_budget'],
            'estimated_cpa': campaign['metrics']['estimated_cpa'],
            'estimated_roas': campaign['metrics']['estimated_roas']
        }])
        campaign_df.to_csv(f'{output_dir}/campaign.csv', index=False)
        
        # Save enhanced ad groups
        ad_groups_data = []
        for ad_group in campaign['ad_groups']:
            ad_groups_data.append({
                'ad_group_id': ad_group['id'],
                'ad_group_name': ad_group['name'],
                'type': ad_group['type'],
                'keyword_count': len(ad_group['keywords']),
                'bid_strategy': ad_group['bid_strategy'],
                'max_cpc': ad_group['max_cpc'],
                'target_cpa': ad_group['target_cpa'],
                'daily_budget': ad_group['daily_budget'],
                'priority': ad_group['priority'],
                'status': ad_group['status']
            })
        
        ad_groups_df = pd.DataFrame(ad_groups_data)
        ad_groups_df.to_csv(f'{output_dir}/ad_groups.csv', index=False)
        
        # Save ads
        ads_data = []
        for ad in campaign['ads']:
            ads_data.append({
                'ad_id': ad['id'],
                'ad_group_id': ad['ad_group_id'],
                'ad_group_name': ad['ad_group_name'],
                'headlines': ' | '.join(ad['headlines']),
                'descriptions': ' | '.join(ad['descriptions']),
                'final_url': ad['final_url'],
                'display_url': ad['display_url'],
                'status': ad['status']
            })
        
        ads_df = pd.DataFrame(ads_data)
        ads_df.to_csv(f'{output_dir}/ads.csv', index=False)
        
        # Save enhanced keywords with match types
        keywords_data = []
        for ad_group in campaign['ad_groups']:
            for keyword_data in ad_group['keyword_data']:
                # Get match type for this keyword
                match_type = self._get_keyword_match_type(keyword_data['keyword'], ad_group['match_types'])
                
                keywords_data.append({
                    'ad_group_id': ad_group['id'],
                    'ad_group_name': ad_group['name'],
                    'keyword': keyword_data['keyword'],
                    'match_type': match_type,
                    'search_intent': keyword_data.get('search_intent', 'unknown'),
                    'keyword_theme': keyword_data.get('keyword_theme', 'unknown'),
                    'search_volume': keyword_data.get('search_volume', 0),
                    'search_volume_category': keyword_data.get('search_volume_category', 'unknown'),
                    'competition': keyword_data.get('competition', 0.0),
                    'cpc': keyword_data.get('cpc', 0.0),
                    'commercial_intent': keyword_data.get('commercial_intent', 0.0),
                    'difficulty_score': keyword_data.get('difficulty_score', 0),
                    'difficulty_category': keyword_data.get('difficulty_category', 'unknown'),
                    'relevance_score': keyword_data.get('relevance_score', 0.0),
                    'source': keyword_data.get('source', 'unknown')
                })
        
        keywords_df = pd.DataFrame(keywords_data)
        keywords_df.to_csv(f'{output_dir}/campaign_keywords.csv', index=False)
        
        # Save targeting
        targeting_data = []
        for location in campaign['targeting']['locations']:
            targeting_data.append({
                'type': 'location',
                'name': location['name'],
                'radius_miles': location['radius_miles'],
                'priority': location['priority']
            })
        
        targeting_df = pd.DataFrame(targeting_data)
        targeting_df.to_csv(f'{output_dir}/targeting.csv', index=False)
        
        # Save campaign metrics
        metrics_df = pd.DataFrame([campaign['metrics']])
        metrics_df.to_csv(f'{output_dir}/campaign_metrics.csv', index=False)
        
        # Generate Google Ads compatible format
        self._generate_google_ads_format(campaign, output_dir)
        
        self.logger.info(f"Enhanced campaign data saved to {output_dir}/")
        
        # Generate campaign summary
        self._generate_campaign_summary(campaign, output_dir)
    
    def _get_keyword_match_type(self, keyword: str, match_types: Dict[str, List[str]]) -> str:
        """Get the appropriate match type for a keyword."""
        for match_type, keywords_list in match_types.items():
            if keyword in keywords_list:
                return match_type
        return 'broad'  # Default to broad match
    
    def _generate_google_ads_format(self, campaign: Dict[str, Any], output_dir: str):
        """Generate Google Ads compatible CSV format for easy import."""
        import os
        
        # Google Ads Campaign format
        campaign_rows = []
        for ad_group in campaign['ad_groups']:
            for keyword_data in ad_group['keyword_data']:
                match_type = self._get_keyword_match_type(keyword_data['keyword'], ad_group['match_types'])
                
                # Format match type for Google Ads
                google_ads_match = {
                    'broad': keyword_data['keyword'],
                    'phrase': f'"{keyword_data["keyword"]}"',
                    'exact': f'[{keyword_data["keyword"]}]',
                    'modified_broad': f'+{keyword_data["keyword"].replace(" ", " +")}'
                }.get(match_type, keyword_data['keyword'])
                
                campaign_rows.append({
                    'Campaign': campaign['name'],
                    'Ad group': ad_group['name'],
                    'Keyword': google_ads_match,
                    'Match type': match_type.upper(),
                    'Max CPC': ad_group['max_cpc'],
                    'Target CPA': ad_group['target_cpa'],
                    'Bid strategy': ad_group['bid_strategy'],
                    'Status': ad_group['status'],
                    'Quality score': '--',
                    'First page bid': '--',
                    'Top of page bid': '--',
                    'First position bid': '--'
                })
        
        # Create Google Ads format CSV
        google_ads_df = pd.DataFrame(campaign_rows)
        google_ads_df.to_csv(f'{output_dir}/google_ads_campaign.csv', index=False)
        
        # Create Google Ads Editor format (more detailed)
        editor_rows = []
        for ad_group in campaign['ad_groups']:
            for keyword_data in ad_group['keyword_data']:
                match_type = self._get_keyword_match_type(keyword_data['keyword'], ad_group['match_types'])
                
                editor_rows.append({
                    'Campaign': campaign['name'],
                    'Ad group': ad_group['name'],
                    'Keyword': keyword_data['keyword'],
                    'Match type': match_type.upper(),
                    'Max CPC': ad_group['max_cpc'],
                    'Target CPA': ad_group['target_cpa'],
                    'Bid strategy': ad_group['bid_strategy'],
                    'Status': ad_group['status'],
                    'Search volume': keyword_data.get('search_volume', 0),
                    'Competition': keyword_data.get('competition', 0.0),
                    'CPC': keyword_data.get('cpc', 0.0),
                    'Commercial intent': keyword_data.get('commercial_intent', 0.0),
                    'Difficulty score': keyword_data.get('difficulty_score', 0),
                    'Search intent': keyword_data.get('search_intent', 'unknown'),
                    'Keyword theme': keyword_data.get('keyword_theme', 'unknown'),
                    'Source': keyword_data.get('source', 'unknown')
                })
        
        editor_df = pd.DataFrame(editor_rows)
        editor_df.to_csv(f'{output_dir}/google_ads_editor.csv', index=False)
        
        # Create negative keywords file
        negative_keywords = []
        for keyword in campaign['negative_keywords']:
            negative_keywords.append({
                'Campaign': campaign['name'],
                'Ad group': 'All ad groups',
                'Keyword': keyword,
                'Match type': 'NEGATIVE',
                'Status': 'Active'
            })
        
        if negative_keywords:
            negative_df = pd.DataFrame(negative_keywords)
            negative_df.to_csv(f'{output_dir}/google_ads_negative_keywords.csv', index=False)
        
        self.logger.info(f"Google Ads compatible files generated in {output_dir}/")
    
    def _generate_campaign_summary(self, campaign: Dict[str, Any], output_dir: str):
        """Generate a comprehensive summary report of the enhanced campaign."""
        # Enhanced summary with all metrics
        summary = {
            'campaign_name': campaign['name'],
            'campaign_type': campaign['type'],
            'status': campaign['status'],
            'start_date': campaign['start_date'],
            'end_date': campaign['end_date'],
            'total_ad_groups': len(campaign['ad_groups']),
            'total_ads': len(campaign['ads']),
            'total_keywords': campaign['metrics']['total_keywords'],
            'total_daily_budget': campaign['metrics']['total_daily_budget'],
            'total_monthly_budget': campaign['metrics']['total_monthly_budget'],
            'avg_search_volume': campaign['metrics']['avg_search_volume'],
            'avg_competition': campaign['metrics']['avg_competition'],
            'avg_cpc': campaign['metrics']['avg_cpc'],
            'avg_difficulty_score': campaign['metrics']['avg_difficulty_score'],
            'estimated_clicks': campaign['metrics']['estimated_clicks'],
            'estimated_cost': campaign['metrics']['estimated_cost'],
            'estimated_conversions': campaign['metrics']['estimated_conversions'],
            'estimated_cpa': campaign['metrics']['estimated_cpa'],
            'estimated_roas': campaign['metrics']['estimated_roas'],
            'target_locations': len(campaign['targeting']['locations']),
            'negative_keywords': len(campaign['negative_keywords']),
            'conversion_rate_assumption': campaign['metrics']['conversion_rate_assumption'],
            'click_through_rate_assumption': campaign['metrics']['click_through_rate_assumption'],
            'created_at': campaign['created_at']
        }
        
        summary_df = pd.DataFrame([summary])
        summary_df.to_csv(f'{output_dir}/campaign_summary.csv', index=False)
        
        # Generate ad group type distribution
        ad_group_types = {}
        for ag in campaign['ad_groups']:
            ag_type = ag['type']
            if ag_type not in ad_group_types:
                ad_group_types[ag_type] = {
                    'count': 0,
                    'total_keywords': 0,
                    'total_budget': 0,
                    'avg_cpc': 0,
                    'avg_target_cpa': 0
                }
            
            ad_group_types[ag_type]['count'] += 1
            ad_group_types[ag_type]['total_keywords'] += len(ag['keywords'])
            ad_group_types[ag_type]['total_budget'] += ag['daily_budget']
            ad_group_types[ag_type]['avg_cpc'] += ag['max_cpc']
            ad_group_types[ag_type]['avg_target_cpa'] += ag['target_cpa']
        
        # Calculate averages
        for ag_type in ad_group_types:
            count = ad_group_types[ag_type]['count']
            ad_group_types[ag_type]['avg_cpc'] /= count
            ad_group_types[ag_type]['avg_target_cpa'] /= count
        
        # Save ad group type distribution
        ag_distribution = []
        for ag_type, data in ad_group_types.items():
            ag_distribution.append({
                'ad_group_type': ag_type,
                'count': data['count'],
                'total_keywords': data['total_keywords'],
                'total_daily_budget': data['total_budget'],
                'avg_cpc': data['avg_cpc'],
                'avg_target_cpa': data['avg_target_cpa']
            })
        
        ag_distribution_df = pd.DataFrame(ag_distribution)
        ag_distribution_df.to_csv(f'{output_dir}/ad_group_type_distribution.csv', index=False)
        
        # Generate bid strategy distribution
        bid_strategies = {}
        for ag in campaign['ad_groups']:
            strategy = ag['bid_strategy']
            bid_strategies[strategy] = bid_strategies.get(strategy, 0) + 1
        
        bid_strategy_df = pd.DataFrame([
            {'bid_strategy': strategy, 'count': count}
            for strategy, count in bid_strategies.items()
        ])
        bid_strategy_df.to_csv(f'{output_dir}/bid_strategy_distribution.csv', index=False)
        
        self.logger.info("Enhanced campaign summary generated successfully") 