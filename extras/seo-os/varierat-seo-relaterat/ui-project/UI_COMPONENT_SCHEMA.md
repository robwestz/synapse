# UI COMPONENT SCHEMA: SEO Intelligence Dashboard

> Design for utokade paneler i siex-dashboard.
> Baserat pa befintlig struktur i `SIE-X/siex-dashboard/`.

---

## OVERSIKT

### Befintliga paneler (behalles)

| Panel | Funktion | Prioritet |
|-------|----------|-----------|
| Hub Map | Systemoverblick | BEHALLES |
| Flight Deck | Live controls, alerts | BEHALLES |
| Command Deck | Keyword extraction | BEHALLES |
| Connections | Kopplingar | BEHALLES |
| Pipelines | Workflow state | BEHALLES |
| Models | Laddade modeller | BEHALLES |
| Endpoints | API routes | BEHALLES |
| Runs | Senaste korningar | BEHALLES |
| Metrics | API stats | BEHALLES |
| Activity | Event log | BEHALLES |

### Nya paneler (MVP)

| Panel | Funktion | Prioritet |
|-------|----------|-----------|
| **Intent Classification** | BERT-baserad sokavsiktsklassificering | MVP |
| **Keyword Clustering** | Word2Vec + K-means klustring | MVP |
| **SERP Analysis** | SERP-features och ranking | MVP |
| **Content Scoring** | LightGBM kvalitetspoang | FAS 4 |
| **Traffic Prediction** | LSTM trafikprognos | FAS 4 |

---

## PANEL 1: INTENT CLASSIFICATION

### Visuell design

```
+----------------------------------------------------------+
| Intent Classification                    [i] Live analysis |
+----------------------------------------------------------+
| Keywords to classify:                                      |
| +------------------------------------------------------+ |
| | best laptop 2024                                      | |
| | how to fix iphone screen                              | |
| | amazon login                                          | |
| | buy nike shoes online                                 | |
| +------------------------------------------------------+ |
|                                                            |
| [Classify] [Clear] [Load samples]                          |
|                                                            |
| Results:                                                   |
| +------------------+------------------+------------------+ |
| | Keyword          | Intent           | Confidence       | |
| +------------------+------------------+------------------+ |
| | best laptop 2024 | Commercial       | 0.92 [====]      | |
| | how to fix...    | Informational    | 0.87 [===]       | |
| | amazon login     | Navigational     | 0.95 [=====]     | |
| | buy nike shoes   | Transactional    | 0.89 [====]      | |
| +------------------+------------------+------------------+ |
|                                                            |
| Intent Distribution:                                       |
| [======] Commercial 25%                                    |
| [========] Informational 35%                               |
| [===] Navigational 15%                                     |
| [=====] Transactional 25%                                  |
+----------------------------------------------------------+
```

### Data Schema

```typescript
interface IntentClassificationInput {
  keywords: string[];
  options?: {
    include_confidence: boolean;
    batch_size: number;
  };
}

interface IntentClassificationResult {
  keyword: string;
  intent: "commercial" | "informational" | "navigational" | "transactional";
  confidence: number;  // 0-1
  secondary_intent?: string;
  secondary_confidence?: number;
}

interface IntentClassificationResponse {
  success: boolean;
  results: IntentClassificationResult[];
  distribution: {
    commercial: number;
    informational: number;
    navigational: number;
    transactional: number;
  };
  processing_time_ms: number;
}
```

### API Endpoint

```
POST /api/v1/classify-intent
Host: localhost:8003

Request:
{
  "keywords": ["best laptop 2024", "how to fix iphone"],
  "options": {
    "include_confidence": true
  }
}

Response:
{
  "success": true,
  "results": [
    {
      "keyword": "best laptop 2024",
      "intent": "commercial",
      "confidence": 0.92
    }
  ],
  "distribution": {...},
  "processing_time_ms": 245
}
```

### HTML Struktur (foljande siex-dashboard stil)

```html
<details class="panel is-collapsible" data-component="intent-classification" open>
  <summary class="panel-summary">
    <div class="panel-head">
      <h3>Intent Classification</h3>
      <span class="panel-note">BERT-powered</span>
    </div>
  </summary>
  <div class="panel-body">
    <div class="intent-input">
      <label class="field-label">Keywords to classify</label>
      <textarea data-field="intent-keywords" rows="4"
        placeholder="Enter keywords (one per line)"></textarea>
      <div class="command-actions">
        <button class="chip primary" data-action="run-intent">Classify</button>
        <button class="chip ghost" data-action="load-intent-samples">Samples</button>
        <button class="chip ghost" data-action="clear-intent">Clear</button>
      </div>
    </div>
    <div class="intent-results" data-list="intent-results"></div>
    <div class="intent-distribution" data-chart="intent-distribution"></div>
  </div>
</details>
```

---

## PANEL 2: KEYWORD CLUSTERING

### Visuell design

```
+----------------------------------------------------------+
| Keyword Clustering                       [i] Semantic grouping |
+----------------------------------------------------------+
| Keywords to cluster:                                       |
| +------------------------------------------------------+ |
| | (paste 50-500 keywords or load from file)            | |
| +------------------------------------------------------+ |
|                                                            |
| Options:                                                   |
| Clusters: [5-20] [=====10=====]   Algorithm: [K-means v] |
| Min cluster size: [3]   Similarity threshold: [0.7]       |
|                                                            |
| [Cluster] [Export] [Visualize]                             |
|                                                            |
| Clusters (10 found):                                       |
| +----------------------------------------------------------+
| | Cluster 1: "laptop reviews" (15 keywords)     [Expand] |
| |   - best laptop 2024                                   |
| |   - laptop comparison                                  |
| |   - top rated laptops                                  |
| |   + 12 more...                                         |
| +----------------------------------------------------------+
| | Cluster 2: "laptop specs" (8 keywords)        [Expand] |
| |   - laptop ram upgrade                                 |
| |   - ssd vs hdd laptop                                  |
| |   + 6 more...                                          |
| +----------------------------------------------------------+
|                                                            |
| Outliers (4 keywords):                                     |
| [keyword1] [keyword2] [keyword3] [keyword4]                |
+----------------------------------------------------------+
```

### Data Schema

```typescript
interface KeywordClusteringInput {
  keywords: string[];
  options: {
    num_clusters: number;      // 5-50
    min_cluster_size: number;  // 2-10
    algorithm: "kmeans" | "dbscan" | "hierarchical";
    similarity_threshold: number;  // 0-1
  };
}

interface KeywordCluster {
  id: number;
  name: string;              // Auto-generated label
  keywords: string[];
  centroid_keyword: string;  // Most representative
  coherence_score: number;   // 0-1
  size: number;
}

interface KeywordClusteringResponse {
  success: boolean;
  clusters: KeywordCluster[];
  outliers: string[];        // Keywords that didn't fit
  metrics: {
    silhouette_score: number;
    num_clusters: number;
    total_keywords: number;
    clustered_keywords: number;
  };
  processing_time_ms: number;
}
```

### API Endpoint

```
POST /api/v1/cluster-keywords
Host: localhost:8003

Request:
{
  "keywords": ["keyword1", "keyword2", ...],
  "options": {
    "num_clusters": 10,
    "min_cluster_size": 3,
    "algorithm": "kmeans"
  }
}

Response:
{
  "success": true,
  "clusters": [
    {
      "id": 1,
      "name": "laptop reviews",
      "keywords": ["best laptop", "laptop comparison"],
      "centroid_keyword": "best laptop",
      "coherence_score": 0.85,
      "size": 15
    }
  ],
  "outliers": ["random keyword"],
  "metrics": {...}
}
```

### HTML Struktur

```html
<details class="panel is-collapsible" data-component="keyword-clustering" open>
  <summary class="panel-summary">
    <div class="panel-head">
      <h3>Keyword Clustering</h3>
      <span class="panel-note">Word2Vec + K-means</span>
    </div>
  </summary>
  <div class="panel-body">
    <div class="cluster-input">
      <label class="field-label">Keywords to cluster</label>
      <textarea data-field="cluster-keywords" rows="6"
        placeholder="Enter keywords (one per line, 50-500 recommended)"></textarea>
      <div class="cluster-options">
        <div class="field">
          <label>Clusters</label>
          <input type="range" min="5" max="50" value="10" data-field="num-clusters">
          <span data-value="num-clusters">10</span>
        </div>
        <div class="field">
          <label>Algorithm</label>
          <select data-field="algorithm">
            <option value="kmeans" selected>K-means</option>
            <option value="dbscan">DBSCAN</option>
            <option value="hierarchical">Hierarchical</option>
          </select>
        </div>
      </div>
      <div class="command-actions">
        <button class="chip primary" data-action="run-cluster">Cluster</button>
        <button class="chip ghost" data-action="export-clusters">Export</button>
        <button class="chip ghost" data-action="visualize-clusters">Visualize</button>
      </div>
    </div>
    <div class="cluster-results" data-list="cluster-results"></div>
    <div class="cluster-outliers" data-list="cluster-outliers"></div>
  </div>
</details>
```

---

## PANEL 3: SERP ANALYSIS

### Visuell design

```
+----------------------------------------------------------+
| SERP Analysis                            [i] Search insight |
+----------------------------------------------------------+
| Query to analyze:                                          |
| +------------------------------------------------------+ |
| | best laptop for programming                           | |
| +------------------------------------------------------+ |
|                                                            |
| Location: [United States v]  Device: [Desktop v]          |
|                                                            |
| [Analyze SERP] [Track changes] [Compare]                   |
|                                                            |
| SERP Features Detected:                                    |
| +----------------------------------------------------------+
| | [x] Featured Snippet   | [x] People Also Ask            |
| | [x] Knowledge Panel    | [ ] Local Pack                 |
| | [x] Image Pack         | [x] Video Carousel             |
| | [ ] Shopping Results   | [x] Related Searches           |
| +----------------------------------------------------------+
|                                                            |
| Top 10 Results:                                            |
| +----------------------------------------------------------+
| | #1  techradar.com           | DA: 92 | Words: 3,240    |
| |     "Best laptops for coding 2024"                      |
| |----------------------------------------------------------+
| | #2  pcmag.com               | DA: 94 | Words: 2,890    |
| |     "Best Programming Laptops"                          |
| |----------------------------------------------------------+
| | ...                                                      |
| +----------------------------------------------------------+
|                                                            |
| Content Gap Analysis:                                      |
| Missing topics: [RAM requirements] [IDE performance] [...]  |
|                                                            |
| Recommendations:                                            |
| - Target Featured Snippet with direct answer               |
| - Add FAQ section for People Also Ask                      |
| - Include comparison table (competitors have)              |
+----------------------------------------------------------+
```

### Data Schema

```typescript
interface SerpAnalysisInput {
  query: string;
  options?: {
    location: string;       // "us", "uk", "se", etc.
    device: "desktop" | "mobile";
    language: string;
    include_content_analysis: boolean;
  };
}

interface SerpFeatures {
  featured_snippet: boolean;
  knowledge_panel: boolean;
  people_also_ask: boolean;
  local_pack: boolean;
  image_pack: boolean;
  video_carousel: boolean;
  shopping_results: boolean;
  related_searches: boolean;
  news_results: boolean;
}

interface SerpResult {
  position: number;
  url: string;
  domain: string;
  title: string;
  description: string;
  domain_authority?: number;
  word_count?: number;
  schema_types?: string[];
}

interface ContentGap {
  topic: string;
  importance: "high" | "medium" | "low";
  found_in_competitors: number;  // How many top 10 have it
}

interface SerpAnalysisResponse {
  success: boolean;
  query: string;
  features: SerpFeatures;
  results: SerpResult[];
  content_gaps: ContentGap[];
  recommendations: string[];
  metrics: {
    avg_word_count: number;
    avg_domain_authority: number;
    difficulty_score: number;  // 0-100
  };
  processing_time_ms: number;
}
```

### API Endpoint

```
POST /api/v1/analyze-serp
Host: localhost:8003

Request:
{
  "query": "best laptop for programming",
  "options": {
    "location": "us",
    "device": "desktop",
    "include_content_analysis": true
  }
}

Response:
{
  "success": true,
  "query": "best laptop for programming",
  "features": {
    "featured_snippet": true,
    "people_also_ask": true,
    ...
  },
  "results": [...],
  "content_gaps": [...],
  "recommendations": [...],
  "metrics": {...}
}
```

### HTML Struktur

```html
<details class="panel is-collapsible" data-component="serp-analysis" open>
  <summary class="panel-summary">
    <div class="panel-head">
      <h3>SERP Analysis</h3>
      <span class="panel-note">Search insights</span>
    </div>
  </summary>
  <div class="panel-body">
    <div class="serp-input">
      <label class="field-label">Query to analyze</label>
      <input type="text" data-field="serp-query"
        placeholder="Enter search query">
      <div class="serp-options">
        <div class="field">
          <label>Location</label>
          <select data-field="serp-location">
            <option value="us" selected>United States</option>
            <option value="uk">United Kingdom</option>
            <option value="se">Sweden</option>
          </select>
        </div>
        <div class="field">
          <label>Device</label>
          <select data-field="serp-device">
            <option value="desktop" selected>Desktop</option>
            <option value="mobile">Mobile</option>
          </select>
        </div>
      </div>
      <div class="command-actions">
        <button class="chip primary" data-action="run-serp">Analyze</button>
        <button class="chip ghost" data-action="track-serp">Track</button>
        <button class="chip ghost" data-action="compare-serp">Compare</button>
      </div>
    </div>
    <div class="serp-features" data-list="serp-features"></div>
    <div class="serp-results" data-list="serp-results"></div>
    <div class="serp-gaps" data-list="serp-gaps"></div>
    <div class="serp-recommendations" data-list="serp-recommendations"></div>
  </div>
</details>
```

---

## GEMENSAM CSS (tillagg till styles.css)

```css
/* Intent Classification */
.intent-results {
  display: grid;
  gap: 0.5rem;
  margin-top: 1rem;
}

.intent-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  align-items: center;
  padding: 0.5rem;
  background: var(--surface-1);
  border-radius: 6px;
}

.intent-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.intent-badge.commercial { background: var(--green-surface); color: var(--green); }
.intent-badge.informational { background: var(--blue-surface); color: var(--blue); }
.intent-badge.navigational { background: var(--purple-surface); color: var(--purple); }
.intent-badge.transactional { background: var(--orange-surface); color: var(--orange); }

.confidence-bar {
  height: 4px;
  background: var(--surface-2);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-bar-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}

/* Keyword Clustering */
.cluster-card {
  background: var(--surface-1);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

.cluster-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.cluster-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.cluster-keyword {
  padding: 0.125rem 0.5rem;
  background: var(--surface-2);
  border-radius: 4px;
  font-size: 0.75rem;
}

/* SERP Analysis */
.serp-features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin: 1rem 0;
}

.serp-feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--surface-1);
  border-radius: 6px;
}

.serp-feature.active {
  background: var(--green-surface);
  color: var(--green);
}

.serp-result {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.serp-position {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--muted);
}

.serp-gap-tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--orange-surface);
  color: var(--orange);
  border-radius: 4px;
  font-size: 0.75rem;
  margin: 0.125rem;
}
```

---

## JAVASCRIPT TILLAGG (tillagg till app.js)

```javascript
// Intent Classification
async function runIntentClassification() {
  const keywords = getField('intent-keywords').value
    .split('\n')
    .filter(k => k.trim());

  if (!keywords.length) return showError('Enter keywords to classify');

  setStatus('intent', 'classifying');

  try {
    const response = await fetch(`${ML_API_BASE}/classify-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords })
    });

    const data = await response.json();
    renderIntentResults(data);
    setStatus('intent', 'complete');
  } catch (error) {
    showError('Intent classification failed: ' + error.message);
    setStatus('intent', 'error');
  }
}

// Keyword Clustering
async function runKeywordClustering() {
  const keywords = getField('cluster-keywords').value
    .split('\n')
    .filter(k => k.trim());

  const options = {
    num_clusters: parseInt(getField('num-clusters').value),
    algorithm: getField('algorithm').value
  };

  if (keywords.length < 10) return showError('Enter at least 10 keywords');

  setStatus('clustering', 'processing');

  try {
    const response = await fetch(`${ML_API_BASE}/cluster-keywords`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, options })
    });

    const data = await response.json();
    renderClusterResults(data);
    setStatus('clustering', 'complete');
  } catch (error) {
    showError('Clustering failed: ' + error.message);
    setStatus('clustering', 'error');
  }
}

// SERP Analysis
async function runSerpAnalysis() {
  const query = getField('serp-query').value.trim();

  if (!query) return showError('Enter a search query');

  const options = {
    location: getField('serp-location').value,
    device: getField('serp-device').value,
    include_content_analysis: true
  };

  setStatus('serp', 'analyzing');

  try {
    const response = await fetch(`${ML_API_BASE}/analyze-serp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, options })
    });

    const data = await response.json();
    renderSerpResults(data);
    setStatus('serp', 'complete');
  } catch (error) {
    showError('SERP analysis failed: ' + error.message);
    setStatus('serp', 'error');
  }
}

// Register actions
actions['run-intent'] = runIntentClassification;
actions['run-cluster'] = runKeywordClustering;
actions['run-serp'] = runSerpAnalysis;
```

---

## IMPLEMENTATION ORDNING

### Steg 1: Intent Classification (enklast)
1. Lagg till panel i index.html
2. Lagg till CSS i styles.css
3. Lagg till JS i app.js
4. Testa mot ML-service

### Steg 2: Keyword Clustering
1. Lagg till panel
2. Implementera renderClusterResults()
3. Lagg till export-funktion

### Steg 3: SERP Analysis (kravs datakalla forst)
1. Skapa mock-data for utveckling
2. Lagg till panel
3. Implementera datakalla-abstraction
4. Koppla mot extern API (DataForSEO/SerpAPI)

---

## NOTERINGAR

- Foljer befintlig panelstruktur fran siex-dashboard
- Ateranvander CSS-variabler och komponenter
- API-anrop gar mot ML-service (port 8003)
- SERP-panelen kraver extern datakalla (se SERP_FEATURE_ANALYSIS.md)

---

*Skapad: 2025-12-30 | Version: 1.0.0*