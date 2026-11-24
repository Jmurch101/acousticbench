# AcoustiBench

## A Sim-to-Real Evaluation Harness for Acoustic Inference Models

**Team:** Jonathankeith Murchison, Javon Whitfield, Jonathan Price  
**Advisor:** Dr. Sambit Bhattacharya  
**Course:** Senior design, Fall 2026  
**Date:** November 24, 2026  
**Code:** https://github.com/Jmurch101/acousticbench

The course final-report form was not in the project notes. This report follows the midterm sections: abstract, background, project description, software and hardware, technical method, completed work, contributions, and references.

---

## Abstract

AcoustiBench runs one acoustic model on computer-generated audio and on real recordings, then compares the scores. The team built the harness in Python and measured four tasks: reverberation time, room type, source-to-microphone distance, and sound type. Simulated rooms come from Pyroomacoustics and from a public OpenSLR image-source set. Real rooms come from the ACE Challenge, recorded at Imperial College London. Sponsor files were not provided. The team used classical methods and one public neural checkpoint, PANNs Cnn14, and recorded that choice. Schroeder error averaged 0.12 seconds on 36 Pyroom rooms and 0.06 seconds on 14 ACE impulse responses. A fixed room-type rule was correct on 86 percent of the Pyroom rooms and 43 percent of the ACE rooms. Distance error on the Pyroom rooms averaged 0.70 meters. A clip-level noise rule was correct on 81 percent of 42 ACE noise recordings. PANNs was correct on 60 percent of those same recordings. Every number comes from a saved run.

---

## 1. Problem

Acoustic models are often built on simulated rooms and then used in real rooms. The score can change between those two settings. The project goal is a repeatable way to measure that change.

The harness keeps the model, the dataset, the settings, and the score for every run. A comparison report subtracts the simulated score from the real score. Files are not paired across the two datasets. The comparison is an overall gap, not a claim that one simulated room is the same physical room as one ACE room.

## 2. Background

### Reverberation time

Reverberation is the sound that continues after the source stops. T60 is how many seconds that sound takes to fall by 60 decibels. A short T60 is a dry room. A longer T60 is a live room.

On the simulated files, the correct T60 is Sabine's formula. It uses the room's volume, wall area, and a single absorption number. It does not listen to the recording. The code is `src/acousticbench/sim/sabine.py`.

On the ACE files, the correct T60 is the fullband value published by the ACE authors for cruciform microphone channel 1.

### The Schroeder estimator

Manfred Schroeder's 1965 method estimates T60 from an impulse response. An impulse response is the recording of a short sound, such as a clap, and the reflections that follow. The method adds the remaining energy from the end of the file backward, fits a straight line to the fade from −5 dB to −35 dB, and reads how long a 60 dB drop would take. The implementation is `src/acousticbench/models/schroeder_t60.py`.

### Pyroomacoustics

Pyroomacoustics builds a rectangular room, places one source and one microphone, and writes an impulse response. The team used version 0.10.1, image order 40, and air absorption off. The paper is Scheibler, Bezzam, and Dokmanić, ICASSP 2018. The license is MIT.

### ACE Challenge

The ACE Challenge is a published set of real room recordings from Imperial College London. The paper is Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM TASLP, 2016. The download is Zenodo record 10.5281/zenodo.6257551. The team used the single-channel archive. Zenodo lists CC BY 4.0. The Imperial College page states CC BY-ND 4.0. The team followed the stricter reading: the audio stays on the local machine and is not in the GitHub repository.

The seven rooms are Office 1, Office 2, Meeting Room 1, Meeting Room 2, Lecture Room 1, Lecture Room 2, and the building lobby. Each room has two setups.

### OpenSLR simulated impulse responses

OpenSLR 26 is a public set of simulated room impulse responses. The paper is Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017. The license is Apache 2.0. Rooms are grouped by floor size: small (1–10 m), medium (10–30 m), and large (30–50 m). The archive prints length, width, height, and one absorption coefficient per room. It does not print T60. The team computed Sabine T60 from those printed numbers. `acousticbench prepare-openslr` keeps 36 files: the first impulse response from rooms 1–12 in each size group. The zip stays on the local machine.

### PANNs Cnn14

PANNs Cnn14 is a neural network trained by other researchers to tag audio with 527 AudioSet labels. The paper is Kong, Cao, Iqbal, Wang, Wang, and Plumbley, IEEE/ACM TASLP 2020. The checkpoint used here is the 16 kHz file `Cnn14_16k_mAP=0.438.pth` from Zenodo record 3987831. It is 358,668,570 bytes. Its md5 is `362fc5ff18f1d6ad2f6d464b45893f2c`. The weights are CC BY 4.0. The team did not train the network and did not change the weights. The file stays in `data/models/` and is not in the GitHub repository.

## 3. What was built

The program lives in `src/acousticbench/`. It can:

- Register a dataset as simulated or real.
- Run a model through `load`, `predict`, and `get_info`.
- Save each run in a local SQLite database, `data/acousticbench.db`.
- Write Markdown reports, including a breakdown by room or noise class.
- Open a local web page with `acousticbench serve`.

`acousticbench demo` reruns the four tasks and rewrites `reports/final-report.md` from those runs. This document is the submission report. It is not overwritten by that command.

## 4. Decisions made by the team

The sponsor did not provide SoundSpaces, Steam Audio, Unreal files, or neural model checkpoints. Dr. Bhattacharya had not answered the open dataset and model questions. The team closed them in order to finish. These choices are not an advisor signature. They are recorded in `DECISIONS.md`.

| Question | Team decision |
| --- | --- |
| Which datasets? | Pyroomacoustics shoeboxes, ACE impulse responses, ACE ambient, babble, and fan clips, and a 36-file OpenSLR 26 subset. |
| Which room classes? | Office, meeting, lecture, and lobby, taken from the ACE room names. OpenSLR uses its own size labels: small, medium, and large. |
| Which models? | Schroeder T60 and the room-family rule are the two demonstration models. Distance and sound type use their own classical rules. PANNs Cnn14 is an added public checkpoint. No neural model was trained by the team. |
| Where does distance come from? | The simulated rooms only. ACE does not publish distance in meters. |
| What is sound-event detection here? | A label for the whole clip. ACE does not publish start and end times. |

## 5. Software and hardware

Software used to produce the results: Python 3.14.3, NumPy, Pyroomacoustics 0.10.1, FastAPI, SQLite, Git, PyTorch 2.15.0+cpu, and panns-inference 0.1.1. The public repository is https://github.com/Jmurch101/acousticbench.

Hardware: the development PC that holds this project folder. No separate recording device was used. The real audio was downloaded. The simulated audio was computed or downloaded on that PC. PANNs ran on the CPU.

Docker, React, and GitHub Actions were named in the midterm software list. The team did not treat them as required to finish.

## 6. Methods

### T60

The model id is `schroeder-t60`. The simulated label is Sabine T60. The ACE label is published fullband T60. Error is the estimate minus the label. The reported scores are mean absolute error and root mean squared error.

The simulated set has 36 files: 9 rooms and 4 microphone positions. The design T60 values run from about 0.30 seconds to about 1.20 seconds. The ACE set has 14 impulse responses.

### Room type

The model id is `t60-room-rule`. It estimates T60 with Schroeder's method, then applies fixed cuts: below 0.50 seconds is office, below 0.80 seconds is meeting, and every longer decay is lecture. Those cuts sit between the simulated design bands. They were not moved to raise the ACE score. The rule has no lobby class, so a lobby recording is labeled as one of the other three.

### Distance

The model id is `direct-path-distance`. The label is the straight-line distance from the source to the microphone in the shoebox. The estimate is the time of the first sample that reaches 5 percent of the peak, multiplied by 343 meters per second.

### Sound type

The model id is `noise-type-rule`. Classes are ambient, babble, and fan. If at least 5.5 percent of successive samples change sign, the clip is babble. Otherwise, if at least 93 percent of the energy is below 300 Hz, the clip is ambient. Every remaining clip is fan.

Those cuts were chosen by looking at the same 42 ACE files that were scored. The ACE accuracy describes this corpus. It is not a separate hidden test. The 24 synthesized clips only check that the rule recognizes the signals it was written for. Their perfect score is not a study result.

### Public checkpoint

`panns-noise-type` reads the 527 AudioSet scores from Cnn14 and keeps the highest score in three fixed groups. Speech, conversation, babbling, chatter, crowd, and hubbub map to babble. Mechanical fan and air conditioning map to fan. Silence, inside a small room, inside a large room, white noise, and pink noise map to ambient. That list was taken from the AudioSet names. It was not adjusted after the ACE scores were seen.

`panns-room-size` uses two AudioSet tags: inside a small room, and inside a large room or hall. If one score is more than twice the other, the file gets that size. Otherwise the label is medium. AudioSet has no medium-room tag. The network was trained on ordinary recordings, not impulse responses.

## 7. Results

All figures below are copied from runs saved by `acousticbench demo`. Run ids are in `reports/final-report.md`.

### T60

| | Simulated, 36 files | ACE, 14 files | Gap (real − simulated) |
| --- | ---: | ---: | ---: |
| Mean absolute error | 0.1185 s | 0.0623 s | −0.0562 s |
| Root mean squared error | 0.1571 s | 0.0875 s | −0.0696 s |

By simulated room family, mean absolute error was 0.0217 seconds for office, 0.0971 seconds for meeting, and 0.2368 seconds for lecture. The lecture error is larger because image order 40 ends the reflections before Sabine's formula does. The ACE rooms are a different set of rooms. The negative gap means the simulated error was larger than the ACE error.

### Room type

| | Simulated, 36 files | ACE, 14 files | Gap |
| --- | ---: | ---: | ---: |
| Accuracy | 0.8611 | 0.4286 | −0.4325 |
| Macro F1 | 0.8585 | 0.2917 | −0.5669 |

On the simulated set, 4 meeting files were called lecture and 1 office file was called meeting. On ACE, all 4 meeting-room files were called office, both lobby files were called lecture, and 2 lecture files were called meeting. The ACE meeting rooms are drier than the bands the rule learned from the simulated design.

### Distance

On 36 simulated files, mean absolute error was 0.6959 meters, root mean squared error was 0.7009 meters, and median absolute error was 0.7021 meters. Every estimate was long, by about 0.5 meters to 0.9 meters. There is no ACE distance in meters, so there is no real-side distance score.

### Sound type

| | Synthesized, 24 files | ACE, 42 files | Gap |
| --- | ---: | ---: | ---: |
| Accuracy | 1.0000 | 0.8095 | −0.1905 |
| Macro F1 | 1.0000 | 0.8071 | −0.1929 |

The synthesized score is a check, not a research result. On ACE, 34 of 42 clips matched the filename. The misses were 2 ambient clips, 1 babble clip, and 5 fan clips. Four of the fan misses were called babble.

### OpenSLR T60

Schroeder T60 on the 36 OpenSLR files, run `4e6cf2acdaaf`, has mean absolute error 1.4748 seconds and root mean squared error 2.0208 seconds. By size group the mean absolute error is 0.0537 seconds for small, 1.4126 seconds for medium, and 2.9581 seconds for large. The wav files are 0.5, 1.0, or 2.0 seconds long. On the medium and large rooms the estimate runs long, and on the large rooms it is often longer than the file. The label is Sabine T60 from the published dimensions and absorption.

### PANNs

On the 42 ACE noise clips, run `e1ad23bc0f63`, accuracy is 0.5952 and macro F1 is 0.5094. Each file was capped at 30 seconds. All 14 babble clips were called babble. Ambient was 10 of 14. Fan was 1 of 14. Most fan clips were called ambient.

On the 36 OpenSLR files, run `2d990a2bfc51`, the room-size map labeled every file small. Accuracy is 0.3333. The same checkpoint on the 24 synthesized noise clips scored 0.3333. That synthesized score is a harness check, not a study result. The comparison is `reports/panns-noise-synth-vs-ace.md`.

## 8. How to reproduce

From the project folder, with Python 3.10 or newer:

```powershell
python -m pip install -e ".[dev]"
python -m pip install "pyroomacoustics>=0.10"
acousticbench simulate-dev
acousticbench prepare-ace
acousticbench demo
```

`prepare-ace` expects the ACE single-channel archive in `data/ace/downloads/`. The audio is gitignored. Cite Eaton, Gaubitch, Moore, and Naylor, 2016, when the ACE files are used.

The public files are separate downloads. Put `sim_rir_16k.zip` from https://www.openslr.org/26/ in `data/simulated/downloads/`, and put `Cnn14_16k_mAP=0.438.pth` from https://zenodo.org/records/3987831 in `data/models/`. Then:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install panns-inference
acousticbench prepare-openslr
acousticbench eval --model schroeder-t60 --dataset openslr-sim-rir --sample-rate 16000 --max-seconds 30
acousticbench eval --model panns-noise-type --dataset ace-noise-types --sample-rate 16000 --max-seconds 30
acousticbench eval --model panns-room-size --dataset openslr-sim-rir --sample-rate 16000 --max-seconds 30
```

Do not commit the zip, the wav files, or the checkpoint.

The local page is `acousticbench serve`, then http://127.0.0.1:8000.

## 9. Limits

- The simulated rooms and the ACE rooms are not the same rooms.
- The simulated set uses a finite number of reflections, so long rooms fall short of the Sabine label.
- The room rule cannot say lobby.
- Distance has no measured-room result.
- Sound type is the whole clip. The ACE score was not a held-out test.
- The two demonstration models are classical calculations. They are not sponsor neural models.
- PANNs was trained on YouTube-style clips. Its room-size tags do not separate these impulse responses.
- The noise-tag map and the room-size map were not fit to the files being scored.
- The saved runs record git revision `725d3d8` because that was the last published commit when they were scored. This report is published with the code that produced them.

## 10. Conclusion

AcoustiBench is a working harness. It runs the same model on simulated audio and on ACE recordings, stores the run, and writes the gap. Four tasks have a measured classical baseline. A public simulator set and a public neural checkpoint are scored as well. The largest honest findings are that Schroeder T60 is closer to the ACE labels than to the long Sabine lecture rooms, that a T60-only room rule does not transfer to the ACE meeting rooms and lobby, and that PANNs recognizes ACE babble and does not recognize ACE fan or OpenSLR room size.

## 11. Contributions

The October 9, 2026 midterm report assigned each member one third of the work: Jonathankeith Murchison for the project description and the hardware and software section, Javon Whitfield for background, schedule, and lessons, and Jonathan Price for technical detail and progress. The finished code, measurements, and this report are in the shared project folder and repository.

## References

Eaton, J., Gaubitch, N. D., Moore, A. H., and Naylor, P. A. "Estimation of Room Acoustic Parameters: The ACE Challenge." IEEE/ACM Transactions on Audio, Speech, and Language Processing, 2016. Dataset: https://doi.org/10.5281/zenodo.6257551

Scheibler, R., Bezzam, E., and Dokmanić, I. "Pyroomacoustics: A Python Package for Audio Room Simulation and Array Processing Algorithms." IEEE International Conference on Acoustics, Speech and Signal Processing, 2018.

Schroeder, M. R. "New Method of Measuring Reverberation Time." Journal of the Acoustical Society of America, 1965.

Sabine's reverberation formula, as implemented in `src/acousticbench/sim/sabine.py`: T60 = 0.161 × volume / (absorption × surface area), with dimensions in meters.

Ko, T., Peddinti, V., Povey, D., Seltzer, M. L., and Khudanpur, S. "A Study on Data Augmentation of Reverberant Speech for Robust Speech Recognition." IEEE International Conference on Acoustics, Speech and Signal Processing, 2017. Simulated impulse responses: https://www.openslr.org/26/

Kong, Q., Cao, Y., Iqbal, T., Wang, Y., Wang, W., and Plumbley, M. D. "PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition." IEEE/ACM Transactions on Audio, Speech, and Language Processing, 2020. Checkpoint: https://zenodo.org/records/3987831
