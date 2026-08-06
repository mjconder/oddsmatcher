"""Source interface and shared fixture-loading plumbing."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from oddsmatcher.models import Quote


class SourceError(RuntimeError):
    """Raised when a source cannot produce quotes."""


class OddsSource(ABC):
    name: str = "unknown"

    @abstractmethod
    def fetch_quotes(self) -> list[Quote]:
        """Return every quote the source currently offers."""


class FixtureSource(OddsSource):
    """Base class for adapters that replay captured bookmaker responses."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def fetch_quotes(self) -> list[Quote]:
        quotes: list[Quote] = []
        for name, document in self._documents():
            # A fixture can be valid JSON yet still be malformed for this
            # adapter (missing key, wrong type, unusable price). Turn those
            # into a SourceError naming the file, not a raw traceback.
            try:
                quotes.extend(self._quotes_from(document))
            except (KeyError, TypeError, ValueError) as exc:
                raise SourceError(
                    f"{self.name}: malformed fixture {name}: {exc}"
                ) from exc
        return quotes

    @abstractmethod
    def _quotes_from(self, document: dict[str, Any]) -> list[Quote]:
        """Parse a single fixture document into quotes."""

    def _documents(self) -> list[tuple[str, dict[str, Any]]]:
        if not self.root.is_dir():
            raise SourceError(f"{self.name}: fixture directory {self.root} not found")
        documents: list[tuple[str, dict[str, Any]]] = []
        for path in sorted(self.root.glob("*.json")):
            try:
                documents.append((path.name, json.loads(path.read_text())))
            except json.JSONDecodeError as exc:
                raise SourceError(
                    f"{self.name}: malformed fixture {path.name}: {exc}"
                ) from exc
        if not documents:
            raise SourceError(f"{self.name}: no fixtures under {self.root}")
        return documents
