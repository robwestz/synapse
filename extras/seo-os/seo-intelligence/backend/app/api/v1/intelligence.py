"""
Intelligence API endpoints
Executes the 50+ intelligence modes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

from app.core.database import get_db
from app.intelligence_modes.mode_1_1_cluster_dominance import ClusterDominanceAnalyzer
from app.intelligence_modes.mode_1_2_longtail_gap import LongtailGapFinder
from app.intelligence_modes.mode_3_1_common_linker import CommonLinkerDiscovery


router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class IntelligenceMode(str, Enum):
    """
    Available intelligence modes
    """
    # MODE 1: Cluster Dominance Matrix
    CLUSTER_DOMINANCE = "1.1_cluster_dominance"
    LONGTAIL_GAP = "1.2_longtail_gap"
    CLUSTER_MOMENTUM = "1.3_cluster_momentum"
    ENTITY_OVERLAP = "1.4_entity_overlap"
    INTENT_GAP = "1.5_intent_gap"

    # MODE 2: SERP Feature Warfare
    PAA_HIJACK = "2.1_paa_hijack"
    SNIPPET_VULNERABILITY = "2.2_snippet_vulnerability"
    SERP_DENSITY = "2.3_serp_density"
    MULTI_INTENT = "2.4_multi_intent"
    POSITION_ZERO = "2.5_position_zero"

    # MODE 3: Backlink Intelligence
    COMMON_LINKER = "3.1_common_linker"
    ANCHOR_PATTERN = "3.2_anchor_pattern"
    LINK_VELOCITY = "3.3_link_velocity"
    DR_WEIGHTED_GAP = "3.4_dr_weighted_gap"
    CONTENT_TYPE_MAGNET = "3.5_content_type_magnet"

    # ... add all 50+ modes


class IntelligenceModeRequest(BaseModel):
    """
    Request to execute intelligence mode
    """
    mode: IntelligenceMode
    user_id: str = Field(..., description="User ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Mode-specific parameters")


class IntelligenceModeResponse(BaseModel):
    """
    Response from intelligence mode execution
    """
    mode: str
    status: str
    summary: Dict[str, Any]
    result: Dict[str, Any]


@router.post("/execute", response_model=IntelligenceModeResponse)
async def execute_intelligence_mode(
    request: IntelligenceModeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a specific intelligence mode

    Returns strategic insights based on uploaded Ahrefs data
    """

    # Route to appropriate analyzer
    if request.mode == IntelligenceMode.CLUSTER_DOMINANCE:
        analyzer = ClusterDominanceAnalyzer(db, request.user_id)
        result = await analyzer.execute()

    elif request.mode == IntelligenceMode.LONGTAIL_GAP:
        analyzer = LongtailGapFinder(db, request.user_id)
        result = await analyzer.execute()

    elif request.mode == IntelligenceMode.COMMON_LINKER:
        analyzer = CommonLinkerDiscovery(db, request.user_id)
        min_competitors = request.parameters.get('min_competitors', 3)
        result = await analyzer.execute(min_competitors=min_competitors)

    # ... add all other modes

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Mode {request.mode} not yet implemented"
        )

    # Check for errors
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return IntelligenceModeResponse(
        mode=result["mode"],
        status=result["status"],
        summary=result["summary"],
        result=result
    )


@router.get("/available-modes/{user_id}")
async def get_available_modes(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get list of intelligence modes available based on uploaded data

    Different modes require different report types.
    This endpoint tells you which modes you can run.
    """

    from sqlalchemy import select, func
    from app.models.uploads import Upload

    # Get user's uploaded report types
    query = (
        select(Upload.report_type, func.count(Upload.id))
        .where(Upload.user_id == user_id)
        .where(Upload.processing_status == "completed")
        .group_by(Upload.report_type)
    )

    result = await db.execute(query)
    uploaded_reports = {row[0]: row[1] for row in result.fetchall()}

    # Check which modes are available
    available_modes = []

    # MODE 1 requires Organic Keywords
    if 'organic_keywords' in uploaded_reports:
        available_modes.extend([
            {
                "mode": "1.1_cluster_dominance",
                "name": "Cluster Dominance Matrix",
                "category": "Cluster Analysis",
                "requires": ["organic_keywords"],
                "description": "Identify parent topics dominated by competitors"
            },
            {
                "mode": "1.2_longtail_gap",
                "name": "Longtail Gap Finder",
                "category": "Cluster Analysis",
                "requires": ["organic_keywords"],
                "description": "Find longtail keywords (5+ words) competitors rank for"
            },
        ])

    # MODE 3 requires Backlinks or Referring Domains
    if 'backlinks' in uploaded_reports or 'referring_domains' in uploaded_reports:
        available_modes.append({
            "mode": "3.1_common_linker",
            "name": "Common Linker Discovery",
            "category": "Backlink Intelligence",
            "requires": ["referring_domains"],
            "description": "Find domains linking to 3+ competitors but not you"
        })

    # ... check requirements for all other modes

    return {
        "user_id": user_id,
        "uploaded_reports": uploaded_reports,
        "available_modes": available_modes,
        "total_available": len(available_modes),
        "total_possible": 55,  # All 55 modes
    }


@router.get("/presets")
async def get_intelligence_presets() -> List[Dict[str, Any]]:
    """
    Get preset intelligence packs

    Presets are curated combinations of modes for specific use cases
    """

    presets = [
        {
            "id": "ecommerce_domination",
            "name": "E-commerce Domination Pack",
            "description": "Optimized for e-commerce SEO",
            "modes": [
                "1.1_cluster_dominance",  # Product category gaps
                "1.2_longtail_gap",  # Product variation keywords
                "1.5_intent_gap",  # Commercial vs transactional
                "4.2_low_competition",  # Easy product keyword wins
                "8.2_content_roi",  # Revenue potential
            ],
            "estimated_time": "5-10 minutes",
        },
        {
            "id": "saas_crusher",
            "name": "SaaS Competitor Crusher",
            "description": "For SaaS companies competing on SEO",
            "modes": [
                "1.1_cluster_dominance",  # Feature keyword clusters
                "3.1_common_linker",  # B2B link opportunities
                "4.3_branded_ratio",  # Competitor brand dependency
                "7.1_competitor_profile",  # Full competitive landscape
                "8.4_competitive_moat",  # Moat analysis
            ],
            "estimated_time": "10-15 minutes",
        },
        {
            "id": "local_seo_supremacy",
            "name": "Local SEO Supremacy",
            "description": "Dominate local search",
            "modes": [
                "1.2_longtail_gap",  # Local longtails
                "2.1_paa_hijack",  # Local questions
                "2.4_multi_intent",  # Local vs info intent
                "4.2_low_competition",  # Easy local wins
            ],
            "estimated_time": "5-8 minutes",
        },
        {
            "id": "content_empire",
            "name": "Content Empire Builder",
            "description": "Build topical authority",
            "modes": [
                "1.1_cluster_dominance",  # Topic coverage
                "1.3_cluster_momentum",  # Trending topics
                "5.1_cluster_completeness",  # Topic depth
                "5.2_sub_cluster_discovery",  # Niche opportunities
                "5.5_content_depth_gap",  # How deep to go
                "8.9_content_gap_priority",  # What to write first
            ],
            "estimated_time": "10-12 minutes",
        },
        {
            "id": "fuck_ahrefs_complete",
            "name": "The Complete Obliteration",
            "description": "Run ALL intelligence modes (advanced users)",
            "modes": "all",  # Special: runs all 55 modes
            "estimated_time": "30-45 minutes",
        },
    ]

    return presets


@router.post("/execute-preset/{preset_id}")
async def execute_preset(
    preset_id: str,
    user_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Execute a preset intelligence pack

    Runs multiple modes in sequence and combines results
    """

    # This would queue up multiple mode executions
    # and return a job ID to check status

    return {
        "preset_id": preset_id,
        "user_id": user_id,
        "status": "queued",
        "message": "Preset execution started. Check /jobs/{job_id} for progress",
        "job_id": "job_123",  # Would be real job ID
    }
