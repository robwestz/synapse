from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge dict b into a (returns new dict)."""
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
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


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_base_pack(spec_root: Path) -> SpecPack:
    """Load the base spec pack from spec_root/02_specs."""
    specs = spec_root / "02_specs"
    return SpecPack(
        base_dir=spec_root,
        normalization_model=load_yaml(specs / "normalization_model.yaml"),
        intent_model=load_yaml(specs / "intent_model.yaml"),
        perspective_model=load_yaml(specs / "perspective_model.yaml"),
        evidence_model=load_yaml(specs / "evidence_model.yaml"),
        scoring_model=load_yaml(specs / "scoring_model.yaml"),
        clustering_model=load_yaml(specs / "clustering_model.yaml"),
        visual_model=load_yaml(specs / "visual_model.yaml"),
    )


def load_vertical_pack(template_path: Path) -> SpecPack:
    """Load a vertical pack (pack.template.yaml style).

    This is intentionally minimal: it loads includes in order and applies
    top-level overrides into the intent/perspective models where applicable.

    The pack format can evolve; treat this as a starter.
    """
    pack_yaml = load_yaml(template_path)
    pack = pack_yaml.get("pack", {})
    includes: List[str] = pack.get("includes", [])

    # Base directory is template's parent
    base = template_path.parent

    merged: Dict[str, Any] = {}
    for inc in includes:
        merged = deep_merge(merged, load_yaml((base / inc).resolve()))

    # Apply overrides (very limited supported keys)
    overrides = pack.get("overrides", {})

    # intent_model overrides
    if "modifier_rules" in overrides and "intent_model" in merged:
        for intent_id, rule_over in overrides["modifier_rules"].items():
            add = rule_over.get("add_signals", [])
            if add:
                merged["intent_model"].setdefault("modifier_rules", {}).setdefault(intent_id, {}).setdefault("signals", [])
                merged["intent_model"]["modifier_rules"][intent_id]["signals"] += add

    # perspective_model overrides
    if "perspective_signals" in overrides and "perspective_model" in merged:
        for pid, over in overrides["perspective_signals"].items():
            addp = over.get("add_phrases", [])
            if addp:
                merged["perspective_model"].setdefault("signals", {}).setdefault(pid, {}).setdefault("phrases", [])
                merged["perspective_model"]["signals"][pid]["phrases"] += addp

    # Convert merged dict into SpecPack (falling back to base load if missing)
    # The include list already contains all the component specs.
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
