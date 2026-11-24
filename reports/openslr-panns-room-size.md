# AcoustiBench evaluation report

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Run: `2d990a2bfc51`
- Status: completed
- Created: 2026-11-24T20:23:12+00:00
- Model: PANNs Cnn14 room size (`panns-room-size`)
- Dataset: OpenSLR simulated room impulse responses (`simulated`)
- Notes: PANNs Cnn14_16k room-size map on OpenSLR 26 impulse responses. The map was not fit to these files.

## Metrics

- Task: classification
- Items evaluated: 36 of 36
- Load or inference errors: 0
- Mean latency: 53.0275 ms
- Accuracy: 0.3333
- Macro F1: 0.1667
- Weighted F1: 0.1667
- Macro precision: 0.1111
- Macro recall: 0.3333
- Expected calibration error: 0.3253

## Per class

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| large | 0.0000 | 0.0000 | 0.0000 | 12 |
| medium | 0.0000 | 0.0000 | 0.0000 | 12 |
| small | 0.3333 | 1.0000 | 0.5000 | 12 |

## Confusion matrix

| True \ predicted | large | medium | small |
| --- | ---: | ---: | ---: |
| large | 0 | 0 | 12 |
| medium | 0 | 0 | 12 |
| small | 0 | 0 | 12 |

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

## How to read this

- The task assumed here is closed-set classification: one label per file.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.

