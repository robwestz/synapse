"""
Ahrefs Data Normalizer
Integrates with existing normalization system at .agent/workflows/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import re


class AhrefsNormalizer:
    """
    Wrapper around existing Ahrefs normalization logic
    Handles all 10 report types from Ahrefs
    """

    # Report Type Signatures (from normaliserauppdata.md)
    REPORT_SIGNATURES = {
        'serp_overview': {'Parent Topic Volume', 'Type', 'Title'},
        'organic_keywords': {'Previous organic traffic', 'Current organic traffic', 'Branded'},
        'matching_terms_keywords': {'Parent Keyword', 'Traffic potential'},  # AND NOT Term group
        'matching_terms_clusters': {'Term group', 'Parent Keyword'},
        'clusters_by_parent_topic': {'Parent Topic', 'Cluster Volume', 'Cluster keywords'},
        'backlinks': {'Referring page URL', 'Anchor', 'Lost status'},
        'referring_domains': {'Dofollow ref. domains', 'Dofollow linked domains'},
        'organic_competitors': {"Competitor's keywords", 'Common keywords', 'Share'},
        'best_by_links': {'Top DR', 'Referring domains', 'Page URL'},
        'internal_most_linked': {'Canonical', 'Links to target', 'Page URL'}  # AND NOT Top DR
    }

    # Column Name Standardization
    COLUMN_MAPPING = {
        'KD': 'difficulty',
        'Difficulty': 'difficulty',
        'DR': 'domain_rating',
        'Domain rating': 'domain_rating',
        'UR': 'url_rating',
        'URL rating': 'url_rating',
        'SERP features': 'serp_features',
        'SERP Features': 'serp_features',
        '#': 'row_number'
    }

    # List columns (comma-separated → arrays)
    LIST_COLUMNS = [
        'serp_features', 'Intents', 'Languages',
        'Redirect Chain URLs', 'Redirect Chain status codes',
        'Entities'
    }

    def __init__(self):
        self.validation_errors = []

    def identify_report_type(self, df: pd.DataFrame) -> str:
        """
        Identify which of 10 Ahrefs report types this DataFrame represents
        """
        columns = set(df.columns)

        # Check each signature
        for report_type, signature in self.REPORT_SIGNATURES.items():
            if signature.issubset(columns):
                # Special cases that need exclusion checks
                if report_type == 'matching_terms_keywords':
                    if 'Term group' in columns or 'Cluster Volume' in columns:
                        continue
                elif report_type == 'internal_most_linked':
                    if 'Top DR' in columns:
                        continue

                return report_type

        return 'unknown'

    def normalize(self, df: pd.DataFrame, report_type: str) -> pd.DataFrame:
        """
        Apply all normalization transformations
        """
        # 1. Standardize column names
        df = self._standardize_columns(df)

        # 2. Transform data types
        df = self._transform_booleans(df)
        df = self._transform_numerics(df)
        df = self._parse_lists(df)
        df = self._parse_dates(df)

        # 3. Add metadata columns
        df['_normalized_at'] = datetime.utcnow()
        df['_report_type'] = report_type

        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names according to mapping
        """
        rename_map = {}
        for old_name, new_name in self.COLUMN_MAPPING.items():
            if old_name in df.columns:
                rename_map[old_name] = new_name

        df = df.rename(columns=rename_map)

        # Convert column names to snake_case
        df.columns = [self._to_snake_case(col) for col in df.columns]

        return df

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        text = re.sub(r'[\s\-]+', '_', text)
        text = re.sub(r'[^\w_]', '', text)
        return text.lower()

    def _transform_booleans(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform boolean values: TRUE/FALSE → true/false, empty → null
        """
        bool_candidates = df.select_dtypes(include=['object']).columns

        for col in bool_candidates:
            if df[col].isin(['TRUE', 'FALSE', '']).all():
                df[col] = df[col].replace({
                    'TRUE': True,
                    'FALSE': False,
                    '': None
                })

        return df

    def _transform_numerics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform numeric values:
        - Comma → period for decimals
        - Unicode minus → standard minus
        - Remove % symbols
        - Empty → null
        """
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    # Replace comma with period
                    df[col] = df[col].str.replace(',', '.')

                    # Replace unicode minus
                    df[col] = df[col].str.replace('−', '-')

                    # Remove % symbols (keep as number)
                    df[col] = df[col].str.replace('%', '')

                    # Convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except (AttributeError, ValueError):
                    pass

        return df

    def _parse_lists(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse comma-separated columns into arrays
        """
        for col in self.LIST_COLUMNS:
            # Check both original and normalized column names
            col_variants = [col, self._to_snake_case(col)]

            for col_variant in col_variants:
                if col_variant in df.columns:
                    df[col_variant] = df[col_variant].apply(
                        lambda x: self._split_comma_list(x) if pd.notna(x) else None
                    )

        return df

    def _split_comma_list(self, value: str) -> List[str]:
        """Split comma-separated string into list"""
        if not value or value == '':
            return []

        return [item.strip() for item in str(value).split(',')]

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse date columns to datetime
        Format: YYYY-MM-DD HH:MM:SS
        """
        date_candidates = ['first_seen', 'last_seen', 'discovered_status',
                          'previous_date', 'current_date', 'last_update',
                          'upload_date']

        for col in df.columns:
            if any(date_word in col.lower() for date_word in ['date', 'seen', 'update']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass

        return df

    def validate(self, df: pd.DataFrame, report_type: str) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame against report type requirements
        Returns: (is_valid, list_of_errors)
        """
        errors = []

        # Get required columns for this report type
        required_columns = self._get_required_columns(report_type)

        # Check if required columns exist
        df_columns = set(df.columns)
        missing_columns = set(required_columns) - df_columns

        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check if DataFrame has data
        if len(df) == 0:
            errors.append("File contains only header, no data rows")

        # Validate data ranges for critical columns
        if report_type in ['organic_keywords', 'backlinks']:
            if 'domain_rating' in df.columns:
                invalid_dr = df[
                    (df['domain_rating'] < 0) | (df['domain_rating'] > 100)
                ]
                if len(invalid_dr) > 0:
                    errors.append(f"Invalid domain_rating values (should be 0-100): {len(invalid_dr)} rows")

        return len(errors) == 0, errors

    def _get_required_columns(self, report_type: str) -> List[str]:
        """
        Get list of required columns for each report type
        """
        required = {
            'serp_overview': ['keyword', 'url', 'position'],
            'organic_keywords': ['keyword', 'position', 'volume'],
            'backlinks': ['referring_page_url', 'target_url'],
            'referring_domains': ['domain'],
            # ... add others as needed
        }

        return required.get(report_type, [])

    def extract_metadata(self, df: pd.DataFrame, report_type: str, file_path: Optional[str] = None) -> Dict:
        """
        Extract metadata about the upload
        """
        metadata = {
            'report_type': report_type,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'upload_date': datetime.utcnow().isoformat(),
        }

        # Extract date range if available
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if date_columns:
            for col in date_columns:
                try:
                    metadata['data_date_range'] = {
                        'from': df[col].min().isoformat() if pd.notna(df[col].min()) else None,
                        'to': df[col].max().isoformat() if pd.notna(df[col].max()) else None
                    }
                    break
                except:
                    pass

        # Extract domain if possible
        if 'url' in df.columns:
            try:
                sample_url = df['url'].dropna().iloc[0]
                domain = self._extract_domain(sample_url)
                metadata['source_domain'] = domain
            except:
                pass

        # File hash for deduplication
        if file_path:
            metadata['file_hash'] = self._calculate_file_hash(file_path)

        return metadata

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return 'unknown'

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return 'unknown'


# Convenience function
def normalize_ahrefs_export(file_path: str, is_primary: bool = False) -> Tuple[pd.DataFrame, Dict, str]:
    """
    Main entry point for normalizing Ahrefs exports

    Args:
        file_path: Path to CSV/Excel file
        is_primary: Whether this is the user's primary site (vs competitor)

    Returns:
        (normalized_dataframe, metadata, report_type)
    """
    normalizer = AhrefsNormalizer()

    # Read file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    # Identify report type
    report_type = normalizer.identify_report_type(df)

    if report_type == 'unknown':
        raise ValueError(
            f"Could not identify report type. Found columns: {', '.join(df.columns[:10])}... "
            f"Please verify this is an Ahrefs export."
        )

    # Validate
    is_valid, errors = normalizer.validate(df, report_type)
    if not is_valid:
        raise ValueError(f"Validation failed: {', '.join(errors)}")

    # Normalize
    normalized_df = normalizer.normalize(df, report_type)

    # Extract metadata
    metadata = normalizer.extract_metadata(normalized_df, report_type, file_path)
    metadata['is_primary'] = is_primary

    return normalized_df, metadata, report_type
