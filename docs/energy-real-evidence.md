# Real Berlin energy evidence

This document records point-in-time real-source evidence for the Berlin Urban Intelligence energy path. It is intentionally separate from deterministic fixtures and does not commit the provider CSV files.

## Scientific scope

The source is Stromnetz Berlin's publication of annual load curves for the Berlin distribution grid. The evaluated curve is the **2024 high-voltage load curve**. Its values are network-level electrical load in **kW**. They are not total Berlin electricity consumption and they are not a live city-wide demand measurement.

The forecast produced by this evidence workflow is one 15-minute source interval ahead over that historical high-voltage series. Because the evidence year is historical, the persisted forecast is correctly exposed as stale when loaded in the current application. It is evidence that acquisition, validation, chronological evaluation, persistence and API integration work; it is not a current grid-control forecast.

## Why 2024 is used instead of the newer 2025 publication

On 2026-09-16, `.github/workflows/energy-real-evaluation.yml` inspected all five official 2025 network-level load-curve CSV files (high voltage, high/medium voltage, medium voltage, medium/low voltage and low voltage). Each file contained exactly 35,040 numeric quarter-hour values but also contained a contiguous block of **96 rows whose date and time fields were literally `#BEZUG!`**.

The numeric values in every 2025 file reconcile exactly with that file's published annual maximum and rounded annual work. The defect is therefore specifically a timestamp defect, not evidence that the values are synthetic or absent. The repository does **not** invent timestamps for those 96 rows. The strict annual parser rejects the files instead.

The official 2024 high-voltage CSV was then inspected as the reproducible chronological source. It contains 35,136 quarter-hour values for the leap year, no invalid date/time labels, the expected 92/100-row daylight-saving transition days, and a continuous physical 15-minute UTC sequence. Its published maximum of 2,034,416 kW and published annual work of 11,834,389,631 kWh are reproduced exactly by the data (annual work after the provider's whole-kWh rounding convention). The downloaded file observed by the evidence workflow had SHA-256 `dd1e727d0036f58b3bd060e3a4747e9c310e7c2fcb7b999f8457cf2e090b3dab`.

## Reproducible workflow

The workflow downloads the official source at run time and never commits it. The strict `StromnetzBerlinCsvAdapter.parse_published_annual_load_curve()` contract verifies:

- provider, dataset title and publication year;
- `Max in kW`, `Arbeit in kWh` and `Datum;Zeit;` publication semantics;
- exact annual quarter-hour point count;
- the published endpoint convention across Europe/Berlin DST transitions while storing a continuous UTC sequence;
- numeric load parsing with German thousands separators;
- equality between the declared and observed annual maximum; and
- equality between declared annual work and the rounded quarter-hour integral.

After validation, `scripts/evaluate_energy.py` runs the existing leakage-safe chronological holdout workflow, selects the candidate from measured holdout metrics, creates a one-step forecast bound to the same dataset fingerprint and persists `EnergyState`. The workflow then constructs an `EnergyAgent`, exercises its evaluation/forecast fingerprint guard and starts the real FastAPI application with that persisted state before verifying `/api/v1/energy`.

The equivalent command is:

```bash
python scripts/evaluate_energy.py \
  --input /path/to/Jahreshoechstlast-2024-Hochspannung.csv \
  --source-url "https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2024/Jahreshoechstlast-2024-Hochspannung.csv" \
  --dataset "Stromnetz Berlin Hochspannungs-Lastkurve 2024" \
  --published-annual-load-curve \
  --expected-title "Jahreshöchstlast in der Hochspannung" \
  --expected-year 2024 \
  --seasonal-lag 96 \
  --test-fraction 0.2 \
  --state data/runtime/energy.json
```

## Recorded point-in-time evaluation

GitHub Actions run `35082301338` on 2026-09-16 completed the complete source → parser → evaluation → persisted state → `EnergyAgent` → API path successfully. The calculated results were:

| Evidence | Result |
|---|---:|
| Selected candidate | `ridge` |
| Candidate MAE | 6,832.567799 kW |
| Candidate RMSE | 9,488.502204 kW |
| Baseline | `persistence` |
| Baseline MAE | 19,347.097888 kW |
| One-step forecast valid at | 2024-12-31 23:15:00 UTC |
| One-step forecast | 1,173,532.458077 kW |
| Dataset fingerprint | `feb97ff824a8231156cf11c923e4c628988e0e865b3a74e7a79401297825bf00` |

These numbers are evidence from that source snapshot and workflow run, not constants used to make the implementation pass. A future provider revision can change the source hash, model fingerprint and measured metrics; the workflow should then be interpreted as a new point-in-time evaluation rather than silently compared as if the input were unchanged.

## What this evidence does not establish

It does not establish causal relationships between energy and other urban domains, production forecasting quality, uncertainty calibration, current Berlin electricity demand, or operational suitability for grid dispatch. It verifies the implemented historical high-voltage load forecasting path and its provenance/fingerprint boundaries against a real official Berlin-scoped publication.
