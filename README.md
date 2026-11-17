# AcoustiBench

Sim-to-real evaluation harness for acoustic inference models.

AcoustiBench is a senior design project for running the same acoustic model on simulated audio and on real recordings, then comparing the results. Each run keeps the model, dataset, configuration, and scores so the team can review the sim-to-real gap and export a report.

**Team:** Audio AI Team 2 — Jonathankeith Murchison, Javon Whitfield, and Jonathan Price
**Advisor:** Dr. Sambit Bhattacharya

The working problem statement: acoustic models can change behavior when they move from simulated audio to real recordings, and the team needs a repeatable way to measure that change. Treat that statement as a draft until it is checked against the approved proposal. Confirmed facts and open decisions are listed in [AcoustiBench_Project_Reference.md](AcoustiBench_Project_Reference.md).

## What this repository does today

This is an early workflow, version 0.1.0. It can:

- Register a dataset as either `simulated` or `real`.
- Run a model through one Python interface.
- Store the model, dataset, configuration, metrics, and per-file predictions for each run.
- Compare one simulated run with one real run.
- Export Markdown, HTML, CSV, and JSON for a presentation or report.
- Open a local web page for the same workflow.

The task, datasets, models, metrics, and interface are **not confirmed** by the proposal notes. Until the team and advisor choose them, this code evaluates **closed-set classification**: one reference label per audio file, one predicted label per file.

## Assumptions in this version

- Audio is uncompressed WAV (8-, 16-, 24-, or 32-bit). Files are converted to mono.
- Every file is resampled with linear interpolation to the run’s target sample rate, 16 kHz unless the configuration says otherwise. The same rate should be used for both sides of a comparison.
- A run may use at most 120 seconds of each file. The default cap is 30 seconds.
- Metrics are accuracy, macro precision, macro recall, macro F1, weighted F1, a confusion matrix, inference latency, and expected calibration error when the model returns scores from 0 to 1.
- The sim-to-real gap is `real − simulated` on those aggregate scores. Files are not paired across the two datasets.
- For accuracy and F1, a negative gap means the real run scored lower. For calibration error and latency, a positive gap means the real run cost more.
- Scores on the included example audio only show that the harness runs. They are not study results.
- Python, FastAPI, SQLite, and NumPy are the tools used to build this starting point. They are not a confirmed course requirement.
- Registering a model imports and runs local Python. Point it only at code you trust.

## Example data

`acousticbench generate-examples` writes two synthetic datasets under `data/examples/`. Each folder contains `EXAMPLE.txt`.

| Dataset id | Domain label | What it actually is |
| --- | --- | --- |
| `example-sim-clean` | simulated | Generated tones, noise, and chirps with no extra degradation. Not the output of a room simulator. |
| `example-synthetic-realish` | real | The same kinds of signals with noise, gain changes, and low-pass filtering. Registered as `real` only so the comparison screen can be tried. These are not recordings. |

The built-in `example-spectral` model is a rule baseline for those three classes. `constant-label` always predicts one configured label and is there to check that the metrics move. Neither model is a trained research system.

## Setup

Use Python 3.10 or newer from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

On macOS or Linux, activate with `source .venv/bin/activate`.

Run the tests:

```powershell
pytest
```

## Run an evaluation

Generate the labeled example audio, then start the local page at http://127.0.0.1:8000 :

```powershell
acousticbench generate-examples
acousticbench serve
```

In the page, use **Evaluate**, choose **Paired sim-to-real**, and select `example-sim-clean` with `example-synthetic-realish`. The report pages state that those scores are from synthetic example audio.

The same path exists on the command line. `config/example_eval.yaml` is an example configuration, not a completed experiment.

```powershell
acousticbench eval --model example-spectral --dataset example-sim-clean --config config/example_eval.yaml
acousticbench eval --model example-spectral --dataset example-synthetic-realish --config config/example_eval.yaml
acousticbench runs
acousticbench compare --sim <simulated-run-id> --real <real-run-id> --out comparison.md
```

Runs are stored in `data/acousticbench.db`. Item-level predictions are written under `data/runs/`. Those folders are local and are not part of the git history.

## Add a dataset

Two layouts are supported.

**Class folders.** One directory per label:

```text
room-a/
  knock/
    take01.wav
  speech/
    take01.wav
```

**CSV manifest.** `manifest.csv` in the dataset root, with `path` and `label` columns. Optional columns are `split` (`train`, `val`, or `test`) and `domain`.

Copy `config/example_dataset.yaml`, set the real folder path and a description of where the audio came from, then register it:

```powershell
acousticbench datasets add --file config/example_dataset.yaml
acousticbench datasets list
```

Use domain `simulated` or `real` to match the recording condition. Put provenance in the description: simulator or room, sensor, who assigned the labels, and which split is for evaluation.

## Add a model

Copy `examples/custom_model_template.py` to `user_models/my_model.py`. Implement `predict` so it returns a `Prediction` with a label and, when the model has them, per-class scores that sum to 1.

Register it from the web page, from `config/models.yaml`, or by placing the module on the project import path. The qualified name looks like `user_models.my_model:MyModel`.

The runner calls `predict(audio, sample_rate)` with mono audio at the configured sample rate. This version accepts `task = "classification"` only. Detection, localization, and regression need a later interface once the team confirms the task.

## What a report contains

A finished run records the model id and parameters, dataset id and domain, sample rate, split, item cap, notes, per-class precision, recall, and F1, the confusion matrix, latency, and any files that failed to load. Comparison reports repeat the gap definition and warn when a dataset is synthetic, when the label sets differ, or when very few files were evaluated.

## Repository layout

```text
config/                 Example evaluation, dataset, and model configuration
examples/               Template for a team model
src/acousticbench/      Datasets, model interface, runner, metrics, reports, and web UI
tests/                  Tests for metrics, loading, and the evaluation record
user_models/            Folder for the team's own model modules
AcoustiBench_Project_Reference.md
```

## Still needs a team decision

The reference document’s open questions are still open. In particular, the team still needs to confirm the acoustic task, the simulator, the real recordings and their permissions, the first real model, the required metrics, who owns each part of the work, and the final report rules. Replace the example datasets before using any number in a presentation.
