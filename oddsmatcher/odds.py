"""Conversions between odds formats and basic probability math.

Decimal odds are the internal lingua franca: everything else is converted
to decimal on the way in.
"""


def decimal_to_implied(odds: float) -> float:
    """Implied win probability of decimal odds, ignoring vig."""
    if odds <= 1.0:
        raise ValueError(f"decimal odds must exceed 1.0, got {odds}")
    return 1.0 / odds


def american_to_decimal(american: float) -> float:
    if american == 0:
        raise ValueError("american odds cannot be zero")
    return 1.0 + american / 100.0


def normalize_odds(raw: float | str, fmt: str) -> float:
    """Convert odds in a supported format to decimal.

    Supports ``"decimal"`` and ``"american"``. Unparseable or invalid input
    (decimal <= 1.0, American odds under 100 in magnitude) raises ``ValueError``.
    """
    if fmt == "decimal":
        value = float(raw)
        if value <= 1.0:
            raise ValueError(f"decimal odds must exceed 1.0, got {value}")
        return value
    if fmt == "american":
        american = float(raw)
        if abs(american) < 100:
            raise ValueError(f"american odds must be >= 100 in magnitude, got {raw}")
        return american_to_decimal(american)
    raise ValueError(f"unknown odds format {fmt!r}; expected 'decimal' or 'american'")
