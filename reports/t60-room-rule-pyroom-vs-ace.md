# AcoustiBench sim-to-real comparison

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Gap definition: gap = real - simulated
- Simulated run: `b3290320b3c0` / Pyroomacoustics Sabine development set / T60 room-family rule
- Real run: `9a5ca60f3a1d` / ACE single-channel measured impulse responses / T60 room-family rule

For accuracy and F1, a negative gap means the real run scored lower.
For calibration error and latency, a positive gap means the real run cost more.

## Warnings

- Label sets differ. Per-class gaps are reported only for labels present in both runs.

## Metrics

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Accuracy | 0.8611 | 0.4286 | -0.4325 |
| Macro F1 | 0.8585 | 0.2917 | -0.5669 |
| Macro precision | 0.8796 | 0.2500 | -0.6296 |
| Macro recall | 0.8611 | 0.3750 | -0.4861 |
| Weighted F1 | 0.8585 | 0.3333 | -0.5252 |
| Expected calibration error | n/a | n/a | n/a |
| Mean latency (ms) | 0.3738 | 0.4836 | 0.1097 |

## Per-class F1

| Class | Simulated F1 | Real F1 | Gap | Simulated support | Real support |
| --- | ---: | ---: | ---: | ---: | ---: |
| lecture | 0.8571 | 0.5000 | -0.3571 | 12 | 4 |
| meeting | 0.7619 | 0.0000 | -0.7619 | 12 | 4 |
| office | 0.9565 | 0.6667 | -0.2899 | 12 | 4 |

## How to read this

- The task assumed here is closed-set classification: one label per file.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.
