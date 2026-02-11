from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .providers.registry import ProviderRegistry
from .secrets import Secrets


@dataclass
class Budget:
    """Runtime budget controls.

    The goal is to be 'API-lean' by default, and only spend units where the
    extra evidence materially improves ranking/explanations.
    """

    candidate_pool_target: int = 500
    keyword_suggestions_limit: int = 400
    related_keywords_limit: int = 250
    serp_depth: int = 10
    # How many *candidates* to refine with candidate SERP calls (seed SERP is 1 call)
    serp_refine_top_n: int = 30
    # Hard cap for SERP calls in a single run
    serp_calls_max: int = 40


@dataclass
class Runtime:
    secrets: Secrets
    providers: ProviderRegistry
    budget: Budget
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_code: Optional[str] = None

    @staticmethod
    def build(
        secrets: Secrets,
        budget: Optional[Budget] = None,
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
    ) -> "Runtime":
        return Runtime(
            secrets=secrets,
            providers=ProviderRegistry.from_secrets(secrets),
            budget=budget or Budget(),
            location_name=location_name,
            location_code=location_code,
            language_code=language_code,
        )
