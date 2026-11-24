# AcoustiBench sim-to-real comparison

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Gap definition: gap = real - simulated
- Simulated run: `1b8e0fe359ad` / Synthesized noise-type clips / PANNs Cnn14 noise type
- Real run: `e1ad23bc0f63` / ACE noise-type clips / PANNs Cnn14 noise type

For accuracy and F1, a negative gap means the real run scored lower.
For calibration error and latency, a positive gap means the real run cost more.

## Warnings

- The simulated run used example or synthetic audio. Do not present its scores as study results.

## Metrics

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Accuracy | 0.3333 | 0.5952 | 0.2619 |
| Macro F1 | 0.1975 | 0.5094 | 0.3119 |
| Macro precision | 0.1404 | 0.7254 | 0.5850 |
| Macro recall | 0.3333 | 0.5952 | 0.2619 |
| Weighted F1 | 0.1975 | 0.5094 | 0.3119 |
| Expected calibration error | 0.4865 | 0.1882 | -0.2983 |
| Mean latency (ms) | 47.1158 | 266.3890 | 219.2732 |

## Per-class F1

| Class | Simulated F1 | Real F1 | Gap | Simulated support | Real support |
| --- | ---: | ---: | ---: | ---: | ---: |
| ambient | 0.5926 | 0.5714 | -0.0212 | 8 | 14 |
| babble | 0.0000 | 0.8235 | 0.8235 | 8 | 14 |
| fan | 0.0000 | 0.1333 | 0.1333 | 8 | 14 |

## How to read this

- The task assumed here is closed-set classification: one label per file.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.
