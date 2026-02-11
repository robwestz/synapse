from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from synapse_engine.pipeline import run_pipeline
from synapse_engine.providers import Budget, Runtime, Secrets, load_secrets, save_secrets


ROOT = Path(__file__).resolve().parent
SPEC_ROOT = ROOT / "spec"
STATIC_DIR = ROOT / "static"


def _default_location_name(market: str) -> str:
    # Keep simple; user can override in UI.
    m = (market or "").upper().strip()
    return {
        "SE": "Sweden",
        "US": "United States",
        "UK": "United Kingdom",
        "GB": "United Kingdom",
        "DE": "Germany",
        "NO": "Norway",
        "DK": "Denmark",
        "FI": "Finland",
    }.get(m, "Sweden")


class BudgetIn(BaseModel):
    candidate_pool_target: Optional[int] = None
    keyword_suggestions_limit: Optional[int] = None
    related_keywords_limit: Optional[int] = None
    serp_depth: Optional[int] = None
    serp_refine_top_n: Optional[int] = None
    serp_calls_max: Optional[int] = None

    def to_budget(self) -> Budget:
        b = Budget()
        for k, v in self.model_dump(exclude_none=True).items():
            setattr(b, k, v)
        return b


class SecretsIn(BaseModel):
    firecrawl_api_key: Optional[str] = Field(default=None)
    ahrefs_api_key: Optional[str] = Field(default=None)
    dataforseo_login: Optional[str] = Field(default=None)
    dataforseo_password: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)

    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    gemini_api_key: Optional[str] = Field(default=None)

    def to_secrets(self) -> Secrets:
        return Secrets.from_dict(self.model_dump(exclude_none=True))


class RunRequest(BaseModel):
    seed_phrase: str
    language: str = "sv"
    market: str = "SE"
    target: int = 50

    # Provider locale (for DataForSEO)
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_code: Optional[str] = None

    budget: Optional[BudgetIn] = None
    secrets: Optional[SecretsIn] = None

    # If true: persist secrets to ~/.synapse_engine/secrets.json (dev only)
    persist_secrets: bool = False


class RunResponse(BaseModel):
    job_id: str
    graph: Dict[str, Any]
    related: Dict[str, Any]
    secrets_status: Dict[str, Any]


app = FastAPI(title="Synapse Engine API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index() -> FileResponse:
    p = STATIC_DIR / "index.html"
    if not p.exists():
        raise HTTPException(status_code=500, detail="UI missing: static/index.html")
    return FileResponse(str(p))


@app.get("/api/secrets/status")
def secrets_status() -> Dict[str, Any]:
    # Show persisted+env merged (redacted)
    s = load_secrets().merge(Secrets.from_env())
    return {"redacted": s.redacted()}


@app.post("/api/secrets/save")
def secrets_save(payload: SecretsIn) -> Dict[str, Any]:
    current = load_secrets()
    merged = current.merge(payload.to_secrets())
    save_secrets(merged)
    return {"ok": True, "redacted": merged.redacted()}


@app.post("/api/run", response_model=RunResponse)
def run(req: RunRequest) -> RunResponse:
    # Merge: env + persisted + request payload (highest precedence)
    secrets = Secrets.from_env().merge(load_secrets())
    if req.secrets is not None:
        secrets = secrets.merge(req.secrets.to_secrets())

    if req.persist_secrets and req.secrets is not None:
        save_secrets(secrets)

    budget = (req.budget.to_budget() if req.budget is not None else Budget())

    runtime = Runtime.build(
        secrets=secrets,
        budget=budget,
        location_name=req.location_name or _default_location_name(req.market),
        location_code=req.location_code,
        language_code=req.language_code or req.language,
    )

    job_id = str(uuid.uuid4())
    graph, related = run_pipeline(
        seed_phrase=req.seed_phrase,
        language=req.language,
        market=req.market,
        target=req.target,
        spec_root=SPEC_ROOT,
        runtime=runtime,
    )

    return RunResponse(job_id=job_id, graph=graph, related=related, secrets_status=secrets.redacted())


# Static assets (optional)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
