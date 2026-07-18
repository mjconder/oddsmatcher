"""Merge quotes across sources into best-price views per market."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from oddsmatcher.models import Quote
from oddsmatcher.sources.base import OddsSource

DEFAULT_HORIZON = 900.0


@dataclass(frozen=True, slots=True)
class BestPrice:
    decimal_odds: float
    source: str
    fetched_at: float


@dataclass(frozen=True, slots=True)
class MarketView:
    event_key: str
    event_name: str
    sport: str
    market: str
    prices: Mapping[str, BestPrice]


def collect_quotes(sources: Iterable[OddsSource]) -> list[Quote]:
    quotes: list[Quote] = []
    for source in sources:
        quotes.extend(source.fetch_quotes())
    return quotes


def best_prices(
    quotes: Iterable[Quote],
    *,
    horizon: float = DEFAULT_HORIZON,
    now: float | None = None,
) -> list[MarketView]:
    """Best available decimal price per outcome, per market.

    Quotes older than ``horizon`` seconds are discarded. ``now`` defaults
    to the newest capture time in the batch, so replayed fixture data is
    judged against its own clock rather than wall time.
    """
    quotes = list(quotes)
    if not quotes:
        return []
    cutoff = (now if now is not None else max(q.fetched_at for q in quotes)) - horizon
    grouped: dict[tuple[str, str], list[Quote]] = {}
    for quote in quotes:
        if quote.fetched_at < cutoff:
            continue
        grouped.setdefault((quote.event_key, quote.market), []).append(quote)

    views: list[MarketView] = []
    for (key, market), members in sorted(grouped.items()):
        best: dict[str, BestPrice] = {}
        for quote in members:
            current = best.get(quote.outcome)
            if current is None or quote.decimal_odds > current.decimal_odds:
                best[quote.outcome] = BestPrice(
                    quote.decimal_odds, quote.source, quote.fetched_at
                )
        views.append(
            MarketView(
                event_key=key,
                event_name=members[0].event_name,
                sport=members[0].sport,
                market=market,
                prices=best,
            )
        )
    return views
