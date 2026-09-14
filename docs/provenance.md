# Provenance, quality and uncertainty

Every canonical value that can influence analysis carries provenance rather than relying on implicit application context.

`Provenance` records provider, dataset, source URL, original identifier where available, observation/retrieval/processing times, processing method, producing agent/version, optional model version, source licence, quality note and upstream identifiers.

Quality is orthogonal to epistemic state. A value can be `observed` and still be `suspect` because the provider marks it provisional. Freshness is also separate from availability: a source may be reachable while its newest accepted value is stale, or temporarily unavailable while its last successful value remains known.

Reference acquisition preserves source-level identity and retains last-known-good data when an independent source fails. Optional OSM speed imputation is explicitly opt-in and provenance-visible rather than silently treated as observed travel time.

Energy forecasts bind model metrics and forecast artefacts to a dataset fingerprint. This prevents a forecast trained/evaluated on one dataset snapshot from being registered as though it belonged to another.

RDF projection uses PROV-O relationships for lineage and project predicates where no reused vocabulary fits cleanly. Provenance remains visible in API JSON and the dashboard's observation inspector as well as semantic exports.

API requests receive an `X-Operation-Id`; structured logs can correlate an operation with agent/source/error status and duration without logging request bodies or query strings.

No pipeline step may silently upgrade provisional data to validated data, infer a missing unit, erase source attribution or recast a scenario/forecast as an observation.