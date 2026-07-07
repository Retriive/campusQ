"""Source registry — which URLs each school ingests, and how.

Two layers, merged at load time:
  1. schools/<school>/sources.json      — versioned in git, reviewed like code
  2. admin-added sources (SQLite)       — added at runtime via the admin API

Adding a new university = writing a new sources.json. No scraper code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

VALID_EXTRACTORS = ("auto", "course_regex", "llm_courses", "llm_dates", "llm_generic")
VALID_CONNECTORS = ("web", "sitemap", "ics", "filedrop")


@dataclass
class Source:
    school: str
    category: str          # Pinecone namespace this feeds ("courses", "dates", …)
    url: str               # web/sitemap/ics: a URL; filedrop: a local folder path
    extractor: str = "auto"
    connector: str = "web"          # how content is gathered (see connectors/)
    follow_links: bool = False      # crawl same-prefix links found on the page
    include_prefix: str = ""        # required URL prefix for followed links (defaults to url)
    max_pages: int = 1              # hard cap on pages fetched for this source
    min_records: int = 1            # verification floor after extraction
    added_by_admin: bool = False

    def __post_init__(self):
        if self.extractor not in VALID_EXTRACTORS:
            raise ValueError(f"Unknown extractor '{self.extractor}' for {self.url}")
        if self.connector not in VALID_CONNECTORS:
            raise ValueError(f"Unknown connector '{self.connector}' for {self.url}")
        if self.follow_links and not self.include_prefix:
            self.include_prefix = self.url
        if self.follow_links and self.max_pages == 1:
            self.max_pages = 100

    def resolve_extractor(self) -> str:
        if self.extractor != "auto":
            return self.extractor
        if self.category == "courses":
            return "course_regex"
        if self.category == "dates":
            return "llm_dates"
        return "llm_generic"


def schools_dir(backend_dir: str) -> str:
    return os.path.join(backend_dir, "schools")


def list_schools(backend_dir: str) -> list[str]:
    root = schools_dir(backend_dir)
    if not os.path.isdir(root):
        return []
    return sorted(
        name for name in os.listdir(root)
        if os.path.isfile(os.path.join(root, name, "sources.json"))
    )


def load_sources(school: str, backend_dir: str, extra_sources: list[dict] | None = None) -> list[Source]:
    """Merge the school's versioned sources.json with admin-added ones."""
    path = os.path.join(schools_dir(backend_dir), school, "sources.json")
    sources: list[Source] = []

    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for raw in data.get("sources", []):
            sources.append(Source(school=school, **raw))

    seen_urls = {s.url for s in sources}
    for raw in extra_sources or []:
        if raw["url"] in seen_urls:
            continue
        sources.append(Source(
            school=school,
            category=raw["category"],
            url=raw["url"],
            extractor=raw.get("extractor", "auto"),
            added_by_admin=True,
        ))

    return sources


def categories(sources: list[Source]) -> list[str]:
    out: list[str] = []
    for s in sources:
        if s.category not in out:
            out.append(s.category)
    return out
