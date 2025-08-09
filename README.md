# SEM Campaign Automation Tool

A comprehensive Python-based tool for automating Search Engine Marketing (SEM) campaign creation, including web scraping, keyword discovery, and campaign building.

## Features

- **Web Scraping**: Automatically scrape brand and competitor websites for relevant content
- **Keyword Discovery**: AI-powered keyword generation and analysis using OpenAI
- **Campaign Building**: Automated creation of Google Ads campaigns with ad groups and ads
- **Data Analysis**: Comprehensive keyword analysis with search volume and competition estimates
- **Export Capabilities**: Export campaigns to CSV format for easy import into Google Ads

## Project Structure

```
SEM_tool/
├── main.py                   # Main entry point
├── config.yaml               # Configuration file
├── input/keyword_planner.csv # to input keyword csv file of the brand generate it with google ads Keyword planner (Note :- please keep the csv file name same as  keyword_planner.csv)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables 
├── README.md              # This file
├── sem_automation         # Central log file
├── modules/               # Core modules
│   ├── __init__.py
│   ├── web_scraper.py        # Web scraping functionality
│   ├── keyword_discovery.py  # Keyword discovery and analysis
│   ├── campaign_builder.py   # Campaign building and ad generation
│   ├── content_analyzer.py   # AI-powered content analysis
│   ├── performance_max_builder.py  # Performance Max campaigns
│   └── report_generator.py   # Comprehensive report generation
└── output/               # Generated output files (created at runtime)
```

## Installation

1. **Clone or download the project**

   ```bash
   git clone <repository-url>
   cd SEM_tool
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   # Copy the template and rename to .env
   cp env_template.txt .env

   # Edit .env with your actual API keys
   nano .env
   ```

4. **Configure the tool**
   - Edit `config.yaml` with your brand information, competitors, and campaign settings
   - Update the `.env` file with your API keys

## Configuration

### Environment Variables (.env)

Required API keys and configuration:

```bash
# Google's Gemini API (for AI-powered keyword and ad generation)
GOOGLE_API_KEY=your_gemini_api_key_here
# OpenAI API (for AI-powered keyword and ad generation)
OPENAI_API_KEY=your_openai_api_key_here

# Google Ads API (for campaign creation)(Optional currently not required used for future)
GOOGLE_ADS_CLIENT_ID=your_google_ads_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_google_ads_client_secret_here
GOOGLE_ADS_DEVELOPER_TOKEN=your_google_ads_developer_token_here
GOOGLE_ADS_REFRESH_TOKEN=your_google_ads_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_google_ads_customer_id_here
```

### Configuration File (config.yaml)

Key configuration sections:

- **Brand Information**: Your brand name, website, and description
- **Competitors**: List of competitor websites to analyze
- **Locations**: Target service areas with radius and priority
- **Budgets**: Daily/monthly budgets and bid strategies
- **Keywords**: Keyword discovery settings and filters
- **Ads**: Ad creation settings and character limits

## Usage

### Basic Usage

Run the complete automation workflow:

```bash
python main.py
```

This will:

1. Scrape your brand and competitor websites
2. Discover and analyze keywords
3. Build a complete SEM campaign
4. Generate output files in the `output/` directory

### Output Files

The tool generates several files in the `output/` directory:

#### Search Campaign Files

- `campaign.csv` - Campaign overview and settings
- `ad_groups.csv` - Ad group structure and settings
- `ads.csv` - Generated ad content
- `keywords.csv` - Discovered and analyzed keywords
- `targeting.csv` - Location and audience targeting
- `campaign_summary.csv` - Summary statistics

#### Performance Max & Shopping Files

- `performance_max_campaigns.json` - Complete PMax campaign structure
- `pmax_themes.csv` - Performance Max themes with keywords and budgets
- `pmax_asset_groups.csv` - Asset groups with content counts
- `shopping_product_groups.csv` - Shopping campaign product groupings
- `campaign_budget_allocation.csv` - Budget allocation across all campaigns
- `pmax_recommendations.txt` - Budget and optimization recommendations

#### Comprehensive Report Files

- `comprehensive_keywords.csv` - Complete keyword export with all fields
- `keyword_summary.json` - Keyword analysis summary statistics
- `campaign_documentation.json` - Detailed campaign structure documentation
- `bid_recommendations.json` - Bid recommendations with justifications
- `performance_projections.json` - Performance projections and scenarios
- `executive_summary.json` - Executive summary with key insights
- `comprehensive_report.txt` - Human-readable comprehensive report

### Advanced Usage

You can also use individual modules:

```python
from modules.web_scraper import WebScraper
from modules.keyword_discovery import KeywordDiscovery
from modules.campaign_builder import CampaignBuilder

# Load configuration
import yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Use individual modules
scraper = WebScraper(config)
keyword_discovery = KeywordDiscovery(config)
campaign_builder = CampaignBuilder(config)
```

## Modules Overview

### Web Scraper (`modules/web_scraper.py`)

- Scrapes brand and competitor websites
- Extracts titles, meta descriptions, content, and services
- Uses Selenium for dynamic content
- Identifies potential keywords from page content

### Keyword Discovery (`modules/keyword_discovery.py`)

- Extracts keywords from scraped content
- Generates AI-powered keywords using OpenAI
- Analyzes keywords for search volume, competition, and commercial intent
- Groups keywords into ad groups
- Filters keywords based on configurable criteria

### Campaign Builder (`modules/campaign_builder.py`)

- Creates complete Google Ads campaign structure
- Generates ad groups from keyword groups
- Creates compelling ad content (AI-powered or template-based)
- Sets up targeting and budget configurations
- Exports campaign data to CSV format

### Performance Max Builder (`modules/performance_max_builder.py`)

- Creates Performance Max themes based on keyword categories
- Generates asset groups with headlines, descriptions, images, videos, logos
- Creates Shopping campaign product groupings
- Provides budget allocation recommendations across campaigns
- Generates comprehensive campaign structure for PMax and Shopping

### Report Generator (`modules/report_generator.py`)

- Exports keyword lists with all required fields and metrics
- Creates comprehensive campaign structure documentation
- Generates bid recommendations with detailed justifications
- Provides performance projections based on different scenarios
- Creates visual representations of campaign structure and performance
- Generates executive summary with AI-powered insights
- Produces comprehensive reports in multiple formats

### Report Generator (`modules/llm_client.py`)

- Supports multiple LLM providers including OpenAI, Gemini, and local models.


## Requirements

- Python 3.8+
- Chrome browser (for Selenium web scraping)
- OpenAI API key / Gemini API key
- Google Ads API access (optional, for direct campaign creation)

## Dependencies

- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `selenium` - Web browser automation
- `openai` - AI-powered content generation with openai
- `pandas` - Data manipulation and export
- `python-dotenv` - Environment variable management
- `PyYAML` - Configuration file parsing
- `google-generativeai` - AI-powered content generation with gemini
- `webdriver-manager` - Automatic Chrome driver management
- `matplotlib` - Data visualization for reports(optional)
- `seaborn` - Statistical data visualization(optional)

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**

   - Ensure Chrome browser is installed
   - The tool automatically downloads the appropriate Chrome driver

2. **API Key Errors**

   - Verify all required API keys are set in `.env`
   - Check API key permissions and quotas

3. **Web Scraping Failures**

   - Some websites may block automated scraping
   - Check the logs for specific error messages
   - Consider adjusting scraping delays in the code

4. **Memory Issues**
   - Large websites may require more memory
   - Consider processing competitors one at a time

### Logging

The tool generates detailed logs in `sem_automation.log`. Check this file for debugging information.


