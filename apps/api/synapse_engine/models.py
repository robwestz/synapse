"""Synapse Engine — Models, configuration, and validation.

All data classes, enums, config loading, and schema validation live here.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ============================================================
# CONFIGURATION
# ============================================================


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class SpecPack:
    base_dir: Path
    normalization_model: Dict[str, Any]
    intent_model: Dict[str, Any]
    perspective_model: Dict[str, Any]
    evidence_model: Dict[str, Any]
    scoring_model: Dict[str, Any]
    clustering_model: Dict[str, Any]
    visual_model: Dict[str, Any]

    @property
    def language(self) -> str:
        return self.intent_model.get("intent_model", {}).get("language", "")

    @property
    def market(self) -> str:
        return self.intent_model.get("intent_model", {}).get("market", "")


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_base_pack(spec_root: Path) -> SpecPack:
    specs = spec_root / "02_specs"
    return SpecPack(
        base_dir=spec_root,
        normalization_model=_load_yaml(specs / "normalization_model.yaml"),
        intent_model=_load_yaml(specs / "intent_model.yaml"),
        perspective_model=_load_yaml(specs / "perspective_model.yaml"),
        evidence_model=_load_yaml(specs / "evidence_model.yaml"),
        scoring_model=_load_yaml(specs / "scoring_model.yaml"),
        clustering_model=_load_yaml(specs / "clustering_model.yaml"),
        visual_model=_load_yaml(specs / "visual_model.yaml"),
    )


def load_vertical_pack(template_path: Path) -> SpecPack:
    pack_yaml = _load_yaml(template_path)
    pack = pack_yaml.get("pack", {})
    includes: List[str] = pack.get("includes", [])

    base = template_path.parent

    merged: Dict[str, Any] = {}
    for inc in includes:
        merged = _deep_merge(merged, _load_yaml((base / inc).resolve()))

    overrides = pack.get("overrides", {})

    if "modifier_rules" in overrides and "intent_model" in merged:
        for intent_id, rule_over in overrides["modifier_rules"].items():
            add = rule_over.get("add_signals", [])
            if add:
                merged["intent_model"].setdefault("modifier_rules", {}).setdefault(intent_id, {}).setdefault("signals", [])
                merged["intent_model"]["modifier_rules"][intent_id]["signals"] += add

    if "perspective_signals" in overrides and "perspective_model" in merged:
        for pid, over in overrides["perspective_signals"].items():
            addp = over.get("add_phrases", [])
            if addp:
                merged["perspective_model"].setdefault("signals", {}).setdefault(pid, {}).setdefault("phrases", [])
                merged["perspective_model"]["signals"][pid]["phrases"] += addp

    def get(name: str) -> Dict[str, Any]:
        if name not in merged:
            return {}
        return merged[name]

    return SpecPack(
        base_dir=template_path.parent,
        normalization_model=get("normalization_model"),
        intent_model=get("intent_model"),
        perspective_model=get("perspective_model"),
        evidence_model=get("evidence_model"),
        scoring_model=get("scoring_model"),
        clustering_model=get("clustering_model"),
        visual_model=get("visual_model"),
    )


# ============================================================
# DATA TYPES
# ============================================================


@dataclass
class NormalizedPhrase:
    raw: str
    canonical: str
    display: str


@dataclass
class IntentLabel:
    intent: str
    confidence: float
    evidence_used: List[str]
    secondary: List[str]


@dataclass
class PerspectiveLabel:
    perspective: str
    confidence: float
    evidence_used: List[str]


@dataclass
class Entity:
    id: str
    surface: str
    canonical: str
    type: str
    kg_id: str | None
    role: str
    confidence: float


@dataclass
class Candidate:
    phrase: str
    provenance: str
    rationale: str
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class ScoredCandidate:
    id: str
    phrase: str
    provenance: str
    intent: str
    perspective: str
    confidence: float
    features: Dict[str, float]
    relevance_score: float


@dataclass
class Cluster:
    id: str
    label: str
    color: str
    node_ids: List[str]
    dominant_intent: str
    dominant_perspective: str
    hub_entities: List[str]


@dataclass
class SerpSnapshot:
    keyword: str
    top_urls: List[str]
    features: List[str]
    paa_questions: List[str]
    related_searches: List[str]
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "top_urls": self.top_urls,
            "features": self.features,
            "paa": self.paa_questions,
            "related": self.related_searches,
        }


# ============================================================
# SCHEMA VALIDATION (updated to referencing.Registry API)
# ============================================================


class SchemaValidator:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.schemas: Dict[str, Any] = {}
        self._registry = None
        self._load_all()

    def _load_all(self) -> None:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        resources: list[tuple[str, Resource]] = []
        for p in self.schema_dir.glob("*.schema.json"):
            schema = json.loads(p.read_text(encoding="utf-8"))
            name = p.name
            self.schemas[name] = schema
            resource = Resource.from_contents(schema, default_specification=DRAFT202012)
            sid = schema.get("$id")
            if sid:
                resources.append((sid, resource))
            resources.append((name, resource))

        self._registry = Registry().with_resources(resources)

    def validate(self, doc: Dict[str, Any], schema_name: str) -> None:
        import jsonschema

        if schema_name not in self.schemas:
            raise KeyError(f"Schema not found: {schema_name}")
        schema = self.schemas[schema_name]
        validator = jsonschema.Draft202012Validator(schema, registry=self._registry)
        errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
        if errors:
            msg = "\n".join([f"{list(e.path)}: {e.message}" for e in errors[:25]])
            raise jsonschema.ValidationError(f"{schema_name} validation failed:\n{msg}")
