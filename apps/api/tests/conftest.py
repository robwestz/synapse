"""Shared fixtures for synapse-engine tests."""
import sys
from pathlib import Path

import pytest

# Ensure the api package is importable
API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

SPEC_ROOT = API_ROOT / "spec"


@pytest.fixture(scope="session")
def spec_root():
    """Path to the spec directory."""
    assert SPEC_ROOT.exists(), f"Spec root not found: {SPEC_ROOT}"
    return SPEC_ROOT


@pytest.fixture(scope="session")
def spec_pack(spec_root):
    """Loaded SpecPack with all YAML models."""
    from synapse_engine.models import load_base_pack
    return load_base_pack(spec_root)
