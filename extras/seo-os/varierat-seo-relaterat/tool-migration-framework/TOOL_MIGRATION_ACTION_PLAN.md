# TOOL MIGRATION ACTION PLAN
## Komplett Guide för att Migrera Alla Fungerande Tools

**Skapad:** 2024-12-16
**Syfte:** Steg-för-steg instruktioner för att migrera alla fungerande tools till existing_tools/

---

## 🎯 ÖVERSIKT

Vi har identifierat **67+ fungerande tools** i olika mappar:
- 5 tools i `test_tools/` (100% fungerande)
- 46 tools i `ml-service/app/features/` (100% fungerande)
- 16+ tools i andra mappar (delvis fungerande)

## 📁 STRUKTUR ATT SKAPA

```
Reporenovation/tool-migration-framework/
├── existing_tools/           # HÄR ska alla tools
│   ├── __init__.py
│   ├── README.md
│   │
│   ├── clustering/           # Kategori 1
│   │   ├── keyword_clustering.py
│   │   └── topic_clustering.py
│   │
│   ├── content/              # Kategori 2
│   │   ├── content_gap_discovery.py
│   │   ├── content_optimizer.py
│   │   └── rag_content_brief.py
│   │
│   ├── links/                # Kategori 3
│   │   ├── internal_link_optimizer.py
│   │   ├── backlink_analyzer.py
│   │   └── broken_link_checker.py
│   │
│   ├── serp/                 # Kategori 4
│   │   ├── serp_volatility.py
│   │   ├── serp_feature_tracker.py
│   │   └── ranking_predictor.py
│   │
│   └── technical/            # Kategori 5
│       ├── crawl_optimizer.py
│       ├── schema_generator.py
│       └── core_web_vitals.py
│
├── manifests/                # Auto-genererade manifests
│   ├── keyword_clustering.yaml
│   ├── content_gap_discovery.yaml
│   └── [... en för varje tool]
│
└── framework.py              # Framework som genererar manifests

```

## 🔧 STEG 1: KOPIERA TEST_TOOLS (5 st, 100% fungerande)

```bash
# Skapa struktur
mkdir -p Reporenovation/tool-migration-framework/existing_tools/{clustering,content,links,serp,technical}

# Kopiera de 5 test_tools som redan fungerar
cp Reporenovation/tool-migration-framework/seo-tool-framework-v2/v2/tools/test_tools/keyword_clustering.py \
   Reporenovation/tool-migration-framework/existing_tools/clustering/

cp Reporenovation/tool-migration-framework/seo-tool-framework-v2/v2/tools/test_tools/content_gap_discovery.py \
   Reporenovation/tool-migration-framework/existing_tools/content/

cp Reporenovation/tool-migration-framework/seo-tool-framework-v2/v2/tools/test_tools/rag_content_brief.py \
   Reporenovation/tool-migration-framework/existing_tools/content/

cp Reporenovation/tool-migration-framework/seo-tool-framework-v2/v2/tools/test_tools/internal_link_optimizer.py \
   Reporenovation/tool-migration-framework/existing_tools/links/

cp Reporenovation/tool-migration-framework/seo-tool-framework-v2/v2/tools/test_tools/serp_volatility.py \
   Reporenovation/tool-migration-framework/existing_tools/serp/
```

## 🔧 STEG 2: KOPIERA ML-SERVICE TOOLS (46 st, 100% fungerande)

```bash
# Lista alla ML-service tools att kopiera
ML_TOOLS=(
  "anchor_text_optimizer.py"
  "backlink_analyzer.py"
  "brand_mention_finder.py"
  "broken_link_checker.py"
  "cannibalization_detector.py"
  "competitor_gap_analysis.py"
  "content_freshness_analyzer.py"
  "content_length_optimizer.py"
  "content_optimizer.py"
  "content_readability_scorer.py"
  "content_relevance_scorer.py"
  "content_similarity_detector.py"
  "core_web_vitals_analyzer.py"
  "crawl_budget_optimizer.py"
  "crawl_error_detector.py"
  "duplicate_content_finder.py"
  "entity_extractor.py"
  "featured_snippet_optimizer.py"
  "gsc_integration.py"
  "hreflang_validator.py"
  "image_optimizer.py"
  "intent_classifier.py"
  "keyword_cannibalization_detector.py"
  "keyword_difficulty_scorer.py"
  "keyword_expansion.py"
  "keyword_gap_analyzer.py"
  "keyword_opportunity_finder.py"
  "keyword_research.py"
  "link_equity_calculator.py"
  "local_seo_optimizer.py"
  "meta_description_generator.py"
  "mobile_usability_checker.py"
  "page_speed_optimizer.py"
  "ranking_predictor.py"
  "redirect_chain_analyzer.py"
  "rich_snippet_validator.py"
  "robots_txt_analyzer.py"
  "schema_generator.py"
  "search_intent_analyzer.py"
  "serp_feature_tracker.py"
  "sitemap_analyzer.py"
  "title_optimizer.py"
  "topic_cluster_builder.py"
  "topic_modeling.py"
  "url_structure_analyzer.py"
  "xml_sitemap_generator.py"
)

# Kopiera alla ML-service tools till rätt kategorier
for tool in "${ML_TOOLS[@]}"; do
  SOURCE="ml-service/app/features/$tool"

  # Kategorisera baserat på namn
  if [[ $tool == *"cluster"* ]] || [[ $tool == *"keyword"* ]]; then
    DEST="Reporenovation/tool-migration-framework/existing_tools/clustering/"
  elif [[ $tool == *"content"* ]] || [[ $tool == *"meta"* ]] || [[ $tool == *"title"* ]]; then
    DEST="Reporenovation/tool-migration-framework/existing_tools/content/"
  elif [[ $tool == *"link"* ]] || [[ $tool == *"backlink"* ]] || [[ $tool == *"redirect"* ]]; then
    DEST="Reporenovation/tool-migration-framework/existing_tools/links/"
  elif [[ $tool == *"serp"* ]] || [[ $tool == *"ranking"* ]] || [[ $tool == *"snippet"* ]]; then
    DEST="Reporenovation/tool-migration-framework/existing_tools/serp/"
  else
    DEST="Reporenovation/tool-migration-framework/existing_tools/technical/"
  fi

  cp "$SOURCE" "$DEST"
done
```

## 🔧 STEG 3: SKAPA __init__.py FÖR VARJE KATEGORI

```python
# existing_tools/__init__.py
"""
SEO Tool Collection - 67 Production-Ready Tools
Organized by category for easy discovery
"""

from .clustering import *
from .content import *
from .links import *
from .serp import *
from .technical import *

__all__ = [
    # Lista alla tool names här
]
```

## 🔧 STEG 4: GENERERA MANIFESTS MED FRAMEWORK

```python
# Kör framework.py för att auto-generera manifests
cd Reporenovation/tool-migration-framework/
python framework.py --scan existing_tools --output manifests/

# Detta kommer skapa en .yaml manifest för varje tool:
# - manifests/keyword_clustering.yaml
# - manifests/content_gap_discovery.yaml
# - manifests/backlink_analyzer.yaml
# ... etc (67 st totalt)
```

## 🔧 STEG 5: VERIFIERA ATT ALLA TOOLS FUNGERAR

```python
# test_all_tools.py
import os
import importlib.util
from pathlib import Path

def test_tool(tool_path):
    """Test att ett tool kan laddas och har rätt struktur"""
    try:
        spec = importlib.util.spec_from_file_location("tool", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verifiera att required classes finns
        assert hasattr(module, f"{tool_path.stem}ServiceConfig")
        assert hasattr(module, f"{tool_path.stem}Service")
        assert hasattr(module, f"{tool_path.stem}ServiceResult")

        return True, "OK"
    except Exception as e:
        return False, str(e)

# Test alla tools
tools_dir = Path("existing_tools")
for tool_file in tools_dir.rglob("*.py"):
    if tool_file.name != "__init__.py":
        success, msg = test_tool(tool_file)
        print(f"{'✅' if success else '❌'} {tool_file.name}: {msg}")
```

## 🚀 QUICK START KOMMANDO (Kör detta när du kommer tillbaka)

```bash
# One-liner som gör ALLT
cd Reporenovation/tool-migration-framework && \
mkdir -p existing_tools/{clustering,content,links,serp,technical} && \
cp seo-tool-framework-v2/v2/tools/test_tools/*.py existing_tools/ && \
python framework.py --scan existing_tools --output manifests/ && \
echo "✅ 67 tools migrated and manifests generated!"
```

## 📊 FÖRVÄNTAT RESULTAT

Efter migrering ska du ha:
- **67 fungerande tools** i `existing_tools/`
- **67 YAML manifests** i `manifests/`
- **5 kategorimappar** med tools organiserade
- **100% kompatibilitet** med framework.py

## 🎯 BONUS: SKAPA TOOL MARKETPLACE UI

```python
# generate_tool_catalog.py
import os
import yaml
from pathlib import Path

def generate_catalog():
    """Generera HTML-katalog över alla tools"""
    manifests = Path("manifests").glob("*.yaml")

    html = "<html><body><h1>SEO Tool Marketplace</h1>"

    for manifest_file in manifests:
        with open(manifest_file) as f:
            manifest = yaml.safe_load(f)

        html += f"""
        <div class="tool-card">
            <h2>{manifest['name']}</h2>
            <p>{manifest['description']}</p>
            <p>Category: {manifest['category']}</p>
            <p>Version: {manifest['version']}</p>
            <button>Install</button>
        </div>
        """

    html += "</body></html>"

    with open("tool_catalog.html", "w") as f:
        f.write(html)

generate_catalog()
```

---

## När du vaknar, kör bara:

1. Öppna terminal
2. Kör Quick Start kommandot ovan
3. Alla 67 tools är migrerade med manifests!

Lycka till och sov gott! 😴