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

PR #27 implementation head `f9c63349c821164f79a6d74c910730e955823c30` passed protected GitHub Actions run `34980869733` for backend, frontend and containers/Compose/Playwright. PR #35 then hardened only the external live-smoke delivery strategy; protected run `35091630767` passed backend, frontend and containers on head `51a6f28954ee16bb238fc33c8ad349e1cec8663c`.

These deterministic runs prove repository behavior but do not substitute for successful real OSM acquisition.

## Earlier blocked evidence — 2026-09-15 and 2026-09-16

### Default public Overpass endpoint

GitHub Actions run `34979600413` executed a real `drive` acquisition for `Mitte, Berlin, Germany` with explicit OSMnx speed/travel-time imputation enabled.

Result: **EXTERNAL/BLOCKED**.

The request to `overpass-api.de` failed before canonical normalization with a `ConnectTimeout` after the configured 180-second connection timeout. The smoke wrote failure evidence with `synthetic_fallback=false`.

No nodes, edges or route were claimed from this failed attempt.

### Explicit Private.coffee endpoint

GitHub Actions run `34980820676` executed the same real Berlin `drive` smoke against `https://overpass.private.coffee/api`.

The original attempt and its 2026-09-16 rerun both ended with provider-side `ReadTimeout` before a usable snapshot was returned. The rerun uploaded failure artifact `10444471723`. In every failure payload, `synthetic_fallback=false` remained explicit.

No nodes, edges or route were claimed from these failed attempts.

## Successful point-in-time live evidence — 2026-09-16

PR #35 changed only the verification infrastructure so a live run can try multiple real public Overpass delivery endpoints with a hard 300-second budget per endpoint. Endpoint failover does not change the underlying data source, does not cache or generate road topology and cannot make the job pass unless the existing strict readiness verifier accepts a real OSM snapshot and the existing `ResilienceAgent` completes its baseline route.

GitHub Actions run `35091544852` executed the real smoke for:

- place: `Mitte, Berlin, Germany`;
- network type: `drive`;
- speed/travel-time derivation: explicit OSMnx `add_edge_speeds` / `add_edge_travel_times` opt-in;
- synthetic production fallback: `false`.

The first endpoint (`https://maps.mail.ru/osm/tools/overpass/api`) exceeded the workflow's 300-second endpoint budget. The second endpoint (`https://overpass.private.coffee/api`) also exceeded its 300-second budget. Both failures were retained as JSON attempt evidence instead of being hidden.

The third endpoint, `https://overpass-api.de/api`, returned a real OSM network and the full readiness contract passed.

### Verified network

The accepted readiness report recorded:

- provider: `OpenStreetMap contributors`;
- source licence: `ODbL 1.0`;
- retrieval timestamp: `2026-09-16T11:50:57.392711Z`;
- canonical node count: **740**;
- canonical edge count: **1,800**;
- speed/travel-time imputation provenance visible on the validated network: **true**;
- `synthetic_fallback=false`.

### Verified real baseline route

The existing resilience shortest-path implementation completed the deterministic route selected by the readiness verifier:

- origin: `osm-node:10087214573`;
- destination: `osm-node:13043292535`;
- node path: `osm-node:10087214573` → `osm-node:13043292535`;
- selected edge: `osm:10087214573:13043292535:1:1419417017`;
- travel time: approximately **2.139 seconds**.

This is not a fixture route. It was calculated from the real OSM snapshot acquired during run `35091544852`.

### Evidence artifact

Run `35091544852` uploaded artifact `10445300085` (`road-network-smoke-evidence`, SHA-256 `8672bb1325b80c76d54a5722d78cbc7135ad3d9626432796e1e1bb8b20e1595c`). The artifact contains all endpoint-attempt JSON files, the selected endpoint and the successful canonical readiness payload.

## Current conclusion

The acceptance requirement that previously blocked issue #14 is now satisfied by point-in-time real-provider evidence. The repository has demonstrated non-empty real Berlin road-network acquisition, required canonical routing attributes and provenance, explicit OSMnx imputation semantics, no synthetic fallback, and a successful baseline route through the production resilience routing implementation.

This evidence is deliberately point-in-time rather than a claim that public Overpass infrastructure is permanently available. Future provider outages must continue to degrade visibly. The multi-endpoint smoke is an operational verification mechanism, not a production data substitution mechanism.