"""Data connectors — how content reaches the ingestion pipeline.

The pipeline's job starts at "here are pages of text"; connectors are the
pluggable step before that. Each connector turns one configured source into
FetchedPage objects, so everything downstream (change detection, extraction,
verification, promotion, lexical mirror) works identically no matter where
the content came from.

Built in:
  web      — fetch a URL, optionally fan out to same-prefix links (default)
  sitemap  — read sitemap.xml and fetch every listed page under a prefix
  ics      — an academic-calendar .ics feed becomes clean date text
  filedrop — a local folder of PDFs / HTML / text a registrar hands you

A source opts in via "connector": "sitemap" in sources.json. Omitting the
field keeps today's behavior exactly.
"""

from .base import get_connector, CONNECTORS
