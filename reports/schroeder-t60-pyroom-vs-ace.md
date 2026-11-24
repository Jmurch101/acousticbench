# AcoustiBench sim-to-real comparison

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Gap definition: gap = real - simulated
- Simulated run: `a343ba43a4b3` / Pyroomacoustics Sabine development set / Schroeder T60 baseline
- Real run: `13f32650cd71` / ACE single-channel measured impulse responses / Schroeder T60 baseline

For error and latency, a positive gap means the real run cost more.

## Metrics

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Mean absolute error | 0.1185 | 0.0623 | -0.0562 |
| Root mean squared error | 0.1571 | 0.0875 | -0.0696 |
| Median absolute error | 0.1004 | 0.0372 | -0.0633 |
| Mean latency (ms) | 0.4178 | 0.5402 | 0.1224 |

## By condition

Conditions are not paired across the two datasets. Each table is that run's own breakdown.

### Simulated

| Condition | MAE | RMSE | Support |
| --- | ---: | ---: | ---: |
| lecture | 0.2368 | 0.2509 | 12 |
| meeting | 0.0971 | 0.1016 | 12 |
| office | 0.0217 | 0.0281 | 12 |

### Real

| Condition | MAE | RMSE | Support |
| --- | ---: | ---: | ---: |
| Building_Lobby | 0.0691 | 0.0949 | 2 |
| Lecture_Room_1 | 0.1122 | 0.1122 | 2 |
| Lecture_Room_2 | 0.1680 | 0.1688 | 2 |
| Meeting_Room_1 | 0.0019 | 0.0019 | 2 |
| Meeting_Room_2 | 0.0333 | 0.0333 | 2 |
| Office_1 | 0.0484 | 0.0490 | 2 |
| Office_2 | 0.0034 | 0.0034 | 2 |

## Method

- Model: Schroeder backward integration (`schroeder-t60`). This is a classical baseline, not a sponsor neural model.
- Simulated reference: Sabine T60 from room volume, surface area, and absorption.
- Real reference: ACE Challenge fullband T60 for cruciform channel 1.
- Simulated notes: Expanded shoebox set. Reference T60 is Sabine from room absorption, not a measurement. Not a sponsor-model result.
- Real notes: ACE Challenge single-channel impulse responses. Reference is published fullband T60 for cruciform channel 1. Cite Eaton et al. 2016. Not a sponsor-model result.

## How to read this

- The task is numeric estimation. Error is the predicted value minus the reference value.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.
