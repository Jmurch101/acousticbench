# AcoustiBench evaluation report

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Run: `45187d3bc956`
- Status: completed
- Created: 2026-11-24T19:13:22+00:00
- Model: Direct-path distance baseline (`direct-path-distance`)
- Dataset: Pyroomacoustics Sabine development set (`simulated`)
- Notes: Reference is the straight-line source-to-microphone distance in the shoebox. ACE is omitted because the mean table has no distance in meters.

## Metrics

- Task: distance
- Items evaluated: 36 of 36
- Load or inference errors: 0
- Mean latency: 0.0162 ms
- Unit: meters
- Mean absolute error: 0.6959
- Root mean squared error: 0.7009
- Median absolute error: 0.7021

## By condition

| Condition | MAE | RMSE | Support |
| --- | ---: | ---: | ---: |
| lecture | 0.7329 | 0.7354 | 12 |
| meeting | 0.6817 | 0.6884 | 12 |
| office | 0.6730 | 0.6776 | 12 |

## Provenance

- AcoustiBench: 0.1.0
- Python: 3.14.3
- Git revision: 725d3d8bd4d42170b011f70d58ab18be902035c5
- Sample rate: 16000
- Dataset id: pyroom-sabine-dev
- Dataset simulator: pyroomacoustics
- Dataset simulator_version: 0.10.1
- Dataset image_order: 40
- Dataset sample_rate_hz: 16000
- Dataset air_absorption: False
- Dataset t60_reference: sabine
- Dataset distance_reference: euclidean source to microphone
- Model reference: Direct-path onset times 343 m/s
- Model unit: meters
- Model speed_of_sound_m_s: 343.0
- Model onset_fraction: 0.05

## How to read this

- The task is numeric estimation. Error is the predicted value minus the reference value.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.
