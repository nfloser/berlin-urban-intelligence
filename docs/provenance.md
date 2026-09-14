# Provenance and uncertainty

Every canonical value that can influence an analysis carries provenance rather than relying on implicit application context.

`Provenance` records provider, dataset, source URL, original identifier where available, observation/retrieval/processing times, processing method, producing agent/version, optional model version, source licence, quality note and upstream identifiers.

Quality is orthogonal to epistemic state. A value can be `observed` and still be `suspect` because the provider marks it provisional. Freshness is also separate from availability: a source may be reachable while its newest accepted value is stale, or temporarily unavailable while the last successful value remains known.

RDF projection uses PROV-O relationships for lineage and project predicates for properties that do not map cleanly to reused vocabularies. Provenance is preserved in API JSON as well as semantic exports.

No pipeline step may silently upgrade provisional data to validated data, infer a missing unit, or erase source attribution.
