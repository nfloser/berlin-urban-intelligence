# Data directory

No production observations are committed to this repository.

- `runtime/` contains the latest locally retrieved canonical state and is git-ignored except for its placeholder.
- `generated/` contains generated RDF or analytical artefacts and is git-ignored except for its placeholder.
- deterministic source-shaped fixtures belong under `tests/fixtures/` and must be clearly labelled as test data.

Run `python scripts/refresh_live.py` to acquire currently available external data. Missing sources remain missing; the refresh path never synthesises fallback observations.
