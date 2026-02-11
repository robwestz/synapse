from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _env(name: str) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    return v or None


@dataclass
class Secrets:
    """Runtime secrets.

    Design goals:
    - Can be provided via env vars or UI payload.
    - Can optionally be persisted locally for dev.
    - Never logs raw values (use .redacted()).
    """

    # Crawling / extraction
    firecrawl_api_key: Optional[str] = None

    # SEO data providers
    ahrefs_api_key: Optional[str] = None
    dataforseo_login: Optional[str] = None
    dataforseo_password: Optional[str] = None

    # Google (public API-key based)
    google_api_key: Optional[str] = None

    # LLMs (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    @staticmethod
    def from_env() -> "Secrets":
        return Secrets(
            firecrawl_api_key=_env("FIRECRAWL_API_KEY"),
            ahrefs_api_key=_env("AHREFS_API_KEY"),
            dataforseo_login=_env("DATAFORSEO_LOGIN"),
            dataforseo_password=_env("DATAFORSEO_PASSWORD"),
            google_api_key=_env("GOOGLE_API_KEY"),
            openai_api_key=_env("OPENAI_API_KEY"),
            anthropic_api_key=_env("ANTHROPIC_API_KEY"),
            gemini_api_key=_env("GEMINI_API_KEY"),
        )

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Secrets":
        allowed = {
            "firecrawl_api_key",
            "ahrefs_api_key",
            "dataforseo_login",
            "dataforseo_password",
            "google_api_key",
            "openai_api_key",
            "anthropic_api_key",
            "gemini_api_key",
        }
        clean: Dict[str, Any] = {k: v for k, v in d.items() if k in allowed}
        return Secrets(**clean)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def merge(self, other: "Secrets") -> "Secrets":
        base = self.to_dict()
        for k, v in other.to_dict().items():
            if v is not None:
                base[k] = v
        return Secrets.from_dict(base)

    def redacted(self) -> Dict[str, Any]:
        def r(v: Optional[str]) -> Optional[str]:
            if not v:
                return None
            if len(v) <= 6:
                return "***"
            return v[:3] + "…" + v[-3:]

        d = self.to_dict()
        return {k: r(v) if v else None for k, v in d.items()}


def default_secrets_path() -> Path:
    base = Path(os.getenv("SYNAPSE_ENGINE_HOME", str(Path.home() / ".synapse_engine")))
    base.mkdir(parents=True, exist_ok=True)
    return base / "secrets.json"


def load_secrets(path: Optional[Path] = None) -> Secrets:
    path = path or default_secrets_path()
    if not path.exists():
        return Secrets()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Secrets.from_dict(data if isinstance(data, dict) else {})
    except Exception:
        # Fail closed: return empty secrets rather than crashing.
        return Secrets()


def save_secrets(secrets: Secrets, path: Optional[Path] = None) -> None:
    path = path or default_secrets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(secrets.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
