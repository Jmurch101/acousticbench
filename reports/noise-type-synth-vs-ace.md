# AcoustiBench sim-to-real comparison

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Gap definition: gap = real - simulated
- Simulated run: `6e775dc9483d` / Synthesized noise-type clips / Noise-type rule
- Real run: `27f93b8b019f` / ACE noise-type clips / Noise-type rule

For accuracy and F1, a negative gap means the real run scored lower.
For calibration error and latency, a positive gap means the real run cost more.

## Warnings

- The simulated run used example or synthetic audio. Do not present its scores as study results.

## Metrics

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Accuracy | 1.0000 | 0.8095 | -0.1905 |
| Macro F1 | 1.0000 | 0.8071 | -0.1929 |
| Macro precision | 1.0000 | 0.8212 | -0.1788 |
| Macro recall | 1.0000 | 0.8095 | -0.1905 |
| Weighted F1 | 1.0000 | 0.8071 | -0.1929 |
| Expected calibration error | n/a | n/a | n/a |
| Mean latency (ms) | 0.3285 | 7.4008 | 7.0723 |

## Per-class F1

| Class | Simulated F1 | Real F1 | Gap | Simulated support | Real support |
| --- | ---: | ---: | ---: | ---: | ---: |
| ambient | 1.0000 | 0.8889 | -0.1111 | 8 | 14 |
| babble | 1.0000 | 0.8125 | -0.1875 | 8 | 14 |
| fan | 1.0000 | 0.7200 | -0.2800 | 8 | 14 |

## How to read this

- The task assumed here is closed-set classification: one label per file.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.
