# Search Campaign Builder

## Overview

The Search Campaign Builder is an advanced system that creates comprehensive Google Ads search campaign structures with intelligent ad group organization, bid strategy optimization, and Google Ads compatible output formats.

## Key Features

### 1. Intelligent Ad Group Organization

The system automatically groups keywords into logical ad groups based on their characteristics:

- **Brand Keywords**: Company name, brand terms, official website
- **Category Keywords**: Product/service categories and general terms
- **Competitor Keywords**: Competitor names, comparison terms, alternatives
- **Location Keywords**: Local search terms, "near me" queries
- **Long-tail Keywords**: 4+ word phrases with specific intent
- **Informational Keywords**: "How to", "What is", educational queries
- **Transactional Keywords**: "Buy", "Purchase", "Order" queries
- **Commercial Keywords**: "Best", "Compare", "Review" queries

### 2. Advanced Bid Strategy Optimization

Automatically determines optimal bid strategies based on keyword characteristics:

- **Manual CPC**: Brand keywords, low competition terms
- **Target CPA**: High commercial intent keywords (>0.7)
- **Target ROAS**: High competition keywords (>0.6)
- **Enhanced CPC**: High search volume keywords (>5000)

### 3. Smart CPC Bid Calculation

Calculates optimal max CPC bids considering:

- **Ad Group Type Multipliers**:

  - Brand: 1.5x (higher bids for brand protection)
  - Transactional: 1.3x (higher bids for conversion intent)
  - Commercial: 1.2x (higher bids for commercial intent)
  - Competitor: 1.1x (moderate bids for competitor terms)
  - Location: 1.0x (standard bids for local terms)
  - Long-tail: 0.8x (lower bids for specific terms)
  - Informational: 0.7x (lower bids for research terms)

- **Competition Adjustment**: 1 + (competition × 0.5)
- **Search Volume Adjustment**: 1 + (volume/10000 × 0.3)
- **Base CPC**: From configuration (default: $5.00)

### 4. Target CPA Calculation

Uses 2% conversion rate assumption with ad group type adjustments:

- **Brand**: 0.8x (lower CPA due to higher conversion rates)
- **Transactional**: 0.9x (lower CPA for purchase intent)
- **Commercial**: 1.0x (standard CPA)
- **Competitor**: 1.2x (higher CPA for competitive terms)
- **Location**: 1.0x (standard CPA)
- **Long-tail**: 1.1x (slightly higher CPA)
- **Informational**: 1.5x (higher CPA for research terms)

### 5. Budget Allocation Strategy

Intelligent budget distribution across ad group types:

- **Brand**: 25% (highest priority for brand protection)
- **Transactional**: 20% (high priority for conversions)
- **Commercial**: 15% (medium priority)
- **Category**: 15% (medium priority)
- **Location**: 10% (medium priority)
- **Competitor**: 8% (lower priority)
- **Long-tail**: 5% (lower priority)
- **Informational**: 2% (lowest priority)

### 6. Match Type Assignment

Automatically assigns appropriate match types:

- **Single Words**: Broad match
- **Two Words**: Phrase match (if commercial intent >0.7), otherwise broad
- **Three+ Words**: Exact match (if search volume <1000), otherwise phrase

## Output Files

### 1. Standard Campaign Files

- `campaign.csv`: Campaign structure and settings
- `ad_groups.csv`: Ad group details with bid strategies
- `ads.csv`: Ad content and targeting
- `campaign_keywords.csv`: Keywords with match types and metrics
- `targeting.csv`: Location targeting settings
- `campaign_metrics.csv`: Comprehensive performance metrics

### 2. Google Ads Compatible Files

- `google_ads_campaign.csv`: Direct import format for Google Ads
- `google_ads_editor.csv`: Detailed format for Google Ads Editor
- `google_ads_negative_keywords.csv`: Negative keywords for import

### 3. Analysis Files

- `campaign_summary.csv`: Overall campaign summary
- `ad_group_type_distribution.csv`: Distribution by ad group type
- `bid_strategy_distribution.csv`: Distribution by bid strategy

## Campaign Metrics

The system calculates comprehensive performance estimates:

### Performance Assumptions

- **Click-Through Rate**: 1% (industry average)
- **Conversion Rate**: 2% (configurable)
- **Target ROAS**: 4.0 (from configuration)

### Calculated Metrics

- **Estimated Clicks**: Search volume × CTR
- **Estimated Cost**: Estimated clicks × Average CPC
- **Estimated Conversions**: Estimated clicks × Conversion rate
- **Estimated CPA**: Estimated cost ÷ Estimated conversions
- **Estimated ROAS**: Revenue ÷ Estimated cost

## Ad Group Naming Conventions

Follows Google Ads best practices:

- **Brand**: `{BrandName}_Brand_Keywords`
- **Category**: `{BrandName}_{Keyword}_Category`
- **Competitor**: `{BrandName}_Competitor_{Keyword}`
- **Location**: `{BrandName}_Location_{Keyword}`
- **Long-tail**: `{BrandName}_LongTail_{Keyword}`
- **Informational**: `{BrandName}_Info_{Keyword}`
- **Transactional**: `{BrandName}_Transactional_{Keyword}`
- **Commercial**: `{BrandName}_Commercial_{Keyword}`

## Configuration

The system uses configuration from `config.yaml`:

```yaml
campaign:
  name: "Brand Campaign"
  type: "search"
  status: "active"
  start_date: "2024-01-01"
  end_date: "2024-12-31"

budgets:
  daily_budget: 100
  monthly_budget: 3000
  max_cpc: 5.00
  target_roas: 4.0

brand:
  name: "Your Brand Name"
  website: "https://yourbrand.com"

locations:
  - name: "New York, NY"
    radius_miles: 25
    priority: "high"
```

## Integration

The Search Campaign Builder is integrated into the main workflow:

1. **Step 4**: Campaign building (includes enhanced structure creation)
2. **Step 4.5**: Save enhanced campaign with all formats
3. **Step 5**: Generate comprehensive reports

## Usage Example

```python
# The campaign builder runs automatically during the main workflow
campaign = campaign_builder.build_campaign(keywords)

# Save campaign with Google Ads compatible formats
campaign_builder.save_campaign(campaign)
```

## Benefits

### 1. Automated Optimization

- Intelligent ad group organization
- Optimal bid strategy selection
- Smart budget allocation
- Appropriate match type assignment

### 2. Google Ads Compatibility

- Direct import formats
- Proper naming conventions
- Correct match type formatting
- Negative keyword management

### 3. Performance Optimization

- Data-driven bid calculations
- Conversion rate assumptions
- ROI optimization
- Budget efficiency

### 4. Scalability

- Handles large keyword sets
- Configurable parameters
- Automated processing
- Comprehensive reporting

## Advanced Features

### 1. Priority-Based Budget Allocation

Ad groups are assigned priority levels (high/medium/low) for budget allocation and optimization focus.

### 2. Difficulty-Based Bidding

Keywords with lower difficulty scores receive adjusted bids to maximize efficiency.

### 3. Intent-Based Optimization

Different bid strategies and budgets based on search intent (informational, commercial, transactional).

### 4. Competition-Aware Bidding

Bid adjustments based on keyword competition levels to optimize cost efficiency.

This comprehensive Search Campaign Builder ensures that campaigns are structured optimally for maximum performance and ROI while providing easy import into Google Ads.
