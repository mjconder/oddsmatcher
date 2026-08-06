from pathlib import Path

import pytest

from oddsmatcher.sources import NorthwoodSource, OpenlineSource, StatelineSource

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def fixtures_root() -> Path:
    return FIXTURES_ROOT


@pytest.fixture
def fixture_sources(fixtures_root):
    return [
        NorthwoodSource(fixtures_root / "northwood"),
        OpenlineSource(fixtures_root / "openline"),
        StatelineSource(fixtures_root / "stateline"),
    ]
