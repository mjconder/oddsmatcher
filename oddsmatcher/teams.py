"""Canonical team names, shared across every source adapter.

Real books spell the same team differently — "Manchester City" on one
feed, "Man City" on the next, "Man. City" on a third. Event keys are
built from team names, so quotes only line up across books if each adapter
first folds its raw name onto a single canonical spelling.

Each adapter looks its raw names up here (via :func:`canonical_team`) before
building an event key. An adapter that skips this step produces keys that
never match the others, and its quotes silently drop out of the best-price
comparison.
"""

# Canonical spelling -> every raw spelling seen across the feeds.
_ALIASES: dict[str, tuple[str, ...]] = {
    "Manchester City": ("Man City", "Man. City"),
    "Bournemouth": ("AFC Bournemouth",),
    "Newcastle United": ("Newcastle", "Newcastle Utd"),
    "Liverpool": ("Liverpool FC", "LFC"),
    "Chicago Cubs": ("Chi Cubs", "Cubs"),
    "Los Angeles Dodgers": ("LA Dodgers", "Dodgers"),
    "New York Yankees": ("NY Yankees", "Yankees"),
    "St. Louis Cardinals": ("St Louis Cardinals", "Cardinals"),
}

# Raw spelling (lowercased) -> canonical spelling, built without leaking
# the loop variables as module globals.
_CANONICAL: dict[str, str] = {
    raw.lower(): canonical
    for canonical, spellings in _ALIASES.items()
    for raw in (canonical, *spellings)
}


def canonical_team(name: str) -> str:
    """Fold a bookmaker's raw team name onto its canonical spelling.

    Unknown names pass through unchanged, trimmed of surrounding
    whitespace, so a new team shows up rather than vanishing silently.
    """
    return _CANONICAL.get(name.strip().lower(), name.strip())
