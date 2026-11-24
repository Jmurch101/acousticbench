# AcoustiBench evaluation report

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- Run: `e1ad23bc0f63`
- Status: completed
- Created: 2026-11-24T20:24:11+00:00
- Model: PANNs Cnn14 noise type (`panns-noise-type`)
- Dataset: ACE noise-type clips (`real`)
- Notes: PANNs Cnn14_16k on ACE ambient, babble, and fan filenames. The label map was not fit to ACE.

## Metrics

- Task: classification
- Items evaluated: 42 of 42
- Load or inference errors: 0
- Mean latency: 266.3890 ms
- Accuracy: 0.5952
- Macro F1: 0.5094
- Weighted F1: 0.5094
- Macro precision: 0.7254
- Macro recall: 0.5952
- Expected calibration error: 0.1882

## Per class

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| ambient | 0.4762 | 0.7143 | 0.5714 | 14 |
| babble | 0.7000 | 1.0000 | 0.8235 | 14 |
| fan | 1.0000 | 0.0714 | 0.1333 | 14 |

## Confusion matrix

| True \ predicted | ambient | babble | fan |
| --- | ---: | ---: | ---: |
| ambient | 10 | 4 | 0 |
| babble | 0 | 14 | 0 |
| fan | 11 | 2 | 1 |

## Provenance

- AcoustiBench: 0.1.0
- Python: 3.14.3
- Git revision: 725d3d8bd4d42170b011f70d58ab18be902035c5
- Sample rate: 16000
- Dataset id: ace-noise-types
- Dataset t60_table: not used
- Dataset room_label: folder name collapsed to office, meeting, lecture, lobby

## How to read this

- The task assumed here is closed-set classification: one label per file.
- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.
- A model confidence score is used for calibration only when the model provides one.
- Scores from a run marked as example data are not study results.

