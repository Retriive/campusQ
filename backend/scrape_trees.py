"""
CampusQ — Engineering Sequence Scraper (dynamic-column rewrite)
================================================================
Replaces the fragile hardcoded CHART_COL_BOUNDS approach with a
self-calibrating column detector that reads the actual FALL / WINTER
header labels out of every PDF and builds its own column boundaries.

WHY THIS IS BETTER THAN THE ORIGINAL
--------------------------------------
The original scraper used a fixed list of (x0, x1, year, term) tuples
measured from one reference PDF.  Any PDF whose columns land even a
few points outside those ranges silently drops courses.

This rewrite:
  1. Opens the first page and deduplicates the ~33× character
     duplication artefact (unchanged from original).
  2. Scans the top 12 % of the page for the text tokens "FALL" and
     "WINTER" — these are always present as visible column headers.
  3. Sorts those 8 x-positions and pairs them with
     (Year1-Fall, Year1-Winter, … Year4-Winter) in left→right order.
  4. Computes column boundaries as midpoints between adjacent header
     centres, so every course is assigned to the correct cell regardless
     of what page width, margin, or template version was used.
  5. Falls back to a safe default layout if fewer than 8 headers are
     found (e.g. corrupted / non-standard PDFs).

METADATA SCHEMA (per Pinecone vector)
--------------------------------------
  program        str   "SOFT", "ELEC", …
  stream         str   "General", "A", "Combined", …
  entry_year     int   2026
  catalog_key    str   "26-30"
  source_pdf     str   full PDF URL
  section_type   str   "year_1_fall" … "year_4_winter" | "prereq_notes"
  degree_year    int   1-4  (0 = notes)
  term           str   "Fall" | "Winter" | ""
  courses        list  ["MATH 1004", "ELEC 2501", …]
  text           str   structured prose for embedding
  type           str   "section"
  tenant         str   "carleton"

INSTALL
-------
  pip install requests pdfplumber openai pinecone-client python-dotenv tqdm
"""

from __future__ import annotations

import os
import re
import time
import hashlib
import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import requests
import pdfplumber
from dotenv import load_dotenv
from tqdm import tqdm
from pinecone import Pinecone
from openai import OpenAI

# ─────────────────────────────────────────────────────────────────────────────
# PROGRAM DICTIONARY  (source of truth — unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────
PROGRAMS_DICT = {
    "AERO": {
        "Stream A": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/AERO-A-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/AERO-A-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-A-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-A-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-A-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-AERO-A-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-AERO-A.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-AERO-A.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-A_20180615.pdf",
        },
        "Stream B": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/AERO-B-202630.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/AERO-B-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-B-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-B-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-B-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-AERO-B-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-AERO-B.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-AERO-B.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-B_20180605.pdf",
        },
        "Stream C": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/AERO-C-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/AERO-C-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-C-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-C-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-C-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-AERO-C.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-AERO-C.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-AERO-C.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-C_20180605.pdf",
        },
        "Stream D": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/AERO-D-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-21-22-.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/AERO-D-20-21-.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-AERO-D.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/AERO-D_20180615.pdf",
        },
    },
    "ACSE": {
        "Combined Stream (2019-current structure)": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/ACSE-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ACSE-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ACSE-202430.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ACSE-202330.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACSE-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-ACSE-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-ACSE.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-ACSE.pdf",
        },
        "Stream A": {
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACSE-A_20180605.pdf",
            "17-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACS-Structural-Stream-A-_updated-June-1-2017.pdf",
            "16-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACS-Structural-Stream-A-_update-May-26-2016.pdf",
        },
        "Stream B": {
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACSE-B_20180605.pdf",
            "17-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACS-Environmental-Stream-B_update-June-1-2017.pdf",
            "16-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ACS-Environmental-Stream-B_update-May-26-2016.pdf",
        },
    },
    "BMEE": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/BIO-ELEC-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/BIO-ELEC-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BIO-ELEC-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/06/BIO-ELEC-23-24-1.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BIO-ELEC-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-BIO-ELEC.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-BIO-ELEC.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-BIO-ELEC.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BiomedElec_20180605_Aug2020-update.pdf",
        },
    },
    "BMME": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/BIO-MECH-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/BIO-MECH-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BIO-MECH-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BIO-MECH-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BIO-MECH-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-BIO-MECH.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-BIO-MECH.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-BIO-MECH.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/BiomedMech_20180605.pdf",
        },
    },
    "CIVL": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/CIVE-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/CIVE-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/CIVE-202430.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/CIVE-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/CIVE-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-CIVE.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-CIVE.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-CIVIL.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Civil_20180605.pdf",
        },
    },
    "COMM": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/COMM-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/COMM-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/06/COMM-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/06/COMM-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/COMM-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-COM.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-COM.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-COMM.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Communications_20180605.pdf",
        },
    },
    "SYSC": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/CSE-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/CSE-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/CSE-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/CSE-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/CSE-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-COMP-SYS.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-CSE.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-COMP-SYS.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Computersystems_20180605.pdf",
        },
    },
    "ELEC": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/ELEC-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/ELEC-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ELEC-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ELEC-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ELEC-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-ELEC.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-ELEC.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-ELEC.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Electrical_20180605.pdf",
        },
    },
    "PHYS": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/ENG-PHYS-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/03/ENG-PHYS-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ENG-PHYS-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/23-24-ENG-PHYS.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/22-23-ENG-PHYS.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-ENG-PHYS-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-ENG-PHYS.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Engineering-Physics_25-June-2019.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/EngineeringPhysiscs_20180605.pdf",
        },
    },
    "ENVE": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/ENVE-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ENVE-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ENVE-202430.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/01/ENVE-202330.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/ENVE-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-ENVE-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-ENVE.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-ENVIRO.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Environmental_20180605.pdf",
        },
    },
    "MECH": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/MECH-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/MECH-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/MECH-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/MECH-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/MECH-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-MECH-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-MECH.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-MECH.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Mechanical_20180605.pdf",
        },
    },
    "MAAE": {
        "General": {
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/MECT-202530-May-2026.pdf",
        },
    },
    "SOFT": {
        "General": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/SOFT-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/07/SOFT-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/06/SOFT-24-25v2.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SOFT-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SOFT-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-SOFT-1.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-SOFT.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-SOFT.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/Software_20180605.pdf",
        },
    },
    "SREE": {
        "Stream A": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/SREE-A-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/SREE-A-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-A-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-A-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-A-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-SREE-A.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-SREE-A.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-SREE-A.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-A_20180601.pdf",
        },
        "Stream B": {
            "26-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2026/05/SREE-B-202630-1.pdf",
            "25-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/2025/04/SREE-B-202530.pdf",
            "24-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-B-24-25.pdf",
            "23-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-B-23-24.pdf",
            "22-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-B-22-23.pdf",
            "21-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/21-22-SREE-B-2.pdf",
            "20-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/20-21-SREE-B-1.pdf",
            "19-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/19-20-SREE-B-1.pdf",
            "18-30": "https://carleton.ca/engineering-design/wp-content/uploads/sites/63/SREE-B_20180605.pdf",
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
PDF_FOLDER    = "pdfs_eng"
ARCHIVE_FOLDER = "archive_eng"
NAMESPACE     = "carleton"
EMBED_MODEL   = "text-embedding-3-small"

# ─────────────────────────────────────────────────────────────────────────────
# REGEX ATOMS
# ─────────────────────────────────────────────────────────────────────────────
_SUBJ = r'[A-Z]{2,5}'
_NUM  = r'\d{4}[A-Z]?'

SUBJ_RE      = re.compile(r'^[A-Z]{2,5}$')
NUM_RE       = re.compile(r'^' + _NUM + r'$')
NUM_SLASH_RE = re.compile(r'^(' + _NUM + r')/(' + _NUM + r')$')
SPACED_RE    = re.compile(r'^(' + _SUBJ + r')\s+(' + _NUM + r')$')
COMBINED_RE  = re.compile(r'^(' + _SUBJ + r')(' + _NUM + r')$')

# Slash-list: "ELEC 4907 / SYSC 4907 / ECOR 4907"
SLASH_LIST_RE = re.compile(
    r'^(' + _SUBJ + r')\s+(' + _NUM + r')'
    r'(?:\s*/\s*(' + _SUBJ + r')\s+(' + _NUM + r'))?'
    r'(?:\s*/\s*(' + _SUBJ + r')\s+(' + _NUM + r'))?$'
)

# Tokens that look like subjects but are structural words to ignore
STRUCTURAL_TOKENS = {
    'FALL', 'WINTER', 'FIRST', 'SECOND', 'THIRD', 'FOURTH',
    'YEAR', 'HERE', 'NOTE', 'NOTES', 'AND', 'FOR', 'THE',
    'ARE', 'ELECTIVE', 'SAT',
}

# Notes-column noise we strip before storing
NOTES_NOISE_RE = re.compile(
    r'kindly note|EngAcadSupport|ECORSupport|doe\.carleton|'
    r'Updated:|Arrow Legend|run your audit|concurrent prerequisite|'
    r'required prerequisite|please run|please contact|'
    r'arrow legend|\*arrow|\*\*please',
    re.IGNORECASE,
)

# Course code mentioned anywhere in text (for notes section)
ANY_COURSE_RE = re.compile(r'\b([A-Z]{2,5})\s+(\d{4}[A-Z]?)\b')


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASS
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Section:
    section_type: str      # "year_1_fall", "year_3_winter", "prereq_notes"
    degree_year:  int      # 1-4; 0 = notes
    term:         str      # "Fall" | "Winter" | ""
    courses:      list[str] = field(default_factory=list)
    text:         str = ""


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: catalog-key → entry year integer
# ─────────────────────────────────────────────────────────────────────────────
def parse_catalog_key(key: str) -> int:
    parts = key.split("-")
    n = int(parts[0])
    return 2000 + n if n < 100 else n


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: stream name normaliser
# ─────────────────────────────────────────────────────────────────────────────
def normalize_stream(raw: str) -> str:
    s = raw.strip()
    m = re.match(r'^[Ss]tream\s+([A-Z])$', s)
    if m:
        return m.group(1)
    if s.lower().startswith("combined"):
        return "Combined"
    return s.split()[0] if s else s


# ─────────────────────────────────────────────────────────────────────────────
# PDF DOWNLOAD / CACHE
# ─────────────────────────────────────────────────────────────────────────────
def pdf_cache_path(program: str, stream: str, catalog_key: str) -> str:
    safe = re.sub(r'[^\w]', '_', stream)
    return os.path.join(PDF_FOLDER, f"{program}__{safe}__{catalog_key}.pdf")


def download_pdf(url: str, cache_path: str) -> Optional[str]:
    if os.path.exists(cache_path):
        return cache_path
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"    ✗ HTTP {r.status_code}")
            return None
        with open(cache_path, "wb") as f:
            f.write(r.content)
        return cache_path
    except requests.RequestException as e:
        print(f"    ✗ Download error: {e}")
        return None


def archive_pdf(path: Optional[str]) -> None:
    if path and os.path.exists(path):
        try:
            shutil.move(path, os.path.join(ARCHIVE_FOLDER, os.path.basename(path)))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — deduplicate characters
# ─────────────────────────────────────────────────────────────────────────────
def _dedup_chars(chars: list) -> list:
    """Remove ~33× duplicate characters stored at identical positions."""
    seen: set = set()
    out: list = []
    for c in chars:
        key = (round(c['x0'] * 2) / 2, round(c['top'] * 2) / 2, c['text'])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — build tokens from deduplicated characters
# ─────────────────────────────────────────────────────────────────────────────
def _build_tokens(chars: list, gap: float = 5.0) -> list[tuple[str, float, float]]:
    """
    Group characters into (token_text, leftmost_x, y) tuples.
    Characters are split into a new token when the horizontal gap
    between successive characters exceeds `gap` points.
    """
    chars = sorted(chars, key=lambda c: (round(c['top'] / 3), c['x0']))
    bands: dict = defaultdict(list)
    for c in chars:
        bands[round(c['top'] / 3)].append(c)

    tokens: list[tuple[str, float, float]] = []
    for band_key in sorted(bands):
        line = sorted(bands[band_key], key=lambda c: c['x0'])
        tok, tx0, ty, prev_x1 = '', line[0]['x0'], line[0]['top'], line[0]['x1']
        for c in line:
            if c['x0'] - prev_x1 > gap:
                if tok.strip():
                    tokens.append((tok.strip(), tx0, ty))
                tok, tx0, ty = c['text'], c['x0'], c['top']
            else:
                tok += c['text']
            prev_x1 = c['x1']
        if tok.strip():
            tokens.append((tok.strip(), tx0, ty))
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — detect column layout dynamically from header labels
# ─────────────────────────────────────────────────────────────────────────────
# The 8 columns are always labelled in the PDF header as:
#   Year1-Fall  Year1-Winter  Year2-Fall … Year4-Winter
# We find all "FALL" and "WINTER" tokens in the top 12% of the page,
# sort their x-positions, and compute midpoint boundaries between them.
# This works regardless of page width or template generation.

_COL_LABELS: list[tuple[int, str]] = [
    (1, "Fall"), (1, "Winter"),
    (2, "Fall"), (2, "Winter"),
    (3, "Fall"), (3, "Winter"),
    (4, "Fall"), (4, "Winter"),
]

# Fallback bounds if header detection yields < 8 columns
# (measured from the most common 792×612 template)
_FALLBACK_BOUNDS: list[tuple[float, float, int, str]] = [
    (0,    95,  1, "Fall"),
    (95,   185, 1, "Winter"),
    (185,  280, 2, "Fall"),
    (280,  375, 2, "Winter"),
    (375,  465, 3, "Fall"),
    (465,  560, 3, "Winter"),
    (560,  655, 4, "Fall"),
    (655,  765, 4, "Winter"),
    (765,  9999, 0, "Notes"),
]


def _detect_column_bounds(
    tokens: list[tuple[str, float, float]],
    page_height: float,
    page_width: float,
) -> list[tuple[float, float, int, str]]:
    """
    Scan header tokens for 'FALL' / 'WINTER' labels.
    Returns a list of (x_left, x_right, degree_year, term) boundaries
    covering the full page width, including a Notes panel on the right.
    """
    header_thresh = page_height * 0.12
    fall_xs:   list[float] = []
    winter_xs: list[float] = []

    for txt, x, y in tokens:
        if y > header_thresh:
            continue
        if txt == "FALL":
            fall_xs.append(x)
        elif txt == "WINTER":
            winter_xs.append(x)

    # We need exactly 4 FALL and 4 WINTER labels
    if len(fall_xs) != 4 or len(winter_xs) != 4:
        print(f"    ⚠ Header detection: found {len(fall_xs)} FALL, "
              f"{len(winter_xs)} WINTER — using fallback bounds")
        return _FALLBACK_BOUNDS

    # Interleave sorted positions: F W F W F W F W
    all_xs = sorted(fall_xs + winter_xs)

    # Build midpoint boundaries
    centres = all_xs
    bounds: list[tuple[float, float, int, str]] = []
    for i, (yr, trm) in enumerate(_COL_LABELS):
        x_left  = 0.0 if i == 0 else (centres[i - 1] + centres[i]) / 2
        x_right = (centres[i] + centres[i + 1]) / 2 if i < 7 else centres[i] + 60
        bounds.append((x_left, x_right, yr, trm))

    # Notes panel: everything right of the last course column
    notes_left = bounds[-1][1]
    bounds.append((notes_left, page_width + 100, 0, "Notes"))

    return bounds


def _classify_x(
    x: float,
    bounds: list[tuple[float, float, int, str]],
) -> tuple[int, str]:
    """Map an x-coordinate to (degree_year, term) using computed bounds."""
    for x0, x1, yr, trm in bounds:
        if x0 <= x < x1:
            return yr, trm
    # Fallthrough: treat as notes
    return 0, "Notes"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — extract metadata from header tokens
# ─────────────────────────────────────────────────────────────────────────────
def _extract_header_metadata(
    tokens: list[tuple[str, float, float]],
    page_height: float,
) -> dict:
    """
    Pull program title, catalog year, and update date from the top of the page.
    Returns a dict with keys: title, catalog_year_raw, updated_date.
    """
    header_thresh = page_height * 0.08
    meta = {"title": "", "catalog_year_raw": "", "updated_date": ""}

    # The title is usually the longest token in the very top band (y < 15pt)
    top_tokens = [(txt, x, y) for txt, x, y in tokens if y < 15]
    if top_tokens:
        # Pick the longest text as the program title
        meta["title"] = max(top_tokens, key=lambda t: len(t[0]))[0]

    for txt, x, y in tokens:
        if y > header_thresh:
            continue
        # "Catalog Year: 202630"
        m = re.search(r'[Cc]atalog\s+[Yy]ear[:\s]+(\d{6})', txt)
        if m:
            meta["catalog_year_raw"] = m.group(1)
        # "Updated: 25/03/2026"  or  "17/01/2024"  (date-like string)
        m2 = re.search(r'Updated[:\s]+(\d{2}/\d{2}/\d{4})', txt)
        if m2:
            meta["updated_date"] = m2.group(1)
        # Some older PDFs only have a bare date in top-right
        m3 = re.match(r'^(\d{4}/\d{2}/\d{2})$', txt)
        if m3 and not meta["updated_date"]:
            meta["updated_date"] = m3.group(1)

    return meta


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — main extraction function
# ─────────────────────────────────────────────────────────────────────────────
def extract_sections(path: str) -> tuple[list[Section], dict]:
    """
    Parse a Carleton sequence-chart PDF into Section objects.

    Returns (sections, header_meta).

    Course detection (priority order)
    -----------------------------------
    1. Slash-list token  "ELEC 4907 / SYSC 4907 / ECOR 4907"
    2. Already-spaced    "ELEC 3105"   or "CCDP 2100"
    3. No-space combined "ELEC3105"    (rare)
    4a. Bare SUBJ → look ahead for plain NUM within 10px vertically
    4b. Bare SUBJ → look ahead for SLASH-NUM "1006/2006" → two courses

    All courses are assigned to (year, term) by their SUBJ token's x-coord
    using the dynamically computed column bounds.
    """
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        raw_chars = page.chars
        page_w, page_h = page.width, page.height

    chars  = _dedup_chars(raw_chars)
    tokens = _build_tokens(chars)

    # ── Detect column layout for this specific PDF ─────────────────────────
    col_bounds = _detect_column_bounds(tokens, page_h, page_w)

    # ── Collect header metadata ────────────────────────────────────────────
    header_meta = _extract_header_metadata(tokens, page_h)
    header_meta["page_width"]  = page_w
    header_meta["page_height"] = page_h
    header_meta["col_bounds"]  = [(round(b[0],1), round(b[1],1), b[2], b[3])
                                   for b in col_bounds]

    # ── Walk tokens and classify courses ──────────────────────────────────
    course_map: dict[tuple[int, str], list[str]] = defaultdict(list)
    notes_lines: list[tuple[float, str]] = []  # (y, text)

    i = 0
    while i < len(tokens):
        txt, x, y = tokens[i]
        yr, trm = _classify_x(x, col_bounds)

        # ── Notes column ───────────────────────────────────────────────────
        if yr == 0:
            notes_lines.append((y, txt))
            i += 1
            continue

        # ── Rule 1: slash-list ─────────────────────────────────────────────
        m = SLASH_LIST_RE.match(txt)
        if m:
            groups = [g for g in m.groups() if g]
            for j in range(0, len(groups) - 1, 2):
                course_map[(yr, trm)].append(f"{groups[j]} {groups[j+1]}")
            i += 1
            continue

        # ── Rule 2: already-spaced "SUBJ NNNN" ────────────────────────────
        m2 = SPACED_RE.match(txt)
        if m2:
            course_map[(yr, trm)].append(f"{m2.group(1)} {m2.group(2)}")
            i += 1
            continue

        # ── Rule 3: combined no-space "SUBNNN" ────────────────────────────
        m3 = COMBINED_RE.match(txt)
        if m3:
            course_map[(yr, trm)].append(f"{m3.group(1)} {m3.group(2)}")
            i += 1
            continue

        # ── Rule 4: bare SUBJ → look ahead ────────────────────────────────
        if SUBJ_RE.match(txt) and txt not in STRUCTURAL_TOKENS:
            j = i + 1
            matched = False
            while j < len(tokens) and abs(tokens[j][2] - y) < 10:
                nt, _nx, _ny = tokens[j]
                if NUM_RE.match(nt):
                    course_map[(yr, trm)].append(f"{txt} {nt}")
                    i = j + 1
                    matched = True
                    break
                ms = NUM_SLASH_RE.match(nt)
                if ms:
                    course_map[(yr, trm)].append(f"{txt} {ms.group(1)}")
                    course_map[(yr, trm)].append(f"{txt} {ms.group(2)}")
                    i = j + 1
                    matched = True
                    break
                j += 1
            if matched:
                continue

        i += 1

    # ── Build Section objects ──────────────────────────────────────────────
    sections: list[Section] = []
    for (yr, trm), raw_codes in sorted(course_map.items()):
        codes = list(dict.fromkeys(raw_codes))  # deduplicate, preserve order
        label = f"year_{yr}_{trm.lower()}"
        body  = (
            f"Year {yr} {trm} courses:\n"
            + "\n".join(f"  - {c}" for c in codes)
        )
        sections.append(Section(
            section_type=label,
            degree_year=yr,
            term=trm,
            courses=codes,
            text=body,
        ))

    # ── Notes / prereq section ─────────────────────────────────────────────
    notes_lines.sort(key=lambda t: t[0])
    notes_text = "\n".join(
        line for _, line in notes_lines
        if not NOTES_NOISE_RE.search(line)
    ).strip()

    if notes_text:
        notes_codes = list(dict.fromkeys(
            f"{s} {n}" for s, n in ANY_COURSE_RE.findall(notes_text)
        ))
        sections.append(Section(
            section_type="prereq_notes",
            degree_year=0,
            term="",
            courses=notes_codes,
            text=notes_text,
        ))

    if not sections:
        sections.append(Section(
            section_type="full_document",
            degree_year=0,
            term="",
            courses=[],
            text="[extraction failed — no structured content found]",
        ))

    return sections, header_meta


# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDING
# ─────────────────────────────────────────────────────────────────────────────
def embed_batch(texts: list[str], client: OpenAI) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR ID  (deterministic → idempotent re-runs)
# ─────────────────────────────────────────────────────────────────────────────
def vector_id(program: str, stream: str, catalog_key: str, section_type: str) -> str:
    raw = f"{NAMESPACE}::{program}::{stream}::{catalog_key}::{section_type}"
    return hashlib.md5(raw.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# PINECONE UPSERT
# ─────────────────────────────────────────────────────────────────────────────
def upsert_vectors(vectors: list[dict], index) -> None:
    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i : i + 100], namespace=NAMESPACE)


def build_and_upsert(
    sections:      list[Section],
    program:       str,
    stream:        str,
    catalog_key:   str,
    entry_year:    int,
    source_pdf:    str,
    header_meta:   dict,
    openai_client: OpenAI,
    pinecone_index,
) -> None:
    if not sections:
        return

    embeddings = embed_batch([s.text for s in sections], openai_client)
    vectors = []
    for section, emb in zip(sections, embeddings):
        vectors.append({
            "id":     vector_id(program, stream, catalog_key, section.section_type),
            "values": emb,
            "metadata": {
                # ── identity ──────────────────────────────────────────────
                "program":      program,
                "stream":       stream,
                "entry_year":   entry_year,
                "catalog_key":  catalog_key,
                # ── section ───────────────────────────────────────────────
                "section_type": section.section_type,
                "degree_year":  section.degree_year,
                "term":         section.term,
                # ── content ───────────────────────────────────────────────
                "courses":      section.courses,
                "text":         section.text,
                # ── provenance ────────────────────────────────────────────
                "source_pdf":       source_pdf,
                "pdf_title":        header_meta.get("title", ""),
                "catalog_year_raw": header_meta.get("catalog_year_raw", ""),
                "updated_date":     header_meta.get("updated_date", ""),
                # ── system ────────────────────────────────────────────────
                "type":   "section",
                "tenant": NAMESPACE,
            },
        })

    upsert_vectors(vectors, pinecone_index)
    print(f"    ↑ {len(vectors)} sections upserted "
          f"({', '.join(s.section_type for s in sections)})")


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS ONE PDF
# ─────────────────────────────────────────────────────────────────────────────
def process_entry(
    program:       str,
    stream:        str,
    catalog_key:   str,
    pdf_url:       str,
    openai_client: OpenAI,
    pinecone_index,
) -> None:
    entry_year = parse_catalog_key(catalog_key)
    print(f"  [{program} | {stream} | {catalog_key} | entry {entry_year}]")

    cache_path = pdf_cache_path(program, stream, catalog_key)
    pdf_path   = download_pdf(pdf_url, cache_path)
    if not pdf_path:
        print("    ✗ PDF unavailable — skipping")
        return

    try:
        sections, header_meta = extract_sections(pdf_path)
    except Exception as e:
        print(f"    ✗ Extraction error: {e}")
        archive_pdf(pdf_path)
        return

    total_courses = sum(len(s.courses) for s in sections)
    if total_courses == 0:
        print("    ✗ No courses extracted — skipping")
        archive_pdf(pdf_path)
        return

    print(f"    Sections: {[s.section_type for s in sections]}")
    print(f"    Courses : {total_courses}")
    if header_meta.get("updated_date"):
        print(f"    Updated : {header_meta['updated_date']}")

    build_and_upsert(
        sections=sections,
        program=program,
        stream=stream,
        catalog_key=catalog_key,
        entry_year=entry_year,
        source_pdf=pdf_url,
        header_meta=header_meta,
        openai_client=openai_client,
        pinecone_index=pinecone_index,
    )
    archive_pdf(pdf_path)


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def run() -> None:
    load_dotenv()

    openai_api_key    = os.getenv("OPENAI_API_KEY")
    pinecone_api_key  = os.getenv("PINECONE_API_KEY")
    pinecone_index_nm = os.getenv("PINECONE_INDEX_NAME")

    if not all([openai_api_key, pinecone_api_key, pinecone_index_nm]):
        raise EnvironmentError(
            "Missing env vars: OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME"
        )

    openai_client  = OpenAI(api_key=openai_api_key)
    pc             = Pinecone(api_key=pinecone_api_key)
    pinecone_index = pc.Index(pinecone_index_nm)

    os.makedirs(PDF_FOLDER,     exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

    # Flatten program dict into jobs
    jobs: list[tuple[str, str, str, str]] = []
    for program, streams in PROGRAMS_DICT.items():
        for raw_stream, years in streams.items():
            stream = normalize_stream(raw_stream)
            for catalog_key, url in years.items():
                jobs.append((program, stream, catalog_key, url))

    total = len(jobs)
    print(f"\nCampusQ — {total} PDFs to process\n")
    start = time.time()

    for idx, (program, stream, catalog_key, url) in enumerate(jobs):
        print(f"[{idx + 1}/{total}]", end=" ")
        process_entry(
            program=program,
            stream=stream,
            catalog_key=catalog_key,
            pdf_url=url,
            openai_client=openai_client,
            pinecone_index=pinecone_index,
        )
        time.sleep(0.8)  # polite crawl rate

    elapsed = round((time.time() - start) / 60, 2)
    print(f"\n✓ Done in {elapsed} min")


if __name__ == "__main__":
    run()