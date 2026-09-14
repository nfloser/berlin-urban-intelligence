# Test data policy

All values under `tests/` are deterministic synthetic fixtures used only to verify contracts,
algorithms and failure behaviour. They are not Berlin observations and are never read by production
runtime paths. Live-source checks are kept in the separate GitHub Actions smoke workflow.
