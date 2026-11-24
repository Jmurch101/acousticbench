# Working decisions

These choices started from the Fall 2026 proposal and the October 9, 2026 midterm report. The sponsor did not provide simulator files or model checkpoints. The team made the remaining choices so the four tasks could be finished. Those choices are not a signature from Dr. Bhattacharya.

## First task

**Reverberation-time estimation (T60), in seconds.**

The proposal requires four tasks: room-size classification, T60 estimation, source-to-microphone distance estimation, and sound-event detection. All four now have a measured baseline. T60 uses MAE and RMSE. Room family and sound type use the classification metrics. Distance uses MAE and RMSE in meters. Sound type is clip-level because ACE has no event times.

## Simulator

**Pyroomacoustics** (Scheibler, Bezzam, and Dokmanić, ICASSP 2018).

License: MIT, copyright EPFL-LCAV. The team may use it in this project. Cite the paper when reporting simulated results. Pyroomacoustics is the simulator named in the proposal that the team can run in Python.

SoundSpaces 2.0, the GPU image-source method, Steam Audio, and Unreal Engine 5 MetaSounds stay on the sponsor side. The proposal says those simulators, their synthetic datasets, and the sponsor's trained models are external. This repository does not include Matterport or other scene data.

## Real recordings

**ACE Challenge corpus** (Eaton, Gaubitch, Moore, and Naylor).

This is the measured-room benchmark already cited in the proposal. It contains real acoustic impulse responses, noise, and speech recorded in rooms at Imperial College London, with ground-truth T60. The development and evaluation splits are part of the corpus.

Access:

- Imperial College ACE page: https://www.imperial.ac.uk/speech-audio-processing/projects/ace-challenge/
- Zenodo record: https://zenodo.org/records/6257551

Cite Eaton et al., IEEE/ACM TASLP, 2016, when any ACE file is used. A manifest template is in `config/ace_dataset.yaml`.

## Permissions

| Material | License | What the team may do |
| --- | --- | --- |
| Pyroomacoustics | MIT | Use, modify, and run it. Keep the copyright notice with any copy of the software. |
| OpenSLR 26 simulated room impulse responses | Apache 2.0 | Use the archive. Cite Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017. Do not commit the audio. |
| PANNs Cnn14_16k checkpoint | CC BY 4.0 weights; MIT inference code | Use the published weights. Cite Kong, Cao, Iqbal, Wang, Wang, and Plumbley, IEEE/ACM TASLP 2020. Do not commit the checkpoint. |
| ACE corpus | Creative Commons Attribution-NoDerivatives 4.0 | Download and use the unmodified corpus for the project, with attribution. Do not distribute modified ACE audio. Do not commit the audio to GitHub. |
| SoundSpaces 2.0 scene data, Steam Audio, Unreal Engine | Sponsor and vendor terms | Use only inside the sponsor environment after the advisor confirms the license. Do not commit those files. |
| Schroeder T60 code in this repository | Project code | The implementation is the team's. The method is Schroeder, JASA, 1965. |

## First model

**Schroeder backward-integration T60 estimator**, model id `schroeder-t60`.

It estimates T60 from an impulse response. It is a classical acoustic baseline so the harness can be tested before sponsor weights arrive. It is not a neural model, and it is not one of the two sponsor-provided baselines required for the final demonstration.

The sponsor checkpoints were not provided. The team did not train a neural model. The demonstration pair is Schroeder T60 and the room-family rule. Direct-path distance and the noise-type rule cover the other tasks.

A public checkpoint was added later: PANNs Cnn14 trained at 16 kHz (`panns-noise-type` and `panns-room-size`). The weights are Zenodo record 3987831, file `Cnn14_16k_mAP=0.438.pth`, 358,668,570 bytes, md5 `362fc5ff18f1d6ad2f6d464b45893f2c`. They stay in `data/models/` and are gitignored. The AudioSet tag names are mapped to the project labels with a fixed list. That list was not fit to ACE or to OpenSLR.

## Dataset list

SoundSpaces, Steam Audio, and Unreal were not delivered, so they are not in this list. The team is using these datasets.

1. Pyroomacoustics shoebox simulations, domain `simulated`. `acousticbench simulate-dev` writes `data/simulated/pyroom-sabine-dev`. The `t60` column is the Sabine value. The `distance` column is the straight-line source-to-microphone distance. The room classes are office, meeting, and lecture.
2. ACE Challenge impulse responses, domain `real`, dataset `ace-single-rir`. The T60 label is published fullband T60 for cruciform channel 1. The room classes are office, meeting, lecture, and lobby.
3. ACE ambient, babble, and fan clips, domain `real`, dataset `ace-noise-types`. The label is the class in the filename. A synthesized check set, `synth-noise-types`, is the simulated side. The audio stays in `data/ace/` and is gitignored.
4. OpenSLR 26 simulated room impulse responses, domain `simulated`, dataset `openslr-sim-rir`. `acousticbench prepare-openslr` extracts the first impulse response from rooms 1–12 in each size group (36 files). The label is small, medium, or large. The `t60` column is Sabine's formula from the published length, width, height, and absorption. The archive itself does not print T60. The zip stays in `data/simulated/downloads/` and is gitignored. This is not a SoundSpaces, Steam Audio, or Unreal export.

## Development baselines that do not need new sponsor files

- Room family: `t60-room-rule`. Schroeder T60 below 0.50 s is office, below 0.80 s is meeting, and every longer decay is lecture. The cuts sit between the simulated design bands (office at or below 0.45 s, meeting from 0.55 s, lecture from 0.90 s). They were not fit to ACE. ACE adds a lobby class that the rule does not predict.
- Distance: `direct-path-distance` on the simulated set only. The label is the Euclidean source-to-microphone distance. The estimate is the direct-path onset times 343 m/s. The ACE mean table has DRR, not meters.
- `acousticbench demo` rewrites the comparison reports and `reports/draft-final-report.md` from completed runs.

## Still left

- Turn in `reports/final-report.md` and give the presentation.
- If sponsor files arrive later, register them through the same manifest and rerun `acousticbench demo`.
- Docker, React, and GitHub Actions were on the midterm software list. The team is not treating them as required to finish.
