from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..secrets import Secrets
from .ahrefs import AhrefsClient
from .dataforseo import DataForSEOClient, DataForSEOCredentials
from .firecrawl import FirecrawlClient


@dataclass
class ProviderRegistry:
    """Holds instantiated provider clients (or None if not configured)."""

    firecrawl: Optional[FirecrawlClient] = None
    dataforseo: Optional[DataForSEOClient] = None
    ahrefs: Optional[AhrefsClient] = None

    @staticmethod
    def from_secrets(secrets: Secrets) -> "ProviderRegistry":
        reg = ProviderRegistry()

        if secrets.firecrawl_api_key:
            reg.firecrawl = FirecrawlClient(api_key=secrets.firecrawl_api_key)

        if secrets.dataforseo_login and secrets.dataforseo_password:
            reg.dataforseo = DataForSEOClient(
                creds=DataForSEOCredentials(secrets.dataforseo_login, secrets.dataforseo_password)
            )

        if secrets.ahrefs_api_key:
            reg.ahrefs = AhrefsClient(api_key=secrets.ahrefs_api_key)

        return reg
