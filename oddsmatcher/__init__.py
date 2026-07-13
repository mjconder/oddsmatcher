"""oddsmatcher: aggregate bookmaker odds and show the best available price."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("oddsmatcher")
except PackageNotFoundError:  # pragma: no cover - not installed
    __version__ = "0.0.0"
