# 🧠 SEO Intelligence Platform - Tool Framework v2

A manifest-driven framework for the SEO Intelligence Platform's 100+ standardized ML/AI tools.

## 🎯 Overview

This framework provides:
- **Manifest-driven tool registration** - Define tools in YAML, get UI for free
- **Auto-discovery** - Drop Python files in a folder, they become tools
- **Unified API** - Single endpoint pattern for all tools
- **Auto-generating frontend** - UI builds itself from manifests
- **Pipeline orchestration** - Chain tools together

## ✨ Key Feature: 100% Drop-In Compatibility

Analysis of the codebase shows **all 100 tools follow the same pattern**:

```python
@dataclass
class [Tool]Config:       # Configuration
    param1: str
    param2: int

@dataclass  
class [Tool]Result:       # Result with to_dict()
    success: bool
    data: Dict

class [Tool]Service:      # Main service
    async def initialize()
    async def close()
    async def analyze(data) → Result
    def get_metrics() → Dict
```

This means **no wrappers or adapters needed** - just manifest + existing code!

## 📁 Project Structure

```
v2/
├── core/
│   └── framework.py      # Core framework (ToolFramework, Registry, Adapter)
├── api/
│   └── server.py         # FastAPI server
├── frontend/
│   └── index.html        # Auto-generating UI
├── manifests/            # YAML tool definitions
│   ├── content_gap_discovery.yaml
│   ├── keyword_clustering.yaml
│   └── ...
├── tools/                # Your Python tools (symlink to existing)
│   ├── ml_features/
│   ├── tier1/
│   └── tier2/
└── requirements.txt
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pyyaml
```

### 2. Link Your Tools

```bash
# Create symlinks to your existing tool directories
ln -s /path/to/ml-service/app/features tools/ml_features
ln -s /path/to/services/tier1-priority tools/tier1
ln -s /path/to/services/tier2-core tools/tier2
```

### 3. Start the Server

```bash
cd v2
python -m uvicorn api.server:app --reload --port 8000
```

### 4. Open the UI

Navigate to `http://localhost:8000`

## 📝 Creating a Manifest

Minimal manifest (auto-detects most settings):

```yaml
tool:
  id: my_tool
  name: "My Tool"
  description: "Does something useful"
  category: analysis
  archetype: analyzer
  
  backend:
    module: "ml_features.my_tool"
    class: "MyToolService"
```

Full manifest with UI configuration:

```yaml
tool:
  id: content_gap_discovery
  name: "Content Gap Discovery"
  description: "Find content opportunities"
  category: content
  archetype: discoverer
  icon: "🎯"
  
  backend:
    module: "ml_features.content_gap_discovery"
    class: "ContentGapDiscoveryService"
    method: "generate"
  
  inputs:
    - name: domain
      label: "Your Domain"
      type: text
      required: true
    - name: min_volume
      type: number
      default: 100
  
  outputs:
    type: table
    columns:
      - name: keyword
        label: "Keyword"
      - name: volume
        type: number
  
  actions:
    - id: export
      label: "Export CSV"
      type: export
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tools` | List all tools |
| GET | `/api/tools/{id}` | Get tool details |
| POST | `/api/tools/{id}/execute` | Execute a tool |
| POST | `/api/tools/{id}/batch` | Execute on multiple items |
| POST | `/api/pipeline` | Execute a pipeline |
| GET | `/api/categories` | List categories |
| GET | `/api/archetypes` | List archetypes |

### Execute a Tool

```bash
curl -X POST http://localhost:8000/api/tools/content_gap_discovery/execute \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "domain": "example.com",
      "competitors": ["comp1.com", "comp2.com"],
      "min_volume": 100
    }
  }'
```

### Execute a Pipeline

```bash
curl -X POST http://localhost:8000/api/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {
        "tool_id": "content_gap_discovery",
        "data": {"domain": "example.com"},
        "pass_result_to_next": true
      },
      {
        "tool_id": "keyword_clustering",
        "data": {"min_cluster_size": 3}
      }
    ]
  }'
```

## 🔌 Integration with Existing Code

### Option 1: Symlinks (Recommended)

```bash
# Link existing tool directories
ln -s /path/to/ml-service/app/features tools/ml_features
```

### Option 2: Python Path

```python
# In api/server.py
import sys
sys.path.insert(0, "/path/to/your/tools")
```

### Option 3: Environment Variables

```bash
export TOOLS_DIR=/path/to/your/tools
export TOOLS_MODULE=ml_features
```

## 🎨 UI Archetypes

The frontend applies different styling based on archetype:

| Archetype | Icon | Color | Use Case |
|-----------|------|-------|----------|
| `analyzer` | 🔍 | Blue | Analyze data, find patterns |
| `generator` | ✨ | Green | Generate content/artifacts |
| `monitor` | 📊 | Orange | Track changes over time |
| `optimizer` | ⚡ | Purple | Optimize existing content |
| `discoverer` | 🎯 | Red | Find opportunities |

## 🔄 Migrating Existing Tools

Since all tools follow the standard pattern, migration is simple:

1. **Create manifest** - One YAML file per tool
2. **No code changes** - Existing Python code works as-is
3. **Test** - Execute via API or UI

### Batch Migration Script

```python
import os
from pathlib import Path

TOOLS_DIR = Path("tools/ml_features")
MANIFEST_DIR = Path("manifests")

for py_file in TOOLS_DIR.glob("*.py"):
    if py_file.name.startswith("_"):
        continue
    
    tool_id = py_file.stem
    manifest = f"""tool:
  id: {tool_id}
  name: "{tool_id.replace('_', ' ').title()}"
  description: "Auto-generated manifest"
  category: auto
  archetype: analyzer
  
  backend:
    module: "ml_features.{tool_id}"
    class: "{tool_id.title().replace('_', '')}Service"
"""
    
    manifest_path = MANIFEST_DIR / f"{tool_id}.yaml"
    manifest_path.write_text(manifest)
    print(f"Created: {manifest_path}")
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Alpine.js + Tailwind CSS                           │   │
│  │  Auto-generates forms from manifest inputs          │   │
│  │  Displays results based on output schema            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 FastAPI Server                       │   │
│  │  /api/tools, /api/tools/{id}/execute, etc.         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Tool Framework Core                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │  Registry   │  │   Adapter   │  │  Executor   │ │   │
│  │  │ (manifests) │  │ (dynamic)   │  │ (async)     │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Your Existing Tools                     │   │
│  │  100+ Python tools with standardized interface       │   │
│  │  Config → Service → Result pattern                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔒 Production Considerations

### Security

- Add authentication middleware
- Validate inputs against manifest schema
- Rate limiting
- CORS configuration

### Performance

- Tool instance caching (already implemented)
- Result caching with Redis
- Async execution with proper cleanup

### Monitoring

- Metrics endpoint (`/api/tools/{id}/metrics`)
- Execution logging
- Error tracking

## 📈 Next Steps

1. **Deploy** - Docker, Kubernetes, or cloud platform
2. **Add authentication** - JWT, API keys
3. **Enhance UI** - Charts, graphs, real-time updates
4. **Integrate** - Connect to your existing NestJS backend

## 🎯 Summary

- **100 tools** ready to use
- **0 wrappers** needed
- **~500 LOC** framework
- **Auto-generating UI**
- **Pipeline support**

This is the minimal framework that works with your perfectly standardized tools!
