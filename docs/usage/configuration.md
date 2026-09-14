# Usage configuration

Operational configuration is split between environment variables, source metadata and explicit command-line options. The complete configuration reference is maintained in [Implementation configuration](../implementation/configuration.md).

## API state paths

The backend recognizes:

```text
BUI_RUNTIME_STATE
BUI_REFERENCE_STATE
BUI_ENERGY_STATE
```

All are optional. The defaults resolve to `data/runtime/state.json`, `data/runtime/reference.json` and `data/runtime/energy.json` under the application root. Docker mounts the repository `data/` directory at `/app/data`.

The current implementation does not read `BUI_LOG_LEVEL`; do not rely on that variable unless logging configuration is changed in code.

## Source configuration

Source identity and limitations are version-controlled in `config/sources.yaml`. This file is not intended for credentials.

## Acquisition options

Use the CLI rather than editing implementation constants for run-specific output locations:

```bash
python scripts/refresh_live.py --help
python scripts/refresh_reference.py --help
python scripts/evaluate_energy.py --help
```

Reference options include skipping static GTFS, enabling optional OSM acquisition, changing the OSM place/network query and explicitly allowing speed imputation.

Energy evaluation requires explicit upstream schema choices. This is intentional: source columns/units should be inspected rather than guessed.

## After configuration changes

Changing a persisted-state path requires the backend process to be restarted with the new environment. Replacing a state file at the same path also requires restart/reload because snapshots are loaded at startup.

Changes to `config/sources.yaml` affect `/api/v1/sources` immediately only after code/process reload as appropriate, but changing registry metadata alone does not modify already persisted canonical provenance.
