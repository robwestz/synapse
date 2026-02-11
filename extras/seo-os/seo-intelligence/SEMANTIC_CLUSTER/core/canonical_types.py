"""
Entity Atlas - Canonical Types
All Pydantic models for the platform's data contract.
Version: 0.9.0
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib


# ============================================================================
# ENUMS
# ============================================================================

class Intent(str, Enum):
    INFO = "INFO"
    COMMERCIAL = "COMMERCIAL"
    TRANS = "TRANS"
    NAV = "NAV"
    LOCAL = "LOCAL"


class TaskArchetype(str, Enum):
    DEFINITION = "definition"
    GUIDE = "guide"
    COMPARE = "compare"
    REVIEW = "review"
    PRICE = "price"
    BUY = "buy"
    SIGNUP = "signup"
    LOGIN = "login"
    BRAND = "brand"
    OTHER = "other"


class EntityType(str, Enum):
    PRODUCT = "PRODUCT"
    CONCEPT = "CONCEPT"
    BRAND = "BRAND"
    PERSON = "PERSON"
    PLACE = "PLACE"
    ORG = "ORG"
    EVENT = "EVENT"
    OTHER = "OTHER"


class ClusterRole(str, Enum):
    CORE = "CORE"
    SUPPORT = "SUPPORT"
    BRIDGE = "BRIDGE"


class EvidenceClaimType(str, Enum):
    INTENT = "INTENT"
    ENTITY_TYPE = "ENTITY_TYPE"
    CLUSTER_ASSIGNMENT = "CLUSTER_ASSIGNMENT"
    RELATION = "RELATION"
    PAGE_TYPE = "PAGE_TYPE"
    SERP_HOMOGENEITY = "SERP_HOMOGENEITY"


class EvidenceStatus(str, Enum):
    STUB = "STUB"
    FINALIZED = "FINALIZED"


class ProvenanceLayer(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"


class DomainLabel(str, Enum):
    MINE = "mine"
    COMPETITOR = "competitor"


# ============================================================================
# ID GENERATORS (Deterministic)
# ============================================================================

def generate_keyword_id(normalized: str, country: str, language: str) -> str:
    """Generate stable keyword ID: kw_<sha1>"""
    data = f"{normalized}|{country}|{language}"
    h = hashlib.sha1(data.encode()).hexdigest()[:12]
    return f"kw_{h}"


def generate_query_id(normalized: str, country: str, language: str) -> str:
    """Generate stable query ID: q_<sha1>"""
    data = f"{normalized}|{country}|{language}"
    h = hashlib.sha1(data.encode()).hexdigest()[:12]
    return f"q_{h}"


def generate_entity_id(name: str, type_hint: str, language: str) -> str:
    """Generate stable entity ID: e_<sha1>"""
    data = f"{name.lower().strip()}|{type_hint}|{language}"
    h = hashlib.sha1(data.encode()).hexdigest()[:12]
    return f"e_{h}"


def generate_cluster_id(keyword_ids: list[str], primary_entity_id: str, intent: str, engine_version_major: str) -> str:
    """Generate stable cluster ID: c_<sha1>"""
    sorted_kw = "|".join(sorted(keyword_ids))
    data = f"{sorted_kw}|{primary_entity_id}|{intent}|{engine_version_major}"
    h = hashlib.sha1(data.encode()).hexdigest()[:12]
    return f"c_{h}"


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class NormalizedQuery:
    text: str
    tokens: list[str]
    head_term: str
    modifiers: list[str]


@dataclass
class Query:
    query_id: str
    text: str
    language: str
    country: str
    normalized: NormalizedQuery


@dataclass
class EvidenceSignal:
    signal_type: str  # modifier_rule, serp_page_type_distribution, embedding_similarity, etc.
    value: str | dict | float
    weight: float


@dataclass
class EvidenceContradiction:
    signal_a: str
    signal_b: str
    delta: float
    resolution: str  # which signal wins


@dataclass
class EvidenceClaim:
    type: EvidenceClaimType
    value: str


@dataclass
class EvidenceProvenance:
    layer: ProvenanceLayer
    source: str  # rules, embeddings, serpapi, dataforseo, googlekg, wikidata, upload
    source_ref: Optional[str] = None
    observed_at: Optional[datetime] = None


@dataclass
class EvidenceScore:
    confidence: float
    contradiction_rate: float = 0.0
    calibration: str = "uncalibrated"


@dataclass
class Evidence:
    evidence_id: str
    status: EvidenceStatus
    claim: EvidenceClaim
    signals: list[EvidenceSignal]
    contradictions: list[EvidenceContradiction]
    provenance: EvidenceProvenance
    score: EvidenceScore


@dataclass
class EntityRelation:
    entity_id: str
    relation_type: str
    strength: float


@dataclass
class EntityProperty:
    key: str
    value: str
    source: str


@dataclass
class EntityCalculated:
    semantic_mass: float = 0.0
    coverage_score: float = 0.0


@dataclass
class Entity:
    entity_id: str
    name: str
    type: EntityType
    aliases: list[str] = field(default_factory=list)
    properties: list[EntityProperty] = field(default_factory=list)
    parent_entities: list[str] = field(default_factory=list)
    child_entities: list[str] = field(default_factory=list)
    related_entities: list[EntityRelation] = field(default_factory=list)
    calculated: EntityCalculated = field(default_factory=EntityCalculated)
    evidence: list[str] = field(default_factory=list)


@dataclass
class ClusterMetrics:
    total_volume: Optional[int] = None
    avg_difficulty: Optional[float] = None
    serp_features: list[str] = field(default_factory=list)


@dataclass
class Cluster:
    cluster_id: str
    label: str
    keyword_ids: list[str]
    intent: Intent
    task_archetype: TaskArchetype
    intent_modifier: Optional[str] = None
    primary_entity_id: Optional[str] = None
    secondary_entity_ids: list[str] = field(default_factory=list)
    cluster_role: ClusterRole = ClusterRole.SUPPORT
    metrics: ClusterMetrics = field(default_factory=ClusterMetrics)
    stability_signature: Optional[str] = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class Attribution:
    intent: Intent
    intent_confidence: float
    task_archetype: TaskArchetype
    cluster_id: str
    cluster_label: str
    cluster_role: ClusterRole
    primary_entity_id: str
    secondary_entity_ids: list[str]
    entity_confidence: float


@dataclass
class AttributedKeyword:
    keyword_id: str
    keyword: str
    attribution: Attribution
    evidence: list[str]


@dataclass
class SiteInfo:
    domain: str
    label: DomainLabel
    competitor_group: Optional[str] = None


@dataclass 
class ImportMetadata:
    detected_language: str  # sv, en, unknown
    date_range_from: Optional[str] = None
    date_range_to: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportRow:
    keyword_id: str
    keyword: str
    country: Optional[str] = None
    language: Optional[str] = None
    position: Optional[int] = None
    url: Optional[str] = None
    volume: Optional[int] = None
    kd: Optional[float] = None
    traffic: Optional[float] = None
    serp_features: list[str] = field(default_factory=list)
    snapshot_date: Optional[str] = None


@dataclass
class RankingImport:
    import_id: str
    project_id: str
    source: str  # ahrefs, semrush, gsc, simple_keyword_list
    report_type: str
    uploaded_at: datetime
    site: SiteInfo
    metadata: ImportMetadata
    rows: list[ImportRow]


@dataclass
class EntityGapSummary:
    mine_top20: int
    competitor_top20: int
    gap_keywords: int
    priority_score: float


@dataclass
class IntentGap:
    intent: Intent
    gap_keywords: int
    priority_score: float


@dataclass
class ClusterGap:
    cluster_id: str
    cluster_label: str
    gap_keywords: int
    priority_score: float
    role: ClusterRole


@dataclass
class GapAction:
    action_type: str  # create_page, optimize_existing, etc.
    cluster_id: str
    recommended_archetype: TaskArchetype
    why: str


@dataclass
class EntityGap:
    entity_id: str
    entity_name: str
    snapshot_date: str
    mine_domain: str
    competitors: list[str]
    summary: EntityGapSummary
    by_intent: list[IntentGap]
    by_cluster: list[ClusterGap]
    top_actions: list[GapAction]


# ============================================================================
# REPORT TYPES
# ============================================================================

AHREFS_REPORT_TYPES = [
    "serp_overview",
    "organic_keywords",
    "matching_terms",
    "matching_terms_clusters",
    "matching_terms_parent_topic",
    "backlinks",
    "referring_domains",
    "organic_competitors",
    "best_by_links",
    "internal_most_linked",
    "simple_keyword_list",
]
