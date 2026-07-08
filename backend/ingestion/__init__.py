"""Canonical ingestion namespace for CampusQ.

This package mirrors the ingestion implementation that historically lived under
``backend/ingest``. New imports and tooling should use ``ingestion.*``.
"""

from ingest.fetch import *  # noqa: F401,F403
from ingest.extract import *  # noqa: F401,F403
from ingest.pipeline import *  # noqa: F401,F403
from ingest.registry import *  # noqa: F401,F403
from ingest.state import *  # noqa: F401,F403
from ingest.upsert import *  # noqa: F401,F403
