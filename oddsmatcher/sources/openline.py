"""Adapter for Openline's exchange feed: back/lay price ladders.

Openline is a betting exchange, so prices come as back/lay ladders rather
than a single book price. Only back prices are turned into quotes: a back
bet is what a price comparison can actually take. Runners without back
liquidity are skipped.
"""

from typing import Any

from oddsmatcher.models import Quote, event_key, parse_timestamp, sport_slug
from oddsmatcher.odds import normalize_odds
from oddsmatcher.sources.base import FixtureSource
from oddsmatcher.teams import canonical_team


class OpenlineSource(FixtureSource):
    name = "openline"

    def _quotes_from(self, document: dict[str, Any]) -> list[Quote]:
        quotes: list[Quote] = []
        captured_at = parse_timestamp(document["captured_at"])
        for market in document["markets"]:
            event = market["event"]
            sport = sport_slug(market["sport"])
            home = canonical_team(event["home"])
            away = canonical_team(event["away"])
            key = event_key(sport, home, away, event["start_date"])
            event_name = f"{away} @ {home}"
            for runner in market["runners"]:
                ladder = runner.get("back") or []
                if not ladder:
                    continue
                best_back = max(level["price"] for level in ladder)
                decimal = normalize_odds(best_back, "decimal")
                quotes.append(
                    Quote(
                        source=self.name,
                        event_key=key,
                        event_name=event_name,
                        sport=sport,
                        market=market["market_type"],
                        outcome=runner["selection"],
                        decimal_odds=decimal,
                        fetched_at=captured_at,
                    )
                )
        return quotes
