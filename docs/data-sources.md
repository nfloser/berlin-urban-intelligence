# Data sources and licences

`config/sources.yaml` is the machine-readable registry. Runtime adapters must match entries in that registry and preserve source attribution.

| Source | Role | State semantics | Licence / attribution |
|---|---|---|---|
| Berliner Luftgütemessnetz REST API | air quality / LQI | observed; current automatic values remain provisional | Datenlizenz Deutschland – Namensnennung 2.0 |
| VBB GTFS-Realtime | current public-transport updates | observed realtime feed metadata | CC BY 4.0 |
| VBB GTFS static | stops/reference transit topology | reference | CC BY 4.0 |
| DWD CDC 10-minute air temperature, Berlin-Tempelhof 00433 | meteorology | observed; `now` product not final QC | DWD Open Data terms/attribution recorded by registry |
| Berlin Climate Analysis 2022 WFS | urban-climate reference/model fields | `official_modelled`, never live observation | DL-DE-Zero-2.0 |
| OpenStreetMap | road-network reference | community-maintained reference/derived topology | ODbL 1.0, © OpenStreetMap contributors |
| Stromnetz Berlin source boundary | Berlin energy dataset acquisition where configured | source/reference; forecasts require validated evaluation | source-specific terms recorded with artefact |
| UCI Individual Household Electric Power Consumption | methodological research reference only | never Berlin operational state | CC BY 4.0 |

The platform does not redistribute external datasets under a new licence. Generated state keeps provider/source identifiers and source-licence metadata.

Live availability is intentionally not a deterministic CI invariant; live smoke tests are separated from unit/integration tests.
