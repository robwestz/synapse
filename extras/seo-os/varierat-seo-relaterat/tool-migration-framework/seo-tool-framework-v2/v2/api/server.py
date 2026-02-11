"""
SEO Intelligence Platform - API Server
=======================================

FastAPI server that exposes the tool framework via REST API.

Endpoints:
    GET  /api/tools              - List all tools
    GET  /api/tools/{id}         - Get tool details
    POST /api/tools/{id}/execute - Execute a tool
    POST /api/pipeline           - Execute a pipeline
    GET  /api/categories         - List categories
    GET  /api/archetypes         - List archetypes
    WS   /ws/execute/{id}        - WebSocket for streaming execution

Usage:
    uvicorn api:app --reload --port 8000
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.framework import ToolFramework, ExecutionResult

# =============================================================================
# CONFIGURATION
# =============================================================================

MANIFEST_DIR = os.getenv("MANIFEST_DIR", "manifests")
TOOLS_DIR = os.getenv("TOOLS_DIR", "tools")
TOOLS_MODULE = os.getenv("TOOLS_MODULE", "tools")
FRONTEND_DIR = os.getenv("FRONTEND_DIR", "frontend")

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ToolExecuteRequest(BaseModel):
    """Request to execute a tool."""
    data: Dict[str, Any]


class PipelineStep(BaseModel):
    """A step in a pipeline."""
    tool_id: str
    data: Dict[str, Any] = {}
    pass_result_to_next: bool = False
    continue_on_error: bool = False


class PipelineRequest(BaseModel):
    """Request to execute a pipeline."""
    steps: List[PipelineStep]


class BatchRequest(BaseModel):
    """Request to execute a tool on multiple items."""
    items: List[Dict[str, Any]]
    parallel: bool = True


# =============================================================================
# APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="SEO Intelligence Platform API",
    description="Manifest-driven tool execution framework",
    version="2.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Framework instance
framework = ToolFramework()


@app.on_event("startup")
async def startup():
    """Initialize framework on startup."""
    # Load manifests
    manifest_count = framework.load_manifests(MANIFEST_DIR)
    print(f"Loaded {manifest_count} manifests from {MANIFEST_DIR}")
    
    # Auto-discover tools
    if Path(TOOLS_DIR).exists():
        discover_count = framework.auto_discover(TOOLS_DIR, TOOLS_MODULE)
        print(f"Auto-discovered {discover_count} tools from {TOOLS_DIR}")
    
    total = len(framework.list_tools())
    print(f"Total tools available: {total}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await framework.shutdown()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "tools_count": len(framework.list_tools()),
    }


@app.get("/api/tools")
async def list_tools(
    category: Optional[str] = None,
    archetype: Optional[str] = None,
):
    """
    List all available tools.
    
    Optional filters:
    - category: Filter by category
    - archetype: Filter by archetype (analyzer, generator, etc.)
    """
    tools = framework.list_tools()
    
    if category:
        tools = [t for t in tools if t["category"] == category]
    
    if archetype:
        tools = [t for t in tools if t["archetype"] == archetype]
    
    return {
        "tools": tools,
        "count": len(tools),
    }


@app.get("/api/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get details for a specific tool."""
    tool = framework.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    return tool


@app.post("/api/tools/{tool_id}/execute")
async def execute_tool(tool_id: str, request: ToolExecuteRequest):
    """
    Execute a tool with given data.
    
    Request body:
    ```json
    {
        "data": {
            "param1": "value1",
            "param2": "value2"
        }
    }
    ```
    """
    # Check tool exists
    tool = framework.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    # Execute
    result = await framework.execute(tool_id, request.data)
    
    return {
        "success": result.success,
        "tool_id": result.tool_id,
        "data": result.data,
        "execution_time_ms": result.execution_time_ms,
        "error": result.error,
        "metrics": result.metrics,
    }


@app.post("/api/tools/{tool_id}/batch")
async def execute_batch(tool_id: str, request: BatchRequest):
    """
    Execute a tool on multiple items.
    
    Request body:
    ```json
    {
        "items": [
            {"param1": "value1"},
            {"param1": "value2"}
        ],
        "parallel": true
    }
    ```
    """
    # Check tool exists
    tool = framework.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    # Execute batch
    results = await framework.execute_batch(tool_id, request.items, request.parallel)
    
    return {
        "results": [r.to_dict() for r in results],
        "count": len(results),
        "success_count": sum(1 for r in results if r.success),
    }


@app.post("/api/pipeline")
async def execute_pipeline(request: PipelineRequest):
    """
    Execute a pipeline of tools.
    
    Request body:
    ```json
    {
        "steps": [
            {
                "tool_id": "content_gap_discovery",
                "data": {"domain": "example.com"},
                "pass_result_to_next": true
            },
            {
                "tool_id": "keyword_clustering",
                "data": {},
                "pass_result_to_next": false
            }
        ]
    }
    ```
    """
    steps = [
        {
            "tool_id": step.tool_id,
            "data": step.data,
            "pass_result_to_next": step.pass_result_to_next,
            "continue_on_error": step.continue_on_error,
        }
        for step in request.steps
    ]
    
    results = await framework.execute_pipeline(steps)
    
    return {
        "results": [r.to_dict() for r in results],
        "count": len(results),
        "success_count": sum(1 for r in results if r.success),
        "pipeline_success": all(r.success for r in results),
    }


@app.get("/api/categories")
async def list_categories():
    """List all tool categories."""
    categories = framework.registry.get_categories()
    return {
        "categories": categories,
        "count": len(categories),
    }


@app.get("/api/archetypes")
async def list_archetypes():
    """List all tool archetypes."""
    archetypes = framework.registry.get_archetypes()
    
    # Add descriptions
    archetype_info = {
        "analyzer": {
            "name": "Analyzer",
            "description": "Analyzes data and provides insights",
            "icon": "🔍",
            "color": "#3B82F6",
        },
        "generator": {
            "name": "Generator",
            "description": "Generates content or artifacts",
            "icon": "✨",
            "color": "#10B981",
        },
        "monitor": {
            "name": "Monitor",
            "description": "Monitors and tracks changes over time",
            "icon": "📊",
            "color": "#F59E0B",
        },
        "optimizer": {
            "name": "Optimizer",
            "description": "Optimizes content or structure",
            "icon": "⚡",
            "color": "#8B5CF6",
        },
        "discoverer": {
            "name": "Discoverer",
            "description": "Discovers opportunities and gaps",
            "icon": "🎯",
            "color": "#EF4444",
        },
    }
    
    return {
        "archetypes": [
            {
                "id": a,
                **archetype_info.get(a, {"name": a.title(), "description": "", "icon": "⚙️", "color": "#6B7280"})
            }
            for a in archetypes
        ],
        "count": len(archetypes),
    }


# =============================================================================
# WEBSOCKET FOR STREAMING
# =============================================================================

@app.websocket("/ws/execute/{tool_id}")
async def websocket_execute(websocket: WebSocket, tool_id: str):
    """
    WebSocket endpoint for streaming tool execution.
    
    Useful for long-running tools that produce incremental output.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive execution request
            data = await websocket.receive_json()
            
            # Send start message
            await websocket.send_json({
                "type": "start",
                "tool_id": tool_id,
            })
            
            # Execute tool
            result = await framework.execute(tool_id, data.get("data", {}))
            
            # Send result
            await websocket.send_json({
                "type": "complete",
                **result.to_dict(),
            })
            
    except WebSocketDisconnect:
        pass


# =============================================================================
# STATIC FILES & FRONTEND
# =============================================================================

# Serve frontend if it exists
frontend_path = Path(FRONTEND_DIR)
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend."""
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend not found. API available at /api/"}


# =============================================================================
# DEMO MODE (Mock responses when tools aren't available)
# =============================================================================

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    @app.post("/api/demo/tools/{tool_id}/execute")
    async def demo_execute(tool_id: str, request: ToolExecuteRequest):
        """Demo endpoint with mock responses."""
        import random
        import time
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Generate mock response based on tool type
        mock_responses = {
            "content_gap_discovery": {
                "gaps": [
                    {"keyword": "seo tools", "volume": 12000, "difficulty": 45, "opportunity_score": 85},
                    {"keyword": "keyword research", "volume": 8500, "difficulty": 52, "opportunity_score": 72},
                    {"keyword": "backlink analysis", "volume": 5200, "difficulty": 38, "opportunity_score": 88},
                ],
                "total_gaps": 3,
                "avg_opportunity": 81.7,
            },
            "keyword_clustering": {
                "clusters": [
                    {"id": 1, "name": "SEO Tools", "keywords": ["seo tools", "best seo tools", "free seo tools"], "size": 3},
                    {"id": 2, "name": "Keyword Research", "keywords": ["keyword research", "keyword tool"], "size": 2},
                ],
                "total_clusters": 2,
            },
            "internal_link_optimizer": {
                "suggestions": [
                    {"source": "/blog/seo-guide", "target": "/tools/keyword-research", "anchor": "keyword research tool", "relevance": 0.92},
                    {"source": "/blog/seo-guide", "target": "/tools/backlink-checker", "anchor": "backlink analysis", "relevance": 0.87},
                ],
                "total_suggestions": 2,
            },
        }
        
        return {
            "success": True,
            "tool_id": tool_id,
            "data": mock_responses.get(tool_id, {"message": "Mock response", "input": request.data}),
            "execution_time_ms": random.uniform(100, 500),
            "demo_mode": True,
        }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
