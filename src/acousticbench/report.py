"""Markdown and HTML reports for a senior-design presentation."""

from __future__ import annotations

import html
from acousticbench import ADVISOR, EXAMPLE_CAVEAT, PROJECT_NAME, TEAM


def run_report_markdown(run: dict) -> str:
    summary = run.get("summary") or {}
    lines = [
        f"# {PROJECT_NAME} evaluation report",
        "",
        f"- Team: {', '.join(TEAM)}",
        f"- Advisor: {ADVISOR}",
        f"- Run: `{run['id']}`",
        f"- Status: {run['status']}",
        f"- Created: {run['created_at']}",
        f"- Model: {run['model_name']} (`{run['model_id']}`)",
        f"- Dataset: {run['dataset_name']} (`{run['dataset_domain']}`)",
        f"- Notes: {run.get('notes') or 'None'}",
        "",
    ]
    lines.extend(_caveat_lines(run))
    if run.get("error"):
        lines.extend(["## Error", "", run["error"], ""])
    if summary:
        lines.extend(_metric_lines(summary))
        lines.extend(_assumption_lines(summary.get("task")))
    return "\n".join(lines).rstrip() + "\n"


def compare_report_markdown(comparison: dict, simulated: dict, real: dict) -> str:
    lines = [
        f"# {PROJECT_NAME} sim-to-real comparison",
        "",
        f"- Team: {', '.join(TEAM)}",
        f"- Advisor: {ADVISOR}",
        f"- Gap definition: {comparison['gap_definition']}",
        f"- Simulated run: `{simulated['id']}` / {simulated['dataset_name']} / {simulated['model_name']}",
        f"- Real run: `{real['id']}` / {real['dataset_name']} / {real['model_name']}",
        "",
        *_gap_intro(simulated),
        "",
    ]
    if comparison.get("warnings"):
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {warning}" for warning in comparison["warnings"])
        lines.append("")
    lines.extend(
        [
            "## Metrics",
            "",
            "| Metric | Simulated | Real | Gap (real - simulated) |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for metric in comparison["metrics"]:
        lines.append(
            f"| {metric['label']} | {_num(metric['simulated'])} | {_num(metric['real'])} | {_num(metric['gap'])} |"
        )
    task = (simulated.get("summary") or {}).get("task") or "classification"
    if task in {"t60", "distance", "regression"}:
        lines.extend(_condition_compare_lines(simulated, real))
        lines.extend(_t60_method_lines(simulated, real))
    else:
        lines.extend(
            [
                "",
                "## Per-class F1",
                "",
                "| Class | Simulated F1 | Real F1 | Gap | Simulated support | Real support |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in comparison["per_class_f1"]:
            lines.append(
                f"| {row['label']} | {_num(row['simulated_f1'])} | {_num(row['real_f1'])} | {_num(row['gap'])} | "
                f"{row['simulated_support']} | {row['real_support']} |"
            )
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend(_assumption_lines(task))
    return "\n".join(lines).rstrip() + "\n"


def run_report_html(run: dict) -> str:
    body = _markdownish_to_html(run_report_markdown(run))
    return _page(f"{PROJECT_NAME} run {run['id']}", body)


def compare_report_html(comparison: dict, simulated: dict, real: dict) -> str:
    body = _markdownish_to_html(compare_report_markdown(comparison, simulated, real))
    return _page(f"{PROJECT_NAME} comparison", body)


def _metric_lines(summary: dict) -> list[str]:
    lines = [
        "## Metrics",
        "",
        f"- Task: {summary.get('task') or 'classification'}",
        f"- Items evaluated: {summary.get('n_evaluated')} of {summary.get('n_items')}",
        f"- Load or inference errors: {summary.get('n_errors')}",
        f"- Mean latency: {_num(summary.get('mean_latency_ms'))} ms",
    ]
    if summary.get("mae") is not None:
        lines.extend(
            [
                f"- Unit: {summary.get('unit') or 'n/a'}",
                f"- Mean absolute error: {_num(summary.get('mae'))}",
                f"- Root mean squared error: {_num(summary.get('rmse'))}",
                f"- Median absolute error: {_num(summary.get('median_ae'))}",
            ]
        )
        conditions = summary.get("by_condition") or {}
        if conditions:
            lines.extend(
                [
                    "",
                    "## By condition",
                    "",
                    "| Condition | MAE | RMSE | Support |",
                    "| --- | ---: | ---: | ---: |",
                ]
            )
            for name, stats in conditions.items():
                lines.append(
                    f"| {name} | {_num(stats.get('mae'))} | {_num(stats.get('rmse'))} | {stats.get('n')} |"
                )
    if summary.get("accuracy") is not None:
        lines.extend(
            [
                f"- Accuracy: {_num(summary.get('accuracy'))}",
                f"- Macro F1: {_num(summary.get('macro_f1'))}",
                f"- Weighted F1: {_num(summary.get('weighted_f1'))}",
                f"- Macro precision: {_num(summary.get('macro_precision'))}",
                f"- Macro recall: {_num(summary.get('macro_recall'))}",
                f"- Expected calibration error: {_num(summary.get('ece'))}",
                "",
                "## Per class",
                "",
                "| Class | Precision | Recall | F1 | Support |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for label, stats in (summary.get("per_class") or {}).items():
            lines.append(
                f"| {label} | {_num(stats.get('precision'))} | {_num(stats.get('recall'))} | "
                f"{_num(stats.get('f1'))} | {stats.get('support')} |"
            )
        lines.extend(["", "## Confusion matrix", "", _confusion_markdown(summary)])
    provenance = summary.get("provenance") or {}
    if provenance:
        lines.extend(
            [
                "",
                "## Provenance",
                "",
                f"- AcoustiBench: {provenance.get('acousticbench_version')}",
                f"- Python: {provenance.get('python')}",
                f"- Git revision: {provenance.get('git_revision') or 'unavailable'}",
            ]
        )
    lines.append("")
    return lines


def _caveat_lines(run: dict) -> list[str]:
    flags = (run.get("config") or {}).get("dataset_flags") or {}
    if flags.get("is_example") or flags.get("synthetic") or flags.get("synthetic_stand_in"):
        return ["## Example-data caveat", "", EXAMPLE_CAVEAT, ""]
    return []


def _gap_intro(simulated: dict) -> list[str]:
    task = (simulated.get("summary") or {}).get("task") or "classification"
    if task in {"t60", "distance", "regression"}:
        return [
            "For error and latency, a positive gap means the real run cost more.",
        ]
    return [
        "For accuracy and F1, a negative gap means the real run scored lower.",
        "For calibration error and latency, a positive gap means the real run cost more.",
    ]


def _condition_compare_lines(simulated: dict, real: dict) -> list[str]:
    lines = [
        "",
        "## By condition",
        "",
        "Conditions are not paired across the two datasets. Each table is that run's own breakdown.",
        "",
    ]
    lines.extend(_one_condition_table("Simulated", (simulated.get("summary") or {}).get("by_condition") or {}))
    lines.extend(_one_condition_table("Real", (real.get("summary") or {}).get("by_condition") or {}))
    return lines


def _one_condition_table(title: str, conditions: dict) -> list[str]:
    lines = [f"### {title}", ""]
    if not conditions:
        return lines + ["No condition column was recorded.", ""]
    lines.extend(
        [
            "| Condition | MAE | RMSE | Support |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for name, stats in conditions.items():
        lines.append(
            f"| {name} | {_num(stats.get('mae'))} | {_num(stats.get('rmse'))} | {stats.get('n')} |"
        )
    lines.append("")
    return lines


def _t60_method_lines(simulated: dict, real: dict) -> list[str]:
    if simulated.get("model_id") != "schroeder-t60":
        return []
    return [
        "## Method",
        "",
        "- Model: Schroeder backward integration (`schroeder-t60`). This is a classical baseline, not a sponsor neural model.",
        "- Simulated reference: Sabine T60 from room volume, surface area, and absorption.",
        "- Real reference: ACE Challenge fullband T60 for cruciform channel 1.",
        f"- Simulated notes: {simulated.get('notes') or 'None'}",
        f"- Real notes: {real.get('notes') or 'None'}",
        "",
    ]


def _assumption_lines(task: str | None = None) -> list[str]:
    if task in {"t60", "distance", "regression"}:
        task_line = "- The task is numeric estimation. Error is the predicted value minus the reference value."
    else:
        task_line = "- The task assumed here is closed-set classification: one label per file."
    return [
        "## How to read this",
        "",
        task_line,
        "- Sim-to-real gap compares aggregate metrics. Files are not paired across domains.",
        "- A model confidence score is used for calibration only when the model provides one.",
        "- Scores from a run marked as example data are not study results.",
        "",
    ]


def _confusion_markdown(summary: dict) -> str:
    matrix = summary.get("confusion_matrix") or {}
    labels = matrix.get("labels") or []
    counts = matrix.get("counts") or []
    if not labels:
        return "No confusion matrix."
    header = "| True \\ predicted | " + " | ".join(labels) + " |"
    rule = "| --- | " + " | ".join("---:" for _ in labels) + " |"
    body = []
    for label, row in zip(labels, counts):
        body.append("| " + label + " | " + " | ".join(str(value) for value in row) + " |")
    return "\n".join([header, rule, *body])


def _num(value: object) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.4f}"
    return "n/a"


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: "Segoe UI", sans-serif; margin: 2rem auto; max-width: 900px; color: #1c2430; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d9d2c5; padding: 0.4rem 0.55rem; text-align: left; }}
    th {{ background: #f4f1ea; }}
    code {{ font-family: Consolas, monospace; }}
    h1 {{ font-size: 1.6rem; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def _markdownish_to_html(markdown: str) -> str:
    """Render the small markdown subset these reports emit."""
    lines = markdown.splitlines()
    html_lines: list[str] = []
    list_items: list[str] = []
    table_rows: list[list[str]] = []

    def flush_list() -> None:
        if not list_items:
            return
        html_lines.append("<ul>")
        html_lines.extend(f"<li>{_inline(item)}</li>" for item in list_items)
        html_lines.append("</ul>")
        list_items.clear()

    def flush_table() -> None:
        if not table_rows:
            return
        html_lines.append("<table>")
        for index, cells in enumerate(table_rows):
            tag = "th" if index == 0 else "td"
            html_lines.append(
                "<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>"
            )
        html_lines.append("</table>")
        table_rows.clear()

    for line in lines:
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            flush_list()
            table_rows.append(cells)
            continue
        flush_table()
        if line.startswith("# "):
            flush_list()
            html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            flush_list()
            html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            list_items.append(line[2:])
        elif line.strip() == "":
            flush_list()
        else:
            flush_list()
            html_lines.append(f"<p>{_inline(line)}</p>")
    flush_list()
    flush_table()
    return "\n".join(html_lines)


def _inline(text: str) -> str:
    escaped = html.escape(text)
    parts = escaped.split("`")
    rendered = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            rendered.append(f"<code>{part}</code>")
        else:
            rendered.append(part)
    return "".join(rendered)
