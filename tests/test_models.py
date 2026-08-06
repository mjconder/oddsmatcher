from datetime import datetime, timezone

import pytest

from oddsmatcher.models import event_key, parse_timestamp, slugify, sport_slug
from oddsmatcher.teams import canonical_team


def test_sport_slug_unifies_league_and_sport_labels():
    # Every adapter's raw label must fold to the same canonical sport slug,
    # or the same event keys differently across books and never merges.
    assert sport_slug("EPL") == "soccer"
    assert sport_slug("soccer") == "soccer"
    assert sport_slug("MLB") == sport_slug("mlb") == "mlb"
    assert sport_slug("NBA") == "nba"
    assert sport_slug("KHL") == "khl"  # unknown → slugified passthrough


def test_parse_timestamp_naive_is_utc_not_local():
    # A stamp with no offset must be read as UTC, so the epoch value does not
    # depend on the machine's timezone.
    expected = datetime(2026, 3, 14, 23, 33, 5, tzinfo=timezone.utc).timestamp()
    assert parse_timestamp("2026-03-14T23:33:05") == expected


def test_parse_timestamp_handles_trailing_z():
    assert parse_timestamp("2026-03-14T23:33:05Z") == parse_timestamp(
        "2026-03-14T23:33:05+00:00"
    )


def test_canonical_team_maps_aliases_and_passes_through_unknowns():
    assert canonical_team("Man City") == "Manchester City"
    assert canonical_team("Manchester City") == "Manchester City"
    assert canonical_team("  Unlisted Town FC  ") == "Unlisted Town FC"


def test_event_key_is_stable_across_casing():
    assert event_key("NBA", "Los Angeles Lakers", "Boston Celtics", "2026-03-15") == (
        event_key("nba", "los angeles lakers", "BOSTON CELTICS", "2026-03-15")
    )
    assert slugify("Los Angeles Lakers") == slugify("los angeles lakers")


def test_event_key_rejects_non_iso_date():
    # A malformed date must fail where the key is built, not get baked into a
    # key that silently never matches another book's.
    with pytest.raises(ValueError):
        event_key("mlb", "Chicago Cubs", "Los Angeles Dodgers", "08/05/2026")
