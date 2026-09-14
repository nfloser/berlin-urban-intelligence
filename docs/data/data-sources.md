# Data sources

The machine-readable source registry is `config/sources.yaml`. This page explains how each registered source is used by the current implementation. Registry metadata should be updated together with any adapter/source-boundary change.

| Source ID | Provider / dataset | Domain | Access/use | Update semantics | Authority / licence | Important limitation |
|---|---|---|---|---|---|---|
| `berlin_air_quality` | Berliner Luftgütemessnetz, LQI REST API | exposure | Live REST acquisition | expected hourly | authoritative; DL-DE-BY-2.0 | Automatic current values can be provisional; missing component values are not zero. |
| `vbb_gtfs_rt` | VBB GTFS-Realtime | mobility | Live protobuf feed | realtime | authoritative; CC BY 4.0 | Feed/operator coverage varies; absence of updates is not normal-operation evidence. |
| `vbb_gtfs_static` | VBB GTFS schedule data | mobility/reference | Static GTFS reference acquisition | twice weekly per registry | authoritative; CC BY 4.0 | Schedule/reference state is not realtime operational state. |
| `berlin_climate_analysis_2022` | Berlin Climate Analysis 2022 WFS | heat/reference | Selected verified WFS layers | irregular official release | authoritative; DL-DE-Zero-2.0 | Official model output, not a live measurement; source resolution limits interpretation. |
| `dwd_open_data` | DWD CDC/Open Data | heat | 10-minute air-temperature product used by current live path | product-specific | authoritative | `now` product is not final QC; missing-value conventions require explicit parsing. |
| `berlin_hospitals` | Berlin hospitals WFS | resilience/reference | WFS acquisition | provider-specific | authoritative; DL-DE-Zero-2.0 | Facility identity/location does not establish current availability/capacity. |
| `berlin_fire_stations` | Berliner Feuerwehr locations WFS | resilience/reference | WFS acquisition | provider-specific | authoritative; DL-DE-Zero-2.0 | Location does not establish current operational availability. |
| `osm_berlin` | OpenStreetMap | resilience/reference | Optional OSMnx road acquisition | community-updated | non-authoritative; ODbL 1.0 | Completeness and edge attributes vary; speed imputation is modelling, not observation. |
| `stromnetz_berlin_grid_load` | Stromnetz Berlin network-level load publication | energy | Explicit local CSV or verified HTTPS input | annual publication, quarter-hour values for configured publication | authoritative for documented source scope | A network-level/high-voltage curve must not be relabelled as total Berlin electricity demand. |
| `energy_reference_uci` | UCI Individual Household Electric Power Consumption | research reference | Methodology reference only | static | non-authoritative for Berlin; CC BY 4.0 | One household in Sceaux, France; never Berlin operational state. |

## Live-source behavior

### Berlin air quality

The exposure adapter normalizes the current station-oriented LQI payload into per-station records and canonical observations. The producing agent marks these current automatic values `suspect` because provider quality control is not final. Component grades are emitted only when present.

### DWD

The current live client selects an explicit DWD 10-minute air-temperature product and preserves missing-value semantics. Canonical output can include 2 m temperature, near-ground temperature, relative humidity, station pressure and dew point when supplied. Provenance notes that the `now` product has not completed final quality control.

### VBB

GTFS-Realtime is summarized into a mobility snapshot. Static GTFS is acquired separately as reference entities. These inputs deliberately have different semantics and persistence boundaries.

## Reference-source behavior

The reference refresh loads hospital and fire-station WFS data plus a verified subset of Climate Analysis layers. The climate coordinator currently selects five known local layer names and fails explicitly if they disappear from the WFS capabilities response.

Static VBB reference acquisition can be skipped with `--skip-gtfs`. OSM road acquisition is disabled by default and enabled with `--with-osm` because it is heavier and depends on the optional `osm` package extra.

OSM speed/travel-time imputation is not silently enabled. It requires `--allow-osmnx-speed-imputation` and the modelling choice is recorded in provenance.

## Energy-source behavior

`scripts/evaluate_energy.py` intentionally requires explicit dataset title, timestamp column and value column. Remote input is accepted only from the verified `https://www.stromnetz.berlin/` domain; a local copy requires an explicit `--source-url` for provenance.

The current forecasting pipeline assumes a regular time series for next-step forecasting and defaults to a seasonal lag of 96, corresponding to one day only when the input cadence is 15 minutes. The CLI therefore exposes `--seasonal-lag` rather than embedding a universal meaning.

## Licences and redistribution

The project records source licences/attribution where configured and carries licence information in provenance where the implementation supplies it. The repository does not convert external datasets into project-owned data or remove provider attribution.

## Verification status

Live-source and reference-source smoke workflows are operational compatibility checks, not permanent provider-availability guarantees and not scientific evaluation. Any dated success record should be interpreted only as evidence that the corresponding adapters were compatible with the providers at that time.
