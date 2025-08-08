# Performance Max & Shopping Campaign Builder

## Overview

The Performance Max & Shopping Campaign Builder module creates comprehensive campaign structures for Google Ads Performance Max and Shopping campaigns. It automatically generates themes, asset groups, product groupings, and budget allocations based on keyword analysis and business data.

## Features

### 1. Performance Max Themes

- **Automatic Theme Creation**: Groups keywords into logical themes based on intent and category
- **Priority Assignment**: Assigns high/medium/low priority based on keyword metrics
- **Budget Calculation**: Calculates optimal budget allocation for each theme
- **Target Audience Identification**: Identifies specific target audiences for each theme

### 2. Asset Group Generation

- **Headlines**: Generates 5-15 headlines per asset group
- **Descriptions**: Creates 5 descriptions per asset group
- **Images**: Suggests relevant images for each theme
- **Videos**: Recommends video content for high-priority themes
- **Logos**: Suggests logo variations
- **Call-to-Actions**: Generates theme-specific CTAs
- **URLs**: Creates final and display URLs

### 3. Shopping Campaign Product Groupings

- **Service Groups**: Creates product groups for services
- **Product Groups**: Creates product groups for physical products
- **Bid Modifiers**: Applies device-specific bid modifiers
- **Targeting**: Sets up location and audience targeting

### 4. Budget Allocation

- **Smart Distribution**: Allocates budget between PMax (70%) and Shopping (30%)
- **Theme Prioritization**: Distributes PMax budget based on theme priority
- **Performance Recommendations**: Provides optimization recommendations

## Configuration

### Performance Max Settings

```yaml
performance_max:
  enabled: true
  asset_requirements:
    headlines:
      min: 5
      max: 15
    descriptions:
      min: 5
      max: 5
    images:
      min: 1
      max: 20
    videos:
      min: 0
      max: 5
    logos:
      min: 1
      max: 5
    call_to_actions:
      min: 1
      max: 10
    final_urls:
      min: 1
      max: 20
    display_urls:
      min: 1
      max: 20
  budget_allocation:
    pmax_percentage: 0.7
    shopping_percentage: 0.3
  theme_priorities:
    brand: 3
    transactional: 3
    commercial: 2
    category: 2
    location: 2
    competitor: 1
    long_tail: 1
    informational: 1
```

### Shopping Settings

```yaml
shopping:
  enabled: true
  product_feed_url: ""
  merchant_id: ""
  country: "US"
  language: "en"
  bid_modifiers:
    mobile: 1.1
    tablet: 1.0
    desktop: 1.2
  product_grouping:
    services_budget_percentage: 0.4
    products_budget_percentage: 0.6
```

## Usage

### Basic Usage

```python
from modules.performance_max_builder import PerformanceMaxBuilder

# Initialize the builder
pmax_builder = PerformanceMaxBuilder(config)

# Create Performance Max campaigns
pmax_campaigns = pmax_builder.create_performance_max_campaigns(keywords, brand_data)

# Save campaigns to files
pmax_builder.save_pmax_campaigns(pmax_campaigns)
```

### Integration with Main Workflow

The Performance Max Builder is automatically integrated into the main workflow:

```python
# Step 5: Performance Max & Shopping Campaign Builder
logger.info("Step 5: Performance Max & Shopping Campaign Builder")
pmax_campaigns = pmax_builder.create_performance_max_campaigns(keywords, brand_data)

# Step 5.5: Save Performance Max campaigns
logger.info("Step 5.5: Saving Performance Max campaigns")
pmax_builder.save_pmax_campaigns(pmax_campaigns)
```

## Theme Categories

### 1. Brand Themes

- **Purpose**: Brand awareness and recognition
- **Keywords**: Brand-specific terms
- **Target Audience**: Brand aware, existing customers, high-value prospects
- **Priority**: High (3)

### 2. Transactional Themes

- **Purpose**: Drive immediate conversions
- **Keywords**: Purchase intent terms
- **Target Audience**: Ready to buy, purchase intent, high conversion potential
- **Priority**: High (3)

### 3. Commercial Themes

- **Purpose**: Commercial intent targeting
- **Keywords**: Commercial search terms
- **Target Audience**: Commercial intent, business customers, B2B prospects
- **Priority**: Medium (2)

### 4. Category Themes

- **Purpose**: Product/service category targeting
- **Keywords**: Category-specific terms
- **Target Audience**: Product researchers, comparison shoppers, industry professionals
- **Priority**: Medium (2)

### 5. Location Themes

- **Purpose**: Local service targeting
- **Keywords**: Location-specific terms
- **Target Audience**: Local customers, nearby prospects, location-specific
- **Priority**: Medium (2)

### 6. Competitor Themes

- **Purpose**: Competitive targeting
- **Keywords**: Competitor-specific terms
- **Target Audience**: Competitor customers, switching prospects, price-sensitive
- **Priority**: Low (1)

### 7. Long-tail Themes

- **Purpose**: Specific need targeting
- **Keywords**: Long-tail, specific terms
- **Target Audience**: Specific need customers, detailed researchers, niche audience
- **Priority**: Low (1)

### 8. Informational Themes

- **Purpose**: Educational content targeting
- **Keywords**: Informational search terms
- **Target Audience**: Learning audience, problem solvers, research phase
- **Priority**: Low (1)

## Asset Group Content

### Headlines

Generated headlines follow Google Ads requirements:

- Maximum 30 characters
- Relevant to theme category
- Include brand name and service keywords
- Theme-specific variations

### Descriptions

- Maximum 90 characters
- Professional and compelling
- Include call-to-action
- Theme-specific messaging

### Images

- Suggested image names based on brand and theme
- Professional business images
- Theme-specific content (e.g., local service images for location themes)

### Videos

- Company introduction videos
- Service overview videos
- Theme-specific content (e.g., how-to videos for transactional themes)

### Call-to-Actions

- Standard CTAs: "Get Started", "Learn More", "Contact Us"
- Theme-specific CTAs:
  - Brand: "Learn About Us", "Our Story"
  - Transactional: "Buy Now", "Order Today"
  - Location: "Find Near You", "Local Service"

## Budget Allocation Logic

### PMax vs Shopping Split

- **PMax**: 70% of total daily budget
- **Shopping**: 30% of total daily budget

### Theme Budget Distribution

Budget is distributed based on:

1. **Keyword Count**: More keywords = higher budget
2. **Search Volume**: Higher volume = higher budget
3. **CPC**: Higher CPC = higher budget
4. **Quality Score**: Higher relevance = higher budget
5. **Priority Level**: High priority themes get more budget

### Shopping Budget Distribution

- **Services**: 40% of shopping budget
- **Products**: 60% of shopping budget

## Output Files

### 1. `performance_max_campaigns.json`

Complete campaign structure including:

- All themes with keywords and budgets
- All asset groups with content
- Shopping product groupings
- Budget allocation details
- Summary statistics

### 2. `pmax_themes.csv`

Theme details including:

- Theme name and category
- Keyword count
- Target audience
- Budget allocation
- Priority level

### 3. `pmax_asset_groups.csv`

Asset group details including:

- Asset group name
- Theme category
- Content counts (headlines, descriptions, images, etc.)

### 4. `shopping_product_groups.csv`

Shopping campaign details including:

- Product group name and category
- Product count
- Budget allocation
- Bid modifiers

### 5. `campaign_budget_allocation.csv`

Budget allocation across all campaigns:

- Campaign type (PMax/Shopping)
- Name and daily budget
- Percentage allocation
- Priority level

### 6. `pmax_recommendations.txt`

Optimization recommendations:

- Budget allocation suggestions
- Performance monitoring tips
- Seasonal adjustment recommendations

## Best Practices

### 1. Asset Quality

- Ensure all suggested images and videos are high quality
- Test headlines for relevance and performance
- Optimize descriptions for click-through rates

### 2. Budget Management

- Monitor theme performance weekly
- Adjust budgets based on ROAS
- Focus on high-performing themes

### 3. Content Optimization

- Regularly update asset group content
- Test different headlines and descriptions
- Optimize for seasonal trends

### 4. Performance Monitoring

- Track theme-level performance
- Monitor asset group effectiveness
- Adjust bid modifiers based on device performance

## Troubleshooting

### Common Issues

1. **Low Asset Count**

   - Ensure brand data includes sufficient service/product information
   - Check that keywords are properly categorized
   - Verify minimum keyword requirements are met

2. **Budget Allocation Issues**

   - Review keyword metrics and search volumes
   - Check theme priority assignments
   - Verify configuration settings

3. **Asset Group Generation Failures**
   - Ensure brand data includes business name and website
   - Check that services/products are properly extracted
   - Verify URL generation logic

### Performance Optimization

1. **Theme Performance**

   - Focus budget on high-performing themes
   - Pause or reduce budget for low-performing themes
   - Regularly review and adjust theme priorities

2. **Asset Group Optimization**

   - Test different headline combinations
   - Optimize descriptions for better CTR
   - Update images and videos regularly

3. **Budget Efficiency**
   - Monitor cost per conversion by theme
   - Adjust bid modifiers based on performance
   - Implement seasonal budget adjustments

## Integration with Other Modules

The Performance Max Builder integrates seamlessly with:

- **Web Scraper**: Uses scraped brand and competitor data
- **Content Analyzer**: Leverages business analysis for theme creation
- **Keyword Discovery**: Uses processed keywords for theme grouping
- **Campaign Builder**: Complements search campaign creation

This integration ensures consistent campaign structure and optimal budget allocation across all campaign types.
