# oddsmatcher

![CI](https://github.com/mjconder/oddsmatcher/actions/workflows/ci.yml/badge.svg)

Aggregate bookmaker odds across several books and show the best available
price per outcome — price comparison for odds, i.e. line shopping.

oddsmatcher ingests quote feeds from multiple sources, normalizes every book's
format to a common decimal model, and surfaces the best available price for
each outcome of each market. Quotes older than a staleness horizon are
excluded so a stale feed can't win the comparison.

All bundled sources are fixture-backed: they replay captured bookmaker
responses from `fixtures/`, so the whole thing runs offline and
deterministically. Each adapter still does the real normalization work its
live counterpart would (odds format conversion, timestamp parsing, ladder
handling), which keeps the pipeline honest.

## Quickstart

```console
$ python -m venv .venv && source .venv/bin/activate
$ pip install -e ".[dev]"
$ oddsmatcher scan
Los Angeles Dodgers @ Chicago Cubs [moneyline]
  away     1.52  (openline)
  home     2.70  (stateline)
...
```

Each line is the best price on offer for that outcome and the book quoting it.

## Architecture

```
oddsmatcher/
  odds.py        odds format conversions and implied probability
  models.py      Quote and the canonical event key
  teams.py       canonical team names shared across adapters
  sources/       OddsSource interface + one adapter per feed
    northwood.py     decimal odds, ISO-8601 capture timestamps
    openline.py      exchange-style back/lay ladders (best back wins)
    stateline.py     American odds, epoch-millisecond timestamps
  aggregate.py   merge quotes into best-price views, staleness horizon
  cli.py         `oddsmatcher scan`
```

Decimal odds are the internal representation. Adapters convert on ingest via
`oddsmatcher.odds.normalize_odds`, which raises `ValueError` on an unusable price
(unknown format, American odds under 100 in magnitude, decimal at or below
1.0), so a malformed quote fails loudly rather than polluting the best-price
view.

Events are matched across books with a canonical key built from sport, date,
and slugified team names
(`soccer:2026-08-05:bournemouth@manchester-city`), so the three feeds don't
need to share IDs. Real books spell teams differently — Openline's
"Manchester City", Stateline's "Man City", Northwood's "Man. City" — so each
adapter folds its raw names onto a canonical spelling
(`oddsmatcher.teams.canonical_team`) before building the key. Skip that step in a
new adapter and its keys never match the others: the quotes just vanish from
the comparison.

### Staleness

`aggregate.best_prices` drops quotes older than a horizon (default 15
minutes). "Now" defaults to the newest capture time in the batch, so replayed
fixture data is judged against its own clock — one deliberately stale
northwood capture in the fixtures demonstrates the cutoff.

## Fixture format

Each source reads every `*.json` under its directory in `fixtures/`. The
formats intentionally differ per book — that is the point of the adapters:

- `fixtures/northwood/` — decimal prices, ISO-8601 `fetched_at`, one flat
  `markets` list with labeled outcomes.
- `fixtures/openline/` — exchange snapshot with per-runner `back`/`lay`
  price ladders; only back prices become quotes.
- `fixtures/stateline/` — American odds, `generated_ts` in epoch
  milliseconds, `3way_moneyline` mapped onto the canonical match-winner
  market.

The same real-world events appear across the books with different team-name
spellings on purpose (see "Staleness" above): the adapters canonicalize
before keying, so the merged view shows each event once. Coverage is
deliberately partial — openline carries no Yankees market — so the merge has
to surface an event from just the books that quote it.

Add a new capture by dropping another JSON file into the source's directory;
files are read in sorted order.

## Development

```console
$ pip install -e ".[dev]"
$ pytest
```

The suite is fully offline: clocks are injected where timing matters and no
test sleeps or touches the network.

Enable the pre-commit hook to run the tests before each commit:

```console
$ git config core.hooksPath .githooks
```

CI runs ruff, strict mypy, and the test suite (the latter inside the
`Dockerfile` image) on every push and pull request, so a lint error, a type
error, a broken build, or a failing test blocks the change.

## License

[MIT](LICENSE) — see the `LICENSE` file for the full text.
