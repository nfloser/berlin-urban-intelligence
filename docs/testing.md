# Testing and verification

Run from repository root:

```bash
pip install -e ".[dev,live]"
python -m ruff format --check src tests scripts
python -m ruff check src tests scripts
python -m mypy src/berlin_urban_intelligence
python -m pytest --cov=berlin_urban_intelligence
python scripts/validate_knowledge.py
python scripts/check_production_data.py
python scripts/check_secrets.py
cd frontend
npm ci
npm test
npm run build
```

The 23 backend tests cover documented API reads, missing/corrupt runtime state, refresh visibility, scenario validation, unavailable routes, RDF identifiers, non-finite values, UTC/units, immutable road closures, stale scenario baselines, DWD normalization through API/RDF/SHACL/SPARQL, source failure behavior, lag-feature leakage and transactional dependency-cycle rejection. Two frontend tests exercise empty/error states and scenario submission.

The fixture values in tests are deterministic test inputs only. They are never installed as runtime data. The current suite measures approximately 57% backend line coverage and does not justify a claim of complete domain validation. Live tests remain separate: `python scripts/live_smoke.py`. An external outage should fail that acceptance check while deterministic tests continue to pass.

Local validation passed Python formatting, lint, strict typing, 23 backend tests, frontend tests and production build. Container builds require Docker/CI. Full scientific validation, provider schema coverage and independently held-out energy evaluation remain open acceptance work.

Browser visual verification was attempted but the Chromium download timed out. No successful browser screenshot or end-to-end browser run is claimed.

Live acquisition on 2026-09-14 succeeded for Berlin LQI, DWD and VBB: 66 canonical observations plus a mobility snapshot; all three sources reported available with valid freshness. This verifies the live acquisition path at that time, not long-term availability or every reference/energy source.
