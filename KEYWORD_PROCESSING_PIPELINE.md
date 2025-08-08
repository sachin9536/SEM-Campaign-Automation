# Keyword Processing & Filtering Pipeline

## Overview

The Keyword Processing & Filtering Pipeline is a comprehensive system that processes, filters, and analyzes keywords from multiple sources to create high-quality, targeted keyword lists for SEM campaigns.

## Pipeline Steps

### Step 1: Combine Keywords from All Sources

- **Method**: `_combine_keywords_from_sources()`
- **Purpose**: Aggregates keywords from all discovery sources with source tracking
- **Features**:
  - Tracks source distribution (LLM, WordStream, Google Autocomplete, etc.)
  - Ensures all required fields exist with default values
  - Maintains data integrity across sources

### Step 2: Remove Duplicates and Variations

- **Method**: `_remove_duplicates_and_variations()`
- **Purpose**: Eliminates exact duplicates and similar keyword variations
- **Features**:
  - Exact duplicate detection
  - Plural/singular variation detection
  - Similarity analysis using word overlap (80% threshold)
  - Preserves the best data when duplicates are found

### Step 3: Filter by Search Volume

- **Method**: `_filter_by_search_volume()`
- **Purpose**: Filters keywords by minimum search volume threshold
- **Criteria**: >500 monthly searches
- **Features**:
  - Uses actual search volume data when available
  - Falls back to estimated search volume for keywords without data
  - Configurable minimum threshold

### Step 4: Group by Intent and Theme

- **Method**: `_group_by_intent_and_theme()`
- **Purpose**: Categorizes keywords by search intent and thematic categories
- **Intent Categories**:

  - **Informational**: what, how, why, when, where, guide, tips, learn
  - **Navigational**: brand, company, website, official, homepage
  - **Commercial**: best, top, compare, review, vs, alternative
  - **Transactional**: buy, purchase, order, price, cost, deal, discount, sale
  - **Local**: near me, local, nearby, location, address, city, area

- **Theme Categories** (business-type specific):
  - **General**: products, quality, pricing, location, reviews
  - **E-commerce**: products, categories, shipping, returns
  - **SaaS**: features, pricing, integration, support
  - **Service**: services, booking, pricing, location

### Step 5: Assign Preliminary Match Types

- **Method**: `_assign_preliminary_match_types()`
- **Purpose**: Assigns appropriate match types based on keyword characteristics
- **Logic**:
  - **Word Count**: 1 word = broad, 2 words = phrase, 3+ words = exact
  - **Commercial Intent**: High commercial intent (>0.7) = phrase match
  - **Search Volume**: High volume (>10K) = broad, low volume (<1K) = exact

### Step 6: Calculate Keyword Difficulty Scores

- **Method**: `_calculate_keyword_difficulty_scores()`
- **Purpose**: Calculates comprehensive difficulty scores (0-100)
- **Factors**:

  - **Word Count**: Longer keywords = easier (10-40 points)
  - **Competition**: Higher competition = harder (0-30 points)
  - **Search Volume**: Higher volume = more competition (5-20 points)
  - **Commercial Intent**: Higher intent = more competition (0-15 points)
  - **Brand Keywords**: Easier (-20 points)
  - **Local Keywords**: Easier (-10 points)

- **Difficulty Categories**:
  - **Low**: 0-39 (Easy to rank for)
  - **Medium**: 40-69 (Moderate competition)
  - **High**: 70-100 (High competition)

## Output Files

The pipeline generates comprehensive output files:

### 1. `keywords.csv`

Main keyword file with all processing pipeline data:

- Basic keyword data (keyword, search volume, competition, CPC)
- Processing pipeline fields (search intent, theme, difficulty score)
- Match type and categorization data

### 2. Summary Files

- `keyword_volume_summary.csv`: Analysis by search volume category
- `keyword_intent_summary.csv`: Analysis by search intent
- `keyword_difficulty_summary.csv`: Analysis by difficulty category
- `keyword_theme_summary.csv`: Analysis by keyword theme
- `keyword_match_type_summary.csv`: Analysis by match type
- `keyword_source_summary.csv`: Analysis by data source

### 3. `keyword_processing_summary.csv`

Comprehensive summary including:

- Total keywords and ad groups
- Average metrics (search volume, competition, CPC, difficulty)
- Distribution statistics
- Coverage analysis (intents, themes, sources)

### 4. `processing_pipeline_report.json`

Detailed technical report including:

- Pipeline steps executed
- Filtering criteria used
- Scoring methodologies
- Configuration parameters

## Configuration

The pipeline uses configuration from `config.yaml`:

```yaml
keywords:
  min_search_volume: 500
  max_keywords_per_ad_group: 20
  similarity_threshold: 0.8
  difficulty_categories: [low, medium, high]
```

## Integration

The pipeline is integrated into the main workflow:

1. **Step 3**: Enhanced keyword discovery (includes pipeline)
2. **Step 3.5**: Save processed keywords with all pipeline data
3. **Step 4**: Campaign building using processed keywords

## Benefits

### 1. Quality Assurance

- Eliminates low-quality keywords
- Removes duplicates and variations
- Ensures minimum search volume

### 2. Strategic Categorization

- Intent-based grouping for better ad group structure
- Theme-based organization for targeted campaigns
- Difficulty scoring for budget allocation

### 3. Data-Driven Decisions

- Comprehensive metrics for each keyword
- Multiple analysis perspectives
- Detailed reporting for optimization

### 4. Scalability

- Handles large keyword sets efficiently
- Configurable thresholds and criteria
- Automated processing pipeline

## Usage Example

```python
# The pipeline runs automatically during keyword discovery
keywords = keyword_discovery.discover_keywords(
    brand_data=brand_data,
    competitor_data=competitor_data
)

# Save processed keywords with all pipeline data
keyword_groups = keyword_discovery._group_keywords(keywords)
keyword_discovery.save_keywords(keyword_groups)
```

## Monitoring and Optimization

The pipeline provides extensive logging and monitoring:

- Step-by-step progress logging
- Source distribution tracking
- Filtering statistics
- Processing time metrics
- Error handling and recovery

This comprehensive pipeline ensures that only the highest-quality, most relevant keywords are used for SEM campaigns, maximizing ROI and campaign performance.
