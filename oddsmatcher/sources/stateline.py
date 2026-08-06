"""Adapter for Stateline: American odds, epoch-millisecond timestamps."""

from typing import Any

from oddsmatcher.models import Quote, event_key, sport_slug
from oddsmatcher.odds import normalize_odds
from oddsmatcher.sources.base import FixtureSource
from oddsmatcher.teams import canonical_team

_BET_TYPES = {
    "moneyline": "moneyline",
    "3way_moneyline": "match_winner",
}


class StatelineSource(FixtureSource):
    name = "stateline"

    def _quotes_from(self, document: dict[str, Any]) -> list[Quote]:
        quotes: list[Quote] = []
        fetched_at = document["generated_ts"] / 1000.0
        for line in document["lines"]:
            sport = sport_slug(line["league"])
            home = canonical_team(line["home_team"])
            away = canonical_team(line["away_team"])
            key = event_key(sport, home, away, line["game_date"])
            event_name = f"{away} @ {home}"
            market = _BET_TYPES.get(line["bet_type"], line["bet_type"])
            for side in line["prices"]:
                decimal = normalize_odds(side["american"], "american")
                quotes.append(
                    Quote(
                        source=self.name,
                        event_key=key,
                        event_name=event_name,
                        sport=sport,
                        market=market,
                        outcome=side["side"],
                        decimal_odds=decimal,
                        fetched_at=fetched_at,
                    )
                )
        return quotes
