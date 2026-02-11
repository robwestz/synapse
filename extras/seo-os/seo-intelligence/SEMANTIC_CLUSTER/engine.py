"""
ENTITY & CLUSTER INTELLIGENCE ENGINE v3.0
==========================================
"The Only Tool You'll Ever Need for Semantic SEO Research"

ARCHITECTURE:
- Entity Gravity Engine (semantic_mass with 4 components)
- Cluster Role Classifier (deterministic CORE/SUPPORT/BRIDGE)
- SERP Field Reader (role, shape, entity_regime)

PIPELINE:
1. NORMALIZE (with lemma_tokens, modifiers)
2. EXPAND (Google Autocomplete)
3. SERP FIELD READ (before entity extract!)
4. INTENT + TASK_TYPE MODEL
5. ENTITY EXTRACT (informed by SERP expectations)
6. GRAPH BUILD
7. CLUSTER (dual: intent + entity-neighborhood)
8. SCORE (Entity Gravity + Cluster Role)
9. GAP ANALYSIS
"""

import re
import math
import json
import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from datetime import datetime
import urllib.parse
import urllib.request

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Intent(str, Enum):
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"
    LOCAL = "local"
    MIXED = "mixed"

class TaskType(str, Enum):
    """What the user is trying to GET DONE (separate from intent)"""
    DEFINITION = "definition"
    HOW_TO = "how_to"
    REVIEW = "review"
    COMPARISON = "comparison"
    BUY = "buy"
    PRICE = "price"
    BEST_OF = "best_of"
    TROUBLESHOOT = "troubleshoot"
    BRAND_NAV = "brand_nav"
    LOCAL_PROVIDER = "local_provider"
    LIST = "list"
    GUIDE = "guide"
    OTHER = "other"

class EntityType(str, Enum):
    PRODUCT = "product"
    CONCEPT = "concept"
    BRAND = "brand"
    PERSON = "person"
    PLACE = "place"
    ATTRIBUTE = "attribute"
    ACTION = "action"
    GENERAL = "general"

class ClusterRole(str, Enum):
    CORE = "core"       # High volume/SERP-dominance, low entity entropy
    SUPPORT = "support" # Narrower scope, high link to CORE entity
    BRIDGE = "bridge"   # High betweenness, links disparate entities

class EdgeType(str, Enum):
    CO_OCCUR = "co_occur"
    IS_ABOUT = "is_about"
    ATTRIBUTE_OF = "attribute_of"
    SAME_INTENT = "same_intent"
    BRIDGES = "bridges"
    PARENT_OF = "parent_of"
    RELATED_TO = "related_to"

class SerpRole(str, Enum):
    """What role Google expects content to play"""
    EDUCATOR = "educator"
    COMPARATOR = "comparator"
    SELECTOR = "selector"
    SELLER = "seller"
    NAVIGATOR = "navigator"
    TROUBLESHOOTER = "troubleshooter"

class SerpShape(str, Enum):
    """What content form Google expects"""
    GUIDE = "guide"
    LISTICLE = "listicle"
    COMPARISON_TABLE = "comparison_table"
    TOOL_PAGE = "tool_page"
    CATEGORY_PAGE = "category_page"
    FORUM_QA = "forum_qa"
    VIDEO_FIRST = "video_first"
    NEWS = "news"
    PRODUCT_PAGE = "product_page"


# ═══════════════════════════════════════════════════════════════════════════════
# CORE DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Keyword:
    """Enhanced keyword with normalization trace"""
    id: str
    raw: str                          # Original input
    normalized: str                   # Cleaned
    lemma_tokens: List[str] = field(default_factory=list)   # Stemmed tokens
    modifiers: List[str] = field(default_factory=list)      # bäst, 2025, billig...
    language: str = "sv"
    
    volume: int = 0
    difficulty: float = 0.0
    intent: Intent = Intent.MIXED
    task_type: TaskType = TaskType.OTHER
    
    is_seed: bool = False
    source: str = "user"
    
    # SERP-informed
    serp_analyzed: bool = False


@dataclass
class EntityGravity:
    """The gravity components for an entity"""
    cluster_mass: float = 0.0      # Sum of cluster contributions
    bridge_mass: float = 0.0       # Betweenness centrality
    centrality_mass: float = 0.0   # PageRank-style
    serp_mass: float = 0.0         # SERP presence score
    
    @property
    def semantic_mass(self) -> float:
        """
        semantic_mass = 
            0.45 * cluster_mass +
            0.20 * bridge_mass +
            0.20 * centrality_mass +
            0.15 * serp_mass
        """
        return (
            0.45 * self.cluster_mass +
            0.20 * self.bridge_mass +
            0.20 * self.centrality_mass +
            0.15 * self.serp_mass
        )


@dataclass
class Entity:
    """Entity with gravity calculation"""
    id: str
    name: str
    type: EntityType = EntityType.GENERAL
    properties: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    
    # Gravity
    gravity: EntityGravity = field(default_factory=EntityGravity)
    
    @property
    def semantic_mass(self) -> float:
        return self.gravity.semantic_mass
    
    # Classification
    is_dominant: bool = False      # Top entity in universe
    is_peripheral: bool = False    # Edge entity
    is_bridge: bool = False        # Connects intents


@dataclass
class ClusterRoleReason:
    """Why a cluster got its role"""
    rule: str
    score: float
    explanation: str


@dataclass
class Cluster:
    """Cluster with role classification"""
    id: str
    name: str
    keywords: List[str] = field(default_factory=list)
    
    primary_entity_id: Optional[str] = None
    secondary_entity_ids: List[str] = field(default_factory=list)
    
    intent: Intent = Intent.MIXED
    task_type: TaskType = TaskType.OTHER
    
    # Role classification
    role: ClusterRole = ClusterRole.SUPPORT
    role_reasons: List[ClusterRoleReason] = field(default_factory=list)
    role_confidence: float = 0.0
    
    # Metrics
    total_volume: int = 0
    avg_difficulty: float = 0.0
    bridge_score: float = 0.0
    entity_entropy: float = 0.0    # Low = cluster "hör hemma"


@dataclass
class SerpEntityRegime:
    """What entities Google expects for this query"""
    required_entities: List[str] = field(default_factory=list)   # Must mention
    dominant_entities: List[str] = field(default_factory=list)   # Usually prominent
    toxic_entities: List[str] = field(default_factory=list)      # Avoid (competitors, irrelevant)


@dataclass
class SerpField:
    """SERP Field Reader output - Google's 'opinion'"""
    query: str
    
    role_primary: SerpRole = SerpRole.EDUCATOR
    role_confidence: float = 0.0
    
    shape_primary: SerpShape = SerpShape.GUIDE
    shape_confidence: float = 0.0
    
    entity_regime: SerpEntityRegime = field(default_factory=SerpEntityRegime)
    
    homogeneity: float = 0.0       # 0-1, how uniform is SERP?
    confidence: float = 0.0
    
    # Raw signals
    paa_questions: List[str] = field(default_factory=list)
    related_searches: List[str] = field(default_factory=list)
    top_titles: List[str] = field(default_factory=list)


@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0


@dataclass
class GapCluster:
    """A missing cluster for coverage"""
    suggested_name: str
    suggested_keywords: List[str]
    target_entity_id: str
    priority_score: float
    reason: str


@dataclass
class AnalysisResult:
    """Complete analysis output"""
    project_id: str
    created_at: str
    seed_keywords: List[str]
    
    keywords: Dict[str, Keyword] = field(default_factory=dict)
    entities: Dict[str, Entity] = field(default_factory=dict)
    clusters: Dict[str, Cluster] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    serp_fields: Dict[str, SerpField] = field(default_factory=dict)
    
    gaps: List[GapCluster] = field(default_factory=list)
    
    stats: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY GRAVITY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class EntityGravityEngine:
    """
    Calculate semantic_mass for entities.
    
    Formula:
    semantic_mass = 
        0.45 * normalized(sum(cluster.contribution)) +
        0.20 * normalized(betweenness_centrality) +
        0.20 * normalized(pagerank) +
        0.15 * normalized(serp_presence)
    """
    
    def calculate_gravity(
        self,
        entities: Dict[str, Entity],
        clusters: Dict[str, Cluster],
        edges: List[Edge],
        serp_fields: Dict[str, SerpField]
    ) -> Dict[str, Entity]:
        """Calculate gravity for all entities."""
        
        # 1. Cluster Mass
        cluster_contributions = self._calc_cluster_mass(entities, clusters)
        
        # 2. Bridge Mass (Betweenness)
        betweenness = self._calc_betweenness(entities, edges)
        
        # 3. Centrality Mass (PageRank-style)
        pagerank = self._calc_pagerank(entities, edges)
        
        # 4. SERP Mass
        serp_presence = self._calc_serp_mass(entities, serp_fields)
        
        # Normalize and assign
        max_cluster = max(cluster_contributions.values()) if cluster_contributions else 1
        max_between = max(betweenness.values()) if betweenness else 1
        max_pr = max(pagerank.values()) if pagerank else 1
        max_serp = max(serp_presence.values()) if serp_presence else 1
        
        for entity_id, entity in entities.items():
            entity.gravity = EntityGravity(
                cluster_mass=cluster_contributions.get(entity_id, 0) / max(max_cluster, 0.001),
                bridge_mass=betweenness.get(entity_id, 0) / max(max_between, 0.001),
                centrality_mass=pagerank.get(entity_id, 0) / max(max_pr, 0.001),
                serp_mass=serp_presence.get(entity_id, 0) / max(max_serp, 0.001)
            )
        
        # Mark dominant/peripheral/bridge
        if entities:
            masses = [(eid, e.semantic_mass) for eid, e in entities.items()]
            masses.sort(key=lambda x: -x[1])
            
            # Top 20% are dominant
            top_n = max(1, len(masses) // 5)
            for eid, _ in masses[:top_n]:
                entities[eid].is_dominant = True
            
            # Bottom 20% are peripheral
            for eid, _ in masses[-top_n:]:
                entities[eid].is_peripheral = True
            
            # High bridge_mass = bridge entity
            for eid, e in entities.items():
                if e.gravity.bridge_mass > 0.6:
                    e.is_bridge = True
        
        return entities
    
    def _calc_cluster_mass(self, entities: Dict[str, Entity], clusters: Dict[str, Cluster]) -> Dict[str, float]:
        """Sum of cluster volumes for each entity."""
        mass = defaultdict(float)
        for cluster in clusters.values():
            if cluster.primary_entity_id:
                mass[cluster.primary_entity_id] += cluster.total_volume
            for eid in cluster.secondary_entity_ids:
                mass[eid] += cluster.total_volume * 0.3  # Secondary gets less weight
        return dict(mass)
    
    def _calc_betweenness(self, entities: Dict[str, Entity], edges: List[Edge]) -> Dict[str, float]:
        """Simplified betweenness: count unique paths through each entity."""
        betweenness = defaultdict(float)
        entity_ids = set(entities.keys())
        
        for edge in edges:
            if edge.source_id in entity_ids:
                betweenness[edge.source_id] += edge.weight
            if edge.target_id in entity_ids:
                betweenness[edge.target_id] += edge.weight
        
        # Bridge entities get bonus for connecting disparate nodes
        for eid in entity_ids:
            connected = set()
            for edge in edges:
                if edge.source_id == eid:
                    connected.add(edge.target_id)
                if edge.target_id == eid:
                    connected.add(edge.source_id)
            # More diverse connections = higher betweenness
            betweenness[eid] *= (1 + len(connected) * 0.1)
        
        return dict(betweenness)
    
    def _calc_pagerank(self, entities: Dict[str, Entity], edges: List[Edge], iterations: int = 10) -> Dict[str, float]:
        """Simplified PageRank."""
        entity_ids = list(entities.keys())
        n = len(entity_ids)
        if n == 0:
            return {}
        
        pr = {eid: 1.0 / n for eid in entity_ids}
        damping = 0.85
        
        # Build adjacency
        outlinks = defaultdict(list)
        for edge in edges:
            if edge.source_id in entities and edge.target_id in entities:
                outlinks[edge.source_id].append((edge.target_id, edge.weight))
        
        for _ in range(iterations):
            new_pr = {}
            for eid in entity_ids:
                incoming = 0
                for edge in edges:
                    if edge.target_id == eid and edge.source_id in entities:
                        out_count = len(outlinks[edge.source_id]) or 1
                        incoming += pr[edge.source_id] * edge.weight / out_count
                new_pr[eid] = (1 - damping) / n + damping * incoming
            pr = new_pr
        
        return pr
    
    def _calc_serp_mass(self, entities: Dict[str, Entity], serp_fields: Dict[str, SerpField]) -> Dict[str, float]:
        """How often entity appears in SERP signals."""
        mass = defaultdict(float)
        for serp in serp_fields.values():
            for ename in serp.entity_regime.dominant_entities:
                # Find entity by name
                for eid, e in entities.items():
                    if e.name.lower() == ename.lower():
                        mass[eid] += 1.0
            for ename in serp.entity_regime.required_entities:
                for eid, e in entities.items():
                    if e.name.lower() == ename.lower():
                        mass[eid] += 0.5
        return dict(mass)


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER ROLE CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

class ClusterRoleClassifier:
    """
    Deterministic rules for CORE/SUPPORT/BRIDGE classification.
    """
    
    def classify(
        self,
        clusters: Dict[str, Cluster],
        entities: Dict[str, Entity],
        edges: List[Edge]
    ) -> Dict[str, Cluster]:
        """Classify all clusters."""
        
        max_volume = max((c.total_volume for c in clusters.values()), default=1)
        
        for cluster_id, cluster in clusters.items():
            reasons = []
            scores = {"core": 0, "support": 0, "bridge": 0}
            
            # Rule 1: Volume/SERP dominance
            volume_ratio = cluster.total_volume / max(max_volume, 1)
            if volume_ratio > 0.3:
                scores["core"] += 0.4
                reasons.append(ClusterRoleReason("high_volume", volume_ratio, f"Volume {cluster.total_volume} is top-tier"))
            elif volume_ratio < 0.1:
                scores["support"] += 0.3
                reasons.append(ClusterRoleReason("low_volume", volume_ratio, "Lower volume, supportive role"))
            
            # Rule 2: Entity entropy (low = cluster "belongs")
            if len(cluster.secondary_entity_ids) <= 1:
                cluster.entity_entropy = 0.1
                scores["core"] += 0.3
                reasons.append(ClusterRoleReason("low_entropy", 0.1, "Cluster clearly belongs to one entity"))
            elif len(cluster.secondary_entity_ids) <= 3:
                cluster.entity_entropy = 0.4
                scores["support"] += 0.2
            else:
                cluster.entity_entropy = 0.8
                scores["bridge"] += 0.4
                reasons.append(ClusterRoleReason("high_entropy", 0.8, f"Touches {len(cluster.secondary_entity_ids)} entities"))
            
            # Rule 3: Betweenness in cluster graph
            cluster_edges = [e for e in edges if cluster_id in (e.source_id, e.target_id)]
            if len(cluster_edges) > 5:
                scores["bridge"] += 0.3
                reasons.append(ClusterRoleReason("high_connectivity", len(cluster_edges), "Many connections"))
            
            # Rule 4: Links to disparate entities
            if cluster.secondary_entity_ids:
                entity_types = set()
                for eid in cluster.secondary_entity_ids:
                    if eid in entities:
                        entity_types.add(entities[eid].type)
                if len(entity_types) > 2:
                    scores["bridge"] += 0.35
                    reasons.append(ClusterRoleReason("entity_diversity", len(entity_types), "Bridges different entity types"))
            
            # Determine role
            max_role = max(scores.items(), key=lambda x: x[1])
            cluster.role = ClusterRole(max_role[0])
            cluster.role_reasons = reasons
            cluster.role_confidence = max_role[1] / max(sum(scores.values()), 0.01)
            
            # Calculate bridge_score
            cluster.bridge_score = scores["bridge"]
        
        return clusters


# ═══════════════════════════════════════════════════════════════════════════════
# SERP FIELD READER
# ═══════════════════════════════════════════════════════════════════════════════

class SerpFieldReader:
    """
    Read Google's 'opinion' on a query.
    Output: role, shape, entity_regime, homogeneity.
    """
    
    def __init__(self):
        self.cache = {}
    
    def read(self, query: str) -> SerpField:
        """
        Analyze a query and return SERP field.
        In production: scrape SERP and analyze.
        Here: pattern-based heuristics + autocomplete signals.
        """
        if query in self.cache:
            return self.cache[query]
        
        normalized = query.lower().strip()
        
        # Detect role
        role, role_conf = self._detect_role(normalized)
        
        # Detect shape
        shape, shape_conf = self._detect_shape(normalized, role)
        
        # Detect entity regime (what entities are expected)
        entity_regime = self._detect_entity_regime(normalized)
        
        # Get PAA and related (from autocomplete as proxy)
        paa = self._get_paa_proxy(query)
        related = self._get_related_proxy(query)
        
        # Homogeneity (heuristic based on specificity)
        homogeneity = self._estimate_homogeneity(normalized, role)
        
        result = SerpField(
            query=query,
            role_primary=role,
            role_confidence=role_conf,
            shape_primary=shape,
            shape_confidence=shape_conf,
            entity_regime=entity_regime,
            homogeneity=homogeneity,
            confidence=(role_conf + shape_conf) / 2,
            paa_questions=paa,
            related_searches=related
        )
        
        self.cache[query] = result
        return result
    
    def _detect_role(self, text: str) -> Tuple[SerpRole, float]:
        """Detect what role Google expects."""
        
        if any(w in text for w in ["jämför", "vs", "eller", "bättre", "versus"]):
            return SerpRole.COMPARATOR, 0.85
        
        if any(w in text for w in ["bäst", "topp", "top", "lista", "ranking"]):
            return SerpRole.SELECTOR, 0.80
        
        if any(w in text for w in ["köp", "pris", "billig", "beställ", "handla"]):
            return SerpRole.SELLER, 0.85
        
        if any(w in text for w in ["problem", "fel", "funkar inte", "fixa", "lös"]):
            return SerpRole.TROUBLESHOOTER, 0.75
        
        if any(w in text for w in ["login", "logga in", "hemsida", "kontakt"]):
            return SerpRole.NAVIGATOR, 0.90
        
        # Default: educator
        return SerpRole.EDUCATOR, 0.60
    
    def _detect_shape(self, text: str, role: SerpRole) -> Tuple[SerpShape, float]:
        """Detect expected content shape."""
        
        if role == SerpRole.COMPARATOR:
            return SerpShape.COMPARISON_TABLE, 0.80
        
        if role == SerpRole.SELECTOR:
            return SerpShape.LISTICLE, 0.75
        
        if role == SerpRole.SELLER:
            return SerpShape.PRODUCT_PAGE, 0.70
        
        if any(w in text for w in ["hur", "how", "steg", "guide"]):
            return SerpShape.GUIDE, 0.75
        
        if any(w in text for w in ["vad är", "what is"]):
            return SerpShape.GUIDE, 0.70
        
        if any(w in text for w in ["video", "youtube"]):
            return SerpShape.VIDEO_FIRST, 0.80
        
        if any(w in text for w in ["forum", "diskussion", "reddit"]):
            return SerpShape.FORUM_QA, 0.70
        
        return SerpShape.GUIDE, 0.50
    
    def _detect_entity_regime(self, text: str) -> SerpEntityRegime:
        """Detect expected entities."""
        regime = SerpEntityRegime()
        
        words = text.split()
        
        # Extract potential entities (capitalized, nouns)
        for word in words:
            clean = word.strip(".,!?")
            if len(clean) > 2:
                # Add as dominant if it's a noun-like word
                if not any(clean.lower() == w for w in ["bäst", "hur", "vad", "var", "köp"]):
                    regime.dominant_entities.append(clean.title())
        
        # Remove duplicates
        regime.dominant_entities = list(set(regime.dominant_entities))[:5]
        
        return regime
    
    def _get_paa_proxy(self, query: str) -> List[str]:
        """Get PAA-like questions from autocomplete."""
        question_starters = ["hur", "vad", "varför", "när", "var"]
        paa = []
        for starter in question_starters[:2]:
            paa.append(f"{starter} {query}?")
        return paa
    
    def _get_related_proxy(self, query: str) -> List[str]:
        """Get related searches proxy."""
        return [f"{query} tips", f"{query} guide", f"bästa {query}"]
    
    def _estimate_homogeneity(self, text: str, role: SerpRole) -> float:
        """Estimate SERP homogeneity."""
        # More specific queries = more homogeneous SERPs
        word_count = len(text.split())
        
        if word_count >= 4:
            base = 0.75
        elif word_count >= 2:
            base = 0.55
        else:
            base = 0.35
        
        # Certain roles are more homogeneous
        if role in [SerpRole.NAVIGATOR, SerpRole.TROUBLESHOOTER]:
            base += 0.15
        
        return min(1.0, base)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class Pipeline:
    """
    Production-grade pipeline with:
    - Enhanced normalization (lemma_tokens, modifiers)
    - SERP Field Reader before Entity Extract
    - Entity Gravity calculation
    - Cluster Role classification
    """
    
    # Swedish modifiers for extraction
    MODIFIERS = {
        "bäst", "bästa", "billig", "billiga", "bra", "dyr", "dyra",
        "gratis", "online", "2024", "2025", "test", "recension",
        "jämför", "guide", "tips", "hur", "vad", "var"
    }
    
    def __init__(self):
        self.logger = logging.getLogger("PIPELINE")
        self.cache = {}
        self.serp_reader = SerpFieldReader()
        self.gravity_engine = EntityGravityEngine()
        self.role_classifier = ClusterRoleClassifier()
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 1: NORMALIZE (Enhanced)
    # ═══════════════════════════════════════════════════════════════════
    
    def normalize(self, keywords: List[str]) -> List[Keyword]:
        """Normalize with lemma_tokens and modifiers."""
        seen = set()
        result = []
        
        for kw in keywords:
            raw = kw.strip()
            if not raw:
                continue
            
            normalized = raw.lower()
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            if normalized in seen:
                continue
            seen.add(normalized)
            
            # Extract tokens and modifiers
            tokens = normalized.split()
            lemma_tokens = []
            modifiers = []
            
            for token in tokens:
                if token in self.MODIFIERS:
                    modifiers.append(token)
                else:
                    lemma_tokens.append(token)
            
            kw_id = self._hash_id(normalized)
            result.append(Keyword(
                id=kw_id,
                raw=raw,
                normalized=normalized,
                lemma_tokens=lemma_tokens,
                modifiers=modifiers,
                is_seed=True,
                source="user"
            ))
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 2: EXPAND
    # ═══════════════════════════════════════════════════════════════════
    
    def expand(self, keywords: List[Keyword], max_per: int = 8) -> List[Keyword]:
        """Expand with Google Autocomplete."""
        all_kw = list(keywords)
        seen = {kw.normalized for kw in keywords}
        
        for kw in keywords:
            suggestions = self._fetch_autocomplete(kw.normalized)
            for suggestion in suggestions[:max_per]:
                norm = suggestion.lower().strip()
                if norm in seen:
                    continue
                seen.add(norm)
                
                tokens = norm.split()
                lemma = [t for t in tokens if t not in self.MODIFIERS]
                mods = [t for t in tokens if t in self.MODIFIERS]
                
                all_kw.append(Keyword(
                    id=self._hash_id(norm),
                    raw=suggestion,
                    normalized=norm,
                    lemma_tokens=lemma,
                    modifiers=mods,
                    is_seed=False,
                    source="autocomplete"
                ))
        
        return all_kw
    
    def _fetch_autocomplete(self, query: str) -> List[str]:
        """Fetch Google Autocomplete."""
        cache_key = f"ac:{query}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            encoded = urllib.parse.quote(query)
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={encoded}&hl=sv"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                suggestions = data[1] if len(data) > 1 else []
                self.cache[cache_key] = suggestions
                return suggestions
        except Exception as e:
            self.logger.warning(f"Autocomplete failed: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 3: SERP FIELD READ (Before Entity Extract!)
    # ═══════════════════════════════════════════════════════════════════
    
    def read_serp_fields(self, keywords: List[Keyword], sample_size: int = 10) -> Dict[str, SerpField]:
        """Read SERP fields for top keywords."""
        serp_fields = {}
        
        # Prioritize seed keywords + top expanded
        seeds = [kw for kw in keywords if kw.is_seed]
        expanded = [kw for kw in keywords if not kw.is_seed][:sample_size]
        to_analyze = seeds + expanded
        
        for kw in to_analyze:
            serp = self.serp_reader.read(kw.normalized)
            serp_fields[kw.id] = serp
            kw.serp_analyzed = True
        
        return serp_fields
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 4: INTENT + TASK_TYPE
    # ═══════════════════════════════════════════════════════════════════
    
    def classify_intent_and_task(self, keywords: List[Keyword]) -> List[Keyword]:
        """Classify both intent and task_type."""
        for kw in keywords:
            kw.intent = self._detect_intent(kw.normalized)
            kw.task_type = self._detect_task_type(kw.normalized, kw.modifiers)
        return keywords
    
    def _detect_intent(self, text: str) -> Intent:
        if any(w in text for w in ["köp", "pris", "billig", "beställ"]):
            return Intent.TRANSACTIONAL
        if any(w in text for w in ["bäst", "test", "recension", "jämför"]):
            return Intent.COMMERCIAL
        if any(w in text for w in ["vad är", "hur", "varför", "guide"]):
            return Intent.INFORMATIONAL
        if any(w in text for w in ["login", "kontakt", "hemsida"]):
            return Intent.NAVIGATIONAL
        if any(w in text for w in ["nära", "stockholm", "göteborg"]):
            return Intent.LOCAL
        return Intent.MIXED
    
    def _detect_task_type(self, text: str, modifiers: List[str]) -> TaskType:
        if "jämför" in text or "vs" in text:
            return TaskType.COMPARISON
        if "recension" in text:
            return TaskType.REVIEW
        if any(w in modifiers for w in ["bäst", "bästa"]):
            return TaskType.BEST_OF
        if "pris" in text or "kosta" in text:
            return TaskType.PRICE
        if "köp" in text or "beställ" in text:
            return TaskType.BUY
        if "hur" in text:
            return TaskType.HOW_TO
        if "vad är" in text:
            return TaskType.DEFINITION
        if "guide" in modifiers:
            return TaskType.GUIDE
        if any(w in text for w in ["problem", "fel", "funkar inte"]):
            return TaskType.TROUBLESHOOT
        return TaskType.OTHER
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 5: ENTITY EXTRACT (SERP-informed)
    # ═══════════════════════════════════════════════════════════════════
    
    def extract_entities(
        self,
        keywords: List[Keyword],
        serp_fields: Dict[str, SerpField]
    ) -> Tuple[List[Keyword], Dict[str, Entity], Dict[str, List[str]]]:
        """Extract entities, informed by SERP expectations."""
        entities = {}
        kw_entity_map = defaultdict(list)
        
        # Collect SERP-expected entities
        serp_expected = set()
        for serp in serp_fields.values():
            for e in serp.entity_regime.dominant_entities:
                serp_expected.add(e.lower())
        
        for kw in keywords:
            extracted = self._extract_from_keyword(kw, serp_expected)
            
            for entity_name, entity_type in extracted:
                entity_id = self._hash_id(entity_name.lower())
                
                if entity_id not in entities:
                    entities[entity_id] = Entity(
                        id=entity_id,
                        name=entity_name,
                        type=entity_type
                    )
                
                kw_entity_map[kw.id].append(entity_id)
        
        return keywords, entities, kw_entity_map
    
    def _extract_from_keyword(self, kw: Keyword, serp_expected: Set[str]) -> List[Tuple[str, EntityType]]:
        """Extract entities from keyword."""
        entities = []
        
        # Use lemma tokens (excluding modifiers)
        for token in kw.lemma_tokens:
            if len(token) > 2:
                # Check if SERP expects this
                if token.lower() in serp_expected:
                    entities.append((token.title(), EntityType.CONCEPT))
                elif token[0].isupper() if kw.raw else False:
                    entities.append((token, EntityType.BRAND))
                else:
                    entities.append((token.title(), EntityType.CONCEPT))
        
        return entities
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 6: GRAPH BUILD
    # ═══════════════════════════════════════════════════════════════════
    
    def build_graph(
        self,
        keywords: List[Keyword],
        entities: Dict[str, Entity],
        kw_entity_map: Dict[str, List[str]]
    ) -> List[Edge]:
        """Build relationship graph."""
        edges = []
        
        # Keyword → Entity (IS_ABOUT)
        for kw in keywords:
            for eid in kw_entity_map.get(kw.id, []):
                edges.append(Edge(kw.id, eid, EdgeType.IS_ABOUT, 1.0))
        
        # Entity ↔ Entity (CO_OCCUR)
        entity_kws = defaultdict(set)
        for kw_id, eids in kw_entity_map.items():
            for eid in eids:
                entity_kws[eid].add(kw_id)
        
        elist = list(entities.keys())
        for i, e1 in enumerate(elist):
            for e2 in elist[i+1:]:
                shared = entity_kws[e1] & entity_kws[e2]
                if shared:
                    weight = len(shared) / max(len(entity_kws[e1]), len(entity_kws[e2]))
                    edges.append(Edge(e1, e2, EdgeType.CO_OCCUR, weight))
        
        # Keyword ↔ Keyword (SAME_INTENT)
        intent_groups = defaultdict(list)
        for kw in keywords:
            if kw.intent != Intent.MIXED:
                intent_groups[kw.intent].append(kw)
        
        for intent, kw_list in intent_groups.items():
            for i, kw1 in enumerate(kw_list[:15]):
                for kw2 in kw_list[i+1:15]:
                    edges.append(Edge(kw1.id, kw2.id, EdgeType.SAME_INTENT, 0.5))
        
        return edges
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 7: CLUSTER (Dual)
    # ═══════════════════════════════════════════════════════════════════
    
    def cluster_dual(
        self,
        keywords: List[Keyword],
        entities: Dict[str, Entity],
        kw_entity_map: Dict[str, List[str]]
    ) -> Dict[str, Cluster]:
        """Dual clustering: intent + entity-neighborhood."""
        clusters = {}
        
        # A) Intent Clustering
        intent_groups = defaultdict(list)
        for kw in keywords:
            intent_groups[kw.intent].append(kw)
        
        for intent, kw_list in intent_groups.items():
            if not kw_list:
                continue
            
            cid = f"intent_{intent.value}"
            
            # Find primary entity
            entity_counts = defaultdict(int)
            for kw in kw_list:
                for eid in kw_entity_map.get(kw.id, []):
                    entity_counts[eid] += 1
            
            primary = max(entity_counts, key=entity_counts.get) if entity_counts else None
            
            # Dominant task_type
            task_counts = defaultdict(int)
            for kw in kw_list:
                task_counts[kw.task_type] += 1
            dom_task = max(task_counts, key=task_counts.get) if task_counts else TaskType.OTHER
            
            clusters[cid] = Cluster(
                id=cid,
                name=f"{intent.value.title()} Cluster",
                keywords=[kw.id for kw in kw_list],
                primary_entity_id=primary,
                secondary_entity_ids=list(entity_counts.keys())[:5],
                intent=intent,
                task_type=dom_task,
                total_volume=sum(kw.volume for kw in kw_list)
            )
        
        # B) Entity-Neighborhood Clustering
        for eid, entity in entities.items():
            related = [kw for kw in keywords if eid in kw_entity_map.get(kw.id, [])]
            if len(related) < 2:
                continue
            
            cid = f"entity_{eid}"
            intent_set = {kw.intent for kw in related}
            
            clusters[cid] = Cluster(
                id=cid,
                name=f"{entity.name} Cluster",
                keywords=[kw.id for kw in related],
                primary_entity_id=eid,
                intent=Intent.MIXED if len(intent_set) > 1 else list(intent_set)[0],
                total_volume=sum(kw.volume for kw in related)
            )
        
        return clusters
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 8: SCORE (Gravity + Role)
    # ═══════════════════════════════════════════════════════════════════
    
    def score_all(
        self,
        entities: Dict[str, Entity],
        clusters: Dict[str, Cluster],
        edges: List[Edge],
        serp_fields: Dict[str, SerpField]
    ) -> Tuple[Dict[str, Entity], Dict[str, Cluster]]:
        """Calculate Entity Gravity and Cluster Roles."""
        
        # Entity Gravity
        entities = self.gravity_engine.calculate_gravity(entities, clusters, edges, serp_fields)
        
        # Cluster Roles
        clusters = self.role_classifier.classify(clusters, entities, edges)
        
        return entities, clusters
    
    # ═══════════════════════════════════════════════════════════════════
    # STEP 9: GAP ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    def analyze_gaps(
        self,
        entities: Dict[str, Entity],
        clusters: Dict[str, Cluster],
        serp_fields: Dict[str, SerpField]
    ) -> List[GapCluster]:
        """Find missing clusters for coverage."""
        gaps = []
        
        for eid, entity in entities.items():
            if not entity.is_dominant:
                continue
            
            # Check if entity has clusters for all major intents
            entity_intents = set()
            for cluster in clusters.values():
                if cluster.primary_entity_id == eid:
                    entity_intents.add(cluster.intent)
            
            # Gap: Missing Commercial
            if Intent.COMMERCIAL not in entity_intents:
                gaps.append(GapCluster(
                    suggested_name=f"Commercial cluster for {entity.name}",
                    suggested_keywords=[f"bästa {entity.name.lower()}", f"{entity.name.lower()} test"],
                    target_entity_id=eid,
                    priority_score=entity.semantic_mass * 0.8,
                    reason="Missing commercial intent coverage for dominant entity"
                ))
            
            # Gap: Missing Informational
            if Intent.INFORMATIONAL not in entity_intents:
                gaps.append(GapCluster(
                    suggested_name=f"Informational cluster for {entity.name}",
                    suggested_keywords=[f"vad är {entity.name.lower()}", f"hur fungerar {entity.name.lower()}"],
                    target_entity_id=eid,
                    priority_score=entity.semantic_mass * 0.6,
                    reason="Missing informational content for entity"
                ))
        
        gaps.sort(key=lambda x: -x.priority_score)
        return gaps
    
    # ═══════════════════════════════════════════════════════════════════
    # MAIN RUN
    # ═══════════════════════════════════════════════════════════════════
    
    def run(self, seed_keywords: List[str], expand: bool = True) -> AnalysisResult:
        """Run full pipeline."""
        pid = self._hash_id("_".join(seed_keywords[:3]))
        
        # 1. Normalize
        keywords = self.normalize(seed_keywords)
        
        # 2. Expand
        if expand:
            keywords = self.expand(keywords)
        
        # 3. SERP Field Read
        serp_fields = self.read_serp_fields(keywords)
        
        # 4. Intent + TaskType
        keywords = self.classify_intent_and_task(keywords)
        
        # 5. Entity Extract
        keywords, entities, kw_entity_map = self.extract_entities(keywords, serp_fields)
        
        # 6. Graph Build
        edges = self.build_graph(keywords, entities, kw_entity_map)
        
        # 7. Dual Cluster
        clusters = self.cluster_dual(keywords, entities, kw_entity_map)
        
        # 8. Score
        entities, clusters = self.score_all(entities, clusters, edges, serp_fields)
        
        # 9. Gap Analysis
        gaps = self.analyze_gaps(entities, clusters, serp_fields)
        
        return AnalysisResult(
            project_id=pid,
            created_at=datetime.now().isoformat(),
            seed_keywords=seed_keywords,
            keywords={kw.id: kw for kw in keywords},
            entities=entities,
            clusters=clusters,
            edges=edges,
            serp_fields=serp_fields,
            gaps=gaps,
            stats={
                "total_keywords": len(keywords),
                "seed_count": len([k for k in keywords if k.is_seed]),
                "entity_count": len(entities),
                "cluster_count": len(clusters),
                "edge_count": len(edges),
                "gap_count": len(gaps),
                "dominant_entities": [e.name for e in entities.values() if e.is_dominant],
                "bridge_entities": [e.name for e in entities.values() if e.is_bridge]
            }
        )
    
    def _hash_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW GENERATORS (Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

class ViewGenerator:
    """Generate views with enhanced data."""
    
    def galaxy_view(self, result: AnalysisResult) -> Dict:
        """Galaxy with gravity and role info."""
        nodes = []
        links = []
        
        # Keywords
        for kid, kw in result.keywords.items():
            nodes.append({
                "id": kid,
                "label": kw.raw,
                "type": "keyword",
                "intent": kw.intent.value,
                "taskType": kw.task_type.value,
                "isSeed": kw.is_seed,
                "size": 8 if kw.is_seed else 5
            })
        
        # Entities with gravity
        for eid, entity in result.entities.items():
            nodes.append({
                "id": eid,
                "label": entity.name,
                "type": "entity",
                "entityType": entity.type.value,
                "semanticMass": round(entity.semantic_mass, 3),
                "isDominant": entity.is_dominant,
                "isBridge": entity.is_bridge,
                "gravityComponents": {
                    "cluster": round(entity.gravity.cluster_mass, 2),
                    "bridge": round(entity.gravity.bridge_mass, 2),
                    "centrality": round(entity.gravity.centrality_mass, 2),
                    "serp": round(entity.gravity.serp_mass, 2)
                },
                "size": 12 + entity.semantic_mass * 20
            })
        
        # Clusters with role
        for cid, cluster in result.clusters.items():
            if cluster.role == ClusterRole.BRIDGE:
                nodes.append({
                    "id": cid,
                    "label": cluster.name,
                    "type": "cluster",
                    "role": cluster.role.value,
                    "roleConfidence": round(cluster.role_confidence, 2),
                    "reasons": [r.explanation for r in cluster.role_reasons],
                    "size": 10
                })
        
        # Edges
        for edge in result.edges:
            links.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "weight": edge.weight
            })
        
        return {"nodes": nodes, "links": links, "stats": result.stats}
    
    def serp_alignment_view(self, result: AnalysisResult) -> Dict:
        """SERP Alignment view."""
        alignments = []
        
        for kw_id, serp in result.serp_fields.items():
            kw = result.keywords.get(kw_id)
            alignments.append({
                "keyword": kw.raw if kw else serp.query,
                "role": serp.role_primary.value,
                "roleConfidence": round(serp.role_confidence * 100),
                "shape": serp.shape_primary.value,
                "shapeConfidence": round(serp.shape_confidence * 100),
                "homogeneity": round(serp.homogeneity * 100),
                "requiredEntities": serp.entity_regime.required_entities,
                "dominantEntities": serp.entity_regime.dominant_entities,
                "paaQuestions": serp.paa_questions
            })
        
        return {"alignments": alignments}
    
    def gap_view(self, result: AnalysisResult) -> Dict:
        """Gap Analysis view."""
        gaps = []
        for gap in result.gaps:
            entity = result.entities.get(gap.target_entity_id)
            gaps.append({
                "name": gap.suggested_name,
                "keywords": gap.suggested_keywords,
                "targetEntity": entity.name if entity else gap.target_entity_id,
                "priority": round(gap.priority_score, 2),
                "reason": gap.reason
            })
        return {"gaps": gaps}


# ═══════════════════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════════════════

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Entity & Cluster Intelligence", version="3.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    
    pipeline = Pipeline()
    views = ViewGenerator()
    
    # Storage (in-memory for demo, would be DB in production)
    _imports: Dict[str, Any] = {}
    _attributions: Dict[str, Any] = {}
    
    class AnalyzeRequest(BaseModel):
        keywords: List[str]
        expand: bool = True
    
    class ImportRequest(BaseModel):
        file_content: str
        domain: str
        label: str = "mine"  # mine | competitor
        project_id: str = "default"
    
    class AttributionRequest(BaseModel):
        import_id: str
        project_id: str = "default"
    
    class GapRequest(BaseModel):
        mine_domain: str
        competitor_domains: List[str]
        entity_id: Optional[str] = None
    
    class DominanceRequest(BaseModel):
        focus_keyword: str
        mine_domain: str
        include_cluster_siblings: bool = True
    
    @app.post("/analyze/full")
    async def analyze_full(request: AnalyzeRequest):
        result = pipeline.run(request.keywords, request.expand)
        return {
            "status": "success",
            "galaxy": views.galaxy_view(result),
            "serpAlignment": views.serp_alignment_view(result),
            "gaps": views.gap_view(result),
            "stats": result.stats
        }
    
    @app.post("/imports")
    async def create_import(request: ImportRequest):
        """Upload and normalize Ahrefs/keyword data."""
        try:
            from core.normalizers.ahrefs_normalizer import process_ahrefs_upload
            
            result = process_ahrefs_upload(
                file_content=request.file_content,
                domain=request.domain,
                label=request.label,
                project_id=request.project_id
            )
            
            if result.success:
                _imports[result.import_id] = result.canonical_data
                return {
                    "status": "success",
                    "import_id": result.import_id,
                    "report_type": result.report_type,
                    "row_count": len(result.canonical_data.rows) if result.canonical_data else 0,
                    "warnings": result.warnings
                }
            else:
                raise HTTPException(400, result.error)
        except ImportError:
            raise HTTPException(500, "Normalizer not available")
    
    @app.get("/imports/{import_id}")
    async def get_import(import_id: str):
        """Get import data."""
        if import_id not in _imports:
            raise HTTPException(404, "Import not found")
        return {"status": "success", "data": _imports[import_id]}
    
    @app.post("/attribution/run")
    async def run_attribution(request: AttributionRequest):
        """Run attribution pipeline on import."""
        if request.import_id not in _imports:
            raise HTTPException(404, "Import not found")
        
        try:
            from pipelines.attribution_pipeline import run_attribution
            
            import_data = _imports[request.import_id]
            job = run_attribution(import_data.rows, request.project_id)
            
            _attributions[job.job_id] = job
            
            return {
                "status": "success",
                "job_id": job.job_id,
                "stage": job.stage.value,
                "result_count": len(job.results),
                "errors": job.errors
            }
        except ImportError:
            raise HTTPException(500, "Attribution pipeline not available")
    
    @app.get("/attribution/{job_id}")
    async def get_attribution(job_id: str):
        """Get attribution results."""
        if job_id not in _attributions:
            raise HTTPException(404, "Job not found")
        
        job = _attributions[job_id]
        return {
            "status": "success",
            "job_id": job.job_id,
            "stage": job.stage.value,
            "results": [
                {
                    "keyword": r.keyword,
                    "intent": r.attribution.intent.value,
                    "intent_confidence": r.attribution.intent_confidence,
                    "task_archetype": r.attribution.task_archetype.value,
                    "primary_entity_id": r.attribution.primary_entity_id,
                    "entity_confidence": r.attribution.entity_confidence
                }
                for r in job.results
            ]
        }
    
    @app.post("/gaps/entities")
    async def get_entity_gaps(request: GapRequest):
        """Get entity gaps between mine and competitors."""
        try:
            from analyzers.gap_analyzer import get_entity_gaps as _get_gaps, RankData
            
            # In production: gather attributed keywords and rank data from DB
            # For demo: return mock
            return {
                "status": "success",
                "gaps": [],
                "note": "Provide attributed_keywords and rank_data in production"
            }
        except ImportError:
            raise HTTPException(500, "Gap analyzer not available")
    
    @app.post("/dominance")
    async def get_dominance(request: DominanceRequest):
        """Get dominance lens for focus keyword."""
        try:
            from analyzers.dominance_lens import get_dominance_lens as _get_lens
            
            # In production: gather data from DB
            return {
                "status": "success",
                "focus_keyword": request.focus_keyword,
                "note": "Provide attributed_keywords and rank_data in production"
            }
        except ImportError:
            raise HTTPException(500, "Dominance lens not available")
    
    @app.get("/health")
    async def health():
        return {"status": "operational", "version": "3.0.0", "phase": "1.5"}


# ═══════════════════════════════════════════════════════════════════════════════
# CLI DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🌌 ENTITY & CLUSTER INTELLIGENCE v3.0 🌌")
    print("   Production-Grade Pipeline\n")
    
    seeds = ["elgitarr", "bästa elgitarr", "köpa elgitarr"]
    
    pipe = Pipeline()
    result = pipe.run(seeds, expand=True)
    
    print(f"[STATS]")
    print(f"  Keywords: {result.stats['total_keywords']}")
    print(f"  Entities: {result.stats['entity_count']}")
    print(f"  Clusters: {result.stats['cluster_count']}")
    print(f"  Gaps: {result.stats['gap_count']}")
    
    print(f"\n[DOMINANT ENTITIES]")
    for name in result.stats['dominant_entities']:
        print(f"  ⭐ {name}")
    
    print(f"\n[BRIDGE ENTITIES]")
    for name in result.stats['bridge_entities']:
        print(f"  🔗 {name}")
    
    print(f"\n[ENTITY GRAVITY]")
    for eid, e in list(result.entities.items())[:5]:
        print(f"  {e.name}: mass={e.semantic_mass:.3f} (C:{e.gravity.cluster_mass:.2f} B:{e.gravity.bridge_mass:.2f})")
    
    print(f"\n[CLUSTER ROLES]")
    for cid, c in list(result.clusters.items())[:5]:
        print(f"  {c.role.value.upper()}: {c.name} (conf={c.role_confidence:.2f})")
    
    print(f"\n[GAPS]")
    for gap in result.gaps[:3]:
        print(f"  ❗ {gap.suggested_name}")
        print(f"     Reason: {gap.reason}")
    
    print(f"\n✨ API: uvicorn engine:app --reload --port 8001")
