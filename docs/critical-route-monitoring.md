# Dynamic critical-route monitoring

Berlin Urban Intelligence can automatically derive and display monitored routes between persisted critical facilities over the current persisted road network.

## What the monitor does

The backend derives one route for every critical facility that can be snapped to the road network. Its destination is the nearest reachable facility in a **different facility category** according to the persisted edge travel-time weights. The result is deterministic and bounded by the persisted facility/network state.

Each monitored route exposes:

- origin and destination facility ID, name and category;
- weighted baseline travel time;
- road-network distance;
- ordered road node path and edge IDs;
- GeoJSON `LineString` geometry for MapLibre;
- quality and freshness fields;
- source provider, dataset and licence provenance;
- the reference-snapshot timestamp and route computation timestamp.

The API is:

```text
GET /api/v1/resilience/critical-routes?offset=0&limit=48
```

Responses include total/returned/truncated metadata. The hard API limit is 250 routes per response.

## Dynamic refresh model

Critical-route calculation is tied to the persisted `ReferenceState`, not to individual HTTP requests.

When `reference.json` **or** `traffic-disruptions.json` is loaded or replaced with a newer valid snapshot, the API state controller recomputes the critical-route snapshot. Changes only to runtime, energy or derived state do **not** rerun road routing.

The dashboard polls the already-computed critical-route API every 15 seconds. This makes map refresh cheap while still reflecting a changed persisted reference/network snapshot without restarting the application.

The MapLibre dashboard:

- displays monitored routes automatically; no manual origin/destination click is required;
- renders routes by state: baseline, disrupted, rerouted or blocked;
- uses an official VIZ disruption layer for current source-backed incidents/closures;
- preserves the baseline and separately exposes effective rerouted travel time, distance and geometry;
- highlights the selected route separately;
- provides a layer visibility checkbox;
- supports route inspection through a keyboard-accessible select control;
- exposes travel time, distance, edge count and source/licence provenance.

Manual baseline/disruption routing remains a separate analytical workflow and is not replaced by the monitor.

## What “live” means here

The monitor is **live with respect to the platform's current persisted reference/network state**. It is not a Google Maps traffic feed.

The current road-network edge weights originate from the persisted source-backed road snapshot and its documented speed/travel-time processing. Official Berlin VIZ road-disruption data is now persisted separately and can change route availability when the source explicitly classifies an active disruption as `Vollsperrung`.

This still does **not** provide live congestion speeds. Therefore:

```text
disruption_data_available = true|false
traffic_data_available = false
```

have deliberately different meanings. A fresh VIZ snapshot can mark a route `disrupted`, `rerouted` or `blocked`, but partial closures and other incidents do not receive an invented speed penalty. Baseline edge weights are never relabelled as current congestion data.

Provider-content freshness is derived from VIZ `tstore`. A stale last-known-good disruption snapshot remains inspectable but is not allowed to alter routing.

## Selection algorithm

Facilities are first snapped to the nearest road node with the existing projected metric snapping implementation and the configured maximum snap distance.

For each origin facility category, the monitor treats all snapped facilities in other categories as target nodes and runs a multi-source Dijkstra search on the reversed weighted network. This finds the nearest cross-category destination for each origin without an all-pairs route search.

Route reconstruction then uses the same deterministic minimum-`travel_time_s` parallel-edge selection semantics as the resilience router.

The monitor is recalculated only when the reference or persisted traffic-disruption snapshot changes, so expensive graph work is not repeated by 15-second dashboard polling.

## Failure and degradation semantics

No production values are fabricated.

The monitor is **unavailable** when, for example:

- no persisted reference snapshot exists;
- the road network is missing;
- fewer than two critical facilities are available;
- no cross-category route can be resolved.

The monitor is **degraded** when usable routes remain but the snapshot has source errors, facilities cannot be snapped, or snapped facilities are unreachable.

An isolated snapped road node therefore affects only the relevant facility and does not crash or invalidate unrelated monitored routes.

Existing last-known-good reference replacement semantics remain authoritative. An invalid replacement does not displace a previously validated in-process reference snapshot.

## Verification

Deterministic backend tests cover:

- automatic nearest cross-category route derivation;
- travel time, distance, edge IDs and exact GeoJSON geometry;
- source/licence provenance;
- explicit separation of VIZ disruption availability from `traffic_data_available=false`;
- full-closure rerouting and blocked-route fallback;
- no inferred penalty for non-full restrictions;
- stale disruption state remaining visible but unable to alter routes;
- shared-node spatial false-positive prevention;
- reference-source error degradation;
- missing-input unavailability;
- isolated/unreachable facility degradation;
- bounded/truncated API responses;
- recomputation after persisted reference-snapshot replacement.

The composed browser acceptance fixture contains multiple critical-facility categories and a persisted road network. Playwright verifies that routes appear automatically in the running nginx → FastAPI → persisted state → React/MapLibre stack, can be hidden/shown, and remain keyboard inspectable without manually calculating a route first.

## Operational requirement

The feature needs a persisted road network and at least two routable critical facilities from different categories.

The normal slow-reference refresh does not silently invent an OSM network. To populate optional OSM roads explicitly, use the repository's documented OSM/reference acquisition path, for example:

```bash
python scripts/refresh_reference.py --with-osm
```

Public Overpass availability remains external. If OSM acquisition fails, the monitor must report that required route data is unavailable or continue from an existing validated last-known-good persisted reference snapshot; it must never substitute synthetic production topology.
