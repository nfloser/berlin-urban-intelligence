# Data sources

`config/sources.yaml` contains provider URLs, licensing and known limitations. Runtime transport status is independent of metadata and of the scientific quality of a value.

`python scripts/refresh_live.py` acquires DWD, Berlin LQI and VBB independently. A failed source preserves previously persisted values while recording failure; the age of those values continues to increase. DWD -999 values remain absent. Missing VBB trip updates are not proof of normal service.

`python scripts/refresh_reference.py --skip-gtfs` acquires official WFS layers. Omit the flag to include static GTFS. Add `--with-osm` only after installing the optional osm extra. Road speed imputation requires the explicit command flag and is recorded in provenance. The reference CLI retains previous layers on individual failures; inspect reference errors before using retained layers.

Energy input requires an inspected Stromnetz Berlin CSV and explicit column names. Run `python scripts/evaluate_energy.py --help`. The UCI household series is not Berlin operational data.

The LQI adapter supports the official station/data/component envelope and groups component grades by exact station timestamp. Null and negative unavailable grades are omitted; values are never truncated into a valid index. Coverage is therefore the set of usable published station records, not a claim that every station reported.
