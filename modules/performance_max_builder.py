"""
Performance Max Campaign Builder Module
Creates Performance Max campaigns with themes, asset groups, and budget allocation.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd
from datetime import datetime


@dataclass
class PMaxTheme:
    """Data class for Performance Max campaign themes."""
    theme_name: str
    theme_category: str
    keywords: List[str]
    target_audience: List[str]
    budget_allocation: float
    priority: str
    asset_groups: List[str]


@dataclass
class PMaxAssetGroup:
    """Data class for Performance Max asset groups."""
    asset_group_name: str
    theme_category: str
    headlines: List[str]
    descriptions: List[str]
    images: List[str]
    videos: List[str]
    logos: List[str]
    call_to_actions: List[str]
    final_urls: List[str]
    display_urls: List[str]


@dataclass
class ShoppingProductGroup:
    """Data class for Shopping campaign product groupings."""
    product_group_name: str
    category: str
    products: List[Dict[str, Any]]
    bid_modifiers: Dict[str, float]
    targeting: Dict[str, Any]
    budget_allocation: float


class PerformanceMaxBuilder:
    """Performance Max and Shopping campaign builder."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Performance Max builder with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # PMax settings
        self.pmax_settings = config.get('performance_max', {})
        self.shopping_settings = config.get('shopping', {})
        
        # Asset requirements
        self.asset_requirements = {
            'headlines': {'min': 5, 'max': 15},
            'descriptions': {'min': 5, 'max': 5},
            'images': {'min': 1, 'max': 20},
            'videos': {'min': 0, 'max': 5},
            'logos': {'min': 1, 'max': 5},
            'call_to_actions': {'min': 1, 'max': 10},
            'final_urls': {'min': 1, 'max': 20},
            'display_urls': {'min': 1, 'max': 20}
        }

    def create_performance_max_campaigns(self, keywords: List[Dict[str, Any]], 
                                       brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Performance Max campaigns based on keyword categories.
        
        Args:
            keywords: List of processed keywords
            brand_data: Brand website data
            
        Returns:
            Dictionary containing PMax campaign structure
        """
        try:
            self.logger.info("Creating Performance Max campaigns...")
            
            # Step 1: Create themes based on keyword categories
            themes = self._create_pmax_themes(keywords, brand_data)
            
            # Step 2: Create asset groups for each theme
            asset_groups = self._create_asset_groups(themes, brand_data)
            
            # Step 3: Create Shopping product groupings
            shopping_groups = self._create_shopping_product_groups(brand_data)
            
            # Step 4: Calculate budget allocation
            budget_allocation = self._calculate_budget_allocation(themes, shopping_groups)
            
            # Step 5: Generate campaign structure
            pmax_campaigns = self._generate_pmax_campaign_structure(
                themes, asset_groups, shopping_groups, budget_allocation
            )
            
            self.logger.info(f"Created {len(themes)} PMax themes and {len(asset_groups)} asset groups")
            return pmax_campaigns
            
        except Exception as e:
            self.logger.error(f"Error creating Performance Max campaigns: {e}")
            return {}

    def _create_pmax_themes(self, keywords: List[Dict[str, Any]], 
                           brand_data: Dict[str, Any]) -> List[PMaxTheme]:
        """Create Performance Max themes based on keyword categories."""
        themes = []
        
        # Group keywords by theme and intent
        keyword_groups = self._group_keywords_for_themes(keywords)
        
        # Create themes for each major category
        for category, category_keywords in keyword_groups.items():
            if len(category_keywords) >= 5:  # Minimum keywords for a theme
                theme = PMaxTheme(
                    theme_name=self._generate_theme_name(category, brand_data),
                    theme_category=category,
                    keywords=[kw['keyword'] for kw in category_keywords],
                    target_audience=self._identify_target_audience(category, brand_data),
                    budget_allocation=self._calculate_theme_budget(category_keywords),
                    priority=self._determine_theme_priority(category, category_keywords),
                    asset_groups=[]
                )
                themes.append(theme)
        
        return themes

    def _group_keywords_for_themes(self, keywords: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group keywords into theme categories."""
        groups = {
            'Brand': [],
            'Category': [],
            'Competitor': [],
            'Location': [],
            'Long-tail': [],
            'Informational': [],
            'Transactional': [],
            'Commercial': []
        }
        
        for keyword in keywords:
            # Use existing classifications
            intent = keyword.get('search_intent', 'Commercial')
            theme = keyword.get('keyword_theme', 'Category')
            
            # Map to theme categories
            if keyword.get('is_brand_keyword', False):
                groups['Brand'].append(keyword)
            elif keyword.get('is_competitor_keyword', False):
                groups['Competitor'].append(keyword)
            elif keyword.get('is_location_keyword', False):
                groups['Location'].append(keyword)
            elif keyword.get('is_long_tail_keyword', False):
                groups['Long-tail'].append(keyword)
            elif intent == 'informational':
                groups['Informational'].append(keyword)
            elif intent == 'transactional':
                groups['Transactional'].append(keyword)
            else:
                groups['Commercial'].append(keyword)
        
        return groups

    def _generate_theme_name(self, category: str, brand_data: Dict[str, Any]) -> str:
        """Generate a theme name for Performance Max campaigns."""
        brand_name = brand_data.get('business_name', 'Business')
        
        theme_names = {
            'Brand': f"{brand_name} - Brand Awareness",
            'Category': f"{brand_name} - Product Category",
            'Competitor': f"{brand_name} - Competitive",
            'Location': f"{brand_name} - Local Service",
            'Long-tail': f"{brand_name} - Long-tail Keywords",
            'Informational': f"{brand_name} - Educational Content",
            'Transactional': f"{brand_name} - Purchase Intent",
            'Commercial': f"{brand_name} - Commercial Intent"
        }
        
        return theme_names.get(category, f"{brand_name} - {category}")

    def _identify_target_audience(self, category: str, brand_data: Dict[str, Any]) -> List[str]:
        """Identify target audience for each theme category."""
        base_audience = brand_data.get('target_audience', [])
        
        audience_mapping = {
            'Brand': ['Brand aware', 'Existing customers', 'High-value prospects'],
            'Category': ['Product researchers', 'Comparison shoppers', 'Industry professionals'],
            'Competitor': ['Competitor customers', 'Switching prospects', 'Price-sensitive'],
            'Location': ['Local customers', 'Nearby prospects', 'Location-specific'],
            'Long-tail': ['Specific need customers', 'Detailed researchers', 'Niche audience'],
            'Informational': ['Learning audience', 'Problem solvers', 'Research phase'],
            'Transactional': ['Ready to buy', 'Purchase intent', 'High conversion potential'],
            'Commercial': ['Commercial intent', 'Business customers', 'B2B prospects']
        }
        
        return audience_mapping.get(category, base_audience)

    def _calculate_theme_budget(self, keywords: List[Dict[str, Any]]) -> float:
        """Calculate budget allocation for a theme based on keyword metrics."""
        total_search_volume = sum(kw.get('search_volume', 0) for kw in keywords)
        avg_cpc = sum(kw.get('cpc', 0) for kw in keywords) / len(keywords) if keywords else 0
        
        # Base budget calculation
        base_budget = total_search_volume * avg_cpc * 0.1  # 10% of potential spend
        
        # Adjust based on keyword count and quality
        keyword_count_multiplier = min(len(keywords) / 10, 2.0)  # Cap at 2x
        quality_multiplier = sum(kw.get('relevance_score', 0.5) for kw in keywords) / len(keywords) if keywords else 0.5
        
        return base_budget * keyword_count_multiplier * quality_multiplier

    def _determine_theme_priority(self, category: str, keywords: List[Dict[str, Any]]) -> str:
        """Determine priority level for a theme."""
        priority_scores = {
            'Brand': 3,
            'Transactional': 3,
            'Commercial': 2,
            'Category': 2,
            'Location': 2,
            'Competitor': 1,
            'Long-tail': 1,
            'Informational': 1
        }
        
        base_priority = priority_scores.get(category, 1)
        
        # Adjust based on keyword metrics
        avg_volume = sum(kw.get('search_volume', 0) for kw in keywords) / len(keywords) if keywords else 0
        avg_cpc = sum(kw.get('cpc', 0) for kw in keywords) / len(keywords) if keywords else 0
        
        if avg_volume > 1000 and avg_cpc > 2.0:
            base_priority += 1
        elif avg_volume < 100 or avg_cpc < 0.5:
            base_priority -= 1
        
        if base_priority >= 3:
            return 'high'
        elif base_priority >= 2:
            return 'medium'
        else:
            return 'low'

    def _create_asset_groups(self, themes: List[PMaxTheme], 
                           brand_data: Dict[str, Any]) -> List[PMaxAssetGroup]:
        """Create asset groups for Performance Max campaigns."""
        asset_groups = []
        
        for theme in themes:
            asset_group = PMaxAssetGroup(
                asset_group_name=f"{theme.theme_name} - Assets",
                theme_category=theme.theme_category,
                headlines=self._generate_headlines(theme, brand_data),
                descriptions=self._generate_descriptions(theme, brand_data),
                images=self._suggest_images(theme, brand_data),
                videos=self._suggest_videos(theme, brand_data),
                logos=self._suggest_logos(brand_data),
                call_to_actions=self._generate_call_to_actions(theme),
                final_urls=self._generate_final_urls(theme, brand_data),
                display_urls=self._generate_display_urls(brand_data)
            )
            asset_groups.append(asset_group)
            
            # Add asset group to theme
            theme.asset_groups.append(asset_group.asset_group_name)
        
        return asset_groups

    def _generate_headlines(self, theme: PMaxTheme, brand_data: Dict[str, Any]) -> List[str]:
        """Generate headlines for asset groups."""
        brand_name = brand_data.get('business_name', 'Business')
        services = brand_data.get('services', [])
        
        base_headlines = [
            f"{brand_name} - Professional Service",
            f"Best {brand_name} in Your Area",
            f"Trusted {brand_name} Experts",
            f"Quality {brand_name} Service",
            f"Local {brand_name} Professionals"
        ]
        
        # Theme-specific headlines
        theme_headlines = {
            'Brand': [
                f"{brand_name} - Your Trusted Partner",
                f"Choose {brand_name} for Quality",
                f"{brand_name} - Industry Leaders"
            ],
            'Location': [
                f"{brand_name} Near You",
                f"Local {brand_name} Service",
                f"Find {brand_name} in Your Area"
            ],
            'Transactional': [
                f"Get {brand_name} Today",
                f"Book {brand_name} Now",
                f"Start Your {brand_name} Project"
            ]
        }
        
        headlines = base_headlines + theme_headlines.get(theme.theme_category, [])
        
        # Add service-specific headlines
        for service in services[:3]:  # Limit to 3 services
            headlines.append(f"{service} by {brand_name}")
        
        return headlines[:self.asset_requirements['headlines']['max']]

    def _generate_descriptions(self, theme: PMaxTheme, brand_data: Dict[str, Any]) -> List[str]:
        """Generate descriptions for asset groups."""
        brand_name = brand_data.get('business_name', 'Business')
        description = brand_data.get('meta_description', 'Professional service provider')
        
        base_descriptions = [
            f"{brand_name} provides professional services with quality and reliability. Contact us today for expert solutions.",
            f"Choose {brand_name} for your professional needs. We deliver results with excellence and customer satisfaction.",
            f"{brand_name} - your trusted partner for professional services. Experience quality and reliability."
        ]
        
        # Theme-specific descriptions
        theme_descriptions = {
            'Brand': [
                f"{brand_name} - the name you can trust. Professional service with proven results.",
                f"Choose {brand_name} for excellence. We're the industry leaders in professional services."
            ],
            'Location': [
                f"Local {brand_name} service in your area. Professional and reliable solutions nearby.",
                f"Find {brand_name} near you. Local expertise with professional quality."
            ]
        }
        
        descriptions = base_descriptions + theme_descriptions.get(theme.theme_category, [])
        return descriptions[:self.asset_requirements['descriptions']['max']]

    def _suggest_images(self, theme: PMaxTheme, brand_data: Dict[str, Any]) -> List[str]:
        """Suggest images for asset groups."""
        brand_name = brand_data.get('business_name', 'Business')
        
        image_suggestions = [
            f"{brand_name.lower()}-logo.png",
            f"{brand_name.lower()}-team.jpg",
            f"{brand_name.lower()}-service.jpg",
            f"{brand_name.lower()}-office.jpg",
            f"{brand_name.lower()}-work.jpg"
        ]
        
        # Theme-specific images
        theme_images = {
            'Brand': [
                f"{brand_name.lower()}-brand-story.jpg",
                f"{brand_name.lower()}-company-culture.jpg"
            ],
            'Location': [
                f"{brand_name.lower()}-local-service.jpg",
                f"{brand_name.lower()}-community.jpg"
            ]
        }
        
        images = image_suggestions + theme_images.get(theme.theme_category, [])
        return images[:self.asset_requirements['images']['max']]

    def _suggest_videos(self, theme: PMaxTheme, brand_data: Dict[str, Any]) -> List[str]:
        """Suggest videos for asset groups."""
        brand_name = brand_data.get('business_name', 'Business')
        
        video_suggestions = [
            f"{brand_name.lower()}-company-intro.mp4",
            f"{brand_name.lower()}-service-overview.mp4"
        ]
        
        # Theme-specific videos
        theme_videos = {
            'Brand': [f"{brand_name.lower()}-brand-story.mp4"],
            'Transactional': [f"{brand_name.lower()}-how-to-book.mp4"]
        }
        
        videos = video_suggestions + theme_videos.get(theme.theme_category, [])
        return videos[:self.asset_requirements['videos']['max']]

    def _suggest_logos(self, brand_data: Dict[str, Any]) -> List[str]:
        """Suggest logos for asset groups."""
        brand_name = brand_data.get('business_name', 'Business')
        
        return [
            f"{brand_name.lower()}-logo-primary.png",
            f"{brand_name.lower()}-logo-secondary.png",
            f"{brand_name.lower()}-logo-icon.png"
        ][:self.asset_requirements['logos']['max']]

    def _generate_call_to_actions(self, theme: PMaxTheme) -> List[str]:
        """Generate call-to-action buttons for asset groups."""
        base_ctas = [
            "Get Started",
            "Learn More",
            "Contact Us",
            "Get Quote",
            "Book Now"
        ]
        
        # Theme-specific CTAs
        theme_ctas = {
            'Brand': ["Learn About Us", "Our Story"],
            'Transactional': ["Buy Now", "Order Today", "Get Started"],
            'Location': ["Find Near You", "Local Service"]
        }
        
        ctas = base_ctas + theme_ctas.get(theme.theme_category, [])
        return ctas[:self.asset_requirements['call_to_actions']['max']]

    def _generate_final_urls(self, theme: PMaxTheme, brand_data: Dict[str, Any]) -> List[str]:
        """Generate final URLs for asset groups."""
        base_url = brand_data.get('website_url', 'https://example.com')
        
        urls = [
            base_url,
            f"{base_url}/services",
            f"{base_url}/about",
            f"{base_url}/contact"
        ]
        
        # Theme-specific URLs
        theme_urls = {
            'Brand': [f"{base_url}/about", f"{base_url}/company"],
            'Transactional': [f"{base_url}/pricing", f"{base_url}/order"],
            'Location': [f"{base_url}/locations", f"{base_url}/local"]
        }
        
        final_urls = urls + theme_urls.get(theme.theme_category, [])
        return final_urls[:self.asset_requirements['final_urls']['max']]

    def _generate_display_urls(self, brand_data: Dict[str, Any]) -> List[str]:
        """Generate display URLs for asset groups."""
        base_url = brand_data.get('website_url', 'example.com')
        domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        return [
            domain,
            f"www.{domain}",
            f"{domain}/services",
            f"{domain}/about"
        ][:self.asset_requirements['display_urls']['max']]

    def _create_shopping_product_groups(self, brand_data: Dict[str, Any]) -> List[ShoppingProductGroup]:
        """Create Shopping campaign product groupings."""
        product_groups = []
        
        # Extract products/services from brand data
        services = brand_data.get('services', [])
        products = brand_data.get('products', [])
        
        # Create product groups for services
        if services:
            service_group = ShoppingProductGroup(
                product_group_name="Services",
                category="Services",
                products=[{
                    'name': service,
                    'category': 'Service',
                    'price_range': '$50-$500',
                    'availability': 'Available'
                } for service in services],
                bid_modifiers={
                    'mobile': 1.1,
                    'tablet': 1.0,
                    'desktop': 1.2
                },
                targeting={
                    'locations': brand_data.get('locations', []),
                    'audience': ['Service seekers', 'Professional customers']
                },
                budget_allocation=0.4  # 40% of shopping budget
            )
            product_groups.append(service_group)
        
        # Create product groups for products
        if products:
            product_group = ShoppingProductGroup(
                product_group_name="Products",
                category="Products",
                products=[{
                    'name': product,
                    'category': 'Product',
                    'price_range': '$10-$200',
                    'availability': 'In Stock'
                } for product in products],
                bid_modifiers={
                    'mobile': 1.0,
                    'tablet': 1.1,
                    'desktop': 1.1
                },
                targeting={
                    'locations': brand_data.get('locations', []),
                    'audience': ['Product buyers', 'E-commerce customers']
                },
                budget_allocation=0.6  # 60% of shopping budget
            )
            product_groups.append(product_group)
        
        return product_groups

    def _calculate_budget_allocation(self, themes: List[PMaxTheme], 
                                   shopping_groups: List[ShoppingProductGroup]) -> Dict[str, Any]:
        """Calculate budget allocation across all campaign types."""
        total_pmax_budget = sum(theme.budget_allocation for theme in themes)
        total_shopping_budget = sum(group.budget_allocation for group in shopping_groups)
        
        # Get base budget from config
        base_daily_budget = self.config.get('budgets', {}).get('daily_budget', 100)
        
        # Allocate between PMax and Shopping
        pmax_percentage = 0.7  # 70% to PMax
        shopping_percentage = 0.3  # 30% to Shopping
        
        allocation = {
            'total_daily_budget': base_daily_budget,
            'pmax_daily_budget': base_daily_budget * pmax_percentage,
            'shopping_daily_budget': base_daily_budget * shopping_percentage,
            'theme_allocations': {},
            'shopping_allocations': {},
            'recommendations': []
        }
        
        # Allocate PMax budget across themes
        if total_pmax_budget > 0:
            for theme in themes:
                percentage = theme.budget_allocation / total_pmax_budget
                allocation['theme_allocations'][theme.theme_name] = {
                    'daily_budget': allocation['pmax_daily_budget'] * percentage,
                    'percentage': percentage,
                    'priority': theme.priority
                }
        
        # Allocate Shopping budget across groups
        if total_shopping_budget > 0:
            for group in shopping_groups:
                percentage = group.budget_allocation / total_shopping_budget
                allocation['shopping_allocations'][group.product_group_name] = {
                    'daily_budget': allocation['shopping_daily_budget'] * percentage,
                    'percentage': percentage
                }
        
        # Generate recommendations
        allocation['recommendations'] = self._generate_budget_recommendations(allocation, themes, shopping_groups)
        
        return allocation

    def _generate_budget_recommendations(self, allocation: Dict[str, Any], 
                                       themes: List[PMaxTheme], 
                                       shopping_groups: List[ShoppingProductGroup]) -> List[str]:
        """Generate budget allocation recommendations."""
        recommendations = []
        
        # High priority theme recommendations
        high_priority_themes = [t for t in themes if t.priority == 'high']
        if high_priority_themes:
            recommendations.append(
                f"Focus 60% of PMax budget on {len(high_priority_themes)} high-priority themes"
            )
        
        # Shopping campaign recommendations
        if shopping_groups:
            recommendations.append(
                f"Allocate 30% of total budget to Shopping campaigns for {len(shopping_groups)} product groups"
            )
        
        # Performance monitoring recommendations
        recommendations.extend([
            "Monitor PMax performance weekly and adjust theme budgets based on ROAS",
            "Use Shopping campaign bid modifiers to optimize for mobile vs desktop",
            "Consider seasonal budget adjustments for high-performing themes"
        ])
        
        return recommendations

    def _generate_pmax_campaign_structure(self, themes: List[PMaxTheme], 
                                        asset_groups: List[PMaxAssetGroup],
                                        shopping_groups: List[ShoppingProductGroup],
                                        budget_allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete Performance Max campaign structure."""
        return {
            'campaign_type': 'Performance Max & Shopping',
            'created_at': datetime.now().isoformat(),
            'themes': [self._theme_to_dict(theme) for theme in themes],
            'asset_groups': [self._asset_group_to_dict(ag) for ag in asset_groups],
            'shopping_groups': [self._shopping_group_to_dict(sg) for sg in shopping_groups],
            'budget_allocation': budget_allocation,
            'summary': self._generate_pmax_summary(themes, asset_groups, shopping_groups, budget_allocation)
        }

    def _theme_to_dict(self, theme: PMaxTheme) -> Dict[str, Any]:
        """Convert PMaxTheme to dictionary."""
        return {
            'theme_name': theme.theme_name,
            'theme_category': theme.theme_category,
            'keywords': theme.keywords,
            'target_audience': theme.target_audience,
            'budget_allocation': theme.budget_allocation,
            'priority': theme.priority,
            'asset_groups': theme.asset_groups
        }

    def _asset_group_to_dict(self, asset_group: PMaxAssetGroup) -> Dict[str, Any]:
        """Convert PMaxAssetGroup to dictionary."""
        return {
            'asset_group_name': asset_group.asset_group_name,
            'theme_category': asset_group.theme_category,
            'headlines': asset_group.headlines,
            'descriptions': asset_group.descriptions,
            'images': asset_group.images,
            'videos': asset_group.videos,
            'logos': asset_group.logos,
            'call_to_actions': asset_group.call_to_actions,
            'final_urls': asset_group.final_urls,
            'display_urls': asset_group.display_urls
        }

    def _shopping_group_to_dict(self, shopping_group: ShoppingProductGroup) -> Dict[str, Any]:
        """Convert ShoppingProductGroup to dictionary."""
        return {
            'product_group_name': shopping_group.product_group_name,
            'category': shopping_group.category,
            'products': shopping_group.products,
            'bid_modifiers': shopping_group.bid_modifiers,
            'targeting': shopping_group.targeting,
            'budget_allocation': shopping_group.budget_allocation
        }

    def _generate_pmax_summary(self, themes: List[PMaxTheme], 
                             asset_groups: List[PMaxAssetGroup],
                             shopping_groups: List[ShoppingProductGroup],
                             budget_allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of Performance Max campaigns."""
        return {
            'total_themes': len(themes),
            'total_asset_groups': len(asset_groups),
            'total_shopping_groups': len(shopping_groups),
            'total_keywords': sum(len(theme.keywords) for theme in themes),
            'total_daily_budget': budget_allocation['total_daily_budget'],
            'pmax_budget': budget_allocation['pmax_daily_budget'],
            'shopping_budget': budget_allocation['shopping_daily_budget'],
            'high_priority_themes': len([t for t in themes if t.priority == 'high']),
            'recommendations': budget_allocation['recommendations']
        }

    def save_pmax_campaigns(self, pmax_campaigns: Dict[str, Any]) -> None:
        """Save Performance Max campaigns to files."""
        try:
            # Create output directory
            os.makedirs('output', exist_ok=True)
            
            # Save main campaign structure
            with open('output/performance_max_campaigns.json', 'w') as f:
                json.dump(pmax_campaigns, f, indent=2)
            
            # Save themes to CSV
            themes_df = pd.DataFrame([
                {
                    'theme_name': theme['theme_name'],
                    'theme_category': theme['theme_category'],
                    'keyword_count': len(theme['keywords']),
                    'target_audience': ', '.join(theme['target_audience']),
                    'budget_allocation': theme['budget_allocation'],
                    'priority': theme['priority']
                }
                for theme in pmax_campaigns['themes']
            ])
            themes_df.to_csv('output/pmax_themes.csv', index=False)
            
            # Save asset groups to CSV
            asset_groups_data = []
            for ag in pmax_campaigns['asset_groups']:
                asset_groups_data.append({
                    'asset_group_name': ag['asset_group_name'],
                    'theme_category': ag['theme_category'],
                    'headlines_count': len(ag['headlines']),
                    'descriptions_count': len(ag['descriptions']),
                    'images_count': len(ag['images']),
                    'videos_count': len(ag['videos']),
                    'logos_count': len(ag['logos']),
                    'call_to_actions_count': len(ag['call_to_actions']),
                    'final_urls_count': len(ag['final_urls']),
                    'display_urls_count': len(ag['display_urls'])
                })
            
            asset_groups_df = pd.DataFrame(asset_groups_data)
            asset_groups_df.to_csv('output/pmax_asset_groups.csv', index=False)
            
            # Save shopping groups to CSV
            shopping_data = []
            for sg in pmax_campaigns['shopping_groups']:
                shopping_data.append({
                    'product_group_name': sg['product_group_name'],
                    'category': sg['category'],
                    'product_count': len(sg['products']),
                    'budget_allocation': sg['budget_allocation'],
                    'mobile_bid_modifier': sg['bid_modifiers'].get('mobile', 1.0),
                    'desktop_bid_modifier': sg['bid_modifiers'].get('desktop', 1.0)
                })
            
            shopping_df = pd.DataFrame(shopping_data)
            shopping_df.to_csv('output/shopping_product_groups.csv', index=False)
            
            # Save budget allocation to CSV
            budget_data = []
            for theme_name, allocation in pmax_campaigns['budget_allocation']['theme_allocations'].items():
                budget_data.append({
                    'campaign_type': 'PMax',
                    'name': theme_name,
                    'daily_budget': allocation['daily_budget'],
                    'percentage': allocation['percentage'],
                    'priority': allocation['priority']
                })
            
            for group_name, allocation in pmax_campaigns['budget_allocation']['shopping_allocations'].items():
                budget_data.append({
                    'campaign_type': 'Shopping',
                    'name': group_name,
                    'daily_budget': allocation['daily_budget'],
                    'percentage': allocation['percentage'],
                    'priority': 'N/A'
                })
            
            budget_df = pd.DataFrame(budget_data)
            budget_df.to_csv('output/campaign_budget_allocation.csv', index=False)
            
            # Save recommendations
            with open('output/pmax_recommendations.txt', 'w') as f:
                f.write("Performance Max & Shopping Campaign Recommendations\n")
                f.write("=" * 50 + "\n\n")
                for i, rec in enumerate(pmax_campaigns['budget_allocation']['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
            
            self.logger.info("Performance Max campaigns saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving Performance Max campaigns: {e}") 