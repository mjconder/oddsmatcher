"""Adapter for Northwood: decimal prices, ISO-8601 capture times."""

from oddsmatcher.models import Quote, event_key, parse_timestamp, sport_slug
from oddsmatcher.odds import normalize_odds
from oddsmatcher.sources.base import FixtureSource
from oddsmatcher.teams import canonical_team


class NorthwoodSource(FixtureSource):
    name = "northwood"

    def fetch_quotes(self) -> list[Quote]:
        quotes: list[Quote] = []
        for document in self._documents():
            fetched_at = parse_timestamp(document["fetched_at"])
            for market in document["markets"]:
                sport = sport_slug(market["sport"])
                home = canonical_team(market["home"])
                away = canonical_team(market["away"])
                key = event_key(sport, home, away, market["start_date"])
                event_name = f"{away} @ {home}"
                for entry in market["outcomes"]:
                    decimal = normalize_odds(entry["price"], "decimal")
                    quotes.append(
                        Quote(
                            source=self.name,
                            event_key=key,
                            event_name=event_name,
                            sport=sport,
                            market=market["market"],
                            outcome=entry["label"],
                            decimal_odds=decimal,
                            fetched_at=fetched_at,
                        )
                    )
        return quotes
