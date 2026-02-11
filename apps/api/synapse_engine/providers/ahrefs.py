from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .http import HttpClient


class AhrefsClient:
    """Ahrefs API v3 client.

    We intentionally keep this lightweight and only implement the few calls we
    need for the Synapse Engine pipeline.

    Auth: Authorization: Bearer <API_KEY>
    Base URL examples in docs show: https://api.ahrefs.com/v3/...
    """

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
        """Keyword ideas that contain the words from your query.

        Endpoint shown in docs:
          GET https://api.ahrefs.com/v3/keywords-explorer/matching-terms
        """
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
    """Best-effort parsing of Matching Terms response.

    Response shapes differ depending on Ahrefs' report and fields selected.
    We try a few common patterns.
    """
    out: List[Dict[str, Any]] = []

    # Some endpoints return { "data": [ ... ] }
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

    # Some endpoints return {"tasks": ...} etc (unlikely for v3)
    if isinstance(payload.get("tasks"), list):
        for t in payload.get("tasks") or []:
            for r in t.get("result") or []:
                for row in r.get("items") or []:
                    kw = row.get("keyword")
                    if kw:
                        out.append({"keyword": str(kw)})
        return out

    # Fallback: search for any list-like field
    for k, v in payload.items():
        if isinstance(v, list):
            for row in v:
                if isinstance(row, dict):
                    kw = row.get("keyword") or row.get("term")
                    if kw:
                        out.append({"keyword": str(kw)})
    return out
