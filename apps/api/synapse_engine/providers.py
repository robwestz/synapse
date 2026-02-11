"""Synapse Engine — External providers, secrets, and runtime.

All network IO, API clients, secret management, and provider registry live here.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from .models import SerpSnapshot

# ============================================================
# HTTP CLIENT
# ============================================================


class ProviderError(RuntimeError):
    pass


@dataclass
class RetryPolicy:
    retries: int = 2
    backoff_seconds: float = 0.8
    backoff_multiplier: float = 2.0
    timeout_seconds: float = 30.0


def _is_retryable(status_code: int) -> bool:
    return status_code in {408, 409, 425, 429, 500, 502, 503, 504}


class HttpClient:
    def __init__(self, retry: Optional[RetryPolicy] = None):
        self.retry = retry or RetryPolicy()

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
        auth: Any = None,
    ) -> Dict[str, Any]:
        last_err: Optional[Exception] = None
        delay = self.retry.backoff_seconds

        for attempt in range(self.retry.retries + 1):
            try:
                r = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    auth=auth,
                    timeout=self.retry.timeout_seconds,
                )

                if r.status_code >= 400:
                    msg = None
                    try:
                        msg = r.json()
                    except Exception:
                        msg = r.text[:500]

                    if attempt < self.retry.retries and _is_retryable(r.status_code):
                        time.sleep(delay)
                        delay *= self.retry.backoff_multiplier
                        continue
                    raise ProviderError(f"HTTP {r.status_code} from {url}: {msg}")

                if not r.text:
                    return {}
                try:
                    return r.json()
                except json.JSONDecodeError:
                    return {"raw": r.text}

            except Exception as e:
                last_err = e
                if attempt < self.retry.retries:
                    time.sleep(delay)
                    delay *= self.retry.backoff_multiplier
                    continue
                break

        raise ProviderError(f"Request failed: {method} {url}: {last_err}")


# ============================================================
# SECRETS
# ============================================================


def _env(name: str) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return None
    v = v.strip()
    return v or None


@dataclass
class Secrets:
    firecrawl_api_key: Optional[str] = None
    ahrefs_api_key: Optional[str] = None
    dataforseo_login: Optional[str] = None
    dataforseo_password: Optional[str] = None
    google_api_key: Optional[str] = None
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


def _default_secrets_path() -> Path:
    base = Path(os.getenv("SYNAPSE_ENGINE_HOME", str(Path.home() / ".synapse_engine")))
    base.mkdir(parents=True, exist_ok=True)
    return base / "secrets.json"


def load_secrets(path: Optional[Path] = None) -> Secrets:
    path = path or _default_secrets_path()
    if not path.exists():
        return Secrets()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Secrets.from_dict(data if isinstance(data, dict) else {})
    except Exception:
        return Secrets()


def save_secrets(secrets: Secrets, path: Optional[Path] = None) -> None:
    path = path or _default_secrets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(secrets.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# DATAFORSEO
# ============================================================


@dataclass
class DataForSEOCredentials:
    login: str
    password: str


class DataForSEOClient:
    def __init__(
        self,
        creds: DataForSEOCredentials,
        base_url: str = "https://api.dataforseo.com",
        api_version: str = "v3",
        http: Optional[HttpClient] = None,
    ):
        self.creds = creds
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version.strip("/")
        self.http = http or HttpClient()

    def _post(self, path: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.api_version}/{path.lstrip('/')}"
        return self.http.request(
            "POST",
            url,
            auth=HTTPBasicAuth(self.creds.login, self.creds.password),
            json_body=tasks,
        )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.api_version}/{path.lstrip('/')}"
        return self.http.request(
            "GET",
            url,
            auth=HTTPBasicAuth(self.creds.login, self.creds.password),
            params=params,
        )

    def keyword_suggestions(
        self,
        seed: str,
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        limit: int = 500,
        include_seed_keyword: bool = True,
        include_serp_info: bool = False,
        ignore_synonyms: bool = False,
    ) -> Dict[str, Any]:
        task: Dict[str, Any] = {
            "keyword": seed,
            "limit": int(limit),
            "include_seed_keyword": bool(include_seed_keyword),
            "include_serp_info": bool(include_serp_info),
            "ignore_synonyms": bool(ignore_synonyms),
        }
        if location_code is not None:
            task["location_code"] = int(location_code)
        elif location_name:
            task["location_name"] = location_name
        if language_code:
            task["language_code"] = language_code
        return self._post("dataforseo_labs/google/keyword_suggestions/live", [task])

    def related_keywords(
        self,
        seed: str,
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        limit: int = 500,
        include_seed_keyword: bool = False,
        include_serp_info: bool = False,
    ) -> Dict[str, Any]:
        task: Dict[str, Any] = {
            "keyword": seed,
            "limit": int(limit),
            "include_seed_keyword": bool(include_seed_keyword),
            "include_serp_info": bool(include_serp_info),
        }
        if location_code is not None:
            task["location_code"] = int(location_code)
        elif location_name:
            task["location_name"] = location_name
        if language_code:
            task["language_code"] = language_code
        return self._post("dataforseo_labs/google/related_keywords/live", [task])

    def serp_live_advanced(
        self,
        keyword: str,
        location_name: Optional[str] = None,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        depth: int = 10,
        device: str = "desktop",
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        task: Dict[str, Any] = {
            "keyword": keyword,
            "depth": int(depth),
            "device": device,
        }
        if tag:
            task["tag"] = tag
        if location_code is not None:
            task["location_code"] = int(location_code)
        elif location_name:
            task["location_name"] = location_name
        if language_code:
            task["language_code"] = language_code
        return self._post("serp/google/organic/live/advanced", [task])

    def locations_and_languages(self) -> Dict[str, Any]:
        return self._get("dataforseo_labs/locations_and_languages")


def _dfs_extract_result_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    tasks = payload.get("tasks") or []
    if not tasks:
        return []
    task0 = tasks[0] or {}
    result = task0.get("result") or []
    if not result:
        return []
    r0 = result[0] or {}
    return r0.get("items") or []


def parse_keyword_suggestions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in _dfs_extract_result_items(payload):
        kw = it.get("keyword") or it.get("key")
        if not kw:
            continue
        out.append({
            "keyword": str(kw),
            "search_volume": it.get("search_volume"),
            "cpc": it.get("cpc"),
            "competition": it.get("competition"),
            "competition_level": it.get("competition_level"),
            "monthly_searches": it.get("monthly_searches"),
            "serp_info": it.get("serp_info"),
        })
    return out


def parse_serp_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    tasks = payload.get("tasks") or []
    if not tasks:
        return {"top_urls": [], "features": [], "paa": [], "related": []}
    task0 = tasks[0] or {}
    result = task0.get("result") or []
    if not result:
        return {"top_urls": [], "features": [], "paa": [], "related": []}
    r0 = result[0] or {}
    items = r0.get("items") or []

    top_urls: List[str] = []
    features: List[str] = []
    paa: List[str] = []
    related: List[str] = []

    def add_feature(t: str) -> None:
        if t and t not in features:
            features.append(t)

    for it in items:
        t = it.get("type")
        if t:
            add_feature(str(t))
        if t in {"organic", "paid", "featured_snippet", "top_stories", "local_pack"}:
            url = it.get("url")
            if url and url not in top_urls:
                top_urls.append(url)
        if t == "people_also_ask":
            for qi in it.get("items") or []:
                q = qi.get("question") or qi.get("title")
                if q and q not in paa:
                    paa.append(str(q))
        if t in {"related_searches", "related_search"}:
            for ri in it.get("items") or []:
                q = ri.get("query") or ri.get("title")
                if q and q not in related:
                    related.append(str(q))

    if not top_urls:
        for it in items:
            for sub in it.get("items") or []:
                url = sub.get("url")
                if url and url not in top_urls:
                    top_urls.append(url)

    return {
        "top_urls": top_urls[:20],
        "features": features,
        "paa": paa[:30],
        "related": related[:30],
        "datetime": r0.get("datetime"),
        "check_url": r0.get("check_url"),
    }


# ============================================================
# AHREFS
# ============================================================


class AhrefsClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.ahrefs.com/v3",
        http: Optional[HttpClient] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.http = http or HttpClient()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return self.http.request("GET", url, headers=headers, params=params)

    def keywords_matching_terms(
        self,
        keywords: List[str] | str,
        limit: int = 1000,
        match_mode: str = "terms",
        keyword_list_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        if isinstance(keywords, list):
            kw = ",".join([k.strip() for k in keywords if k.strip()])
        else:
            kw = str(keywords).strip()

        params: Dict[str, Any] = {
            "keywords": kw,
            "limit": int(limit),
            "match_mode": match_mode,
        }
        if keyword_list_id is not None:
            params["keyword_list_id"] = int(keyword_list_id)

        return self._get("keywords-explorer/matching-terms", params=params)


def parse_matching_terms(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    if isinstance(payload.get("data"), list):
        for row in payload["data"]:
            if not isinstance(row, dict):
                continue
            kw = row.get("keyword") or row.get("term") or row.get("query")
            if not kw:
                continue
            out.append({
                "keyword": str(kw),
                "search_volume": row.get("search_volume") or row.get("volume"),
                "cpc": row.get("cpc"),
                "kd": row.get("kd") or row.get("keyword_difficulty"),
                "traffic_potential": row.get("traffic_potential") or row.get("tp"),
            })
        return out

    if isinstance(payload.get("tasks"), list):
        for t in payload.get("tasks") or []:
            for r in t.get("result") or []:
                for row in r.get("items") or []:
                    kw = row.get("keyword")
                    if kw:
                        out.append({"keyword": str(kw)})
        return out

    for k, v in payload.items():
        if isinstance(v, list):
            for row in v:
                if isinstance(row, dict):
                    kw = row.get("keyword") or row.get("term")
                    if kw:
                        out.append({"keyword": str(kw)})
    return out


# ============================================================
# SERP SNAPSHOT
# ============================================================


def fetch_seed_serp(
    dfs: DataForSEOClient,
    keyword: str,
    *,
    location_name: Optional[str] = None,
    location_code: Optional[int] = None,
    language_code: Optional[str] = None,
    depth: int = 10,
) -> SerpSnapshot:
    payload = dfs.serp_live_advanced(
        keyword=keyword,
        location_name=location_name,
        location_code=location_code,
        language_code=language_code,
        depth=depth,
    )
    snap = parse_serp_snapshot(payload)
    return SerpSnapshot(
        keyword=keyword,
        top_urls=list(snap.get("top_urls", []) or []),
        features=list(snap.get("features", []) or []),
        paa_questions=list(snap.get("paa", []) or []),
        related_searches=list(snap.get("related", []) or []),
        raw=snap,
    )


def serp_overlap(seed_top_urls: List[str], cand_top_urls: List[str]) -> float:
    sa, sb = set(seed_top_urls), set(cand_top_urls)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# ============================================================
# PROVIDER REGISTRY + RUNTIME
# ============================================================


@dataclass
class ProviderRegistry:
    dataforseo: Optional[DataForSEOClient] = None
    ahrefs: Optional[AhrefsClient] = None

    @staticmethod
    def from_secrets(secrets: Secrets) -> "ProviderRegistry":
        reg = ProviderRegistry()

        if secrets.dataforseo_login and secrets.dataforseo_password:
            reg.dataforseo = DataForSEOClient(
                creds=DataForSEOCredentials(secrets.dataforseo_login, secrets.dataforseo_password)
            )

        if secrets.ahrefs_api_key:
            reg.ahrefs = AhrefsClient(api_key=secrets.ahrefs_api_key)

        return reg


@dataclass
class Budget:
    candidate_pool_target: int = 500
    keyword_suggestions_limit: int = 400
    related_keywords_limit: int = 250
    serp_depth: int = 10
    serp_refine_top_n: int = 30
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
