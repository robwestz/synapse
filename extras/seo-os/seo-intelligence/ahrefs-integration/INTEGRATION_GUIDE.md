# Ahrefs Integration Guide

## Existing System Integration

This project integrates with the existing Ahrefs normalization system located at:
`C:\Users\robin\Videos\SerPopS\.agent\workflows\`

### Files We Use

1. **normaliserauppdata.md** - Complete schema for all 10 Ahrefs report types
2. **ahrefs_agent_prompt.md** - Agent behavior for data processing

### Integration Architecture

```
User Upload
    ↓
Our Upload Handler (backend/app/api/upload.py)
    ↓
Existing Normalization System (.agent/workflows/)
    ↓
Normalized Data → PostgreSQL
    ↓
Intelligence Mode Execution
    ↓
AI-Powered Insights
```

### Supported Report Types (All 10)

From the existing normalization system:

1. **SERP Overview** - Identified by: `Parent Topic Volume` + `Type` + `Title`
2. **Organic Keywords** - Identified by: `Previous organic traffic` + `Current organic traffic` + `Branded`
3. **Matching Terms (keywords)** - Identified by: `Parent Keyword` + `Traffic potential` (no `Term group`)
4. **Matching Terms (clusters)** - Identified by: `Term group` + `Parent Keyword`
5. **Clusters by Parent Topic** - Identified by: `Parent Topic` + `Cluster Volume` + `Cluster keywords`
6. **Backlinks** - Identified by: `Referring page URL` + `Anchor` + `Lost status`
7. **Referring Domains** - Identified by: `Dofollow ref. domains` + `Dofollow linked domains`
8. **Organic Competitors** - Identified by: `Competitor's keywords` + `Common keywords` + `Share`
9. **Best by Links** - Identified by: `Top DR` + `Referring domains` + `Page URL`
10. **Internal Most Linked** - Identified by: `Canonical` + `Links to target` + `Page URL`

### Normalization Rules (From Existing System)

#### Column Name Standardization
```python
COLUMN_MAPPING = {
    'KD': 'difficulty',
    'Difficulty': 'difficulty',
    'DR': 'domain_rating',
    'Domain rating': 'domain_rating',
    'UR': 'url_rating',
    'URL rating': 'url_rating',
    'SERP features': 'serp_features',
    'SERP Features': 'serp_features',
    '#': 'row_number'
}
```

#### Data Type Transformations
```python
# Booleans
TRUE/FALSE → true/false
Empty boolean cells → null

# Numerics
Decimal comma (,) → decimal point (.)
Unicode minus (−) → standard minus (-)
Percent (21%) → 0.21 or 21 (depending on context)
Empty numeric cells → null

# Lists (comma-separated to arrays)
SERP features, Intents, Languages, Entities → parsed as arrays

# Dates
Format: YYYY-MM-DD HH:MM:SS
Empty dates → null
```

### Upload Metadata Structure

Every upload gets tagged with:

```json
{
  "source_domain": "example.com",
  "is_primary": true,
  "report_type": "organic_keywords",
  "upload_date": "2024-12-19T10:30:00Z",
  "data_date_range": {
    "from": "2024-06-19",
    "to": "2024-12-14"
  },
  "row_count": 1247,
  "file_hash": "sha256...",
  "validation_status": "valid"
}
```

### How Intelligence Modes Use This Data

Once normalized, data flows to intelligence modes:

#### Example: MODE 1.1 (Cluster Dominance)

```python
# Get normalized data
your_keywords = get_organic_keywords(is_primary=True)
competitor_keywords = get_organic_keywords(is_primary=False)

# Parent topics already normalized
your_clusters = group_by(your_keywords, 'parent_topic')
competitor_clusters = group_by(competitor_keywords, 'parent_topic')

# Calculate coverage (the intelligence)
for topic in all_topics:
    your_coverage = len(your_clusters[topic]) / total_keywords
    competitor_coverage = len(competitor_clusters[topic]) / total_keywords

    if competitor_coverage > 0.8 and your_coverage < 0.2:
        # INSIGHT: Huge opportunity
        opportunities.append({
            'topic': topic,
            'gap': '8x traffic potential',
            'action': 'Create comprehensive content'
        })
```

### Validation Before Mode Execution

Before running intelligence modes, validate:

1. **Report Type Identified** - Must match one of 10 known types
2. **Required Columns Present** - Check against schema
3. **Data Quality** - No corrupt rows, reasonable value ranges
4. **Sufficient Data** - Minimum row counts per report type

### Error Handling

From existing system:

```python
# If report type unknown
→ "Cannot identify report type. Found columns: [list]. Which type is this?"

# If missing critical columns
→ "Missing column 'Keyword' required for Organic Keywords report."

# If no data rows
→ "File contains only header, no data."
```

### Performance Considerations

- **Large Files:** Backlinks reports can have 50K+ rows
- **Strategy:** Stream processing, batch inserts
- **Caching:** Store normalized data, don't re-normalize

### Next Steps for Integration

1. Create Python wrapper around existing normalization logic
2. Build upload API endpoint
3. Store normalized data in PostgreSQL
4. Make available to intelligence modes
5. Track which reports are uploaded per session

---

## Code Integration Example

```python
# backend/app/core/ahrefs_normalizer.py

import sys
from pathlib import Path

# Add existing workflow path
WORKFLOW_PATH = Path('C:/Users/robin/Videos/SerPopS/.agent/workflows')
sys.path.insert(0, str(WORKFLOW_PATH))

class AhrefsNormalizer:
    """
    Wrapper around existing Ahrefs normalization system
    """

    def __init__(self):
        self.report_signatures = self._load_signatures()

    def identify_report_type(self, df):
        """
        Identify which of 10 report types this is
        Based on column signatures from normaliserauppdata.md
        """
        columns = set(df.columns)

        # SERP overview
        if {'Parent Topic Volume', 'Type', 'Title'}.issubset(columns):
            return 'serp_overview'

        # Organic keywords
        if {'Previous organic traffic', 'Current organic traffic', 'Branded'}.issubset(columns):
            return 'organic_keywords'

        # ... check all 10 types

        return 'unknown'

    def normalize(self, df, report_type):
        """
        Apply normalization rules from existing system
        """
        # Standardize column names
        df = self._standardize_columns(df)

        # Transform data types
        df = self._transform_booleans(df)
        df = self._transform_numerics(df)
        df = self._parse_lists(df)
        df = self._parse_dates(df)

        return df

    def validate(self, df, report_type):
        """
        Validate against schema
        """
        required_columns = self._get_required_columns(report_type)
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValidationError(f"Missing columns: {missing}")

        return True
```

---

## Intelligence Mode Requirements

For each mode to work, it needs specific report types:

**MODE 1 (Cluster Dominance):** Organic Keywords
**MODE 2 (SERP Warfare):** SERP Overview
**MODE 3 (Backlink Intelligence):** Backlinks + Referring Domains
**MODE 4 (Traffic Potential):** Organic Keywords + Matching Terms
**MODE 5 (Semantic Warfare):** Matching Terms (clusters)
**MODE 6 (Evolution):** Organic Keywords (with position change data)
**MODE 7 (Synthesis):** ALL 10 report types
**MODE 8 (Predictive):** Combination of multiple reports
**MODE 9 (Fuck Ahrefs):** Metadata + usage patterns

---

This integration ensures:
✅ Zero duplication of normalization logic
✅ Consistent data quality
✅ All 10 report types supported
✅ Fast time-to-intelligence (data already normalized)
