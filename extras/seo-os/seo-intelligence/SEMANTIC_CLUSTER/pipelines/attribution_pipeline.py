"""
Attribution Pipeline - Assigns Intent, Entity, Cluster to keywords.
State machine: INTAKE → NORMALIZE → ATTRIBUTION → STORE → FINALIZED
"""

from __future__ import annotations
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
import hashlib

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit("pipelines", 1)[0].rstrip("/\\"))

from core.canonical_types import (
    Intent, TaskArchetype, ClusterRole, EntityType,
    AttributedKeyword, Attribution, EvidenceSignal,
    ImportRow, generate_keyword_id
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
    TaskArchetype.BRAND: []
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


def extract_entities(keyword: str) -> tuple[str, EntityType, float, List[EvidenceSignal]]:
    """Extract primary entity from keyword."""
    tokens = keyword.lower().split()
    signals = []
    
    modifiers = {"bästa", "billig", "köpa", "hur", "vad", "är", "i", "för", "med", "utan"}
    content_tokens = [t for t in tokens if t not in modifiers]
    
    if not content_tokens:
        content_tokens = tokens
    
    head_term = content_tokens[-1] if content_tokens else tokens[-1]
    
    entity_type = EntityType.CONCEPT
    if any(brand in keyword.lower() for brand in ["apple", "samsung", "google", "nike"]):
        entity_type = EntityType.BRAND
    elif any(product in keyword.lower() for product in ["telefon", "dator", "bil", "gitarr"]):
        entity_type = EntityType.PRODUCT
    
    signals.append(EvidenceSignal(
        signal_type="head_term_extraction",
        value=f"head_term='{head_term}'",
        weight=0.6
    ))
    
    return head_term.capitalize(), entity_type, 0.65, signals


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
            job.stage = PipelineStage.INTAKE
            if not rows:
                raise ValueError("No rows to process")
            
            job.stage = PipelineStage.NORMALIZE
            job.stage = PipelineStage.ATTRIBUTION
            
            for row in rows:
                attributed = self._attribute_keyword(row)
                job.results.append(attributed)
            
            job.stage = PipelineStage.STORE
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
        
        intent, intent_conf, intent_signals = infer_intent(keyword)
        archetype, archetype_signals = infer_task_archetype(keyword, intent)
        entity_name, entity_type, entity_conf, entity_signals = extract_entities(keyword)
        
        evidence_id = self._generate_evidence_id()
        
        attribution = Attribution(
            intent=intent,
            intent_confidence=intent_conf,
            task_archetype=archetype,
            cluster_id="",
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
