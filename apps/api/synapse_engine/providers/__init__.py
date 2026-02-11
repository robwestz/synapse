"""External data providers (optional).

These providers are *pluggable* and are only used when keys/credentials are present.

Design principles:
- Do not make any provider mandatory.
- Keep provider outputs normalized into small internal DTOs.
- Separate network IO from scoring/selection logic.
"""
