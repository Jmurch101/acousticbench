"""Compare one simulated run with one real run.

The gap is aggregate: real metric minus simulated metric. Items are not paired
across datasets unless a future manifest adds a shared item id.
"""

from __future__ import annotations

METRIC_SPECS = (
    ("accuracy", "Accuracy", "higher"),
    ("macro_f1", "Macro F1", "higher"),
    ("macro_precision", "Macro precision", "higher"),
    ("macro_recall", "Macro recall", "higher"),
    ("weighted_f1", "Weighted F1", "higher"),
    ("ece", "Expected calibration error", "lower"),
    ("mean_latency_ms", "Mean latency (ms)", "lower"),
)

REGRESSION_SPECS = (
    ("mae", "Mean absolute error", "lower"),
    ("rmse", "Root mean squared error", "lower"),
    ("median_ae", "Median absolute error", "lower"),
    ("mean_latency_ms", "Mean latency (ms)", "lower"),
)

REGRESSION_TASKS = {"t60", "distance", "regression"}


def compare_runs(simulated: dict, real: dict) -> dict:
    if simulated.get("status") != "completed" or real.get("status") != "completed":
        raise ValueError("Both runs must be completed before they can be compared.")
    sim_summary = simulated.get("summary") or {}
    real_summary = real.get("summary") or {}
    sim_task = sim_summary.get("task") or "classification"
    real_task = real_summary.get("task") or "classification"
    if sim_task != real_task:
        raise ValueError(
            f"Cannot compare task '{sim_task}' with task '{real_task}'. Use two runs of the same task."
        )
    specs = REGRESSION_SPECS if sim_task in REGRESSION_TASKS else METRIC_SPECS

    warnings = _warnings(simulated, real, sim_summary, real_summary)
    metrics = []
    for key, label, better in specs:
        sim_value = sim_summary.get(key)
        real_value = real_summary.get(key)
        gap = None
        if _is_number(sim_value) and _is_number(real_value):
            gap = float(real_value) - float(sim_value)
        metrics.append(
            {
                "key": key,
                "label": label,
                "better": better,
                "simulated": sim_value,
                "real": real_value,
                "gap": gap,
            }
        )

    sim_classes = sim_summary.get("per_class") or {}
    real_classes = real_summary.get("per_class") or {}
    shared = sorted(set(sim_classes) & set(real_classes))
    only_sim = sorted(set(sim_classes) - set(real_classes))
    only_real = sorted(set(real_classes) - set(sim_classes))
    if only_sim or only_real:
        warnings.append(
            "Label sets differ. Per-class gaps are reported only for labels present in both runs."
        )
    per_class = []
    for label in shared:
        sim_f1 = sim_classes[label].get("f1")
        real_f1 = real_classes[label].get("f1")
        gap = None
        if _is_number(sim_f1) and _is_number(real_f1):
            gap = float(real_f1) - float(sim_f1)
        per_class.append(
            {
                "label": label,
                "simulated_f1": sim_f1,
                "real_f1": real_f1,
                "gap": gap,
                "simulated_support": sim_classes[label].get("support"),
                "real_support": real_classes[label].get("support"),
            }
        )

    return {
        "sim_run_id": simulated["id"],
        "real_run_id": real["id"],
        "model_id": simulated.get("model_id"),
        "metrics": metrics,
        "per_class_f1": per_class,
        "warnings": warnings,
        "gap_definition": "gap = real - simulated",
    }


def _warnings(simulated: dict, real: dict, sim_summary: dict, real_summary: dict) -> list[str]:
    warnings: list[str] = []
    if _example_run(simulated):
        warnings.append(
            "The simulated run used example or synthetic audio. Do not present its scores as study results."
        )
    if _example_run(real):
        warnings.append(
            "The real run used example or synthetic audio. Do not present its scores as study results."
        )
    if simulated.get("dataset_domain") != "simulated":
        warnings.append(
            f"The run selected as simulated is registered as domain '{simulated.get('dataset_domain')}'."
        )
    if real.get("dataset_domain") != "real":
        warnings.append(
            f"The run selected as real is registered as domain '{real.get('dataset_domain')}'."
        )
    if simulated.get("model_id") != real.get("model_id"):
        warnings.append("The two runs used different models. The gap mixes model change with domain change.")
    sim_rate = (simulated.get("config") or {}).get("sample_rate")
    real_rate = (real.get("config") or {}).get("sample_rate")
    if sim_rate and real_rate and sim_rate != real_rate:
        warnings.append("The runs used different target sample rates.")
    for name, summary in (("simulated", sim_summary), ("real", real_summary)):
        count = summary.get("n_evaluated") or 0
        if count < 10:
            warnings.append(
                f"The {name} run evaluated {count} items. A gap from a very small set is unstable."
            )
    return warnings


def _example_run(run: dict) -> bool:
    flags = (run.get("config") or {}).get("dataset_flags") or {}
    return bool(flags.get("is_example") or flags.get("synthetic_stand_in") or flags.get("synthetic"))


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
