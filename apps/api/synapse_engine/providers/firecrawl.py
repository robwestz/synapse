from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .http import HttpClient


@dataclass
class FirecrawlScrapeOptions:
    formats: List[str] = None
    only_main_content: bool = True
    timeout_ms: int = 30000
    mobile: bool = False
    proxy: str = "auto"  # basic|enhanced|auto
    location_country: Optional[str] = None  # e.g. "SE"
    location_languages: Optional[List[str]] = None  # e.g. ["sv-SE"]

    def to_payload(self, url: str) -> Dict[str, Any]:
        fmts = self.formats or ["markdown", "links"]
        payload: Dict[str, Any] = {
            "url": url,
            "formats": fmts,
            "onlyMainContent": bool(self.only_main_content),
            "timeout": int(self.timeout_ms),
            "mobile": bool(self.mobile),
            "proxy": self.proxy,
            "storeInCache": True,
        }
        if self.location_country or self.location_languages:
            payload["location"] = {
                "country": self.location_country or "US",
                "languages": self.location_languages or ["en-US"],
            }
        return payload


class FirecrawlClient:
    """Firecrawl client (scrape only).

    Docs: Firecrawl /v2/scrape with Bearer auth.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev",
        api_version: str = "v2",
        http: Optional[HttpClient] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version.strip("/")
        self.http = http or HttpClient()

    def scrape(self, url: str, options: Optional[FirecrawlScrapeOptions] = None) -> Dict[str, Any]:
        opts = options or FirecrawlScrapeOptions()
        endpoint = f"{self.base_url}/{self.api_version}/scrape"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return self.http.request("POST", endpoint, headers=headers, json_body=opts.to_payload(url))
