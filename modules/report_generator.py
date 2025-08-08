"""
Comprehensive Report Generator Module
Phase 6: Output Generation & Validation - Step 6.1
Handles comprehensive output generation including keyword exports, campaign documentation,
bid recommendations, performance projections, and visual representations.
"""

import logging
import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from .llm_client import LLMClient


class ReportGenerator:
    """Comprehensive report generator for SEM campaign automation results."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the report generator with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Setup LLM client (Hugging Face) for insights if enabled
        self.use_ai_insights = bool(self.config.get('reports', {}).get('use_ai_generation', False))
        if self.use_ai_insights:
            self.client = LLMClient(provider="huggingface")
            if not self.client.is_available():
                self.logger.warning("AI insights enabled but no LLM provider available; proceeding without AI insights.")
                self.client = None
        else:
            self.client = None
            self.logger.info("AI insights disabled by config; proceeding with deterministic summaries.")
        
        # Output settings
        self.output_dir = 'output'
        self.report_format = config.get('output', {}).get('report_format', 'pdf')
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Performance assumptions
        self.performance_assumptions = {
            'avg_ctr': 0.02,  # 2% average click-through rate
            'avg_conversion_rate': 0.02,  # 2% conversion rate
            'avg_order_value': 100.0,  # $100 average order value
            'target_roas': 4.0,  # 400% ROAS target
            'max_cpa': 50.0,  # $50 maximum cost per acquisition
        }
    
    def generate_comprehensive_report(self, 
                                   campaign: Dict[str, Any],
                                   keywords: List[Dict[str, Any]],
                                   brand_analysis: Optional[Any] = None,
                                   pmax_campaigns: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report with all required components.
        
        Args:
            campaign: Search campaign data
            keywords: Processed keyword data
            brand_analysis: Business analysis results
            pmax_campaigns: Performance Max campaign data
            
        Returns:
            Dictionary containing all report data
        """
        self.logger.info("Starting comprehensive report generation...")
        
        try:
            # Step 1: Export keyword lists with all required fields
            keyword_report = self._export_keyword_lists(keywords)
            
            # Step 2: Create campaign structure documentation
            campaign_docs = self._create_campaign_documentation(campaign, pmax_campaigns)
            
            # Step 3: Generate bid recommendations with justifications
            bid_recommendations = self._generate_bid_recommendations(campaign, keywords)
            
            # Step 4: Provide performance projections based on budgets
            performance_projections = self._generate_performance_projections(campaign, keywords)
            
            # Step 5: Create visual representations
            visual_reports = self._create_visual_representations(campaign, keywords, pmax_campaigns)
            
            # Step 6: Generate executive summary
            executive_summary = self._generate_executive_summary(
                keyword_report, campaign_docs, bid_recommendations, 
                performance_projections, brand_analysis
            )
            
            # Step 7: Save all reports
            self._save_all_reports(
                keyword_report, campaign_docs, bid_recommendations,
                performance_projections, visual_reports, executive_summary
            )
            
            self.logger.info("Comprehensive report generation completed successfully")
            
            return {
                'keyword_report': keyword_report,
                'campaign_documentation': campaign_docs,
                'bid_recommendations': bid_recommendations,
                'performance_projections': performance_projections,
                'visual_reports': visual_reports,
                'executive_summary': executive_summary,
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            raise
    
    def _export_keyword_lists(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export keyword lists with all required fields."""
        self.logger.info("Exporting comprehensive keyword lists...")
        
        # Create detailed keyword export
        keyword_data = []
        for kw in keywords:
            keyword_data.append({
                'keyword': kw.get('keyword', ''),
                'search_volume': kw.get('search_volume', 0),
                'search_volume_category': kw.get('search_volume_category', 'unknown'),
                'competition': kw.get('competition', 0.0),
                'cpc': kw.get('cpc', 0.0),
                'commercial_intent': kw.get('commercial_intent', 0.0),
                'relevance_score': kw.get('relevance_score', 0.0),
                'difficulty_score': kw.get('difficulty_score', 0),
                'difficulty_category': kw.get('difficulty_category', 'unknown'),
                'match_type': kw.get('match_type', 'unknown'),
                'intent_type': kw.get('intent_type', 'unknown'),
                'search_intent': kw.get('search_intent', 'unknown'),
                'keyword_theme': kw.get('keyword_theme', 'unknown'),
                'source': kw.get('source', 'unknown'),
                'preliminary_match_type': kw.get('preliminary_match_type', 'unknown'),
                'competitor_type': kw.get('competitor_type', 'unknown'),
                'location_type': kw.get('location_type', 'unknown'),
                'longtail_type': kw.get('longtail_type', 'unknown'),
                'intent_theme_group': kw.get('intent_theme_group', 'unknown'),
                'estimated_clicks': self._estimate_keyword_clicks(kw),
                'estimated_cost': self._estimate_keyword_cost(kw),
                'estimated_conversions': self._estimate_keyword_conversions(kw),
                'estimated_roas': self._estimate_keyword_roas(kw),
                'priority_score': self._calculate_priority_score(kw),
                'recommended_bid': self._calculate_recommended_bid(kw)
            })
        
        # Create keyword summary statistics
        keyword_summary = {
            'total_keywords': len(keyword_data),
            'high_volume_keywords': len([k for k in keyword_data if k['search_volume_category'] == 'high']),
            'medium_volume_keywords': len([k for k in keyword_data if k['search_volume_category'] == 'medium']),
            'low_volume_keywords': len([k for k in keyword_data if k['search_volume_category'] == 'low']),
            'high_difficulty_keywords': len([k for k in keyword_data if k['difficulty_category'] == 'high']),
            'medium_difficulty_keywords': len([k for k in keyword_data if k['difficulty_category'] == 'medium']),
            'low_difficulty_keywords': len([k for k in keyword_data if k['difficulty_category'] == 'low']),
            'total_estimated_clicks': sum(k['estimated_clicks'] for k in keyword_data),
            'total_estimated_cost': sum(k['estimated_cost'] for k in keyword_data),
            'total_estimated_conversions': sum(k['estimated_conversions'] for k in keyword_data),
            'average_cpc': np.mean([k['cpc'] for k in keyword_data if k['cpc'] > 0]),
            'average_competition': np.mean([k['competition'] for k in keyword_data]),
            'average_commercial_intent': np.mean([k['commercial_intent'] for k in keyword_data])
        }
        
        return {
            'keyword_data': keyword_data,
            'keyword_summary': keyword_summary,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def _create_campaign_documentation(self, campaign: Dict[str, Any], 
                                     pmax_campaigns: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create comprehensive campaign structure documentation."""
        self.logger.info("Creating campaign structure documentation...")
        
        # Search campaign documentation
        search_campaign_docs = {
            'campaign_overview': {
                'name': campaign.get('name', ''),
                'type': campaign.get('type', ''),
                'status': campaign.get('status', ''),
                'start_date': campaign.get('start_date', ''),
                'end_date': campaign.get('end_date', ''),
                'total_ad_groups': len(campaign.get('ad_groups', [])),
                'total_ads': len(campaign.get('ads', [])),
                'total_keywords': sum(len(ag.get('keywords', [])) for ag in campaign.get('ad_groups', []))
            },
            'ad_groups_detailed': [],
            'budget_allocation': campaign.get('budgets', {}),
            'targeting_settings': campaign.get('targeting', {}),
            'negative_keywords': campaign.get('negative_keywords', []),
            'campaign_metrics': campaign.get('metrics', {})
        }
        
        # Add detailed ad group information
        for ag in campaign.get('ad_groups', []):
            search_campaign_docs['ad_groups_detailed'].append({
                'name': ag.get('name', ''),
                'type': ag.get('type', ''),
                'keyword_count': len(ag.get('keywords', [])),
                'bid_strategy': ag.get('bid_strategy', ''),
                'max_cpc': ag.get('max_cpc', 0.0),
                'target_cpa': ag.get('target_cpa', 0.0),
                'daily_budget': ag.get('daily_budget', 0.0),
                'priority': ag.get('priority', ''),
                'match_types': ag.get('match_types', {}),
                'estimated_metrics': {
                    'estimated_clicks': ag.get('estimated_clicks', 0),
                    'estimated_cost': ag.get('estimated_cost', 0.0),
                    'estimated_conversions': ag.get('estimated_conversions', 0),
                    'estimated_cpa': ag.get('estimated_cpa', 0.0)
                }
            })
        
        # Performance Max documentation
        pmax_docs = {}
        if pmax_campaigns:
            pmax_docs = {
                'themes_overview': {
                    'total_themes': len(pmax_campaigns.get('themes', [])),
                    'high_priority_themes': len([t for t in pmax_campaigns.get('themes', []) if t.get('priority') == 'high']),
                    'total_asset_groups': len(pmax_campaigns.get('asset_groups', [])),
                    'total_shopping_groups': len(pmax_campaigns.get('shopping_groups', []))
                },
                'themes_detailed': pmax_campaigns.get('themes', []),
                'asset_groups_detailed': pmax_campaigns.get('asset_groups', []),
                'shopping_groups_detailed': pmax_campaigns.get('shopping_groups', []),
                'budget_allocation': pmax_campaigns.get('budget_allocation', {}),
                'recommendations': pmax_campaigns.get('recommendations', [])
            }
        
        return {
            'search_campaign': search_campaign_docs,
            'performance_max_campaign': pmax_docs,
            'documentation_timestamp': datetime.now().isoformat()
        }
    
    def _generate_bid_recommendations(self, campaign: Dict[str, Any], 
                                    keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate bid recommendations with detailed justifications."""
        self.logger.info("Generating bid recommendations with justifications...")
        
        bid_recommendations = {
            'overall_strategy': self._generate_overall_bid_strategy(campaign),
            'ad_group_recommendations': [],
            'keyword_recommendations': [],
            'budget_optimization': self._generate_budget_optimization(campaign),
            'competitive_analysis': self._analyze_competitive_bidding(keywords),
            'performance_based_recommendations': self._generate_performance_based_recommendations(campaign)
        }
        
        # Generate ad group bid recommendations
        for ag in campaign.get('ad_groups', []):
            recommendation = self._generate_ad_group_bid_recommendation(ag, keywords)
            bid_recommendations['ad_group_recommendations'].append(recommendation)
        
        # Generate keyword-level bid recommendations
        for keyword in keywords:
            kw_recommendation = self._generate_keyword_bid_recommendation(keyword)
            bid_recommendations['keyword_recommendations'].append(kw_recommendation)
        
        return bid_recommendations
    
    def _generate_performance_projections(self, campaign: Dict[str, Any], 
                                       keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance projections based on budgets."""
        self.logger.info("Generating performance projections...")
        
        # Calculate total budget
        total_daily_budget = campaign.get('metrics', {}).get('total_daily_budget', 0)
        total_monthly_budget = campaign.get('metrics', {}).get('total_monthly_budget', 0)
        
        # Generate projections for different scenarios
        projections = {
            'conservative_scenario': self._project_performance_scenario(
                total_daily_budget, keywords, 'conservative'
            ),
            'moderate_scenario': self._project_performance_scenario(
                total_daily_budget, keywords, 'moderate'
            ),
            'aggressive_scenario': self._project_performance_scenario(
                total_daily_budget, keywords, 'aggressive'
            ),
            'budget_breakdown': self._generate_budget_breakdown(campaign),
            'roi_projections': self._generate_roi_projections(campaign, keywords),
            'conversion_projections': self._generate_conversion_projections(campaign, keywords),
            'cost_projections': self._generate_cost_projections(campaign, keywords)
        }
        
        return projections
    
    def _create_visual_representations(self, campaign: Dict[str, Any], 
                                     keywords: List[Dict[str, Any]], 
                                     pmax_campaigns: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create visual representations of campaign structure and performance."""
        self.logger.info("Creating visual representations...")
        
        visual_reports = {
            'campaign_structure_charts': self._create_campaign_structure_charts(campaign),
            'keyword_analysis_charts': self._create_keyword_analysis_charts(keywords),
            'performance_projections_charts': self._create_performance_projections_charts(campaign, keywords),
            'budget_allocation_charts': self._create_budget_allocation_charts(campaign, pmax_campaigns),
            'competitive_analysis_charts': self._create_competitive_analysis_charts(keywords)
        }
        
        return visual_reports
    
    def _generate_executive_summary(self, keyword_report: Dict[str, Any],
                                  campaign_docs: Dict[str, Any],
                                  bid_recommendations: Dict[str, Any],
                                  performance_projections: Dict[str, Any],
                                  brand_analysis: Optional[Any] = None) -> Dict[str, Any]:
        """Generate executive summary with key insights and recommendations."""
        self.logger.info("Generating executive summary...")
        
        # Calculate key metrics
        total_keywords = keyword_report.get('keyword_summary', {}).get('total_keywords', 0)
        total_estimated_cost = keyword_report.get('keyword_summary', {}).get('total_estimated_cost', 0)
        total_estimated_conversions = keyword_report.get('keyword_summary', {}).get('total_estimated_conversions', 0)
        
        # Generate AI-powered insights if enabled and OpenAI is available
        ai_insights = {}
        if self.client and self.use_ai_insights:
            ai_insights = self._generate_ai_insights(
                keyword_report, campaign_docs, bid_recommendations, performance_projections, brand_analysis
            )
        
        executive_summary = {
            'campaign_overview': {
                'total_keywords': total_keywords,
                'total_ad_groups': campaign_docs.get('search_campaign', {}).get('campaign_overview', {}).get('total_ad_groups', 0),
                'total_ads': campaign_docs.get('search_campaign', {}).get('campaign_overview', {}).get('total_ads', 0),
                'estimated_monthly_cost': total_estimated_cost * 30,
                'estimated_monthly_conversions': total_estimated_conversions * 30,
                'estimated_roas': self._calculate_overall_roas(total_estimated_cost, total_estimated_conversions)
            },
            'key_recommendations': self._generate_key_recommendations(
                keyword_report, campaign_docs, bid_recommendations, performance_projections
            ),
            'risk_assessment': self._assess_campaign_risks(keyword_report, campaign_docs),
            'opportunity_analysis': self._analyze_opportunities(keyword_report, campaign_docs),
            'ai_insights': ai_insights,
            'next_steps': self._generate_next_steps(keyword_report, campaign_docs, performance_projections),
            'summary_timestamp': datetime.now().isoformat()
        }
        
        return executive_summary
    
    def _save_all_reports(self, keyword_report: Dict[str, Any],
                         campaign_docs: Dict[str, Any],
                         bid_recommendations: Dict[str, Any],
                         performance_projections: Dict[str, Any],
                         visual_reports: Dict[str, Any],
                         executive_summary: Dict[str, Any]) -> None:
        """Save all generated reports to files."""
        self.logger.info("Saving all reports to files...")
        
        # Save keyword report
        keyword_df = pd.DataFrame(keyword_report['keyword_data'])
        keyword_df.to_csv(f'{self.output_dir}/comprehensive_keywords.csv', index=False)
        
        # Save keyword summary
        with open(f'{self.output_dir}/keyword_summary.json', 'w') as f:
            json.dump(keyword_report['keyword_summary'], f, indent=2)
        
        # Save campaign documentation
        with open(f'{self.output_dir}/campaign_documentation.json', 'w') as f:
            json.dump(campaign_docs, f, indent=2)
        
        # Save bid recommendations
        with open(f'{self.output_dir}/bid_recommendations.json', 'w') as f:
            json.dump(bid_recommendations, f, indent=2)
        
        # Save performance projections
        with open(f'{self.output_dir}/performance_projections.json', 'w') as f:
            json.dump(performance_projections, f, indent=2)
        
        # Save executive summary
        with open(f'{self.output_dir}/executive_summary.json', 'w') as f:
            json.dump(executive_summary, f, indent=2)
        
        # Generate comprehensive report
        self._generate_comprehensive_report_file(
            keyword_report, campaign_docs, bid_recommendations,
            performance_projections, executive_summary
        )
        
        self.logger.info(f"All reports saved to {self.output_dir}/")
    
    # Helper methods for calculations and estimations
    def _estimate_keyword_clicks(self, keyword: Dict[str, Any]) -> int:
        """Estimate clicks for a keyword based on search volume and CTR."""
        search_volume = keyword.get('search_volume', 0)
        ctr = self.performance_assumptions['avg_ctr']
        return int(search_volume * ctr)
    
    def _estimate_keyword_cost(self, keyword: Dict[str, Any]) -> float:
        """Estimate cost for a keyword based on estimated clicks and CPC."""
        estimated_clicks = self._estimate_keyword_clicks(keyword)
        cpc = keyword.get('cpc', 0.0)
        return estimated_clicks * cpc
    
    def _estimate_keyword_conversions(self, keyword: Dict[str, Any]) -> float:
        """Estimate conversions for a keyword based on estimated clicks and conversion rate."""
        estimated_clicks = self._estimate_keyword_clicks(keyword)
        conversion_rate = self.performance_assumptions['avg_conversion_rate']
        return estimated_clicks * conversion_rate
    
    def _estimate_keyword_roas(self, keyword: Dict[str, Any]) -> float:
        """Estimate ROAS for a keyword."""
        estimated_cost = self._estimate_keyword_cost(keyword)
        estimated_conversions = self._estimate_keyword_conversions(keyword)
        avg_order_value = self.performance_assumptions['avg_order_value']
        
        if estimated_cost > 0:
            return (estimated_conversions * avg_order_value) / estimated_cost
        return 0.0
    
    def _calculate_priority_score(self, keyword: Dict[str, Any]) -> float:
        """Calculate priority score for keyword ranking."""
        search_volume = keyword.get('search_volume', 0)
        commercial_intent = keyword.get('commercial_intent', 0.0)
        relevance_score = keyword.get('relevance_score', 0.0)
        competition = keyword.get('competition', 0.0)
        
        # Normalize values
        search_volume_norm = min(search_volume / 10000, 1.0)  # Cap at 10k
        competition_norm = 1 - competition  # Lower competition is better
        
        # Calculate weighted score
        priority_score = (
            search_volume_norm * 0.3 +
            commercial_intent * 0.25 +
            relevance_score * 0.25 +
            competition_norm * 0.2
        )
        
        return round(priority_score, 3)
    
    def _calculate_recommended_bid(self, keyword: Dict[str, Any]) -> float:
        """Calculate recommended bid for a keyword."""
        base_cpc = keyword.get('cpc', 0.0)
        competition = keyword.get('competition', 0.0)
        commercial_intent = keyword.get('commercial_intent', 0.0)
        
        # Adjust bid based on factors
        competition_multiplier = 1 + (competition * 0.2)  # Higher competition = higher bid
        intent_multiplier = 1 + (commercial_intent * 0.3)  # Higher intent = higher bid
        
        recommended_bid = base_cpc * competition_multiplier * intent_multiplier
        
        return round(recommended_bid, 2)
    
    def _calculate_overall_roas(self, total_cost: float, total_conversions: float) -> float:
        """Calculate overall ROAS."""
        if total_cost > 0:
            return (total_conversions * self.performance_assumptions['avg_order_value']) / total_cost
        return 0.0
    
    # Bid recommendation methods
    def _generate_overall_bid_strategy(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall bid strategy recommendations."""
        return {
            'strategy_type': 'hybrid_approach',
            'recommendations': [
                'Use Target CPA for high-converting ad groups',
                'Use Manual CPC for brand and competitor keywords',
                'Use Enhanced CPC for broad match keywords',
                'Implement bid adjustments for mobile and location targeting'
            ],
            'justification': 'Hybrid approach balances automation with control for optimal performance',
            'expected_impact': '15-25% improvement in ROAS with proper optimization'
        }
    
    def _generate_ad_group_bid_recommendation(self, ad_group: Dict[str, Any], keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate bid recommendation for specific ad group."""
        group_type = ad_group.get('type', '')
        current_bid = ad_group.get('max_cpc', 0.0)
        
        # Calculate recommended bid based on group type
        if group_type == 'brand':
            recommended_bid = current_bid * 1.2  # Higher bids for brand terms
            justification = 'Brand keywords have high conversion rates and should be prioritized'
        elif group_type == 'competitor':
            recommended_bid = current_bid * 1.1  # Moderate increase for competitor terms
            justification = 'Competitor keywords can capture market share but require careful monitoring'
        elif group_type == 'long_tail':
            recommended_bid = current_bid * 0.9  # Lower bids for long-tail terms
            justification = 'Long-tail keywords typically have lower competition and can be bid more conservatively'
        else:
            recommended_bid = current_bid
            justification = 'Standard bidding approach for this ad group type'
        
        return {
            'ad_group_name': ad_group.get('name', ''),
            'group_type': group_type,
            'current_bid': current_bid,
            'recommended_bid': round(recommended_bid, 2),
            'bid_change_percentage': round(((recommended_bid - current_bid) / current_bid * 100) if current_bid > 0 else 0, 1),
            'justification': justification,
            'expected_impact': 'Improved performance and cost efficiency'
        }
    
    def _generate_keyword_bid_recommendation(self, keyword: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bid recommendation for specific keyword."""
        current_cpc = keyword.get('cpc', 0.0)
        search_volume = keyword.get('search_volume', 0)
        competition = keyword.get('competition', 0.0)
        commercial_intent = keyword.get('commercial_intent', 0.0)
        
        # Calculate recommended bid
        recommended_bid = self._calculate_recommended_bid(keyword)
        
        # Generate justification
        justification_parts = []
        if search_volume > 5000:
            justification_parts.append('High search volume indicates strong demand')
        if commercial_intent > 0.7:
            justification_parts.append('High commercial intent suggests good conversion potential')
        if competition < 0.5:
            justification_parts.append('Low competition allows for more aggressive bidding')
        
        justification = '; '.join(justification_parts) if justification_parts else 'Standard bidding approach'
        
        return {
            'keyword': keyword.get('keyword', ''),
            'current_cpc': current_cpc,
            'recommended_bid': recommended_bid,
            'bid_change_percentage': round(((recommended_bid - current_cpc) / current_cpc * 100) if current_cpc > 0 else 0, 1),
            'justification': justification,
            'priority_score': keyword.get('priority_score', 0.0)
        }
    
    def _generate_budget_optimization(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate budget optimization recommendations."""
        total_budget = campaign.get('metrics', {}).get('total_daily_budget', 0)
        
        return {
            'current_budget': total_budget,
            'recommendations': [
                'Allocate 40% to brand and high-converting keywords',
                'Allocate 30% to competitor and category keywords',
                'Allocate 20% to long-tail and informational keywords',
                'Reserve 10% for testing and optimization'
            ],
            'expected_roi_improvement': '20-30% with proper budget allocation',
            'optimization_timeline': '2-4 weeks for full optimization'
        }
    
    def _analyze_competitive_bidding(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze competitive bidding landscape."""
        high_competition_keywords = [k for k in keywords if k.get('competition', 0) > 0.7]
        medium_competition_keywords = [k for k in keywords if 0.3 <= k.get('competition', 0) <= 0.7]
        low_competition_keywords = [k for k in keywords if k.get('competition', 0) < 0.3]
        
        return {
            'high_competition_count': len(high_competition_keywords),
            'medium_competition_count': len(medium_competition_keywords),
            'low_competition_count': len(low_competition_keywords),
            'recommendations': [
                'Focus on low-competition keywords for cost efficiency',
                'Use aggressive bidding for high-value, high-competition keywords',
                'Monitor competitor bidding patterns regularly',
                'Consider long-tail alternatives for expensive keywords'
            ]
        }
    
    def _generate_performance_based_recommendations(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance-based bid recommendations."""
        return {
            'top_performers': 'Increase bids by 10-15% for keywords with ROAS > 400%',
            'underperformers': 'Decrease bids by 20-30% for keywords with ROAS < 200%',
            'testing_recommendations': 'Test new keywords with 10% of budget',
            'optimization_schedule': 'Weekly bid adjustments based on performance data'
        }
    
    # Performance projection methods
    def _project_performance_scenario(self, daily_budget: float, keywords: List[Dict[str, Any]], scenario: str) -> Dict[str, Any]:
        """Project performance for different scenarios."""
        if scenario == 'conservative':
            ctr_multiplier = 0.8
            conversion_multiplier = 0.8
            cpc_multiplier = 1.2
        elif scenario == 'moderate':
            ctr_multiplier = 1.0
            conversion_multiplier = 1.0
            cpc_multiplier = 1.0
        else:  # aggressive
            ctr_multiplier = 1.2
            conversion_multiplier = 1.2
            cpc_multiplier = 0.8
        
        # Calculate projections
        total_search_volume = sum(k.get('search_volume', 0) for k in keywords)
        estimated_clicks = int(total_search_volume * self.performance_assumptions['avg_ctr'] * ctr_multiplier)
        estimated_cost = estimated_clicks * np.mean([k.get('cpc', 0) for k in keywords if k.get('cpc', 0) > 0]) * cpc_multiplier
        estimated_conversions = estimated_clicks * self.performance_assumptions['avg_conversion_rate'] * conversion_multiplier
        estimated_revenue = estimated_conversions * self.performance_assumptions['avg_order_value']
        estimated_roas = estimated_revenue / estimated_cost if estimated_cost > 0 else 0
        
        return {
            'scenario': scenario,
            'daily_budget': daily_budget,
            'estimated_clicks': estimated_clicks,
            'estimated_cost': round(estimated_cost, 2),
            'estimated_conversions': round(estimated_conversions, 2),
            'estimated_revenue': round(estimated_revenue, 2),
            'estimated_roas': round(estimated_roas, 2),
            'estimated_cpa': round(estimated_cost / estimated_conversions, 2) if estimated_conversions > 0 else 0
        }
    
    def _generate_budget_breakdown(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed budget breakdown."""
        total_budget = campaign.get('metrics', {}).get('total_daily_budget', 0)
        
        return {
            'total_daily_budget': total_budget,
            'total_monthly_budget': total_budget * 30,
            'budget_allocation': {
                'brand_keywords': total_budget * 0.25,
                'category_keywords': total_budget * 0.25,
                'competitor_keywords': total_budget * 0.20,
                'long_tail_keywords': total_budget * 0.20,
                'testing_budget': total_budget * 0.10
            },
            'recommendations': [
                'Monitor brand keyword performance closely',
                'Adjust competitor keyword bids based on market conditions',
                'Scale successful long-tail keywords',
                'Reallocate budget from underperforming keywords'
            ]
        }
    
    def _generate_roi_projections(self, campaign: Dict[str, Any], keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ROI projections."""
        total_cost = sum(k.get('estimated_cost', 0) for k in keywords)
        total_conversions = sum(k.get('estimated_conversions', 0) for k in keywords)
        total_revenue = total_conversions * self.performance_assumptions['avg_order_value']
        
        return {
            'projected_roi': round((total_revenue - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
            'projected_roas': round(total_revenue / total_cost, 2) if total_cost > 0 else 0,
            'projected_cpa': round(total_cost / total_conversions, 2) if total_conversions > 0 else 0,
            'monthly_projections': {
                'revenue': total_revenue * 30,
                'cost': total_cost * 30,
                'profit': (total_revenue - total_cost) * 30,
                'conversions': total_conversions * 30
            }
        }
    
    def _generate_conversion_projections(self, campaign: Dict[str, Any], keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate conversion projections."""
        total_conversions = sum(k.get('estimated_conversions', 0) for k in keywords)
        
        return {
            'daily_conversions': total_conversions,
            'monthly_conversions': total_conversions * 30,
            'conversion_rate': self.performance_assumptions['avg_conversion_rate'],
            'conversion_by_intent': {
                'transactional': total_conversions * 0.4,
                'commercial': total_conversions * 0.35,
                'informational': total_conversions * 0.15,
                'navigational': total_conversions * 0.10
            }
        }
    
    def _generate_cost_projections(self, campaign: Dict[str, Any], keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cost projections."""
        total_cost = sum(k.get('estimated_cost', 0) for k in keywords)
        
        return {
            'daily_cost': total_cost,
            'monthly_cost': total_cost * 30,
            'cost_by_ad_group': self._calculate_cost_by_ad_group(campaign),
            'cost_efficiency_metrics': {
                'avg_cpc': np.mean([k.get('cpc', 0) for k in keywords if k.get('cpc', 0) > 0]),
                'cost_per_conversion': total_cost / sum(k.get('estimated_conversions', 0) for k in keywords) if sum(k.get('estimated_conversions', 0) for k in keywords) > 0 else 0
            }
        }
    
    def _calculate_cost_by_ad_group(self, campaign: Dict[str, Any]) -> Dict[str, float]:
        """Calculate cost breakdown by ad group."""
        cost_by_group = {}
        for ag in campaign.get('ad_groups', []):
            group_name = ag.get('name', '')
            estimated_cost = ag.get('estimated_cost', 0)
            cost_by_group[group_name] = estimated_cost
        return cost_by_group
    
    # Visual representation methods
    def _create_campaign_structure_charts(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Create campaign structure visualization data."""
        ad_groups = campaign.get('ad_groups', [])
        
        # Prepare data for charts
        group_types = [ag.get('type', 'unknown') for ag in ad_groups]
        group_counts = {}
        for group_type in group_types:
            group_counts[group_type] = group_counts.get(group_type, 0) + 1
        
        keyword_counts = [len(ag.get('keywords', [])) for ag in ad_groups]
        budgets = [ag.get('daily_budget', 0) for ag in ad_groups]
        
        return {
            'ad_group_types': list(group_counts.keys()),
            'ad_group_counts': list(group_counts.values()),
            'keyword_distribution': keyword_counts,
            'budget_distribution': budgets,
            'chart_data_ready': True
        }
    
    def _create_keyword_analysis_charts(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create keyword analysis visualization data."""
        # Prepare data for various charts
        search_volumes = [k.get('search_volume', 0) for k in keywords]
        competitions = [k.get('competition', 0) for k in keywords]
        cpcs = [k.get('cpc', 0) for k in keywords]
        commercial_intents = [k.get('commercial_intent', 0) for k in keywords]
        
        # Categorize keywords
        volume_categories = [k.get('search_volume_category', 'unknown') for k in keywords]
        difficulty_categories = [k.get('difficulty_category', 'unknown') for k in keywords]
        
        return {
            'search_volumes': search_volumes,
            'competitions': competitions,
            'cpcs': cpcs,
            'commercial_intents': commercial_intents,
            'volume_categories': volume_categories,
            'difficulty_categories': difficulty_categories,
            'chart_data_ready': True
        }
    
    def _create_performance_projections_charts(self, campaign: Dict[str, Any], keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create performance projections visualization data."""
        # Generate projection data for different scenarios
        scenarios = ['conservative', 'moderate', 'aggressive']
        projection_data = {}
        
        for scenario in scenarios:
            projection = self._project_performance_scenario(
                campaign.get('metrics', {}).get('total_daily_budget', 0),
                keywords, scenario
            )
            projection_data[scenario] = projection
        
        return {
            'scenarios': scenarios,
            'projection_data': projection_data,
            'chart_data_ready': True
        }
    
    def _create_budget_allocation_charts(self, campaign: Dict[str, Any], pmax_campaigns: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create budget allocation visualization data."""
        # Search campaign budget allocation
        search_budget = campaign.get('metrics', {}).get('total_daily_budget', 0)
        
        # PMax budget allocation
        pmax_budget = 0
        if pmax_campaigns:
            pmax_budget = pmax_campaigns.get('budget_allocation', {}).get('pmax_daily_budget', 0)
        
        return {
            'search_campaign_budget': search_budget,
            'pmax_campaign_budget': pmax_budget,
            'total_budget': search_budget + pmax_budget,
            'chart_data_ready': True
        }
    
    def _create_competitive_analysis_charts(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create competitive analysis visualization data."""
        # Analyze competition levels
        high_comp = len([k for k in keywords if k.get('competition', 0) > 0.7])
        medium_comp = len([k for k in keywords if 0.3 <= k.get('competition', 0) <= 0.7])
        low_comp = len([k for k in keywords if k.get('competition', 0) < 0.3])
        
        return {
            'competition_levels': ['High', 'Medium', 'Low'],
            'competition_counts': [high_comp, medium_comp, low_comp],
            'avg_competition': np.mean([k.get('competition', 0) for k in keywords]),
            'chart_data_ready': True
        }
    
    # Executive summary methods
    def _generate_key_recommendations(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any], 
                                    bid_recommendations: Dict[str, Any], performance_projections: Dict[str, Any]) -> List[str]:
        """Generate key recommendations for the executive summary."""
        recommendations = []
        
        # Keyword recommendations
        total_keywords = keyword_report.get('keyword_summary', {}).get('total_keywords', 0)
        if total_keywords > 0:
            recommendations.append(f"Focus on {total_keywords} high-quality keywords for optimal performance")
        
        # Budget recommendations
        moderate_projection = performance_projections.get('moderate_scenario', {})
        if moderate_projection.get('estimated_roas', 0) < 4.0:
            recommendations.append("Optimize keyword mix to improve ROAS to target 400%")
        
        # Bid strategy recommendations
        recommendations.append("Implement hybrid bidding strategy for optimal performance")
        recommendations.append("Monitor competitor keywords closely and adjust bids accordingly")
        
        return recommendations
    
    def _assess_campaign_risks(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential risks in the campaign."""
        risks = []
        risk_level = 'low'
        
        # Check for high competition keywords
        high_comp_keywords = [k for k in keyword_report.get('keyword_data', []) if k.get('competition', 0) > 0.8]
        if len(high_comp_keywords) > 10:
            risks.append(f"High competition on {len(high_comp_keywords)} keywords may increase costs")
            risk_level = 'medium'
        
        # Check for low volume keywords
        low_vol_keywords = [k for k in keyword_report.get('keyword_data', []) if k.get('search_volume', 0) < 100]
        if len(low_vol_keywords) > 20:
            risks.append(f"Low search volume on {len(low_vol_keywords)} keywords may limit reach")
        
        return {
            'risk_level': risk_level,
            'identified_risks': risks,
            'mitigation_strategies': [
                'Monitor high-competition keywords closely',
                'Consider alternative long-tail keywords',
                'Implement strict budget controls',
                'Regular performance reviews'
            ]
        }
    
    def _analyze_opportunities(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze opportunities for campaign improvement."""
        opportunities = []
        
        # Analyze keyword opportunities
        keyword_data = keyword_report.get('keyword_data', [])
        high_roas_keywords = [k for k in keyword_data if k.get('estimated_roas', 0) > 5.0]
        if high_roas_keywords:
            opportunities.append(f"Scale {len(high_roas_keywords)} high-ROAS keywords")
        
        low_competition_keywords = [k for k in keyword_data if k.get('competition', 0) < 0.3]
        if low_competition_keywords:
            opportunities.append(f"Expand {len(low_competition_keywords)} low-competition keywords")
        
        return {
            'identified_opportunities': opportunities,
            'expected_impact': '15-25% improvement in overall performance',
            'implementation_timeline': '2-4 weeks for full implementation'
        }
    
    def _generate_next_steps(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any], 
                           performance_projections: Dict[str, Any]) -> List[str]:
        """Generate next steps for campaign optimization."""
        return [
            "Launch campaign with conservative bidding initially",
            "Monitor performance daily for first 2 weeks",
            "Adjust bids based on conversion data",
            "Scale successful keywords and pause underperformers",
            "Implement A/B testing for ad copy",
            "Review and optimize monthly"
        ]
    
    def _generate_ai_insights(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any],
                            bid_recommendations: Dict[str, Any], performance_projections: Dict[str, Any],
                            brand_analysis: Optional[Any] = None) -> Dict[str, Any]:
        """Generate AI-powered insights using the configured LLM provider (Hugging Face)."""
        if not self.client:
            return {}
        
        try:
            # Prepare context for AI analysis
            context = f"""
            Campaign Overview:
            - Total Keywords: {keyword_report.get('keyword_summary', {}).get('total_keywords', 0)}
            - Estimated Monthly Cost: ${keyword_report.get('keyword_summary', {}).get('total_estimated_cost', 0) * 30}
            - Estimated ROAS: {performance_projections.get('moderate_scenario', {}).get('estimated_roas', 0)}
            
            Key Metrics:
            - High Volume Keywords: {keyword_report.get('keyword_summary', {}).get('high_volume_keywords', 0)}
            - Average CPC: ${keyword_report.get('keyword_summary', {}).get('average_cpc', 0)}
            - Average Competition: {keyword_report.get('keyword_summary', {}).get('average_competition', 0)}
            """
            
            prompt = f"""
            Based on this SEM campaign data, provide 3-5 strategic insights and recommendations:
            
            {context}
            
            Provide insights in this JSON format:
            {{
                "strategic_insights": ["insight1", "insight2", "insight3"],
                "optimization_recommendations": ["rec1", "rec2", "rec3"],
                "risk_mitigation": ["mitigation1", "mitigation2"],
                "opportunity_analysis": ["opportunity1", "opportunity2"]
            }}
            """
            messages = [
                {"role": "system", "content": "You are an expert SEM strategist providing strategic insights."},
                {"role": "user", "content": prompt}
            ]

            # Call HF via LLMClient
            import re
            response_text = self.client.generate_response(messages=messages, max_tokens=500, temperature=0.7) or ""
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {e}")
            return {}
    
    def _generate_comprehensive_report_file(self, keyword_report: Dict[str, Any], campaign_docs: Dict[str, Any],
                                          bid_recommendations: Dict[str, Any], performance_projections: Dict[str, Any],
                                          executive_summary: Dict[str, Any]) -> None:
        """Generate a comprehensive report file."""
        report_content = f"""
# SEM Campaign Comprehensive Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- Total Keywords: {executive_summary.get('campaign_overview', {}).get('total_keywords', 0)}
- Estimated Monthly Cost: ${executive_summary.get('campaign_overview', {}).get('estimated_monthly_cost', 0):,.2f}
- Estimated ROAS: {executive_summary.get('campaign_overview', {}).get('estimated_roas', 0):.2f}

## Key Recommendations
{chr(10).join([f"- {rec}" for rec in executive_summary.get('key_recommendations', [])])}

## Performance Projections
- Conservative Scenario ROAS: {performance_projections.get('conservative_scenario', {}).get('estimated_roas', 0):.2f}
- Moderate Scenario ROAS: {performance_projections.get('moderate_scenario', {}).get('estimated_roas', 0):.2f}
- Aggressive Scenario ROAS: {performance_projections.get('aggressive_scenario', {}).get('estimated_roas', 0):.2f}

## Risk Assessment
- Risk Level: {executive_summary.get('risk_assessment', {}).get('risk_level', 'unknown')}
- Identified Risks: {chr(10).join([f"- {risk}" for risk in executive_summary.get('risk_assessment', {}).get('identified_risks', [])])}

## Next Steps
{chr(10).join([f"- {step}" for step in executive_summary.get('next_steps', [])])}
        """
        
        with open(f'{self.output_dir}/comprehensive_report.txt', 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Comprehensive report saved to {self.output_dir}/comprehensive_report.txt")
