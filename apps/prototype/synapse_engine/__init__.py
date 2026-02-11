"""Synapse Engine prototype.

This is a reference implementation of the synapse-engine-spec-v1 pack.
It is designed to be *tool-agnostic* and to run without external APIs
(by using heuristic + TF-IDF based proxies). Swap the adapters to plug
in real SERP/Ads/GSC/LLM.
"""

from .pipeline import run_pipeline

__all__ = ["run_pipeline"]
