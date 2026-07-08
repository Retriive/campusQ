"""Canonical CLI entrypoint for CampusQ ingestion.

Usage:
  py -m ingestion.run --school carleton --list
  py -m ingestion.run --school carleton --category dates
"""

from __future__ import annotations

import sys

from ingest.run import main


if __name__ == "__main__":
    sys.exit(main())
