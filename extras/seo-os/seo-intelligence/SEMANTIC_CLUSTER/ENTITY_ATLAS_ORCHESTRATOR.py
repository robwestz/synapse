#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗███╗   ██╗████████╗██╗████████╗██╗   ██╗                          ║
║   ██╔════╝████╗  ██║╚══██╔══╝██║╚══██╔══╝╚██╗ ██╔╝                          ║
║   █████╗  ██╔██╗ ██║   ██║   ██║   ██║    ╚████╔╝                           ║
║   ██╔══╝  ██║╚██╗██║   ██║   ██║   ██║     ╚██╔╝                            ║
║   ███████╗██║ ╚████║   ██║   ██║   ██║      ██║                             ║
║   ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝   ╚═╝      ╚═╝                             ║
║                                                                              ║
║              █████╗ ████████╗██╗      █████╗ ███████╗                       ║
║             ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝                       ║
║             ███████║   ██║   ██║     ███████║███████╗                       ║
║             ██╔══██║   ██║   ██║     ██╔══██║╚════██║                       ║
║             ██║  ██║   ██║   ███████╗██║  ██║███████║                       ║
║             ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝                       ║
║                                                                              ║
║              ENTITY & CLUSTER INTELLIGENCE PLATFORM                          ║
║                          BUILD ORCHESTRATOR                                  ║
║                                                                              ║
║   "Evidence-first. Deterministic. World-class."                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

This orchestrator:
1. Reads BUILD_CONTRACT.json to know current state
2. Executes the next pending item
3. Updates BUILD_CONTRACT.json with progress
4. Never loses track even 50,000 tokens in

Run: python ENTITY_ATLAS_ORCHESTRATOR.py [--phase PHASE] [--item ITEM] [--all]
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
CONTRACT_FILE = BASE_DIR / "BUILD_CONTRACT.json"
SPEC_FILE = BASE_DIR / "ENTITY_ATLAS_SPEC.md"


class ItemStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


@dataclass
class BuildItem:
    id: str
    name: str
    status: ItemStatus
    file: Optional[str] = None


@dataclass
class BuildPhase:
    name: str
    status: ItemStatus
    items: List[BuildItem]


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRACT MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ContractManager:
    """Manages the BUILD_CONTRACT.json state file."""
    
    def __init__(self):
        self.contract: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load contract from disk."""
        if CONTRACT_FILE.exists():
            with open(CONTRACT_FILE, 'r', encoding='utf-8') as f:
                self.contract = json.load(f)
        else:
            raise FileNotFoundError(f"Contract file not found: {CONTRACT_FILE}")
    
    def save(self):
        """Save contract to disk."""
        with open(CONTRACT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.contract, f, indent=2)
    
    def get_current_phase(self) -> str:
        return self.contract.get("current_phase", "killer_feature")
    
    def get_current_item(self) -> str:
        return self.contract.get("current_item", "K1")
    
    def get_next_pending_item(self) -> Optional[tuple]:
        """Find the next PENDING item across all phases."""
        phase_order = ["foundation", "killer_feature", "entity_intelligence", 
                       "gap_pro", "professional", "serp_validation"]
        
        for phase_name in phase_order:
            phase = self.contract["phases"].get(phase_name, {})
            for item in phase.get("items", []):
                if item["status"] == "PENDING":
                    return (phase_name, item)
        
        return None
    
    def mark_item_status(self, phase_name: str, item_id: str, status: str):
        """Update an item's status."""
        phase = self.contract["phases"].get(phase_name, {})
        for item in phase.get("items", []):
            if item["id"] == item_id:
                item["status"] = status
                break
        
        # Update current pointers
        self.contract["current_phase"] = phase_name
        self.contract["current_item"] = item_id
        
        # Check if phase is complete
        all_complete = all(i["status"] == "COMPLETE" for i in phase.get("items", []))
        if all_complete:
            phase["status"] = "COMPLETE"
        elif any(i["status"] in ("IN_PROGRESS", "COMPLETE") for i in phase.get("items", [])):
            phase["status"] = "IN_PROGRESS"
        
        self.save()
    
    def add_created_file(self, filepath: str):
        """Track a newly created file."""
        files = self.contract.get("files_created", [])
        if filepath not in files:
            files.append(filepath)
            self.contract["files_created"] = files
            self.save()
    
    def get_hard_rules(self) -> List[str]:
        """Get the hard rules for validation."""
        return self.contract.get("hard_rules", [])
    
    def get_quality_gates(self) -> Dict[str, float]:
        """Get quality gate thresholds."""
        return self.contract.get("quality_gates", {})


# ═══════════════════════════════════════════════════════════════════════════════
# ITEM BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

class ItemBuilder:
    """Builds individual items. Each item has its own build method."""
    
    def __init__(self, contract: ContractManager):
        self.contract = contract
        self.base_dir = BASE_DIR
    
    async def build_item(self, phase_name: str, item: Dict) -> bool:
        """Build a specific item."""
        item_id = item["id"]
        method_name = f"_build_{item_id.lower()}"
        
        if hasattr(self, method_name):
            print(f"\n  [BUILD] {item['name']} ({item_id})")
            self.contract.mark_item_status(phase_name, item_id, "IN_PROGRESS")
            
            try:
                method = getattr(self, method_name)
                await method(item)
                self.contract.mark_item_status(phase_name, item_id, "COMPLETE")
                print(f"  [✓] {item['name']} COMPLETE")
                return True
            except Exception as e:
                self.contract.mark_item_status(phase_name, item_id, "FAILED")
                print(f"  [✗] {item['name']} FAILED: {e}")
                return False
        else:
            print(f"  [?] No builder for {item_id}, marking as TODO")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KILLER FEATURE BUILDERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def _build_k1(self, item: Dict):
        """Build canonical types - already done."""
        filepath = self.base_dir / "core" / "canonical_types.py"
        if filepath.exists():
            self.contract.add_created_file("core/canonical_types.py")
        else:
            raise FileNotFoundError("canonical_types.py not found")
    
    async def _build_k2(self, item: Dict):
        """Build Ahrefs normalizer - already done."""
        filepath = self.base_dir / "core" / "normalizers" / "ahrefs_normalizer.py"
        if filepath.exists():
            self.contract.add_created_file("core/normalizers/ahrefs_normalizer.py")
        else:
            raise FileNotFoundError("ahrefs_normalizer.py not found")
    
    async def _build_k3(self, item: Dict):
        """Build Attribution Pipeline."""
        filepath = self.base_dir / "pipelines" / "attribution_pipeline.py"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        content = self._generate_attribution_pipeline()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create __init__.py
        init_file = filepath.parent / "__init__.py"
        with open(init_file, 'w') as f:
            f.write("from .attribution_pipeline import AttributionPipeline, run_attribution\n")
        
        self.contract.add_created_file("pipelines/attribution_pipeline.py")
    
    async def _build_k4(self, item: Dict):
        """Build Gap Analyzer."""
        filepath = self.base_dir / "analyzers" / "gap_analyzer.py"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        content = self._generate_gap_analyzer()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create __init__.py
        init_file = filepath.parent / "__init__.py"
        with open(init_file, 'w') as f:
            f.write("from .gap_analyzer import GapAnalyzer, get_entity_gaps\n")
        
        self.contract.add_created_file("analyzers/gap_analyzer.py")
    
    async def _build_k5(self, item: Dict):
        """Build Dominance Lens."""
        filepath = self.base_dir / "analyzers" / "dominance_lens.py"
        
        content = self._generate_dominance_lens()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.contract.add_created_file("analyzers/dominance_lens.py")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CODE GENERATORS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _generate_attribution_pipeline(self) -> str:
        return '''"""
Attribution Pipeline - Assigns Intent, Entity, Cluster to keywords.
State machine: INTAKE → NORMALIZE → ATTRIBUTION → STORE → FINALIZED
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import hashlib

import sys
sys.path.insert(0, str(__file__).rsplit("pipelines", 1)[0])

from core.canonical_types import (
    Intent, TaskArchetype, ClusterRole, EntityType,
    AttributedKeyword, Attribution, Evidence, EvidenceSignal,
    EvidenceClaim, EvidenceClaimType, EvidenceProvenance, EvidenceScore,
    EvidenceStatus, ProvenanceLayer, ImportRow, generate_keyword_id
)


class PipelineStage(str, Enum):
    INTAKE = "INTAKE"
    NORMALIZE = "NORMALIZE"
    ATTRIBUTION = "ATTRIBUTION"
    STORE = "STORE"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"


@dataclass
class PipelineJob:
    job_id: str
    import_id: str
    stage: PipelineStage = PipelineStage.INTAKE
    results: List[AttributedKeyword] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# INTENT INFERENCE MODEL
# ═══════════════════════════════════════════════════════════════════════════════

INTENT_RULES = {
    Intent.COMMERCIAL: {
        "modifiers": ["bästa", "bäst", "test", "recension", "review", "jämför", 
                      "vs", "versus", "alternativ", "top", "ranking"],
        "weight": 0.8
    },
    Intent.TRANS: {
        "modifiers": ["köpa", "köp", "pris", "billig", "rea", "rabatt", "beställ",
                      "prenumerera", "signup", "registrera", "boka"],
        "weight": 0.9
    },
    Intent.NAV: {
        "modifiers": ["logga in", "login", "kundtjänst", "kontakt", "support",
                      "app", "download", "ladda ner"],
        "weight": 0.85
    },
    Intent.LOCAL: {
        "modifiers": ["nära mig", "i stockholm", "i göteborg", "i malmö", 
                      "öppettider", "adress", "telefon"],
        "weight": 0.9
    },
    Intent.INFO: {
        "modifiers": ["vad är", "hur", "varför", "när", "guide", "tips",
                      "förklaring", "betydelse", "definition"],
        "weight": 0.7
    }
}

TASK_ARCHETYPE_RULES = {
    TaskArchetype.DEFINITION: ["vad är", "definition", "betydelse", "meaning"],
    TaskArchetype.GUIDE: ["hur", "guide", "steg för steg", "tutorial"],
    TaskArchetype.COMPARE: ["vs", "versus", "jämför", "skillnad", "eller"],
    TaskArchetype.REVIEW: ["recension", "review", "betyg", "omdöme"],
    TaskArchetype.PRICE: ["pris", "kostnad", "billig", "budget"],
    TaskArchetype.BUY: ["köpa", "köp", "beställ", "handla"],
    TaskArchetype.SIGNUP: ["registrera", "signup", "skapa konto", "prenumerera"],
    TaskArchetype.LOGIN: ["logga in", "login", "mitt konto"],
    TaskArchetype.BRAND: []  # Detected via entity, not modifier
}


def infer_intent(keyword: str) -> tuple[Intent, float, List[EvidenceSignal]]:
    """Infer intent from keyword using rule-based classifier."""
    keyword_lower = keyword.lower()
    signals = []
    scores = {intent: 0.0 for intent in Intent}
    
    for intent, rules in INTENT_RULES.items():
        for modifier in rules["modifiers"]:
            if modifier in keyword_lower:
                scores[intent] += rules["weight"]
                signals.append(EvidenceSignal(
                    signal_type="modifier_rule",
                    value=f"contains('{modifier}') => {intent.value}",
                    weight=rules["weight"]
                ))
    
    # Default to INFO if no strong signal
    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]
    
    if best_score < 0.5:
        best_intent = Intent.INFO
        best_score = 0.6
        signals.append(EvidenceSignal(
            signal_type="default_rule",
            value="no_strong_signal => INFO",
            weight=0.6
        ))
    
    return best_intent, min(best_score, 1.0), signals


def infer_task_archetype(keyword: str, intent: Intent) -> tuple[TaskArchetype, List[EvidenceSignal]]:
    """Infer task archetype from keyword."""
    keyword_lower = keyword.lower()
    signals = []
    
    for archetype, patterns in TASK_ARCHETYPE_RULES.items():
        for pattern in patterns:
            if pattern in keyword_lower:
                signals.append(EvidenceSignal(
                    signal_type="archetype_pattern",
                    value=f"contains('{pattern}') => {archetype.value}",
                    weight=0.7
                ))
                return archetype, signals
    
    # Default based on intent
    default_map = {
        Intent.INFO: TaskArchetype.GUIDE,
        Intent.COMMERCIAL: TaskArchetype.COMPARE,
        Intent.TRANS: TaskArchetype.BUY,
        Intent.NAV: TaskArchetype.BRAND,
        Intent.LOCAL: TaskArchetype.OTHER
    }
    archetype = default_map.get(intent, TaskArchetype.OTHER)
    signals.append(EvidenceSignal(
        signal_type="intent_fallback",
        value=f"intent={intent.value} => {archetype.value}",
        weight=0.5
    ))
    return archetype, signals


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTION MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def extract_entities(keyword: str) -> tuple[str, EntityType, float, List[EvidenceSignal]]:
    """Extract primary entity from keyword (simplified heuristic)."""
    tokens = keyword.lower().split()
    signals = []
    
    # Remove common modifiers to find head term
    modifiers = {"bästa", "billig", "köpa", "hur", "vad", "är", "i", "för", "med", "utan"}
    content_tokens = [t for t in tokens if t not in modifiers]
    
    if not content_tokens:
        content_tokens = tokens
    
    # Head term is typically the last content word (Swedish pattern)
    head_term = content_tokens[-1] if content_tokens else tokens[-1]
    
    # Simple type heuristic
    entity_type = EntityType.CONCEPT
    if any(brand_signal in keyword.lower() for brand_signal in ["apple", "samsung", "google", "nike"]):
        entity_type = EntityType.BRAND
    elif any(product_signal in keyword.lower() for product_signal in ["telefon", "dator", "bil", "gitarr"]):
        entity_type = EntityType.PRODUCT
    
    signals.append(EvidenceSignal(
        signal_type="head_term_extraction",
        value=f"head_term='{head_term}'",
        weight=0.6
    ))
    
    confidence = 0.65  # Heuristic extraction has moderate confidence
    
    return head_term.capitalize(), entity_type, confidence, signals


# ═══════════════════════════════════════════════════════════════════════════════
# ATTRIBUTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

class AttributionPipeline:
    """The main attribution pipeline."""
    
    def __init__(self):
        self.evidence_counter = 0
    
    def _generate_evidence_id(self) -> str:
        self.evidence_counter += 1
        return f"ev_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.evidence_counter:04d}"
    
    def run(self, rows: List[ImportRow], project_id: str = "default") -> PipelineJob:
        """Run the attribution pipeline on import rows."""
        job_id = f"job_{hashlib.sha1(f'{project_id}|{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        job = PipelineJob(job_id=job_id, import_id=project_id, started_at=datetime.now())
        
        try:
            # STAGE: INTAKE
            job.stage = PipelineStage.INTAKE
            if not rows:
                raise ValueError("No rows to process")
            
            # STAGE: NORMALIZE (already done by normalizer)
            job.stage = PipelineStage.NORMALIZE
            
            # STAGE: ATTRIBUTION
            job.stage = PipelineStage.ATTRIBUTION
            
            for row in rows:
                attributed = self._attribute_keyword(row)
                job.results.append(attributed)
            
            # STAGE: STORE (would persist to DB in production)
            job.stage = PipelineStage.STORE
            
            # STAGE: FINALIZED
            job.stage = PipelineStage.FINALIZED
            job.finished_at = datetime.now()
            
        except Exception as e:
            job.stage = PipelineStage.FAILED
            job.errors.append(str(e))
            job.finished_at = datetime.now()
        
        return job
    
    def _attribute_keyword(self, row: ImportRow) -> AttributedKeyword:
        """Attribute a single keyword."""
        keyword = row.keyword
        
        # 1. Infer intent
        intent, intent_conf, intent_signals = infer_intent(keyword)
        
        # 2. Infer task archetype
        archetype, archetype_signals = infer_task_archetype(keyword, intent)
        
        # 3. Extract entity
        entity_name, entity_type, entity_conf, entity_signals = extract_entities(keyword)
        
        # 4. Build evidence
        all_signals = intent_signals + archetype_signals + entity_signals
        evidence_id = self._generate_evidence_id()
        
        # 5. Create attribution (cluster assignment would come from clustering step)
        attribution = Attribution(
            intent=intent,
            intent_confidence=intent_conf,
            task_archetype=archetype,
            cluster_id="",  # Set by clustering step
            cluster_label="",
            cluster_role=ClusterRole.SUPPORT,
            primary_entity_id=f"e_{hashlib.sha1(entity_name.lower().encode()).hexdigest()[:12]}",
            secondary_entity_ids=[],
            entity_confidence=entity_conf
        )
        
        return AttributedKeyword(
            keyword_id=row.keyword_id,
            keyword=keyword,
            attribution=attribution,
            evidence=[evidence_id]
        )


def run_attribution(rows: List[ImportRow], project_id: str = "default") -> PipelineJob:
    """Convenience function to run attribution pipeline."""
    pipeline = AttributionPipeline()
    return pipeline.run(rows, project_id)


if __name__ == "__main__":
    # Test
    from core.canonical_types import ImportRow, generate_keyword_id
    
    test_rows = [
        ImportRow(keyword_id=generate_keyword_id("bästa elgitarr", "SE", "sv"), keyword="bästa elgitarr"),
        ImportRow(keyword_id=generate_keyword_id("köpa elgitarr online", "SE", "sv"), keyword="köpa elgitarr online"),
        ImportRow(keyword_id=generate_keyword_id("hur stämmer man en gitarr", "SE", "sv"), keyword="hur stämmer man en gitarr"),
    ]
    
    job = run_attribution(test_rows, "test_project")
    
    print(f"Job: {job.job_id}")
    print(f"Stage: {job.stage}")
    print(f"Results: {len(job.results)}")
    
    for r in job.results:
        print(f"  - {r.keyword}: {r.attribution.intent.value} / {r.attribution.task_archetype.value}")
'''
    
    def _generate_gap_analyzer(self) -> str:
        return '''"""
Gap Analyzer - Identifies entity and cluster gaps vs competitors.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import defaultdict

import sys
sys.path.insert(0, str(__file__).rsplit("analyzers", 1)[0])

from core.canonical_types import (
    Intent, ClusterRole, TaskArchetype,
    EntityGap, EntityGapSummary, IntentGap, ClusterGap, GapAction,
    AttributedKeyword
)


@dataclass
class RankData:
    keyword_id: str
    keyword: str
    domain: str
    position: Optional[int]
    volume: Optional[int] = None


class GapAnalyzer:
    """Analyzes gaps between mine and competitor visibility."""
    
    def __init__(
        self,
        mine_domain: str,
        competitor_domains: List[str],
        attributed_keywords: List[AttributedKeyword],
        rank_data: List[RankData]
    ):
        self.mine_domain = mine_domain
        self.competitor_domains = competitor_domains
        self.attributed = {kw.keyword_id: kw for kw in attributed_keywords}
        
        # Index rank data by keyword_id and domain
        self.rank_index: Dict[str, Dict[str, RankData]] = defaultdict(dict)
        for rd in rank_data:
            self.rank_index[rd.keyword_id][rd.domain] = rd
    
    def get_entity_gaps(self, entity_id: Optional[str] = None) -> List[EntityGap]:
        """Get gaps for all entities or a specific entity."""
        # Group keywords by entity
        entity_keywords: Dict[str, List[AttributedKeyword]] = defaultdict(list)
        for kw in self.attributed.values():
            eid = kw.attribution.primary_entity_id
            if entity_id is None or eid == entity_id:
                entity_keywords[eid].append(kw)
        
        gaps = []
        for eid, keywords in entity_keywords.items():
            gap = self._analyze_entity_gap(eid, keywords)
            if gap.summary.gap_keywords > 0:
                gaps.append(gap)
        
        # Sort by priority
        gaps.sort(key=lambda g: g.summary.priority_score, reverse=True)
        return gaps
    
    def _analyze_entity_gap(self, entity_id: str, keywords: List[AttributedKeyword]) -> EntityGap:
        """Analyze gap for a single entity."""
        mine_top20 = 0
        competitor_top20 = 0
        gap_keywords = 0
        total_volume_gap = 0
        
        intent_gaps: Dict[Intent, int] = defaultdict(int)
        cluster_gaps: Dict[str, int] = defaultdict(int)
        
        for kw in keywords:
            kw_id = kw.keyword_id
            ranks = self.rank_index.get(kw_id, {})
            
            mine_rank = ranks.get(self.mine_domain)
            mine_in_top20 = mine_rank and mine_rank.position and mine_rank.position <= 20
            
            competitor_in_top20 = any(
                ranks.get(cd) and ranks[cd].position and ranks[cd].position <= 20
                for cd in self.competitor_domains
            )
            
            if mine_in_top20:
                mine_top20 += 1
            
            if competitor_in_top20:
                competitor_top20 += 1
                
                if not mine_in_top20:
                    gap_keywords += 1
                    intent_gaps[kw.attribution.intent] += 1
                    cluster_gaps[kw.attribution.cluster_id] += 1
                    
                    # Add volume if available
                    for cd in self.competitor_domains:
                        rd = ranks.get(cd)
                        if rd and rd.volume:
                            total_volume_gap += rd.volume
                            break
        
        # Calculate priority
        avg_kd = 50  # Placeholder - would come from data
        serp_homogeneity = 0.6  # Placeholder
        priority = total_volume_gap * (1 / (1 + avg_kd/100)) * serp_homogeneity
        
        # Build intent gaps
        intent_gap_list = [
            IntentGap(intent=intent, gap_keywords=count, priority_score=count * 10)
            for intent, count in intent_gaps.items()
        ]
        
        # Build cluster gaps (simplified)
        cluster_gap_list = [
            ClusterGap(
                cluster_id=cid, 
                cluster_label=cid,  # Would be looked up
                gap_keywords=count,
                priority_score=count * 10,
                role=ClusterRole.SUPPORT
            )
            for cid, count in cluster_gaps.items()
        ]
        
        # Generate actions
        actions = []
        if gap_keywords > 0:
            # Find the highest-gap cluster
            if cluster_gaps:
                top_cluster = max(cluster_gaps, key=cluster_gaps.get)
                actions.append(GapAction(
                    action_type="create_page",
                    cluster_id=top_cluster,
                    recommended_archetype=TaskArchetype.GUIDE,
                    why=f"High gap ({cluster_gaps[top_cluster]} keywords) in this cluster"
                ))
        
        # Get entity name (simplified)
        entity_name = entity_id.replace("e_", "").capitalize()
        
        return EntityGap(
            entity_id=entity_id,
            entity_name=entity_name,
            snapshot_date=str(__import__("datetime").date.today()),
            mine_domain=self.mine_domain,
            competitors=self.competitor_domains,
            summary=EntityGapSummary(
                mine_top20=mine_top20,
                competitor_top20=competitor_top20,
                gap_keywords=gap_keywords,
                priority_score=priority
            ),
            by_intent=intent_gap_list,
            by_cluster=cluster_gap_list,
            top_actions=actions
        )


def get_entity_gaps(
    mine_domain: str,
    competitor_domains: List[str],
    attributed_keywords: List[AttributedKeyword],
    rank_data: List[RankData],
    entity_id: Optional[str] = None
) -> List[EntityGap]:
    """Convenience function to get entity gaps."""
    analyzer = GapAnalyzer(mine_domain, competitor_domains, attributed_keywords, rank_data)
    return analyzer.get_entity_gaps(entity_id)


if __name__ == "__main__":
    print("Gap Analyzer ready. Use get_entity_gaps() with attributed keywords and rank data.")
'''
    
    def _generate_dominance_lens(self) -> str:
        return '''"""
Dominance Lens - Shows what #1 domain ranks for in same cluster family.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import defaultdict

import sys
sys.path.insert(0, str(__file__).rsplit("analyzers", 1)[0])

from core.canonical_types import Intent, ClusterRole, AttributedKeyword


@dataclass
class DominanceEntry:
    keyword: str
    keyword_id: str
    cluster_id: str
    cluster_label: str
    position_1_domain: str
    position_1_url: Optional[str]
    my_position: Optional[int]
    volume: Optional[int]
    is_underperforming: bool


@dataclass
class DominanceLensResult:
    focus_keyword: str
    focus_entity_id: str
    dominant_domain: str
    dominant_footprint: int  # Number of #1 rankings
    my_footprint: int
    underperforming_keywords: List[DominanceEntry]
    opportunity_score: float


class DominanceLens:
    """Analyzes what the #1 domain ranks for."""
    
    def __init__(
        self,
        mine_domain: str,
        attributed_keywords: List[AttributedKeyword],
        rank_data: List  # List of RankData
    ):
        self.mine_domain = mine_domain
        self.attributed = {kw.keyword_id: kw for kw in attributed_keywords}
        
        # Index rank data
        self.rank_index: Dict[str, Dict[str, any]] = defaultdict(dict)
        for rd in rank_data:
            self.rank_index[rd.keyword_id][rd.domain] = rd
    
    def analyze(
        self,
        focus_keyword: str,
        include_cluster_siblings: bool = True,
        max_results: int = 50
    ) -> DominanceLensResult:
        """Analyze dominance for a focus keyword."""
        
        # Find the focus keyword's entity and cluster
        focus_attr = None
        for kw in self.attributed.values():
            if kw.keyword.lower() == focus_keyword.lower():
                focus_attr = kw
                break
        
        if not focus_attr:
            # Return empty result
            return DominanceLensResult(
                focus_keyword=focus_keyword,
                focus_entity_id="",
                dominant_domain="",
                dominant_footprint=0,
                my_footprint=0,
                underperforming_keywords=[],
                opportunity_score=0.0
            )
        
        entity_id = focus_attr.attribution.primary_entity_id
        cluster_id = focus_attr.attribution.cluster_id
        
        # Find all keywords in same entity (and optionally cluster)
        related_keywords = []
        for kw in self.attributed.values():
            if kw.attribution.primary_entity_id == entity_id:
                if not include_cluster_siblings or kw.attribution.cluster_id == cluster_id:
                    related_keywords.append(kw)
        
        # Find dominant domain at #1
        domain_counts: Dict[str, int] = defaultdict(int)
        for kw in related_keywords:
            ranks = self.rank_index.get(kw.keyword_id, {})
            for domain, rd in ranks.items():
                if rd.position == 1:
                    domain_counts[domain] += 1
        
        dominant_domain = max(domain_counts, key=domain_counts.get) if domain_counts else ""
        dominant_footprint = domain_counts.get(dominant_domain, 0)
        
        # Find my footprint and underperforming keywords
        my_footprint = domain_counts.get(self.mine_domain, 0)
        underperforming = []
        
        for kw in related_keywords:
            ranks = self.rank_index.get(kw.keyword_id, {})
            
            # Get #1 info
            pos1_domain = ""
            pos1_url = None
            for domain, rd in ranks.items():
                if rd.position == 1:
                    pos1_domain = domain
                    pos1_url = getattr(rd, 'url', None)
                    break
            
            # Get my position
            my_rd = ranks.get(self.mine_domain)
            my_pos = my_rd.position if my_rd else None
            volume = my_rd.volume if my_rd else None
            
            # Check if underperforming (they have #1, I don't have top 3)
            is_underperforming = (
                pos1_domain == dominant_domain and
                (my_pos is None or my_pos > 3)
            )
            
            if is_underperforming:
                underperforming.append(DominanceEntry(
                    keyword=kw.keyword,
                    keyword_id=kw.keyword_id,
                    cluster_id=kw.attribution.cluster_id,
                    cluster_label=kw.attribution.cluster_label,
                    position_1_domain=pos1_domain,
                    position_1_url=pos1_url,
                    my_position=my_pos,
                    volume=volume,
                    is_underperforming=True
                ))
        
        # Sort by volume (if available)
        underperforming.sort(key=lambda x: x.volume or 0, reverse=True)
        underperforming = underperforming[:max_results]
        
        # Calculate opportunity score
        total_volume = sum(u.volume or 0 for u in underperforming)
        opportunity_score = total_volume * (dominant_footprint / max(my_footprint, 1))
        
        return DominanceLensResult(
            focus_keyword=focus_keyword,
            focus_entity_id=entity_id,
            dominant_domain=dominant_domain,
            dominant_footprint=dominant_footprint,
            my_footprint=my_footprint,
            underperforming_keywords=underperforming,
            opportunity_score=opportunity_score
        )


def get_dominance_lens(
    focus_keyword: str,
    mine_domain: str,
    attributed_keywords: List[AttributedKeyword],
    rank_data: List,
    include_cluster_siblings: bool = True,
    max_results: int = 50
) -> DominanceLensResult:
    """Convenience function for dominance lens analysis."""
    lens = DominanceLens(mine_domain, attributed_keywords, rank_data)
    return lens.analyze(focus_keyword, include_cluster_siblings, max_results)


if __name__ == "__main__":
    print("Dominance Lens ready. Use get_dominance_lens() with focus keyword and data.")
'''


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class EntityAtlasOrchestrator:
    """Main orchestrator that builds the entire platform."""
    
    def __init__(self):
        self.contract = ContractManager()
        self.builder = ItemBuilder(self.contract)
    
    async def run(self, phase: Optional[str] = None, item: Optional[str] = None, all_items: bool = False):
        """Run the orchestrator."""
        print("\n" + "="*80)
        print("  ENTITY ATLAS BUILD ORCHESTRATOR")
        print("="*80)
        
        self._print_status()
        
        if all_items:
            await self._build_all()
        elif item:
            await self._build_specific(phase, item)
        else:
            await self._build_next()
        
        print("\n" + "="*80)
        print("  BUILD SESSION COMPLETE")
        print("="*80)
        self._print_status()
    
    def _print_status(self):
        """Print current build status."""
        print(f"\n  Current Phase: {self.contract.get_current_phase()}")
        print(f"  Current Item:  {self.contract.get_current_item()}")
        print(f"  Files Created: {len(self.contract.contract.get('files_created', []))}")
        
        # Print phase summary
        print("\n  Phase Summary:")
        for phase_name, phase_data in self.contract.contract.get("phases", {}).items():
            complete = sum(1 for i in phase_data.get("items", []) if i["status"] == "COMPLETE")
            total = len(phase_data.get("items", []))
            status = phase_data.get("status", "PENDING")
            print(f"    {phase_name}: {complete}/{total} [{status}]")
    
    async def _build_next(self):
        """Build the next pending item."""
        next_item = self.contract.get_next_pending_item()
        
        if next_item:
            phase_name, item = next_item
            print(f"\n  [NEXT] Building: {item['name']} ({phase_name})")
            await self.builder.build_item(phase_name, item)
        else:
            print("\n  [✓] All items complete!")
    
    async def _build_specific(self, phase: Optional[str], item_id: str):
        """Build a specific item."""
        phase_name = phase or self.contract.get_current_phase()
        phase_data = self.contract.contract["phases"].get(phase_name, {})
        
        for item in phase_data.get("items", []):
            if item["id"] == item_id:
                await self.builder.build_item(phase_name, item)
                return
        
        print(f"  [!] Item {item_id} not found in phase {phase_name}")
    
    async def _build_all(self):
        """Build all pending items."""
        while True:
            next_item = self.contract.get_next_pending_item()
            if not next_item:
                break
            
            phase_name, item = next_item
            await self.builder.build_item(phase_name, item)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Entity Atlas Build Orchestrator")
    parser.add_argument("--phase", help="Specific phase to build")
    parser.add_argument("--item", help="Specific item ID to build")
    parser.add_argument("--all", action="store_true", help="Build all pending items")
    parser.add_argument("--status", action="store_true", help="Show status only")
    
    args = parser.parse_args()
    
    orchestrator = EntityAtlasOrchestrator()
    
    if args.status:
        orchestrator._print_status()
    else:
        await orchestrator.run(phase=args.phase, item=args.item, all_items=args.all)


if __name__ == "__main__":
    asyncio.run(main())
