"""
Shopping CPC Calculator Module
Calculates Shopping CPC bids using the assignment's formula: Target CPC = (Target CPA) × (Conversion Rate)
"""

import logging
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class ShoppingCPCCalculator:
    """Calculator for Shopping CPC bids based on assignment requirements."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Shopping CPC calculator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get configuration values
        self.shopping_budget = config.get('budgets', {}).get('shopping_ads_budget', 15)
        self.conversion_rate = 0.02  # 2% conversion rate as per assignment
        self.target_roas = config.get('budgets', {}).get('target_roas', 4.0)
        
        # Performance assumptions
        self.avg_order_value = 100.0  # Average order value
        self.max_cpa = 50.0  # Maximum cost per acquisition
        
    def calculate_shopping_cpc(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate Shopping CPC bids for keywords using the assignment formula.
        
        Args:
            keywords: List of keyword dictionaries with CPC and competition data
            
        Returns:
            List of dictionaries with Shopping CPC calculations
        """
        self.logger.info("Calculating Shopping CPC bids using assignment formula...")
        
        shopping_cpc_data = []
        
        for keyword in keywords:
            # Extract keyword data
            keyword_text = keyword.get('keyword', '')
            search_volume = keyword.get('search_volume', 0)
            competition = keyword.get('competition', 0.0)
            current_cpc = keyword.get('cpc', 0.0)
            commercial_intent = keyword.get('commercial_intent', 0.0)
            
            # Skip keywords with no CPC data or invalid data
            if not current_cpc or current_cpc == 0 or pd.isna(current_cpc):
                continue
                
            # Convert to float if it's a string
            try:
                current_cpc = float(current_cpc)
                search_volume = int(search_volume)
                competition = float(competition)
                commercial_intent = float(commercial_intent)
            except (ValueError, TypeError):
                continue
                
            # Calculate Target CPA using 2% conversion rate
            target_cpa = self._calculate_target_cpa(current_cpc, competition, commercial_intent)
            
            # Calculate Target CPC using assignment formula: Target CPC = (Target CPA) × (Conversion Rate)
            target_cpc = target_cpa * self.conversion_rate
            
            # Apply bid modifiers based on competition and commercial intent
            adjusted_cpc = self._apply_bid_modifiers(target_cpc, competition, commercial_intent, search_volume)
            
            # Determine priority based on performance indicators
            priority = self._determine_priority(search_volume, competition, commercial_intent, adjusted_cpc)
            
            # Create shopping CPC record
            shopping_record = {
                'keyword': keyword_text,
                'search_volume': search_volume,
                'competition_level': competition,
                'current_cpc': current_cpc,
                'commercial_intent': commercial_intent,
                'target_cpa': round(target_cpa, 2),
                'conversion_rate': self.conversion_rate,
                'target_cpc': round(target_cpc, 2),
                'adjusted_cpc': round(adjusted_cpc, 2),
                'priority': priority,
                'bid_strategy': self._determine_bid_strategy(adjusted_cpc, competition),
                'expected_roas': self._calculate_expected_roas(adjusted_cpc, target_cpa),
                'budget_allocation': self._calculate_budget_allocation(adjusted_cpc, search_volume),
                'recommendation': self._generate_recommendation(priority, adjusted_cpc, competition)
            }
            
            shopping_cpc_data.append(shopping_record)
        
        # Sort by priority and expected ROAS
        shopping_cpc_data.sort(key=lambda x: (x['priority'], x['expected_roas']), reverse=True)
        
        self.logger.info(f"Calculated Shopping CPC for {len(shopping_cpc_data)} keywords")
        return shopping_cpc_data
    
    def _calculate_target_cpa(self, current_cpc: float, competition: float, commercial_intent: float) -> float:
        """Calculate Target CPA based on current CPC, competition, and commercial intent."""
        # Base Target CPA calculation
        base_target_cpa = current_cpc / self.conversion_rate
        
        # Adjust based on competition (higher competition = higher CPA)
        competition_adjustment = 1 + (competition * 0.3)
        
        # Adjust based on commercial intent (higher intent = lower CPA due to better conversion)
        intent_adjustment = 1 - (commercial_intent * 0.2)
        
        # Calculate final Target CPA
        target_cpa = base_target_cpa * competition_adjustment * intent_adjustment
        
        # Cap at maximum CPA
        return min(target_cpa, self.max_cpa)
    
    def _apply_bid_modifiers(self, target_cpc: float, competition: float, commercial_intent: float, search_volume: int) -> float:
        """Apply bid modifiers based on keyword characteristics."""
        # Base modifier
        modifier = 1.0
        
        # Competition modifier (higher competition = higher bids)
        if competition > 0.7:
            modifier *= 1.2  # High competition
        elif competition > 0.4:
            modifier *= 1.1  # Medium competition
        else:
            modifier *= 0.9  # Low competition
        
        # Commercial intent modifier (higher intent = higher bids)
        if commercial_intent > 0.7:
            modifier *= 1.15  # High commercial intent
        elif commercial_intent > 0.4:
            modifier *= 1.05  # Medium commercial intent
        
        # Search volume modifier (higher volume = higher bids)
        if search_volume > 5000:
            modifier *= 1.1  # High volume
        elif search_volume > 1000:
            modifier *= 1.05  # Medium volume
        
        return target_cpc * modifier
    
    def _determine_priority(self, search_volume: int, competition: float, commercial_intent: float, adjusted_cpc: float) -> str:
        """Determine priority level for the keyword."""
        # Calculate priority score
        priority_score = 0
        
        # Search volume score (0-3 points)
        if search_volume > 5000:
            priority_score += 3
        elif search_volume > 1000:
            priority_score += 2
        elif search_volume > 500:
            priority_score += 1
        
        # Commercial intent score (0-2 points)
        if commercial_intent > 0.7:
            priority_score += 2
        elif commercial_intent > 0.4:
            priority_score += 1
        
        # Competition score (0-2 points) - lower competition is better
        if competition < 0.3:
            priority_score += 2
        elif competition < 0.6:
            priority_score += 1
        
        # CPC efficiency score (0-2 points) - lower CPC relative to value
        if adjusted_cpc < 10:
            priority_score += 2
        elif adjusted_cpc < 25:
            priority_score += 1
        
        # Determine priority level
        if priority_score >= 7:
            return "high"
        elif priority_score >= 4:
            return "medium"
        else:
            return "low"
    
    def _determine_bid_strategy(self, adjusted_cpc: float, competition: float) -> str:
        """Determine bid strategy for the keyword."""
        if competition > 0.7:
            return "aggressive"  # High competition requires aggressive bidding
        elif adjusted_cpc > 20:
            return "conservative"  # High CPC requires conservative approach
        else:
            return "balanced"  # Standard bidding approach
    
    def _calculate_expected_roas(self, adjusted_cpc: float, target_cpa: float) -> float:
        """Calculate expected ROAS based on adjusted CPC and target CPA."""
        if adjusted_cpc > 0:
            # Expected ROAS = (Average Order Value) / (Cost per Conversion)
            # Cost per conversion = Adjusted CPC / Conversion Rate
            cost_per_conversion = adjusted_cpc / self.conversion_rate
            expected_roas = self.avg_order_value / cost_per_conversion
            return round(expected_roas, 2)
        return 0.0
    
    def _calculate_budget_allocation(self, adjusted_cpc: float, search_volume: int) -> float:
        """Calculate recommended budget allocation for this keyword."""
        # Base allocation based on search volume and CPC
        base_allocation = (search_volume * adjusted_cpc * self.conversion_rate) / 1000
        
        # Cap allocation based on total shopping budget
        max_allocation = self.shopping_budget * 0.1  # Max 10% of total budget per keyword
        
        return min(base_allocation, max_allocation)
    
    def _generate_recommendation(self, priority: str, adjusted_cpc: float, competition: float) -> str:
        """Generate recommendation for the keyword."""
        if priority == "high":
            if competition > 0.7:
                return "High priority - aggressive bidding recommended due to high competition"
            else:
                return "High priority - standard bidding recommended"
        elif priority == "medium":
            if adjusted_cpc > 15:
                return "Medium priority - conservative bidding recommended due to high CPC"
            else:
                return "Medium priority - balanced bidding recommended"
        else:
            return "Low priority - monitor performance before increasing bids"
    
    def save_shopping_cpc(self, shopping_cpc_data: List[Dict[str, Any]], output_dir: str = 'output') -> None:
        """Save Shopping CPC data to CSV file."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame(shopping_cpc_data)
        
        # Save to CSV
        output_file = f'{output_dir}/shopping_cpc.csv'
        df.to_csv(output_file, index=False)
        
        # Create summary statistics
        summary = self._create_summary_statistics(shopping_cpc_data)
        
        # Save summary to JSON
        import json
        summary_file = f'{output_dir}/shopping_cpc_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Shopping CPC data saved to {output_file}")
        self.logger.info(f"Shopping CPC summary saved to {summary_file}")
    
    def _create_summary_statistics(self, shopping_cpc_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary statistics for Shopping CPC data."""
        if not shopping_cpc_data:
            return {"error": "No shopping CPC data available"}
        
        # Calculate summary statistics
        total_keywords = len(shopping_cpc_data)
        
        # Calculate averages only for valid data
        valid_target_cpcs = [item['target_cpc'] for item in shopping_cpc_data if item['target_cpc'] > 0]
        valid_adjusted_cpcs = [item['adjusted_cpc'] for item in shopping_cpc_data if item['adjusted_cpc'] > 0]
        valid_expected_roas = [item['expected_roas'] for item in shopping_cpc_data if item['expected_roas'] > 0]
        
        avg_target_cpc = sum(valid_target_cpcs) / len(valid_target_cpcs) if valid_target_cpcs else 0
        avg_adjusted_cpc = sum(valid_adjusted_cpcs) / len(valid_adjusted_cpcs) if valid_adjusted_cpcs else 0
        avg_expected_roas = sum(valid_expected_roas) / len(valid_expected_roas) if valid_expected_roas else 0
        
        # Priority distribution
        priority_counts = {}
        for item in shopping_cpc_data:
            priority = item['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Budget allocation summary
        valid_budget_allocations = [item['budget_allocation'] for item in shopping_cpc_data if item['budget_allocation'] > 0]
        total_budget_allocation = sum(valid_budget_allocations) if valid_budget_allocations else 0
        
        summary = {
            'total_keywords': total_keywords,
            'average_target_cpc': round(avg_target_cpc, 2),
            'average_adjusted_cpc': round(avg_adjusted_cpc, 2),
            'average_expected_roas': round(avg_expected_roas, 2),
            'priority_distribution': priority_counts,
            'total_budget_allocation': round(total_budget_allocation, 2),
            'conversion_rate_used': self.conversion_rate,
            'shopping_budget': self.shopping_budget,
            'target_roas': self.target_roas,
            'calculation_timestamp': datetime.now().isoformat()
        }
        
        return summary
