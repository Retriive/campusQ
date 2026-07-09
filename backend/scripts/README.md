# Backend operational scripts

This folder contains ad-hoc/manual scripts that are intentionally **not**
part of the deterministic pytest suite.

- `pinecone_probe.py` — quick Pinecone connectivity + metadata probe
- `retrieval_probe.py` — quick embedding/retrieval probe

If a script calls live services or depends on real credentials, it belongs
here (or under `backend/evals/`), not in `backend/tests/`.
