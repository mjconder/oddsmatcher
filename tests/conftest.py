from pathlib import Path

import pytest

from oddsmatcher.sources import NorthwoodSource, OpenlineSource, StatelineSource

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


class FakeClock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()
