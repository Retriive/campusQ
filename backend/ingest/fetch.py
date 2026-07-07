"""Polite fetcher: any URL → clean extractable text.

Handles the formats universities actually publish in:
  - HTML pages (tables become pipe-delimited rows; accordion/collapsible
    content is in the DOM even when visually hidden, so plain text
    extraction captures it)
  - PDFs (via PyMuPDF, same library the chat upload path uses)

Respects robots.txt, identifies itself, retries transient failures, and
never hammers a host (fixed delay between requests to the same domain).
"""

from __future__ import annotations

import hashlib
import re
import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "CampusQBot/1.0 (+https://retriive.com; academic data indexing)"
REQUEST_TIMEOUT = 20
POLITE_DELAY_S = 0.5
MAX_PDF_PAGES = 100

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}
_last_hit: dict[str, float] = {}


@dataclass
class FetchedPage:
    url: str
    kind: str            # "html" | "pdf"
    text: str            # cleaned, extraction-ready text
    content_hash: str    # sha256 of the cleaned text (change detection)
    html: str = ""       # raw HTML, kept only for link discovery


class FetchError(Exception):
    pass


def _robots_allowed(url: str) -> bool:
    domain = urlparse(url).netloc
    rp = _robots_cache.get(domain)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"https://{domain}/robots.txt")
        try:
            rp.read()
        except Exception:
            # Unreachable robots.txt → default allow (standard convention)
            rp.allow_all = True
        _robots_cache[domain] = rp
    return rp.can_fetch(USER_AGENT, url)


def _polite_wait(url: str):
    domain = urlparse(url).netloc
    elapsed = time.time() - _last_hit.get(domain, 0)
    if elapsed < POLITE_DELAY_S:
        time.sleep(POLITE_DELAY_S - elapsed)
    _last_hit[domain] = time.time()


def _get(url: str, retries: int = 2) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            _polite_wait(url)
            r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
            if r.status_code == 200:
                return r
            last_exc = FetchError(f"HTTP {r.status_code} for {url}")
        except requests.RequestException as exc:
            last_exc = exc
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise FetchError(str(last_exc))


def _table_to_text(table) -> str:
    """Flatten an HTML table into pipe-delimited rows so column relationships
    survive into plain text (critical for deadline/fee tables)."""
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "form", "aside", "noscript"]):
        tag.decompose()

    # Flatten tables in place before text extraction
    for table in soup.find_all("table"):
        table.replace_with(BeautifulSoup(f"<p>{_table_to_text(table)}</p>", "html.parser"))

    # Same main-content preference the proven Carleton scraper used
    main = soup.find("div", class_="pageblock") or soup.find("main") or soup.find("body") or soup
    raw = main.get_text(separator="\n")

    raw = raw.replace("\xa0", " ").replace("\r", "\n")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def pdf_to_text(data: bytes) -> str:
    import fitz  # PyMuPDF — already a backend dependency

    text_parts = []
    doc = fitz.open(stream=data, filetype="pdf")
    for page_num, page in enumerate(doc):
        if page_num >= MAX_PDF_PAGES:
            break
        text_parts.append(page.get_text("text"))
    raw = "\n".join(text_parts).replace("\xa0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_page(url: str) -> FetchedPage:
    if not _robots_allowed(url):
        raise FetchError(f"robots.txt disallows {url}")

    r = _get(url)
    content_type = (r.headers.get("content-type") or "").lower()

    if "pdf" in content_type or url.lower().endswith(".pdf"):
        text = pdf_to_text(r.content)
        return FetchedPage(url=url, kind="pdf", text=text, content_hash=_hash(text))

    text = html_to_text(r.text)
    return FetchedPage(url=url, kind="html", text=text, content_hash=_hash(text), html=r.text)


def discover_links(page: FetchedPage, include_prefix: str) -> list[str]:
    """Same-prefix links on an HTML page — how one 'courses root' source
    fans out to every department page without listing them by hand."""
    if page.kind != "html":
        return []
    soup = BeautifulSoup(page.html, "html.parser")
    scope = soup.find("div", class_="pageblock") or soup.find("main") or soup

    links: list[str] = []
    for a in scope.find_all("a", href=True):
        url = urljoin(page.url, a["href"]).split("#")[0]
        if url.startswith(include_prefix) and url != page.url and url not in links:
            links.append(url)
    return links
