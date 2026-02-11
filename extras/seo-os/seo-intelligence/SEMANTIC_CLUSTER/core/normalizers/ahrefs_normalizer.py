"""
Ahrefs Normalizer - Central import module for all Ahrefs exports.
RULE: All tools MUST use this module. NEVER manual CSV parsing.
"""

from __future__ import annotations
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib

from core.canonical_types import (
    RankingImport, ImportRow, ImportMetadata, SiteInfo, 
    DomainLabel, generate_keyword_id, AHREFS_REPORT_TYPES
)


# ============================================================================
# COLUMN ALIASES (Swedish + English)
# ============================================================================

COLUMN_ALIASES = {
    # Keyword variants
    "keyword": "keyword",
    "sökord": "keyword",
    "nyckelord": "keyword",
    "query": "keyword",
    
    # Position variants
    "position": "position",
    "placering": "position",
    "rank": "position",
    "ranking": "position",
    
    # Volume variants
    "volume": "volume",
    "volym": "volume",
    "sökvolym": "volume",
    "search volume": "volume",
    
    # Traffic variants
    "traffic": "traffic",
    "trafik": "traffic",
    "estimated traffic": "traffic",
    
    # KD variants
    "kd": "kd",
    "keyword difficulty": "kd",
    "kd %": "kd",
    "svårighetsgrad": "kd",
    
    # URL variants
    "url": "url",
    "current url": "url",
    "top url": "url",
    "best url": "url",
    
    # Country variants
    "country": "country",
    "land": "country",
    "location": "country",
    
    # Domain Rating
    "dr": "domain_rating",
    "domain rating": "domain_rating",
    "domänbetyg": "domain_rating",
    
    # Referring domains
    "referring domains": "referring_domains",
    "refererande domäner": "referring_domains",
    "rd": "referring_domains",
    
    # SERP features
    "serp features": "serp_features",
    "serp-funktioner": "serp_features",
    
    # CPC
    "cpc": "cpc",
    "cpc (usd)": "cpc",
    
    # Date
    "date": "snapshot_date",
    "datum": "snapshot_date",
    "last update": "snapshot_date",
}


# ============================================================================
# REPORT TYPE DETECTION
# ============================================================================

REPORT_SIGNATURES = {
    "organic_keywords": {"keyword", "position", "volume", "url"},
    "matching_terms": {"keyword", "volume", "kd"},
    "matching_terms_clusters": {"keyword", "volume", "parent topic"},
    "serp_overview": {"keyword", "position", "url", "serp features"},
    "backlinks": {"referring page", "anchor", "dr"},
    "referring_domains": {"domain", "dr", "backlinks"},
    "organic_competitors": {"domain", "common keywords", "keywords"},
    "best_by_links": {"url", "referring domains", "dofollow"},
    "internal_most_linked": {"url", "internal links"},
}


def identify_report_type(headers: list[str]) -> str:
    """Identify Ahrefs report type from headers."""
    normalized = {h.lower().strip() for h in headers}
    
    # Check each signature
    for report_type, signature in REPORT_SIGNATURES.items():
        if signature.issubset(normalized):
            return report_type
    
    # Check for simple keyword list (single column or no headers)
    if len(normalized) == 1 or not normalized:
        return "simple_keyword_list"
    
    return "unknown"


# ============================================================================
# VALUE PARSING
# ============================================================================

def parse_numeric(value: str) -> Optional[float]:
    """Parse numeric value handling Swedish/English formats."""
    if not value or value in ("-", "–", "—", "n/a", "N/A"):
        return None
    
    # Remove unicode minus
    value = value.replace("−", "-").replace("–", "-")
    
    # Handle thousand separators and decimal
    # Swedish: 1 234,56 or 1.234,56
    # English: 1,234.56
    
    # Detect format by last separator
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            # Swedish: 1.234,56
            value = value.replace(".", "").replace(",", ".")
        else:
            # English: 1,234.56
            value = value.replace(",", "")
    elif "," in value:
        # Could be Swedish decimal or English thousand
        parts = value.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            # Likely decimal: 1234,56
            value = value.replace(",", ".")
        else:
            # Likely thousand: 1,234
            value = value.replace(",", "")
    
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> Optional[int]:
    """Parse integer value."""
    num = parse_numeric(value)
    return int(num) if num is not None else None


def parse_list(value: str) -> list[str]:
    """Parse comma-separated list."""
    if not value or value in ("-", "–"):
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def detect_language(text: str) -> str:
    """Detect language from text (simple heuristic)."""
    swedish_chars = set("åäöÅÄÖ")
    if any(c in text for c in swedish_chars):
        return "sv"
    
    # Swedish common words
    swedish_words = {"och", "att", "det", "som", "för", "med", "har", "kan", "bästa", "köpa"}
    words = set(text.lower().split())
    if words & swedish_words:
        return "sv"
    
    return "en"


# ============================================================================
# MAIN NORMALIZER
# ============================================================================

@dataclass
class NormalizeResult:
    success: bool
    import_id: Optional[str] = None
    report_type: Optional[str] = None
    canonical_data: Optional[RankingImport] = None
    error: Optional[str] = None
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def normalize_headers(headers: list[str]) -> dict[str, int]:
    """Map headers to canonical names, return {canonical: index}."""
    result = {}
    for i, h in enumerate(headers):
        key = h.lower().strip()
        if key in COLUMN_ALIASES:
            result[COLUMN_ALIASES[key]] = i
    return result


def process_ahrefs_upload(
    file_content: str | bytes,
    domain: str,
    label: str,  # "mine" or "competitor"
    competitor_group: Optional[str] = None,
    project_id: str = "default",
    default_country: str = "SE",
    default_language: str = "sv"
) -> NormalizeResult:
    """
    Main entry point for Ahrefs file processing.
    
    Args:
        file_content: CSV file content as string or bytes
        domain: Domain the data is for
        label: "mine" or "competitor"
        competitor_group: Optional group name for competitors
        project_id: Project ID
        default_country: Default country code
        default_language: Default language code
    
    Returns:
        NormalizeResult with canonical data or error
    """
    try:
        # Decode if bytes
        if isinstance(file_content, bytes):
            # Try UTF-8 first, then latin-1
            try:
                content = file_content.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = file_content.decode("latin-1")
        else:
            content = file_content
        
        # Check for simple keyword list (no tabs/commas or single column)
        lines = content.strip().split("\n")
        first_line = lines[0] if lines else ""
        
        is_simple_list = (
            "\t" not in first_line and
            "," not in first_line and
            len(lines) > 0
        )
        
        if is_simple_list:
            return _process_simple_list(
                lines, domain, label, competitor_group, 
                project_id, default_country, default_language
            )
        
        # Parse as CSV
        dialect = csv.Sniffer().sniff(content[:4096])
        reader = csv.reader(io.StringIO(content), dialect)
        rows = list(reader)
        
        if len(rows) < 2:
            return NormalizeResult(
                success=False,
                error="File has no data rows",
                suggestions=["Upload a file with at least one data row"]
            )
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Identify report type
        report_type = identify_report_type(headers)
        
        # Normalize headers
        col_map = normalize_headers(headers)
        
        if "keyword" not in col_map and report_type not in ("backlinks", "referring_domains"):
            return NormalizeResult(
                success=False,
                error="No keyword column found",
                suggestions=["Ensure file has a 'Keyword' or 'Sökord' column"]
            )
        
        # Process rows
        import_rows = []
        detected_lang = None
        warnings = []
        
        for row in data_rows:
            if not row or not any(row):
                continue
            
            keyword = row[col_map["keyword"]] if "keyword" in col_map else ""
            if not keyword.strip():
                continue
            
            # Detect language from first few keywords
            if detected_lang is None:
                detected_lang = detect_language(keyword)
            
            # Generate stable ID
            kw_id = generate_keyword_id(
                keyword.lower().strip(),
                default_country,
                detected_lang or default_language
            )
            
            import_row = ImportRow(
                keyword_id=kw_id,
                keyword=keyword.strip(),
                country=row[col_map["country"]] if "country" in col_map and col_map["country"] < len(row) else default_country,
                language=detected_lang or default_language,
                position=parse_int(row[col_map["position"]]) if "position" in col_map and col_map["position"] < len(row) else None,
                url=row[col_map["url"]] if "url" in col_map and col_map["url"] < len(row) else None,
                volume=parse_int(row[col_map["volume"]]) if "volume" in col_map and col_map["volume"] < len(row) else None,
                kd=parse_numeric(row[col_map["kd"]]) if "kd" in col_map and col_map["kd"] < len(row) else None,
                traffic=parse_numeric(row[col_map["traffic"]]) if "traffic" in col_map and col_map["traffic"] < len(row) else None,
                serp_features=parse_list(row[col_map["serp_features"]]) if "serp_features" in col_map and col_map["serp_features"] < len(row) else [],
                snapshot_date=row[col_map["snapshot_date"]] if "snapshot_date" in col_map and col_map["snapshot_date"] < len(row) else datetime.now().strftime("%Y-%m-%d"),
            )
            import_rows.append(import_row)
        
        # Check for unknown columns
        known_cols = set(col_map.keys())
        all_cols = {COLUMN_ALIASES.get(h.lower().strip(), h.lower().strip()) for h in headers}
        unknown = all_cols - known_cols - {""}
        if unknown:
            warnings.append(f"Unknown columns ignored: {', '.join(unknown)}")
        
        # Generate import ID
        import_id = f"imp_{hashlib.sha1(f'{project_id}|{domain}|{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        # Build result
        ranking_import = RankingImport(
            import_id=import_id,
            project_id=project_id,
            source="ahrefs",
            report_type=report_type,
            uploaded_at=datetime.now(),
            site=SiteInfo(
                domain=domain,
                label=DomainLabel(label),
                competitor_group=competitor_group
            ),
            metadata=ImportMetadata(
                detected_language=detected_lang or default_language,
                warnings=warnings
            ),
            rows=import_rows
        )
        
        return NormalizeResult(
            success=True,
            import_id=import_id,
            report_type=report_type,
            canonical_data=ranking_import,
            warnings=warnings
        )
        
    except Exception as e:
        return NormalizeResult(
            success=False,
            error=str(e),
            suggestions=["Check file format", "Ensure valid CSV/TSV"]
        )


def _process_simple_list(
    lines: list[str],
    domain: str,
    label: str,
    competitor_group: Optional[str],
    project_id: str,
    default_country: str,
    default_language: str
) -> NormalizeResult:
    """Process a simple keyword list (one keyword per line)."""
    import_rows = []
    detected_lang = None
    
    for line in lines:
        keyword = line.strip()
        if not keyword:
            continue
        
        if detected_lang is None:
            detected_lang = detect_language(keyword)
        
        kw_id = generate_keyword_id(
            keyword.lower(),
            default_country,
            detected_lang or default_language
        )
        
        import_rows.append(ImportRow(
            keyword_id=kw_id,
            keyword=keyword,
            country=default_country,
            language=detected_lang or default_language,
            snapshot_date=datetime.now().strftime("%Y-%m-%d")
        ))
    
    import_id = f"imp_{hashlib.sha1(f'{project_id}|{domain}|{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
    
    return NormalizeResult(
        success=True,
        import_id=import_id,
        report_type="simple_keyword_list",
        canonical_data=RankingImport(
            import_id=import_id,
            project_id=project_id,
            source="simple_keyword_list",
            report_type="simple_keyword_list",
            uploaded_at=datetime.now(),
            site=SiteInfo(
                domain=domain,
                label=DomainLabel(label),
                competitor_group=competitor_group
            ),
            metadata=ImportMetadata(
                detected_language=detected_lang or default_language,
                warnings=["Simple keyword list - no volume/KD data. Consider enrichment."]
            ),
            rows=import_rows
        ),
        warnings=["Simple keyword list detected. Enrichment recommended."]
    )
