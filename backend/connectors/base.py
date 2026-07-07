"""Connector registry. A connector is a callable: (source, log) -> list[FetchedPage]."""

from __future__ import annotations

from typing import Callable

from .filedrop import gather_filedrop
from .ics import gather_ics
from .sitemap import gather_sitemap

# "web" is handled by the pipeline itself (the original _gather_pages logic);
# this registry only lists the alternates.
CONNECTORS: dict[str, Callable] = {
    "sitemap": gather_sitemap,
    "ics": gather_ics,
    "filedrop": gather_filedrop,
}


def get_connector(name: str) -> Callable:
    if name not in CONNECTORS:
        raise ValueError(f"Unknown connector '{name}' (available: web, {', '.join(CONNECTORS)})")
    return CONNECTORS[name]
