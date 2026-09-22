# Data sources and licences

`config/sources.yaml` is the machine-readable registry. Runtime adapters must match registered source boundaries and preserve attribution, source identity and limitations.

| Source | Role | State semantics | Licence / attribution |
|---|---|---|---|
| Berliner Luftgütemessnetz REST API | air quality / LQI | `observed`; current automatic values remain provisional | Datenlizenz Deutschland – Namensnennung 2.0 |
| VBB GTFS-Realtime | current public-transport updates | realtime observation/feed metadata | CC BY 4.0 |
| VBB GTFS static | stops/reference transit topology | reference | CC BY 4.0 |
| DWD CDC 10-minute observations, Berlin-Tempelhof 00433 | meteorology | `observed`; `now` product is not final QC | DWD Open Data terms/attribution recorded by registry |
| Berlin Climate Analysis 2022 WFS | urban-climate model/reference layers | `official_modelled`, never live observation | DL-DE-Zero-2.0 |
| Berlin hospitals WFS | critical-facility identity/location | authoritative reference, not live availability | DL-DE-Zero-2.0 |
| Berlin fire-stations WFS | critical-facility identity/location | authoritative reference, not live availability | DL-DE-Zero-2.0 |
| OpenStreetMap | road-network reference | community-maintained/derived topology | ODbL 1.0, © OpenStreetMap contributors |
| Berlin VIZ editorial road-disruption feed | current/scheduled roadworks and disruptions | observed publisher state; explicit source severity controls closure semantics | Datenlizenz Deutschland – Namensnennung 2.0 |
| Stromnetz Berlin grid-load publication | Berlin distribution-grid load input | source/reference; forecasts require validated chronological evaluation | source terms/URL retained with artefact |
| UCI Individual Household Electric Power Consumption | forecasting methodology reference only | never Berlin operational state | CC BY 4.0 |

## Operational semantics

### Berlin air quality

The current `/api/lqis/data` response groups component rows inside station envelopes. The adapter normalizes these rows into one canonical LQI record per station/timestamp and uses explicit provider `grade` fields. Current automatic measurements remain provisional. A missing component is not zero pollution.

### DWD

The live path uses Berlin-Tempelhof station `00433` for the configured 10-minute product. UTC/timezone handling and `-999` missing sentinels are explicit. The `now` product has not completed final provider QC.

### VBB

GTFS-Realtime and static GTFS have different semantics and cadences. Missing realtime updates are not evidence of normal service. Static schedules/stops are reference data rather than live state.

### Climate and facilities

The reference acquisition workflow ingests the official Climate Analysis WFS plus hospitals and fire-station WFS data. Climate features stay `official_modelled`; facility identity/location does not assert live operational availability.

### Berlin VIZ road disruptions

The map and routing path use the current VIZ editorial feed at `/daten/baustellen_sperrungen_viz.json` because the live-deployed Berlin Masterportal identifies it as the VIZ editorial layer and it carries explicit severity values. The concurrently published Landesmeldestelle feed is broader context but currently does not provide equivalent severity semantics.

Only an active, fresh source record with severity `Vollsperrung` can remove matched routing edges. `Fahrtrichtungssperrung`, `keine Sperrung` and other incident types remain visible without an inferred travel-time multiplier. Source `tstore`, validity interval, licence and provenance are persisted.

This is incident/closure information, **not** measured congestion-speed telemetry.

### OpenStreetMap

OSM network acquisition is optional because it is heavier than the default WFS/GTFS reference refresh. It is qualified as non-authoritative. Missing speed/travel-time information is not silently invented; OSMnx speed imputation requires explicit opt-in and is recorded in provenance.

The delivery endpoint used by OSMnx can be selected explicitly for one acquisition through `OsmnxRoadNetworkClient.fetch(..., overpass_url=...)`, `scripts/refresh_reference.py --overpass-url ...`, or the dedicated road-network smoke. The previous OSMnx setting is restored after the fetch. This is explicit configuration, not silent provider failover, and the selected delivery endpoint is recorded in smoke/provenance evidence.

The canonical source remains OpenStreetMap regardless of which public Overpass delivery endpoint serves the query. A successful delivery request does not turn community-maintained OSM topology into authoritative municipal road data.

### Energy

The Stromnetz Berlin workflow requires explicit upstream timestamp/value column names and units. The published high-voltage/network-level load curve must not be relabelled as total Berlin electricity demand. Forecasts are only persisted after chronological evaluation and dataset-fingerprint binding.

The UCI household electricity dataset remains a research/methodology reference: it represents one household in Sceaux, France and cannot represent Berlin operational energy state.

## Live verification

A point-in-time live smoke run on **2026-09-14** successfully verified the current adapters against Berlin air quality, DWD and VBB GTFS-Realtime. All three sources were available and fresh enough for their configured thresholds in that run, producing 70 canonical observations. Provider availability may change later, so this result is evidence of compatibility at that timestamp rather than a permanent availability guarantee.

Real road-network verification is tracked separately because it is heavier and depends on Overpass availability. On **2026-09-15**, GitHub Actions run `34979600413` attempted `Mitte, Berlin, Germany` through `overpass-api.de` and failed with a 180-second `ConnectTimeout`; run `34980820676` retried the same real Berlin scope through explicit `https://overpass.private.coffee/api` and failed with a 180-second `ReadTimeout`. Both runs wrote failure evidence with `synthetic_fallback=false`. No real network or route success is claimed from these attempts. See `docs/road-network-verification.md`.

The platform does not redistribute external datasets under a new licence. Generated state retains provider/source identifiers and licence metadata.