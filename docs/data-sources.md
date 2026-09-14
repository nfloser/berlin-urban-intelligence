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

### OpenStreetMap

OSM network acquisition is optional because it is heavier than the default WFS/GTFS reference refresh. It is qualified as non-authoritative. Missing speed/travel-time information is not silently invented; OSMnx speed imputation requires explicit opt-in and is recorded in provenance.

### Energy

The Stromnetz Berlin workflow requires explicit upstream timestamp/value column names and units. The published high-voltage/network-level load curve must not be relabelled as total Berlin electricity demand. Forecasts are only persisted after chronological evaluation and dataset-fingerprint binding.

The UCI household electricity dataset remains a research/methodology reference: it represents one household in Sceaux, France and cannot represent Berlin operational energy state.

## Live verification

A point-in-time live smoke run on **2026-09-14** successfully verified the current adapters against Berlin air quality, DWD and VBB GTFS-Realtime. All three sources were available and fresh enough for their configured thresholds in that run, producing 70 canonical observations. Provider availability may change later, so this result is evidence of compatibility at that timestamp rather than a permanent availability guarantee.

The platform does not redistribute external datasets under a new licence. Generated state retains provider/source identifiers and licence metadata.