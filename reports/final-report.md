# AcoustiBench project report

The sponsor did not provide simulator files or model checkpoints. The choices below are the team's, made so the four tasks could be finished. They are not a signature from Dr. Bhattacharya.

- Team: Jonathankeith Murchison, Javon Whitfield, Jonathan Price
- Advisor: Dr. Sambit Bhattacharya
- T60 simulated run: `a343ba43a4b3`
- T60 real run: `13f32650cd71`
- Room-type simulated run: `b3290320b3c0`
- Room-type real run: `9a5ca60f3a1d`
- Distance simulated run: `45187d3bc956`

## Team decisions

- Datasets: Pyroomacoustics shoeboxes, ACE impulse responses, and the ACE ambient, babble, and fan clips. SoundSpaces, Steam Audio, and Unreal files were not delivered.
- Room classes: office, meeting, lecture, and lobby, taken from the ACE room names.
- Demonstration models: Schroeder T60 and the fixed room-family rule. Direct-path distance and the noise-type rule cover the other two tasks. No neural model was trained.
- Distance stays on the simulated rooms. ACE does not publish distance in meters.
- Sound type is clip-level. ACE does not publish event start and end times.

## T60

The model is Schroeder backward integration (`schroeder-t60`). It is a classical baseline, not a sponsor neural model.
The simulated reference is the Sabine T60 for each shoebox. The real reference is the ACE Challenge fullband T60 for cruciform channel 1.
Rooms are not paired. The gap is the ACE aggregate minus the simulated aggregate.

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Mean absolute error | 0.1185 | 0.0623 | -0.0562 |
| Root mean squared error | 0.1571 | 0.0875 | -0.0696 |
| Median absolute error | 0.1004 | 0.0372 | -0.0633 |
| Mean latency (ms) | 0.4178 | 0.5402 | 0.1224 |

## Room type

The classifier is `t60-room-rule`. It estimates Schroeder T60 and applies fixed bands: below 0.50 s is office, below 0.80 s is meeting, and every longer decay is lecture.
Those cuts sit in the gaps between the simulated design bands. They were not adjusted to the ACE scores. The rule has no lobby class. ACE lobby files are a fourth real label.

- Warning: Label sets differ. Per-class gaps are reported only for labels present in both runs.

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Accuracy | 0.8611 | 0.4286 | -0.4325 |
| Macro F1 | 0.8585 | 0.2917 | -0.5669 |
| Macro precision | 0.8796 | 0.2500 | -0.6296 |
| Macro recall | 0.8611 | 0.3750 | -0.4861 |
| Weighted F1 | 0.8585 | 0.3333 | -0.5252 |
| Expected calibration error | n/a | n/a | n/a |
| Mean latency (ms) | 0.3738 | 0.4836 | 0.1097 |

Off-diagonal counts from the completed runs:
- Simulated: 4 meeting file(s) predicted as lecture.
- Simulated: 1 office file(s) predicted as meeting.
- Real: 2 lecture file(s) predicted as meeting.
- Real: 2 lobby file(s) predicted as lecture.
- Real: 4 meeting file(s) predicted as office.

## Distance

Only the simulated set has a distance label. It is the straight-line distance between the source and the microphone.
The estimator is `direct-path-distance`: the first sample at 5 percent of the peak, times 343 m/s.
The ACE mean table publishes direct-to-reverberant ratio, not distance in meters, so this report has no real-side distance run.

- Items: 36
- Mean absolute error: 0.6959 meters
- Root mean squared error: 0.7009 meters
- Median absolute error: 0.7021 meters

## Sound type

The clips are ambient, babble, or fan. The rule uses zero crossings and the share of energy below 300 Hz.
The cuts were inspected on the ACE files, so the ACE accuracy describes this corpus. It is not a separate test set.
The synthesized clips only check that the rule fires. ACE has no start and end times, so this is not timed event detection.

- Simulated run: `6e775dc9483d`
- Real run: `27f93b8b019f`

- Warning: The simulated run used example or synthetic audio. Do not present its scores as study results.

| Metric | Simulated | Real | Gap (real - simulated) |
| --- | ---: | ---: | ---: |
| Accuracy | 1.0000 | 0.8095 | -0.1905 |
| Macro F1 | 1.0000 | 0.8071 | -0.1929 |
| Macro precision | 1.0000 | 0.8212 | -0.1788 |
| Macro recall | 1.0000 | 0.8095 | -0.1905 |
| Weighted F1 | 1.0000 | 0.8071 | -0.1929 |
| Expected calibration error | n/a | n/a | n/a |
| Mean latency (ms) | 0.3285 | 7.4008 | 7.0723 |

Off-diagonal counts from the completed runs:
- Simulated: no off-diagonal counts were stored.
- Real: 1 ambient file(s) predicted as babble.
- Real: 1 ambient file(s) predicted as fan.
- Real: 1 babble file(s) predicted as fan.
- Real: 1 fan file(s) predicted as ambient.
- Real: 4 fan file(s) predicted as babble.

## Provenance

- AcoustiBench: 0.1.0
- Python: 3.14.3
- Git revision: 725d3d8bd4d42170b011f70d58ab18be902035c5
- Sample rate: 16000
- Dataset id: pyroom-sabine-dev
- Dataset simulator: pyroomacoustics
- Dataset simulator_version: 0.10.1
- Dataset image_order: 40
- Dataset sample_rate_hz: 16000
- Dataset air_absorption: False
- Dataset t60_reference: sabine
- Dataset distance_reference: euclidean source to microphone

## Still left for the team

- Turn this report in and give the presentation.
- If the sponsor later sends models or simulator files, register them through the same manifest and rerun `acousticbench demo`.

Full tables are in `reports/schroeder-t60-pyroom-vs-ace.md`, `reports/t60-room-rule-pyroom-vs-ace.md`, `reports/direct-path-distance-pyroom.md`, and `reports/noise-type-synth-vs-ace.md`.
