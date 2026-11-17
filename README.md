# AcoustiBench

Sim-to-real evaluation harness for acoustic inference models.

AcoustiBench is a senior design project for running the same acoustic model on simulated audio and on real recordings, then comparing the results. Each run keeps the model, dataset, configuration, and scores so the team can review the sim-to-real gap and export a report.

**Team:** Audio AI Team 2 — Jonathankeith Murchison, Javon Whitfield, and Jonathan Price
**Advisor:** Dr. Sambit Bhattacharya

The proposal asks for a repeatable way to measure how acoustic models change between simulated audio and real recordings. The selected scope is in [DECISIONS.md](DECISIONS.md). Confirmed facts and the remaining sponsor questions are in [AcoustiBench_Project_Reference.md](AcoustiBench_Project_Reference.md).

## Selected scope

| Choice | Selection | Status |
| --- | --- | --- |
| First task | T60 estimation, in seconds | Implemented. MAE and RMSE. |
| Simulator | Pyroomacoustics (MIT) | Selected. Sponsor simulators stay external. |
| Real recordings | ACE Challenge corpus | Selected. Audio stays local. Zenodo lists CC BY 4.0; Imperial College states CC BY-ND 4.0. Follow the stricter rule. |
| First model | Schroeder T60 baseline (`schroeder-t60`) | Implemented. Not a sponsor neural model. |
| Second model | Sponsor baseline | Not in this repository yet. |

Room-size classification still runs with the earlier classification metrics. Distance estimation uses the same regression runner when a model provides a numeric prediction. Sound-event detection is still a required task and is not implemented.

## What this repository does today

This is an early workflow, version 0.1.0. It can:

- Register a dataset as either `simulated` or `real`.
- Run a model through one Python interface.
- Store the model, dataset, configuration, metrics, and per-file predictions for each run.
- Compare one simulated run with one real run.
- Export Markdown, HTML, CSV, and JSON for a presentation or report.
- Open a local web page for the same workflow.

The first completed task is T60 estimation. `acousticbench simulate-dev` builds a Pyroomacoustics set whose T60 labels are Sabine values and whose distance labels are straight-line source-to-microphone distances. `acousticbench prepare-ace` registers the local ACE impulse responses and a room-family label. `acousticbench demo` reruns Schroeder T60, the fixed room-family rule, and the direct-path distance baseline, then writes [reports/draft-final-report.md](reports/draft-final-report.md). Advisor approval is still required for the dataset list and the sponsor baseline models.

## Assumptions in this version

- Audio is uncompressed WAV (8-, 16-, 24-, or 32-bit). Files are converted to mono.
- Every file is resampled with linear interpolation to the run’s target sample rate, 16 kHz unless the configuration says otherwise. The same rate should be used for both sides of a comparison.
- A run may use at most 120 seconds of each file. The default cap is 30 seconds.
- T60 and distance use mean absolute error and root mean squared error. Classification uses accuracy, precision, recall, F1, a confusion matrix, and calibration error when the model returns scores.
- The sim-to-real gap is `real − simulated` on those aggregate scores. Files are not paired across the two datasets.
- For accuracy and F1, a negative gap means the real run scored lower. For error, calibration, and latency, a positive gap means the real run cost more.
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
python -m pip install "pyroomacoustics>=0.10"
```

`pyroomacoustics` is only needed for `simulate-dev`. The rest of the harness runs without it. Cite Scheibler, Bezzam, and Dokmanić, ICASSP 2018, when reporting those simulations.

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

## T60 evaluation

The built-in model is `schroeder-t60`. It is Schroeder backward integration (Schroeder, JASA, 1965), a classical baseline so the harness can run before sponsor weights arrive. It is not one of the two sponsor baselines required for the demonstration.

A manifest needs a `path` column and a `t60` or `target` column. An optional `condition` column, such as room type, is reported separately.

Create the simulated development set:

```powershell
acousticbench simulate-dev
```

That writes 36 shoebox impulse responses to `data/simulated/pyroom-sabine-dev` and registers dataset `pyroom-sabine-dev`: 9 rooms and 4 microphone positions, in the families office, meeting, and lecture. The `t60` column is the Sabine value for that room's absorption. It is not the Schroeder estimate of the same file. The `distance` column is the straight-line source-to-microphone distance in meters. Simulated wav files are gitignored.

For the ACE corpus, download `ACE_Corpus_RIRN_Single.tbz2` and `ACE_Corpus_Data.tbz2` from [Zenodo](https://doi.org/10.5281/zenodo.6257551) into `data/ace/downloads/`. Then:

```powershell
acousticbench prepare-ace
acousticbench eval --model schroeder-t60 --dataset pyroom-sabine-dev --sample-rate 16000 --max-seconds 10 --notes "Development simulation. Reference T60 is Sabine from room absorption, not a measurement."
acousticbench eval --model schroeder-t60 --dataset ace-single-rir --sample-rate 16000 --max-seconds 30 --notes "ACE Challenge single-channel impulse responses. Reference is published fullband T60 for cruciform channel 1."
acousticbench compare --sim <simulated-run-id> --real <real-run-id> --out reports/schroeder-t60-pyroom-vs-ace.md
```

`prepare-ace` extracts the archive locally, matches the 14 single-channel impulse responses to the published fullband T60 for cruciform channel 1, and registers dataset `ace-single-rir`. The `label` column collapses the published room name to office, meeting, lecture, or lobby. It does not copy audio into git. Cite Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM TASLP, 2016. The Zenodo record lists CC BY 4.0 and the Imperial College page states CC BY-ND 4.0. Do not commit the audio, and do not distribute a modified copy.

After both datasets are registered, one command reruns the three development baselines and rewrites the reports from those runs:

```powershell
acousticbench demo
```

`t60-room-rule` maps Schroeder T60 through fixed bands: below 0.50 s is office, below 0.80 s is meeting, and every longer decay is lecture. Those cuts were taken from the gaps in the simulated design and were not fit to the ACE scores. The rule has no lobby class. `direct-path-distance` is evaluated only on the simulated set, because the ACE mean table has no distance in meters.

The current write-up is [reports/draft-final-report.md](reports/draft-final-report.md). It is a team draft, not the submitted final report. `config/ace_dataset.yaml` remains a template for a manual manifest if the audio lives somewhere else.

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

**CSV manifest.** `manifest.csv` in the dataset root. Classification uses `path` and `label`. T60 or distance uses `path` and `t60`, `target`, `reference`, or `distance`. Optional columns are `split` (`train`, `val`, or `test`), `condition`, and `domain`.

Copy `config/example_dataset.yaml`, set the real folder path and a description of where the audio came from, then register it:

```powershell
acousticbench datasets add --file config/example_dataset.yaml
acousticbench datasets list
```

Use domain `simulated` or `real` to match the recording condition. Put provenance in the description: simulator or room, sensor, who assigned the labels, and which split is for evaluation.

## Add a model

Copy `examples/custom_model_template.py` to `user_models/my_model.py`. Implement `predict` so it returns a `Prediction` with a label and, when the model has them, per-class scores that sum to 1.

Register it from the web page, from `config/models.yaml`, or by placing the module on the project import path. The qualified name looks like `user_models.my_model:MyModel`.

The runner calls `load()` once, then `predict(audio, sample_rate)` with mono audio at the configured sample rate. Classification returns a label. T60 and distance return `Prediction.value` in seconds or meters. Sound-event detection is not implemented.

## What a report contains

A finished run records the model id and parameters, dataset id and domain, sample rate, split, item cap, notes, latency, provenance, and any files that failed to load. Classification reports add per-class precision, recall, F1, and a confusion matrix. T60 and distance reports add MAE, RMSE, median absolute error, and a breakdown by condition. Comparison reports repeat the gap definition and warn when a dataset is synthetic, when the tasks differ, or when very few files were evaluated.

## Repository layout

```text
config/                 Example evaluation, dataset, and model configuration
examples/               Template for a team model
reports/                Exported comparison reports
src/acousticbench/      Datasets, model interface, runner, metrics, reports, and web UI
tests/                  Tests for metrics, loading, T60, and the evaluation record
user_models/            Folder for the team's own model modules
DECISIONS.md            Working task, simulator, corpus, and model choices
AcoustiBench_Project_Reference.md
```

`data/ace/`, `data/simulated/`, `data/examples/`, `data/runs/`, and the SQLite database stay on the machine that ran the evaluation.

## Still open

Dr. Bhattacharya still needs to approve the dataset list. The sponsor simulator export and the two sponsor baseline models are not in this repository. Distance on a measured corpus needs a published meter label; ACE does not provide one. Sound-event detection is not implemented, because ACE has no event time labels. [reports/draft-final-report.md](reports/draft-final-report.md) is the working draft. The submitted final report and the presentation are still open. Do not present the synthetic example datasets as study results.
