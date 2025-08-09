#!/usr/bin/env python3
"""
SEM Campaign Automation Tool
Main entry point for the SEM campaign automation system.
"""

import os
import sys
import logging
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from modules.web_scraper import WebScraper
from modules.keyword_discovery import KeywordDiscovery
from modules.campaign_builder import CampaignBuilder
from modules.content_analyzer import ContentAnalyzer
from modules.performance_max_builder import PerformanceMaxBuilder
from modules.report_generator import ReportGenerator
from modules.shopping_cpc_calculator import ShoppingCPCCalculator


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sem_automation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Reduce noisy third-party loggers
    logging.getLogger("WDM").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger(__name__)


def load_config(config_path='config.yaml'):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        sys.exit(1)


def validate_environment():
    """Validate environment variables but do not hard-fail for optional ones.
    Allows running without paid APIs for local testing.
    """
    optional_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_DEVELOPER_TOKEN'
    ]
    missing = [v for v in optional_vars if not os.getenv(v)]
    if missing:
        logger.warning(f"Missing optional env vars (OK for local run): {', '.join(missing)}")


def main():
    """Main execution function."""
    global logger
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting SEM Campaign Automation Tool")
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    validate_environment()
    
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded successfully")
    
    try:
        # Initialize modules
        scraper = WebScraper(config)
        keyword_discovery = KeywordDiscovery(config)
        campaign_builder = CampaignBuilder(config)
        content_analyzer = ContentAnalyzer(config)
        pmax_builder = PerformanceMaxBuilder(config)
        report_generator = ReportGenerator(config)
        shopping_cpc_calculator = ShoppingCPCCalculator(config)
        
        logger.info("All modules initialized successfully")
        
        # Execute the automation workflow
        logger.info("Starting automation workflow...")
        
        # Step 1: Web scraping
        logger.info("Step 1: Web scraping")
        brand_data = scraper.scrape_brand_website()
        competitor_data = scraper.scrape_competitor_websites()
        
        # Step 2: AI-powered content analysis
        logger.info("Step 2: AI-powered content analysis")
        brand_analysis = content_analyzer.analyze_website_content(brand_data)
        competitor_analyses = content_analyzer.analyze_multiple_websites(competitor_data)
        
        # Step 3: Enhanced keyword discovery
        logger.info("Step 3: Enhanced keyword discovery")
        keywords = keyword_discovery.discover_keywords(
            brand_data=brand_data,
            competitor_data=competitor_data
        )
        
        # Step 3.5: Save processed keywords
        logger.info("Step 3.5: Saving processed keywords")
        keyword_groups = keyword_discovery._group_keywords(keywords)
        keyword_discovery.save_keywords(keyword_groups)
        
        # Step 4: Campaign building
        logger.info("Step 4: Campaign building")
        campaign = campaign_builder.build_campaign(keywords)
        
        # Step 4.5: Save enhanced campaign
        logger.info("Step 4.5: Saving enhanced campaign")
        campaign_builder.save_campaign(campaign)

        # Step 5: Performance Max & Shopping Campaign Builder
        logger.info("Step 5: Performance Max & Shopping Campaign Builder")
        pmax_campaigns = pmax_builder.create_performance_max_campaigns(keywords, brand_data)

        # Step 5.5: Save Performance Max campaigns
        logger.info("Step 5.5: Saving Performance Max campaigns")
        pmax_builder.save_pmax_campaigns(pmax_campaigns)

        # Step 6: Shopping CPC Calculation
        logger.info("Step 6: Shopping CPC Calculation")
        shopping_cpc_data = shopping_cpc_calculator.calculate_shopping_cpc(keywords)
        
        # Step 6.5: Save Shopping CPC data
        logger.info("Step 6.5: Saving Shopping CPC data")
        shopping_cpc_calculator.save_shopping_cpc(shopping_cpc_data)

        logger.info("Automation workflow completed successfully!")
        
        # Save analysis results
        logger.info("Saving analysis results...")
        content_analyzer.save_analysis_results([brand_analysis] + competitor_analyses)
        
        # Step 7: Comprehensive Report Generation
        logger.info("Step 7: Comprehensive Report Generation")
        comprehensive_report = report_generator.generate_comprehensive_report(
            campaign=campaign,
            keywords=keywords,
            brand_analysis=brand_analysis,
            pmax_campaigns=pmax_campaigns
        )
        
        # Generate summary report
        logger.info("Generating summary report...")
        generate_summary_report(campaign, keywords, brand_analysis, pmax_campaigns, shopping_cpc_data)
        
    except Exception as e:
        logger.error(f"Error during automation workflow: {e}")
        sys.exit(1)


def generate_summary_report(campaign, keywords, brand_analysis=None, pmax_campaigns=None, shopping_cpc_data=None):
    """Generate a summary report of the automation results."""
    logger.info("=== SEM Campaign Automation Summary ===")
    logger.info(f"Total keywords discovered: {len(keywords)}")
    logger.info(f"Campaign name: {campaign.get('name', 'N/A')}")
    logger.info(f"Ad groups created: {len(campaign.get('ad_groups', []))}")
    logger.info(f"Total ads created: {len(campaign.get('ads', []))}")

    if brand_analysis:
        logger.info(f"Business type: {brand_analysis.business_type}")
        logger.info(f"Business category: {brand_analysis.business_category}")
        logger.info(f"Seed keywords generated: {len(brand_analysis.seed_keywords)}")
        logger.info(f"Target audience segments: {len(brand_analysis.target_audience)}")

    if pmax_campaigns:
        summary = pmax_campaigns.get('summary', {})
        logger.info(f"Performance Max themes created: {summary.get('total_themes', 0)}")
        logger.info(f"Asset groups created: {summary.get('total_asset_groups', 0)}")
        logger.info(f"Shopping product groups: {summary.get('total_shopping_groups', 0)}")
        logger.info(f"Total daily budget: ${summary.get('total_daily_budget', 0)}")
        logger.info(f"High priority themes: {summary.get('high_priority_themes', 0)}")

    if shopping_cpc_data:
        logger.info(f"Shopping CPC keywords calculated: {len(shopping_cpc_data)}")
        high_priority_count = sum(1 for item in shopping_cpc_data if item.get('priority') == 'high')
        logger.info(f"High priority shopping keywords: {high_priority_count}")
        avg_shopping_cpc = sum(item.get('adjusted_cpc', 0) for item in shopping_cpc_data) / len(shopping_cpc_data) if shopping_cpc_data else 0
        logger.info(f"Average Shopping CPC: ${avg_shopping_cpc:.2f}")

    logger.info("=======================================")


if __name__ == "__main__":
    main() 