# AcoustiBench evaluation report

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Run: `4e6cf2acdaaf`
- Status: completed
- Created: 2026-11-24T20:23:11+00:00
- Model: Schroeder T60 baseline (`schroeder-t60`)
- Dataset: OpenSLR simulated room impulse responses (`simulated`)
- Notes: OpenSLR 26 subset. Reference T60 is Sabine from the published room dimensions and absorption, not a printed T60.

## Metrics

- Task: t60
- Items evaluated: 36 of 36
- Load or inference errors: 0
- Mean latency: 0.5719 ms
- Unit: seconds
- Mean absolute error: 1.4748
- Root mean squared error: 2.0208
- Median absolute error: 1.5359

## By condition

| Condition | MAE | RMSE | Support |
| --- | ---: | ---: | ---: |
| large | 2.9581 | 3.1079 | 12 |
| medium | 1.4126 | 1.6083 | 12 |
| small | 0.0537 | 0.0707 | 12 |

## Provenance

- AcoustiBench: 0.1.0
- Python: 3.14.3
- Git revision: 725d3d8bd4d42170b011f70d58ab18be902035c5
- Sample rate: 16000
- Dataset id: openslr-sim-rir
- Dataset simulator: image-source, Habets RIR generator
- Dataset sample_rate_hz: 16000
- Dataset t60_reference: sabine from published dimensions and absorption
- Dataset room_label: small, medium, large
- Model reference: Schroeder, JASA, 1965
- Model unit: seconds

## How to read this

- The task is numeric estimation. Error is the predicted value minus the reference value.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.

