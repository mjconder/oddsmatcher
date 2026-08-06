import json

import pytest

from oddsmatcher.models import event_key, slugify
from oddsmatcher.sources import (
    NorthwoodSource,
    OpenlineSource,
    SourceError,
    StatelineSource,
)
from oddsmatcher.teams import canonical_team

MANCITY_KEY = "soccer:2026-08-05:bournemouth@manchester-city"
NEWCASTLE_KEY = "soccer:2026-08-05:liverpool@newcastle-united"
CUBS_KEY = "mlb:2026-08-05:los-angeles-dodgers@chicago-cubs"
YANKEES_KEY = "mlb:2026-08-05:st-louis-cardinals@new-york-yankees"

NORTHWOOD_FRESH_TS = 1785866400.0
NORTHWOOD_STALE_TS = 1785865200.0
OPENLINE_TS = 1785866460.0
STATELINE_TS = 1785866520.0


class TestNorthwood:
    @pytest.fixture
    def quotes(self, fixtures_root):
        return NorthwoodSource(fixtures_root / "northwood").fetch_quotes()

    def test_reads_all_captures(self, quotes):
        assert len(quotes) == 10

    def test_fresh_mancity_home_price(self, quotes):
        (quote,) = [
            q for q in quotes if q.event_key == MANCITY_KEY and q.outcome == "home"
        ]
        assert quote.decimal_odds == pytest.approx(1.46)
        assert quote.event_name == "Bournemouth @ Manchester City"
        assert quote.market == "match_winner"
        assert quote.fetched_at == NORTHWOOD_FRESH_TS

    def test_iso_timestamps_parsed_to_epoch(self, quotes):
        assert {q.fetched_at for q in quotes} == {
            NORTHWOOD_FRESH_TS,
            NORTHWOOD_STALE_TS,
        }

    def test_stale_cubs_capture_has_old_timestamp(self, quotes):
        cubs = [q for q in quotes if q.event_key == CUBS_KEY]
        assert cubs
        assert all(q.fetched_at == NORTHWOOD_STALE_TS for q in cubs)


class TestOpenline:
    @pytest.fixture
    def quotes(self, fixtures_root):
        return OpenlineSource(fixtures_root / "openline").fetch_quotes()

    def test_one_quote_per_runner(self, quotes):
        assert len(quotes) == 8

    def test_takes_best_back_price(self, quotes):
        (quote,) = [
            q for q in quotes if q.event_key == MANCITY_KEY and q.outcome == "home"
        ]
        assert quote.decimal_odds == pytest.approx(1.44)

    def test_lay_prices_ignored(self, quotes):
        prices = {q.decimal_odds for q in quotes if q.event_key == MANCITY_KEY}
        assert 1.51 not in prices
        assert 6.04 not in prices

    def test_capture_time_parsed(self, quotes):
        assert all(q.fetched_at == OPENLINE_TS for q in quotes)

    def test_does_not_carry_yankees(self, quotes):
        assert YANKEES_KEY not in {q.event_key for q in quotes}

    def test_runner_without_back_liquidity_skipped(self, tmp_path):
        doc = {
            "exchange": "openline",
            "captured_at": "2026-08-04T18:01:00+00:00",
            "markets": [
                {
                    "market_id": "1.1",
                    "sport": "mlb",
                    "market_type": "moneyline",
                    "event": {"home": "A", "away": "B", "start_date": "2026-08-05"},
                    "runners": [
                        {
                            "selection": "home",
                            "back": [],
                            "lay": [{"price": 1.9, "size": 10.0}],
                        },
                        {
                            "selection": "away",
                            "back": [{"price": 2.1, "size": 50.0}],
                            "lay": [],
                        },
                    ],
                }
            ],
        }
        (tmp_path / "doc.json").write_text(json.dumps(doc))
        quotes = OpenlineSource(tmp_path).fetch_quotes()
        assert [q.outcome for q in quotes] == ["away"]


class TestStateline:
    @pytest.fixture
    def quotes(self, fixtures_root):
        return StatelineSource(fixtures_root / "stateline").fetch_quotes()

    def test_quote_count(self, quotes):
        assert len(quotes) == 10

    def test_american_odds_converted(self, quotes):
        by_outcome = {q.outcome: q for q in quotes if q.event_key == CUBS_KEY}
        assert by_outcome["home"].decimal_odds == pytest.approx(2.70)
        assert by_outcome["away"].decimal_odds == pytest.approx(1.0 + 100 / 200)

    def test_epoch_millis_converted_to_seconds(self, quotes):
        assert all(q.fetched_at == STATELINE_TS for q in quotes)

    def test_three_way_bet_type_mapped(self, quotes):
        mancity = [q for q in quotes if q.event_key == MANCITY_KEY]
        assert len(mancity) == 3
        assert all(q.market == "match_winner" for q in mancity)
        assert all(q.sport == "soccer" for q in mancity)

    def test_mlb_league_mapped(self, quotes):
        yankees = [q for q in quotes if q.event_key == YANKEES_KEY]
        assert len(yankees) == 2
        assert all(q.sport == "mlb" for q in yankees)
        assert all(q.market == "moneyline" for q in yankees)


class TestCrossSource:
    def test_event_keys_line_up_across_adapters(self, fixtures_root):
        northwood = {
            q.event_key
            for q in NorthwoodSource(fixtures_root / "northwood").fetch_quotes()
        }
        openline = {
            q.event_key
            for q in OpenlineSource(fixtures_root / "openline").fetch_quotes()
        }
        stateline = {
            q.event_key
            for q in StatelineSource(fixtures_root / "stateline").fetch_quotes()
        }
        # Openline drops the Yankees game (partial coverage); the other three
        # events are carried by every book and share one canonical key each.
        shared = {MANCITY_KEY, NEWCASTLE_KEY, CUBS_KEY}
        assert shared <= northwood
        assert shared <= openline
        assert shared <= stateline
        assert YANKEES_KEY in northwood
        assert YANKEES_KEY in stateline
        assert YANKEES_KEY not in openline

    def test_team_spellings_canonicalized_before_keying(self, fixtures_root):
        # Each book spells Man City differently in its raw fixture
        # ("Manchester City" / "Man City" / "Man. City"); all three must
        # still land on the same canonical event key.
        for source_cls, subdir in (
            (NorthwoodSource, "northwood"),
            (OpenlineSource, "openline"),
            (StatelineSource, "stateline"),
        ):
            keys = {
                q.event_key for q in source_cls(fixtures_root / subdir).fetch_quotes()
            }
            assert MANCITY_KEY in keys


class TestSportSlugConsistency:
    def test_same_sport_slug_across_books(self, fixtures_root):
        # Every adapter must store the SAME sport value for a shared event.
        by_source = {}
        for cls, subdir in (
            (NorthwoodSource, "northwood"),
            (OpenlineSource, "openline"),
            (StatelineSource, "stateline"),
        ):
            for q in cls(fixtures_root / subdir).fetch_quotes():
                by_source.setdefault(q.event_key, set()).add(q.sport)
        for key, sports in by_source.items():
            assert len(sports) == 1, f"{key} has inconsistent sports {sports}"


class TestCanonicalTeam:
    def test_known_alias_folds(self):
        assert canonical_team("Man City") == "Manchester City"

    def test_unknown_name_passes_through(self):
        assert canonical_team("Some New FC") == "Some New FC"

    def test_whitespace_trimmed(self):
        assert canonical_team("  Cubs  ") == "Chicago Cubs"
        assert canonical_team("  Some New FC  ") == "Some New FC"


class TestSlugAndEventKey:
    def test_slugify(self):
        assert slugify("St. Louis Cardinals") == "st-louis-cardinals"
        assert slugify("Manchester City") == "manchester-city"

    def test_event_key_is_stable(self):
        assert (
            event_key("MLB", "Chicago Cubs", "Los Angeles Dodgers", "2026-08-05")
            == "mlb:2026-08-05:los-angeles-dodgers@chicago-cubs"
        )


class TestFixtureErrors:
    def test_missing_directory(self, tmp_path):
        with pytest.raises(SourceError, match="not found"):
            NorthwoodSource(tmp_path / "nope").fetch_quotes()

    def test_empty_directory(self, tmp_path):
        with pytest.raises(SourceError, match="no fixtures"):
            NorthwoodSource(tmp_path).fetch_quotes()

    def test_malformed_json(self, tmp_path):
        (tmp_path / "bad.json").write_text("{not json")
        with pytest.raises(SourceError, match="malformed"):
            StatelineSource(tmp_path).fetch_quotes()

    def test_schema_error_becomes_source_error(self, tmp_path):
        # Valid JSON but a missing required key is wrapped like malformed JSON,
        # so a schema break surfaces as a SourceError naming the file rather
        # than a raw KeyError from deep inside an adapter. This locks the base
        # class's wrapping in: an adapter that reintroduced its own
        # fetch_quotes would bypass it and fail here.
        (tmp_path / "doc.json").write_text('{"markets": []}')  # no fetched_at
        with pytest.raises(SourceError, match="malformed fixture doc.json"):
            NorthwoodSource(tmp_path).fetch_quotes()
