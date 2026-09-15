# Road-network live verification

This document records point-in-time evidence for the optional real OpenStreetMap road-network acquisition path used by the resilience domain. It deliberately separates deterministic repository correctness from external Overpass availability.

## Verification contract

The road-network smoke path is implemented by `.github/workflows/road-network-smoke.yml` and `scripts/road_network_smoke.py`. It installs the optional `osm` dependency and performs real OSMnx acquisition for a Berlin scope outside required pull-request CI.

A successful live run must prove all of the following before issue #14 can be closed:

- non-empty canonical `NetworkNode` and `NetworkEdge` collections from OpenStreetMap;
- coordinates and edge endpoints are internally consistent;
- positive edge length and travel-time routing attributes are present;
- OSM provider identity and ODbL attribution are retained in provenance;
- when OSMnx speed/travel-time derivation is enabled, that imputation remains explicit and provenance-visible;
- the acquired graph produces at least one valid deterministic baseline route through the existing resilience routing implementation; and
- no synthetic production network fallback is used.

The verifier does not repair or fabricate a network. Provider, schema and routing-readiness failures remain failures.

## Deterministic repository evidence

The implementation is covered by deterministic tests for readiness validation, explicit imputation, provider/schema failure handling and last-known-good retention. The regular protected CI remains independent of OSM availability.

On branch head `f9c63349c821164f79a6d74c910730e955823c30`, GitHub Actions run `34980869733` completed all required jobs successfully:

- `backend`: PASS — Ruff formatting/lint, strict mypy, complete pytest suite, knowledge validation, production-data guard, secret guard and OpenAPI generation;
- `frontend`: PASS — unit tests and production build; and
- `containers`: PASS — Compose validation, backend/frontend image builds, deterministic acceptance state, composed health checks and Playwright browser acceptance.

This proves repository behavior but does **not** substitute for a successful real OSM acquisition.

## Point-in-time live evidence — 2026-09-15

### Attempt 1 — default public Overpass endpoint

GitHub Actions run `34979600413` executed a real `drive` acquisition for `Mitte, Berlin, Germany` with explicit OSMnx speed/travel-time imputation enabled.

Result: **EXTERNAL/BLOCKED**.

The request to `overpass-api.de` failed before canonical normalization with a `ConnectTimeout` after the configured 180-second connection timeout. The smoke wrote failure evidence with `synthetic_fallback=false` and uploaded artifact `10401630471`.

No nodes, edges or route were claimed from this failed attempt.

### Attempt 2 — explicit alternative public Overpass endpoint

The acquisition path was extended so a caller can explicitly select an OSMnx `overpass_url` for one fetch. The previous OSMnx setting is restored afterward, and the selected delivery endpoint is recorded in smoke/provenance evidence. This is an explicit configuration mechanism, not silent automatic failover.

GitHub Actions run `34980820676` then executed the same real Berlin `drive` smoke against `https://overpass.private.coffee/api`.

Result: **EXTERNAL/BLOCKED**.

The endpoint accepted the connection but the Overpass response exceeded the configured 180-second read timeout, producing `ReadTimeout`. The smoke again wrote failure evidence with `synthetic_fallback=false` and uploaded artifact `10401234247`.

No nodes, edges or route were claimed from this failed attempt.

## Current conclusion

The repository-side road-network verification path is implemented and all deterministic/protected CI gates pass. However, the acceptance requirement for a **successful real Berlin network snapshot and real baseline route is not yet satisfied** because both point-in-time public Overpass attempts timed out from GitHub-hosted runners.

Issue #14 therefore remains **EXTERNAL/BLOCKED** and must not be described as completed. A later live smoke may close the issue only after it produces non-empty real Berlin nodes/edges, validates their routing/provenance contract, and completes a baseline route.

The failure state is intentional: external provider unavailability must remain visible rather than being replaced by generated road topology or by a deterministic CI fixture.