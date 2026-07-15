"""Core domain types shared by sources and aggregation."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")


# Raw sport/league labels differ per book (a US league code, or a bare sport).
# Every adapter folds its raw value through here so the same event keys the
# same way regardless of which book it came from.
_SPORT_SLUGS = {
    "nba": "nba",
    "mlb": "mlb",
    "epl": "soccer",
    "laliga": "soccer",
    "mls": "soccer",
    "soccer": "soccer",
}


def sport_slug(raw: str) -> str:
    """Normalize a raw sport or league label to the canonical sport slug."""
    return _SPORT_SLUGS.get(raw.strip().lower(), slugify(raw))


def event_key(sport: str, home: str, away: str, start_date: str) -> str:
    """Canonical event identifier, stable across bookmakers."""
    return f"{slugify(sport)}:{start_date}:{slugify(away)}@{slugify(home)}"


def parse_timestamp(stamp: str) -> float:
    """Parse an ISO-8601 timestamp to a POSIX epoch float.

    Handles a trailing ``Z`` (UTC). A naive datetime (no offset) is
    assumed to be UTC rather than local time, so ``.timestamp()`` does
    not depend on the machine's timezone.
    """
    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


@dataclass(frozen=True, slots=True)
class Quote:
    source: str
    event_key: str
    event_name: str
    sport: str
    market: str
    outcome: str
    decimal_odds: float
    fetched_at: float
