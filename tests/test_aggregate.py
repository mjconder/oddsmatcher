import pytest

from oddsmatcher.aggregate import best_prices, collect_quotes
from oddsmatcher.models import Quote

CUBS_KEY = "mlb:2026-08-05:los-angeles-dodgers@chicago-cubs"
YANKEES_KEY = "mlb:2026-08-05:st-louis-cardinals@new-york-yankees"


def make_quote(**overrides) -> Quote:
    defaults = {
        "source": "northwood",
        "event_key": CUBS_KEY,
        "event_name": "Los Angeles Dodgers @ Chicago Cubs",
        "sport": "mlb",
        "market": "moneyline",
        "outcome": "home",
        "decimal_odds": 2.60,
        "fetched_at": 1_000.0,
    }
    defaults.update(overrides)
    return Quote(**defaults)


class TestBestPrices:
    def test_picks_highest_price_per_outcome(self):
        quotes = [
            make_quote(source="northwood", decimal_odds=2.60),
            make_quote(source="openline", decimal_odds=2.66),
            make_quote(source="stateline", decimal_odds=2.70),
        ]
        (view,) = best_prices(quotes)
        assert view.prices["home"].decimal_odds == pytest.approx(2.70)
        assert view.prices["home"].source == "stateline"

    def test_outcomes_tracked_independently(self):
        quotes = [
            make_quote(outcome="home", source="stateline", decimal_odds=2.70),
            make_quote(outcome="home", source="openline", decimal_odds=2.66),
            make_quote(outcome="away", source="stateline", decimal_odds=1.50),
            make_quote(outcome="away", source="openline", decimal_odds=1.52),
        ]
        (view,) = best_prices(quotes)
        assert view.prices["home"].source == "stateline"
        assert view.prices["away"].source == "openline"

    def test_stale_quotes_excluded(self):
        quotes = [
            make_quote(source="northwood", decimal_odds=1.53, fetched_at=100.0),
            make_quote(source="openline", decimal_odds=1.52, fetched_at=2_000.0),
        ]
        (view,) = best_prices(quotes, horizon=900.0, now=2_000.0)
        assert view.prices["home"].decimal_odds == pytest.approx(1.52)

    def test_now_defaults_to_latest_capture(self):
        quotes = [
            make_quote(source="northwood", decimal_odds=1.53, fetched_at=100.0),
            make_quote(source="openline", decimal_odds=1.52, fetched_at=5_000.0),
        ]
        (view,) = best_prices(quotes, horizon=900.0)
        assert view.prices["home"].source == "openline"

    def test_market_with_only_stale_quotes_dropped(self):
        quotes = [
            make_quote(fetched_at=100.0),
            make_quote(event_key="other", event_name="Other", fetched_at=2_000.0),
        ]
        views = best_prices(quotes, horizon=900.0, now=2_000.0)
        assert [view.event_key for view in views] == ["other"]

    def test_markets_grouped_separately(self):
        quotes = [
            make_quote(market="moneyline"),
            make_quote(market="spread", decimal_odds=1.91),
        ]
        views = best_prices(quotes)
        assert {view.market for view in views} == {"moneyline", "spread"}

    def test_views_sorted_by_event_key(self):
        quotes = [
            make_quote(event_key="z-event", event_name="Z"),
            make_quote(event_key="a-event", event_name="A"),
        ]
        views = best_prices(quotes)
        assert [view.event_key for view in views] == ["a-event", "z-event"]

    def test_empty_input(self):
        assert best_prices([]) == []


class TestFixtureAggregation:
    @pytest.fixture
    def views(self, fixture_sources):
        return best_prices(collect_quotes(fixture_sources))

    def test_cubs_best_prices_merge_across_books(self, views):
        (cubs,) = [v for v in views if v.event_key == CUBS_KEY]
        # away's best is openline's back price, home's best is stateline's line:
        # the winning quotes come from two different books.
        assert cubs.prices["away"].decimal_odds == pytest.approx(1.52)
        assert cubs.prices["away"].source == "openline"
        assert cubs.prices["home"].decimal_odds == pytest.approx(2.70)
        assert cubs.prices["home"].source == "stateline"

    def test_stale_northwood_cubs_capture_excluded(self, views):
        (cubs,) = [v for v in views if v.event_key == CUBS_KEY]
        # The stale northwood capture quotes away at 1.53; if it were not
        # dropped it would beat openline's fresh 1.52.
        assert cubs.prices["away"].source != "northwood"
        assert cubs.prices["away"].decimal_odds == pytest.approx(1.52)

    def test_partial_coverage_event_still_shown(self, views):
        # Openline carries no Yankees market, yet the event still surfaces
        # from the books that do (stateline + northwood).
        (yankees,) = [v for v in views if v.event_key == YANKEES_KEY]
        assert yankees.prices["home"].source == "northwood"
        assert yankees.prices["home"].decimal_odds == pytest.approx(1.30)
        assert yankees.prices["away"].source == "stateline"
        assert yankees.prices["away"].decimal_odds == pytest.approx(3.80)

    def test_all_four_events_present(self, views):
        assert len(views) == 4
