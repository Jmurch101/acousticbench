"""Rerun the development baselines and write the draft report from those runs."""

from __future__ import annotations

from pathlib import Path

from acousticbench.compare import compare_runs
from acousticbench.eval.runner import execute_run
from acousticbench.eval.store import Store
from acousticbench.report import compare_report_markdown, draft_report_markdown, run_report_markdown
from acousticbench.service import queue_run

SIM_DATASET = "pyroom-sabine-dev"
REAL_DATASET = "ace-single-rir"


def run_recorded_demo(project_root: Path, store: Store) -> dict[str, str]:
    _require(store, SIM_DATASET)
    _require(store, REAL_DATASET)
    t60_sim = _evaluate(
        store,
        project_root,
        model_id="schroeder-t60",
        dataset_id=SIM_DATASET,
        max_seconds=30,
        notes=(
            "Expanded shoebox set. Reference T60 is Sabine from room absorption, not a measurement. "
            "Not a sponsor-model result."
        ),
    )
    t60_real = _evaluate(
        store,
        project_root,
        model_id="schroeder-t60",
        dataset_id=REAL_DATASET,
        max_seconds=30,
        notes=(
            "ACE Challenge single-channel impulse responses. Reference is published fullband T60 "
            "for cruciform channel 1. Cite Eaton et al. 2016. Not a sponsor-model result."
        ),
    )
    room_sim = _evaluate(
        store,
        project_root,
        model_id="t60-room-rule",
        dataset_id=SIM_DATASET,
        max_seconds=30,
        notes=(
            "Room family is the design label of each shoebox. The rule uses fixed T60 bands "
            "and was not fit to these scores."
        ),
    )
    room_real = _evaluate(
        store,
        project_root,
        model_id="t60-room-rule",
        dataset_id=REAL_DATASET,
        max_seconds=30,
        notes=(
            "Room family is derived from the ACE room name. Lobby is a fourth class. "
            "The rule has no lobby band and was not fit to these scores."
        ),
    )
    distance = _evaluate(
        store,
        project_root,
        model_id="direct-path-distance",
        dataset_id=SIM_DATASET,
        max_seconds=30,
        notes=(
            "Reference is the straight-line source-to-microphone distance in the shoebox. "
            "ACE is omitted because the mean table has no distance in meters."
        ),
    )
    t60_comparison = compare_runs(t60_sim, t60_real)
    room_comparison = compare_runs(room_sim, room_real)
    reports = project_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    written = {
        "t60_comparison": reports / "schroeder-t60-pyroom-vs-ace.md",
        "room_comparison": reports / "t60-room-rule-pyroom-vs-ace.md",
        "distance": reports / "direct-path-distance-pyroom.md",
        "draft": reports / "draft-final-report.md",
    }
    written["t60_comparison"].write_text(
        compare_report_markdown(t60_comparison, t60_sim, t60_real),
        encoding="utf-8",
    )
    written["room_comparison"].write_text(
        compare_report_markdown(room_comparison, room_sim, room_real),
        encoding="utf-8",
    )
    written["distance"].write_text(run_report_markdown(distance), encoding="utf-8")
    written["draft"].write_text(
        draft_report_markdown(
            t60_comparison=t60_comparison,
            t60_simulated=t60_sim,
            t60_real=t60_real,
            room_comparison=room_comparison,
            room_simulated=room_sim,
            room_real=room_real,
            distance_run=distance,
        ),
        encoding="utf-8",
    )
    return {name: str(path) for name, path in written.items()}


def _require(store: Store, dataset_id: str) -> None:
    try:
        store.get_dataset(dataset_id)
    except KeyError as exc:
        raise ValueError(
            f"Dataset '{dataset_id}' is not registered. Run simulate-dev and prepare-ace first."
        ) from exc


def _evaluate(
    store: Store,
    project_root: Path,
    *,
    model_id: str,
    dataset_id: str,
    max_seconds: float,
    notes: str,
) -> dict:
    queued = queue_run(
        store,
        project_root,
        model_id=model_id,
        dataset_id=dataset_id,
        raw_config={"sample_rate": 16000, "max_seconds": max_seconds, "notes": notes},
    )
    finished = execute_run(store, queued["id"], project_root)
    if finished.get("status") != "completed":
        raise RuntimeError(finished.get("error") or f"{model_id} on {dataset_id} did not complete.")
    return finished
