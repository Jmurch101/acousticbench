AcoustiBench Project Reference
Project title: AcoustiBench — Sim-to-Real Evaluation Harness for Acoustic Inference Models
Course context: Senior Design / Senior Project
Team: Audio AI Team 2 — Jonathankeith Murchison, Javon Whitfield, Jonathan Price
Faculty advisor: Dr. Sambit Bhattacharya
Proposal submitted: September 11, 2026
This reference consolidates project details shared so far. It distinguishes confirmed information from proposed implementation ideas. Update the “Open Questions” section as the team and advisor confirm decisions.

1. Project overview
AcoustiBench is intended to help evaluate acoustic inference models across simulated and real-world audio conditions. The central aim is to create a repeatable way to run evaluations and examine how performance changes between simulated inputs and real recordings.

The project is described as a Sim-to-Real Evaluation Harness for Acoustic Inference Models. The system should support the team’s evaluation work and produce results that can be inspected, compared, and reported. The exact acoustic task, datasets, models, metrics, hardware, and final user interface have not yet been specified in the information available for this reference.
2. Problem and motivation
Acoustic inference models can behave differently when moved from simulated data to real-world recordings. Differences in recording conditions, noise, equipment, environments, or data distributions may affect model performance. AcoustiBench is intended to provide a structured way to evaluate that gap.

Problem statement (working draft): The team needs a repeatable evaluation workflow for acoustic inference models that can compare results on simulated and real-world audio data, preserve the configuration used for each run, and make the findings easier to review.

Treat this statement as a draft until the team confirms it against the project proposal and advisor guidance.
3. Goals
Core project goals
1. Build an evaluation harness for acoustic inference models.
2. Support evaluation on simulated and real-world audio data.
3. Make results from different evaluation conditions comparable.
4. Keep a record of the model, dataset, configuration, and outputs used in each run.
5. Present results in a form the team can review and use in project reporting.
Possible MVP goals to confirm
These are useful implementation candidates, not confirmed requirements:
- A consistent data interface for audio files and their labels or reference targets.
- A model interface that lets the runner invoke one or more acoustic inference models in a consistent way.
- A repeatable evaluation run using a saved configuration.
- Suitable task-specific metrics and a comparison view for simulated versus real data.
- Export of run results for analysis and project reports.
- A small example dataset or example model clearly marked as demonstration material.
4. Scope and boundaries
In scope based on the project title
- Acoustic inference model evaluation.
- Simulated and real-world evaluation conditions.
- A harness/workflow to make evaluations repeatable.
- Comparison and communication of evaluation results.
Not yet established
The supplied project information does not establish:
- The exact inference task (for example, classification, detection, localization, or regression).
- The target acoustic events or classes.
- Which simulator or simulation approach will be used.
- Which real-world dataset, sensors, or recording environments will be used.
- Which model architectures or pretrained models will be evaluated.
- The required metrics, thresholds, or statistical analysis.
- Whether the deliverable is a command-line tool, desktop app, web app, or a combination.
- The required deployment environment or hardware.
- Any privacy, consent, or data-retention requirements for recordings.
Do not present any of these as settled requirements until confirmed.
5. Suggested system workflow
A candidate end-to-end workflow for team discussion:
1. Select an evaluation task, dataset, and model.
2. Validate the dataset files and metadata.
3. Apply documented preprocessing consistently.
4. Run inference using a model adapter.
5. Compare predictions with reference labels or targets, when available.
6. Calculate task-appropriate metrics.
7. Save the run configuration and results with enough metadata to reproduce the evaluation.
8. Compare results across simulated and real-world conditions.
9. Export tables or figures for analysis and reporting.
This workflow is a planning aid. Adjust it to the actual datasets and task.
6. Candidate modules
The following modules are a proposed decomposition, not an approved architecture:
Module	Purpose
Dataset / data adapter	Loads audio and associated labels, metadata, and condition information.
Preprocessing	Applies documented audio transformations consistently.
Model adapter	Provides a common way to load and invoke each evaluated model.
Evaluation runner	Coordinates inference, metric computation, and run capture.
Results store	Saves run configuration, model and dataset identifiers, metrics, and output references.
Comparison/reporting	Displays or exports comparisons between runs and conditions.
User interface or CLI	Lets a user configure, start, and inspect evaluations.


Keep the first implementation small. Add modules only when they support a confirmed project need.
7. Data and evaluation principles
- Keep simulated and real-world data identifiable as distinct conditions.
- Record dataset provenance and relevant recording or simulation metadata.
- Do not mix training data and evaluation data accidentally; document the split or evaluation protocol.
- Apply the same preprocessing rules when making comparisons, unless a documented experiment deliberately changes them.
- Use metrics that match the inference task and available labels.
- Report the number of examples and any exclusions alongside metrics.
- Preserve run settings so results can be reproduced.
- Clearly label example, synthetic, or placeholder data; never describe placeholder results as experimental findings.
- Document limitations, missing labels, and differences between simulated and real-world conditions.
8. Team and project administration
Team members: Jonathankeith Murchison, Javon Whitfield, and Jonathan Price
Advisor: Dr. Sambit Bhattacharya
Team name: Audio AI Team 2

The available project notes do not specify individual member assignments. Agree on ownership for software, data, model integration, evaluation design, and documentation, then add those assignments here.
9. Milestones and timeline information
The proposal material shared previously included this draft milestone structure:
Weeks	Milestone	Planned outputs
1–2	Project definition	Sponsor interviews, domain glossary, user stories, acceptance criteria, risk register, and approved team assignments.
3–4	Architecture review	Task and metric definitions, dataset and model contracts, database design, interface mockups, repository standards, and design review.
5–7	Minimum runner	One task, one dataset adapter, one toy model plugin, deterministic configuration, command-line run, and stored results.
8–10	First complete workflow	The proposal excerpt available here did not include the outputs for this milestone. Fill in from the approved proposal.


The later milestone details were not included in the notes available for this document. Consult the approved proposal and update this timeline before relying on it as the current schedule.
10. Software and hardware specifications
No final software or hardware inventory was included in the supplied project details.

The prior report instructions ask for:
Software (to confirm)
List tools actually being used or currently planned, such as the programming language, source control, development environment, libraries, and data storage. Do not list a tool as confirmed until the team verifies it.
Hardware (to confirm)
List relevant development or evaluation hardware actually used by the team. Include audio recording or simulation equipment only if it is part of the project.
11. Report and presentation requirements shared
Project proposal
The proposal guideline shared for the project asks for:
- Team members and advisor(s).
- A project title that reflects the work.
- Background and related work, including literature search.
- Detailed project description: problem to solve and goals.
- Detailed assignments for each team member.
- Main milestones and/or weekly timeline.
- References / works cited.
- Advisor consent (email confirmation is acceptable).
Midterm report
The guideline shared asks for:
- Cover page with project title, team members, advisor(s), and working period.
- Abstract of 100–200 words.
- Background based on literature search and project motivation.
- Detailed project description and problems to solve.
- Software and hardware specifications.
- Technical details such as algorithm steps, module design, and program design.
- Work completed so far and next steps.
- Each team member’s specific contribution.
Final report
A final-report guideline was mentioned, but its full requirements were not included in the available notes. Retrieve the current course instructions before drafting the final report.
12. Reference and evidence practices
For the related-work and report sections:
- Use credible primary sources where possible, including research papers, official dataset documentation, and official software documentation.
- Keep a citation with each factual claim, dataset description, or reported result.
- Distinguish published findings from the team’s own experimental results.
- Record the source and version of datasets, models, and tools.
- Do not claim an accuracy level or sim-to-real improvement until it has been measured and supported by actual runs.
No bibliography or specific papers for AcoustiBench were included in the supplied project details. Add verified sources as the team selects the task, data, and methods.
13. Decisions and remaining questions
The proposal and midterm report name the required tasks, Pyroomacoustics, the ACE Challenge, and sponsor-supplied models. The working choices are recorded in DECISIONS.md.

Selected for implementation:
1. First task: T60 estimation. Room-size classification, distance estimation, and sound-event detection remain required.
2. Simulator the team can run: Pyroomacoustics (MIT). SoundSpaces 2.0, Steam Audio, and UE5 MetaSounds stay with the sponsor.
3. Real recordings: ACE Challenge corpus, CC BY-ND 4.0. Do not commit or modify-and-redistribute the audio.
4. First model: Schroeder T60 baseline. The second model is still a sponsor baseline and is not in the repository.
5. T60 metrics: mean absolute error and root mean squared error, including a by-condition breakdown when the manifest has a condition column.

Still needs the advisor or sponsor:
6. Approval of the three-dataset list.
7. The two sponsor baseline models.
8. Whether the minimum demonstration is the current command-line and local web page.
9. Confirmation of the midterm software list, including Docker, React, and GitHub Actions.
10. Member assignments for the remaining milestones, and the milestone dates after week 10.
11. The complete final-report and presentation requirements.
14. Guidance for an AI coding agent
When using an AI coding agent to implement AcoustiBench:
- Ask it to inspect the repository and project documents before changing files.
- Have it preserve existing work and summarize its plan before implementing.
- Tell it to treat the project title and team facts above as confirmed, and mark unresolved requirements as assumptions.
- Have it implement a small, usable workflow aligned to the confirmed task, data, and metrics.
- Require it to document setup, configuration, data format, and how to reproduce an evaluation.
- Instruct it not to invent datasets, experiment results, advisor decisions, or requirements.
- Ask it to summarize what it built, how to run it, assumptions made, and unresolved decisions.
15. Project status snapshot
Known: project title, broad sim-to-real evaluation purpose, team name, team members, advisor, proposal submission date, proposal and midterm report guidelines, and an early milestone outline.

Working selection, still needing sponsor approval for the dataset list and the second model: T60 estimation, Pyroomacoustics, the ACE corpus, and the Schroeder T60 baseline. See DECISIONS.md.

Needs confirmation: sponsor dataset approval, sponsor baseline models, distance and sound-event implementations, Docker, React, GitHub Actions, member assignments, later milestone dates, and complete final-report requirements.