# Working decisions

These choices come from the Fall 2026 proposal and the October 9, 2026 midterm report. The team is using them so implementation can continue. Dr. Bhattacharya still needs to approve the dataset list and supply the second baseline model before those items meet the proposal's success criteria.

## First task

**Reverberation-time estimation (T60), in seconds.**

The proposal requires four tasks: room-size classification, T60 estimation, source-to-microphone distance estimation, and sound-event detection. T60 is the first one this harness completes. The proposal assigns it mean absolute error and root mean squared error. Room-size classification can still use the existing classification metrics. Distance uses the same regression runner when a distance model is registered. Sound-event detection is not implemented yet.

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
| ACE corpus | Creative Commons Attribution-NoDerivatives 4.0 | Download and use the unmodified corpus for the project, with attribution. Do not distribute modified ACE audio. Do not commit the audio to GitHub. |
| SoundSpaces 2.0 scene data, Steam Audio, Unreal Engine | Sponsor and vendor terms | Use only inside the sponsor environment after the advisor confirms the license. Do not commit those files. |
| Schroeder T60 code in this repository | Project code | The implementation is the team's. The method is Schroeder, JASA, 1965. |

## First model

**Schroeder backward-integration T60 estimator**, model id `schroeder-t60`.

It estimates T60 from an impulse response. It is a classical acoustic baseline so the harness can be tested before sponsor weights arrive. It is not a neural model, and it is not one of the two sponsor-provided baselines required for the final demonstration.

The second baseline is still the sponsor's model. The proposal says the team will not train a new model as required work, and no sponsor checkpoint is in this repository.

## Proposed dataset list

1. Pyroomacoustics shoebox simulations, domain `simulated`, for development. `acousticbench simulate-dev` writes `data/simulated/pyroom-sabine-dev`. The `t60` column is the Sabine value for that room's absorption. It is not the Schroeder estimate of the same file.
2. ACE Challenge measured impulse responses, domain `real`. `acousticbench prepare-ace` registers the local single-channel archive as `ace-single-rir`. The label is published fullband T60 for cruciform channel 1. The audio stays in `data/ace/` and is gitignored.
3. Sponsor SoundSpaces 2.0, Steam Audio, or MetaSounds exports, connected through the same manifest when those files are provided.

Items 1 and 3 are not substitutes for each other. Pyroomacoustics is the runnable development simulator. The sponsor pipeline remains the research simulator.

## Still open

- Advisor approval of this dataset list.
- The sponsor's two baseline models, and a repeatable seed for those runs.
- Distance estimation and sound-event detection implementations.
- Full DCASE sound-event metrics, Docker packaging, React, and GitHub Actions from the midterm software list.
- The final report and presentation.
