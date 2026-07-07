"""Sitemap connector — one sitemap.xml URL fans out to every listed page.

Better than link-following for big sites: the sitemap is the site's own
authoritative page inventory, so nothing reachable only through JavaScript
menus gets missed, and include_prefix still scopes what we take.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ingest import fetch as fetch_mod

_NS_STRIP = re.compile(r"\{.*?\}")


def parse_sitemap_urls(xml_text: str) -> list[str]:
    """<loc> values from a urlset or sitemapindex (one level, no recursion bombs)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    urls: list[str] = []
    for elem in root.iter():
        if _NS_STRIP.sub("", elem.tag) == "loc" and elem.text:
            url = elem.text.strip()
            if url and url not in urls:
                urls.append(url)
    return urls


def gather_sitemap(source, log=print) -> list:
    """source.url = the sitemap.xml; include_prefix scopes which pages to fetch."""
    r = fetch_mod._get(source.url)
    listed = parse_sitemap_urls(r.text)
    prefix = source.include_prefix or ""
    wanted = [u for u in listed if u.startswith(prefix)][: source.max_pages]
    log(f"  sitemap {source.url} → {len(listed)} listed, {len(wanted)} in scope")

    pages = []
    for url in wanted:
        if url.endswith(".xml"):
            continue  # nested sitemaps: configure them as their own source
        try:
            pages.append(fetch_mod.fetch_page(url))
        except fetch_mod.FetchError as exc:
            log(f"    ✗ {url}: {exc}")
    return pages
