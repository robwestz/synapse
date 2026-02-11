from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from requests.auth import HTTPBasicAuth

from .http import HttpClient, ProviderError


@dataclass
class DataForSEOCredentials:
    login: str
    password: str


class DataForSEOClient:
    """DataForSEO v3 client.

    We use *live* endpoints to stay as "Google-real" as possible while staying ToS-safe.
    """

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

    # -------------------------
    # Candidate generation
    # -------------------------
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

    # -------------------------
    # SERP snapshot
    # -------------------------
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

    # -------------------------
    # Utility
    # -------------------------
    def locations_and_languages(self) -> Dict[str, Any]:
        # Unified endpoint for labs.
        return self._get("dataforseo_labs/locations_and_languages")


def _dfs_extract_result_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Best-effort extractor for DataForSEO responses.

    DataForSEO APIs are task-based: tasks -> result -> items.
    We try to return the `items` list for the first task.
    """
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
    """Extract a compact SERP snapshot from DataForSEO Live SERP Advanced."""
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
        # organic results
        if t in {"organic", "paid", "featured_snippet", "top_stories", "local_pack"}:
            url = it.get("url")
            if url and url not in top_urls:
                top_urls.append(url)
        # People also ask
        if t == "people_also_ask":
            for qi in it.get("items") or []:
                q = qi.get("question") or qi.get("title")
                if q and q not in paa:
                    paa.append(str(q))
        # Related searches
        if t in {"related_searches", "related_search"}:
            for ri in it.get("items") or []:
                q = ri.get("query") or ri.get("title")
                if q and q not in related:
                    related.append(str(q))

    # Fallback: some organic results may be under `items[i].items` (depending on type)
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
