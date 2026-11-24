# AcoustiBench, explained

This note is for reading the project in plain language. It says what each term means, what the program is doing, and where that work lives on the computer and on GitHub.

The public code is at https://github.com/Jmurch101/acousticbench. The audio files are only on this computer. They are not on GitHub.

## What the project is

AcoustiBench is a testing tool for acoustic models. An acoustic model is a program that listens to a sound file and returns a number or a label. Examples in this project: how long a room rings, what kind of room it is, and how far the sound traveled.

The point of the project is sim-to-real testing. The same model is run twice:

1. On audio that a computer program created.
2. On audio that was recorded in real rooms.

Then the scores are compared. If the model does well on the fake rooms and worse on the real rooms, that difference is the sim-to-real gap.

The tool that runs the model, saves the scores, and writes the report is called the harness. The harness is the software in this repository. The models and the audio are plugged into it.

Team: Jonathankeith Murchison, Javon Whitfield, and Jonathan Price. Advisor: Dr. Sambit Bhattacharya. Course: senior design, Fall 2026.

## Where things live

| What | Where |
| --- | --- |
| This explanation | `AcoustiBench_Explained.md` in the Senior Project folder |
| The program | `src/acousticbench/` |
| The measured write-up | `reports/draft-final-report.md` |
| Saved run scores | `data/acousticbench.db` on this computer only |
| Per-file predictions | `data/runs/` on this computer only |
| Simulated rooms | `data/simulated/pyroom-sabine-dev/` on this computer only |
| Real ACE recordings | `data/ace/` on this computer only |
| Public copy of the code and reports | https://github.com/Jmurch101/acousticbench |

One command reruns the three tests and rewrites the reports:

```powershell
acousticbench demo
```

The local web page is `acousticbench serve`, then http://127.0.0.1:8000. That page is on your computer. It is not a public website.

## The path of one test

1. A dataset is a folder of sound files plus a spreadsheet called `manifest.csv`. Each row names one file and the correct answer for that file.
2. A model reads one file and gives an answer.
3. The harness compares the model's answer with the correct answer.
4. It saves the comparison in the database and writes a report in `reports/`.

The correct answer is called the label or the reference. The model's answer is the prediction. The mistake is prediction minus reference.

## Sound words

### Audio file

The project uses WAV files. A WAV file is uncompressed audio: a long list of loudness numbers. The program converts every file to one channel (mono) and to 16,000 samples per second unless a run says otherwise. Sample rate means how many loudness numbers are stored for each second of sound.

Code: `src/acousticbench/audio.py`.

### Decibel (dB)

A decibel is a way to write loudness as a ratio. A drop of 60 dB means the sound energy has fallen to one millionth of what it was. People hear that as the sound dying away. T60 is defined with this 60 dB drop.

### Room impulse response

Clap once in a room. The clap is short. What the microphone records afterward is the room's response: the clap, then the reflections off the walls, then the fade. That recording is a room impulse response, often shortened to RIR.

Every test in the current results uses an impulse response, not a song or a sentence. The file is the room's fingerprint.

### Reverberation

Reverberation is the lingering sound after the source stops. A bathroom lingers. A closet lined with coats does not. A large hard room lingers longer than a small soft room.

### T60, also called reverberation time

T60 is the time, in seconds, for the sound to drop by 60 dB after the source stops.

A small furnished office might be around 0.3 to 0.5 seconds. A large hard lecture room can be around 1 second or more. Those are examples of the sizes used in this project, not a rule for every building.

T60 is the first task this harness finishes. The proposal also asks for room type, distance, and sound-event detection. Those are separate tasks, described below.

### Sabine T60

Sabine's formula estimates T60 from the room's shape and how absorbent the walls are. It does not listen to a recording.

In words: a bigger room rings longer, and softer walls ring for a shorter time.

In the code, with length, width, and height in meters:

`T60 = 0.161 × volume / (absorption × wall area)`

Absorption is a number between 0 and 1. A value near 0 is a hard wall. A value near 1 soaks up the sound.

This formula is the correct answer on the simulated files. The file `data/simulated/pyroom-sabine-dev/manifest.csv` has a `t60` column. That number came from Sabine's formula. It did not come from listening to the file.

Code: `src/acousticbench/sim/sabine.py`.

### Shoebox and image source

A shoebox room is a simple rectangle: four walls, a floor, and a ceiling. Pyroomacoustics builds that box and places one sound source and one microphone inside it.

The image-source method pretends each wall is a mirror. The sound bounces by coming from an imaginary copy of the source behind the wall. Image order is how many bounces are kept. This project uses order 40. Air absorption is turned off, so the air itself does not soak up sound in the simulation.

Because the bounce count is finite, the simulated recording can fade sooner than Sabine's formula says. That difference shows up in the lecture rooms. It is a real result of the method. The report keeps it.

### Pyroomacoustics

Pyroomacoustics is the Python program that builds the shoeboxes and writes the impulse responses. It was made at EPFL. The paper is Scheibler, Bezzam, and Dokmanić, ICASSP 2018. The license is MIT, so the team can run it.

It is installed on this computer as version 0.10.1. The generated files are created by:

```powershell
acousticbench simulate-dev
```

That command writes 36 files: 9 rooms and 4 microphone positions in each. The families are office, meeting, and lecture. The design T60 values run from about 0.30 seconds for the driest office to about 1.20 seconds for the livest lecture room.

The files are under `data/simulated/pyroom-sabine-dev/rir/`. The generator is `src/acousticbench/sim/pyroom_dev.py`.

Pyroomacoustics is the simulator the team can run. SoundSpaces 2.0, Steam Audio, and Unreal Engine 5 are named in the proposal as the sponsor's simulators. Those files are not in this project. Dr. Bhattacharya still has to provide them or approve this list.

## The ACE Challenge recordings

ACE is a published set of real room recordings. Researchers at Imperial College London recorded impulse responses, noise, and speech in rooms on that campus. The paper is Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM Transactions on Audio, Speech, and Language Processing, 2016.

The download page is the Zenodo record https://doi.org/10.5281/zenodo.6257551. The project page is https://www.imperial.ac.uk/speech-audio-processing/projects/ace-challenge/.

On this computer the download sits in `data/ace/downloads/`. The impulse responses used for T60 were unpacked to `data/ace/single/`. There are 14 of them: 7 rooms, and 2 setups in each room. The file names look like `Single_502_1_RIR.wav`.

The 7 rooms, using the names in the ACE tables, are:

| ACE name | Kind of room |
| --- | --- |
| Office_1 | Office |
| Office_2 | Office |
| Meeting_Room_1 | Meeting room |
| Meeting_Room_2 | Meeting room |
| Lecture_Room_1 | Lecture room |
| Lecture_Room_2 | Lecture room |
| Building_Lobby | Lobby |

The published T60 for each room and setup is in a table the ACE authors released: `20150814T154139_Corpus_Mean_DRRs_and_T60s.csv`. On this computer that file is under `data/ace/corpus-data/`. The column used is fullband T60. Fullband means the whole audible range, not one narrow frequency band. The microphone setup used is called Crucif, channel 1. Crucif is the ACE name for a cross-shaped microphone array. The single-channel archive is that array's channel 1.

`acousticbench prepare-ace` does not copy the audio into git. It writes `data/ace/prepared/manifest.csv`, which points at the original files and copies in the published T60 and the room family.

The Zenodo page lists the license as CC BY 4.0. The Imperial College page says CC BY-ND 4.0. The project follows the stricter reading: keep the files local, and do not post a changed copy of the audio. Any write-up that uses the files should cite Eaton and the coauthors, 2016.

## The Schroeder T60 estimator

Manfred Schroeder published this method in the Journal of the Acoustical Society of America in 1965. It estimates T60 by listening to an impulse response.

The steps in this project's code (`src/acousticbench/models/schroeder_t60.py`):

1. Start at the loudest sample. That is treated as the arrival of the direct sound.
2. Add up the sound energy from the end of the file backward. Walking backward makes a smooth curve of how much energy is left. This is the backward integration.
3. Turn that curve into decibels.
4. Fit a straight line to the part of the curve between −5 dB and −35 dB. If that stretch is too short, the code uses −5 dB to −25 dB.
5. Extend the line until it has fallen 60 dB. The time that takes is the T60 estimate.

The model id inside the program is `schroeder-t60`. It is a classical method: a fixed calculation, with no training and no downloaded neural-network weights. The proposal's final demo still needs two models from the sponsor. Those weights are not in the repository.

On the simulated files, Schroeder's answer is compared with Sabine's formula. On the ACE files, Schroeder's answer is compared with the published fullband T60.

The latest run is in `reports/schroeder-t60-pyroom-vs-ace.md`. Average absolute error: 0.1185 seconds on the 36 simulated files, and 0.0623 seconds on the 14 ACE files. The simulated lecture rooms are the weak spot, at 0.2368 seconds average error, because the limited number of bounces fades before Sabine's formula does.

## Scores

Mean absolute error (MAE) is the average size of the mistakes, ignoring whether the model was high or low. Root mean squared error (RMSE) is another average that gives extra weight to the big mistakes. Both are in seconds for T60, and in meters for distance. Lower is better.

The gap is the ACE score minus the simulated score. For error, a positive gap means the real recordings were harder. In the current T60 run the gap is negative, because the simulated lecture rooms produced the larger error.

A condition is a group name stored next to each file, such as office or Lecture_Room_2. The report breaks the error out by those groups. The simulated rooms and the ACE rooms do not share names, so the groups are not matched one to one.

## Room family

Room-size classification, in the proposal, means guessing the kind of room from the audio. This project uses four family names taken from the file's room: office, meeting, lecture, and lobby.

The current guesser is `t60-room-rule`, in `src/acousticbench/models/room_rule.py`. It runs the Schroeder estimate, then applies fixed cuts:

- Under 0.50 seconds: office
- Under 0.80 seconds: meeting
- 0.80 seconds or more: lecture

Those cuts were placed in the gaps between the simulated design targets. They were not adjusted to make the ACE score look better. There is no lobby choice, so a lobby file is labeled as one of the other three.

On the simulated files this rule is right on 86.11% of the files. On ACE it is right on 42.86%. All 4 ACE meeting-room files were called office, and both lobby files were called lecture. The full table is `reports/t60-room-rule-pyroom-vs-ace.md`.

Dr. Bhattacharya still needs to say whether these four names are the classes he wants.

## Distance

Source-to-microphone distance is how far the sound traveled in a straight line from where it was made to the microphone, in meters.

On a simulated file that distance is known, because the program placed both points. It is the `distance` column in the simulated manifest.

The estimator is `direct-path-distance`, in `src/acousticbench/models/direct_path_distance.py`. The direct path is the first sound to arrive, before the wall reflections. The code finds the first sample that reaches 5% of the loudest peak. Time from the start of the file to that sample, multiplied by 343 meters per second, is the distance estimate. 343 meters per second is the usual speed of sound in air near room temperature.

On the 36 simulated files the average absolute error is 0.6959 meters. Every estimate is long, by roughly half a meter to nine tenths of a meter. The report is `reports/direct-path-distance-pyroom.md`.

The ACE table does publish a related number called DRR, the direct-to-reverberant ratio. That is a loudness comparison between the first arrival and the later reflections. It is not a distance in meters. This project does not treat DRR as a distance. A real-room distance test needs a dataset that prints the distance in meters. That dataset is one of the items to ask the advisor for.

## Sound-event detection

Sound-event detection means marking what happened in a recording and when, such as a door closing or a phone ringing. ACE includes noise files, and it does not include those start and end times. The project therefore scores the whole clip. The classical rule is `noise-type-rule`. A separate public neural tagger, `panns-noise-type`, is described below. Neither one is timed sound-event detection.

## Other words that show up in the reports

| Word | Meaning in this project |
| --- | --- |
| Baseline | A simple, known method used so the harness can be tested before the sponsor models arrive. |
| Sponsor model | A model the advisor or the project sponsor provides. Two of these are required for the final demo. They are not in the repository. |
| Neural model | A model trained on many examples. The classical rules are calculations. PANNs Cnn14 is a neural model trained by other researchers. The team did not train it. |
| Manifest | The spreadsheet that lists each audio file and the correct answer. |
| Domain | Either `simulated` or `real`. It records which side of the comparison a dataset belongs to. |
| Provenance | The record of how a run was produced: program version, Python version, git revision, sample rate, simulator version, and which label table was used. |
| Git revision | The id of the code version that produced the run. |
| Split | A tag such as train, test, or dev. The current runs use every file. |
| Latency | How many milliseconds the model took to answer one file. |
| Calibration | A check of whether a model's confidence matches how often it is right. The current room rule does not give a confidence score, so that number is blank. |
| Example datasets | Tiny synthetic tones, noise, and chirps under `data/examples/`. They only show that the program runs. They are not the study. |

## Team decisions

The sponsor did not send SoundSpaces, Steam Audio, Unreal, or model checkpoints. The team closed the open questions as follows. These are not a signature from Dr. Bhattacharya.

- The datasets are the Pyroomacoustics shoeboxes, the ACE impulse responses, the ACE ambient, babble, and fan clips, and a 36-file subset of the OpenSLR 26 simulated impulse responses.
- The room classes are office, meeting, lecture, and lobby.
- The two demonstration models are Schroeder T60 and the room-family rule. Distance and sound type use their own classical rules. No neural model was trained. PANNs Cnn14 is an extra public checkpoint, not one of those two demonstration models.
- Distance is reported only for the simulated rooms, because ACE does not publish meters.
- Sound type is the whole clip. ACE does not say when an event starts or ends. The rule is `noise-type-rule`. The cuts were read from these ACE files, so the score describes this corpus. The synthesized clips in `data/simulated/synth-noise-types/` only check that the rule fires.

The measured write-up is `reports/final-report.md`.

## Public simulator files and a public checkpoint

The sponsor did not send SoundSpaces, Steam Audio, Unreal, or model weights. The team downloaded two public sources instead.

**OpenSLR 26** is a set of simulated room impulse responses made with the image method. The paper is Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017. The license is Apache 2.0. The download is `sim_rir_16k.zip` from https://www.openslr.org/26/. It lives in `data/simulated/downloads/` and is not on GitHub. `acousticbench prepare-openslr` keeps 36 files: the first impulse response from rooms 1 through 12 in the small, medium, and large groups. The size label is that group. The archive prints room length, width, height, and an absorption coefficient. It does not print T60. The `t60` column is Sabine's formula on those printed numbers. The code is `src/acousticbench/sim/openslr.py`.

Schroeder T60 on those 36 files, run `4e6cf2acdaaf`, has MAE 1.4748 seconds and RMSE 2.0208 seconds. By size group the MAE is 0.0537 seconds for small, 1.4126 for medium, and 2.9581 for large. The wav files are 0.5, 1.0, or 2.0 seconds long. On the medium and large rooms the Schroeder estimate runs long, and on the large rooms it is often longer than the file.

**PANNs Cnn14_16k** is a neural network trained by Kong and coauthors to tag YouTube clips with 527 AudioSet labels. The paper is Kong, Cao, Iqbal, Wang, Wang, and Plumbley, IEEE/ACM TASLP 2020. The weights are CC BY 4.0, Zenodo record 3987831, file `Cnn14_16k_mAP=0.438.pth`, 358,668,570 bytes. The md5 is `362fc5ff18f1d6ad2f6d464b45893f2c`. The file stays in `data/models/` and is gitignored. The loader is `src/acousticbench/models/panns_cnn14.py`. The team did not train it and did not change the weights.

The noise model, `panns-noise-type`, takes the highest score in three fixed groups of AudioSet names. Speech, conversation, babbling, chatter, crowd, and hubbub map to babble. Mechanical fan and air conditioning map to fan. Silence, inside a small room, inside a large room, white noise, and pink noise map to ambient. That list was chosen from the names. It was not adjusted after seeing the ACE scores.

On the 42 ACE noise clips, run `e1ad23bc0f63`, accuracy is 0.5952 and macro F1 is 0.5094. All 14 babble clips are called babble. Ambient is 10 of 14. Fan is 1 of 14: most fan clips are called ambient. Each file is capped at 30 seconds.

The room-size model, `panns-room-size`, calls a file small when the inside-small-room tag is more than twice the inside-large-room tag, large when the large tag leads by that same ratio, and medium otherwise. AudioSet has no medium-room tag, and the network was trained on ordinary recordings, not impulse responses. On the 36 OpenSLR files, run `2d990a2bfc51`, it labels every file small. Accuracy is 0.3333.

The synthesized noise clips are only a check that the harness can run the same model on both sides. Their scores are not a study result. The comparison is `reports/panns-noise-synth-vs-ace.md`.

## What is done, and what is not

Done on this computer. The classical runs are in `reports/final-report.md`. The OpenSLR and PANNs runs are in `reports/openslr-schroeder-t60.md`, `reports/openslr-panns-room-size.md`, `reports/panns-noise-ace.md`, and `reports/panns-noise-synth-vs-ace.md`.

- The harness, the web page, and the command-line tool.
- Simulated shoeboxes with Sabine T60 labels and straight-line distance labels.
- ACE impulse responses with the published T60 labels and a room-family label.
- ACE ambient, babble, and fan clips, labeled from the filenames.
- Schroeder T60, the room-family rule, direct-path distance, and the noise-type rule, with saved scores.
- A 36-file OpenSLR 26 subset, with Sabine T60 from the published room geometry, and a Schroeder run on that subset.
- PANNs Cnn14_16k loaded from the public checkpoint, scored on the ACE noise clips and on the OpenSLR size labels. The weights are not in git.

The submission report is `AcoustiBench_Final_Report.md`. The slides are `AcoustiBench_Presentation.pptx`. Both include the OpenSLR and PANNs scores. Left for the team: turn the report in and give the presentation.
