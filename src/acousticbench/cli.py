"""Command line for AcoustiBench."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from acousticbench import __version__
from acousticbench.compare import compare_runs
from acousticbench.eval.runner import execute_run
from acousticbench.eval.store import Store
from acousticbench.examples_data import generate_example_datasets
from acousticbench.paths import database_path, find_project_root, prepare_runtime
from acousticbench.report import compare_report_markdown, run_report_markdown
from acousticbench.service import add_dataset, dataset_summary, queue_run


def main(argv: list[str] | None = None) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(
        prog="acousticbench",
        description="Evaluate acoustic classification models on simulated and real audio.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--root", type=Path, help="Project root. Defaults to this repository.")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Start the local web interface.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    generate = sub.add_parser("generate-examples", help="Write labeled synthetic example datasets.")
    generate.set_defaults(func=cmd_generate)

    simulate = sub.add_parser(
        "simulate-dev",
        help="Write the Pyroomacoustics shoebox set with Sabine T60 labels.",
    )
    simulate.set_defaults(func=cmd_simulate)

    prepare_ace = sub.add_parser(
        "prepare-ace",
        help="Register the local ACE single-channel impulse responses and published T60 labels.",
    )
    prepare_ace.set_defaults(func=cmd_prepare_ace)

    demo = sub.add_parser(
        "demo",
        help="Rerun Schroeder, the room-family rule, and direct-path distance, then write the draft report.",
    )
    demo.set_defaults(func=cmd_demo)

    datasets = sub.add_parser("datasets", help="List or register datasets.")
    datasets_sub = datasets.add_subparsers(dest="datasets_command", required=True)
    datasets_list = datasets_sub.add_parser("list", help="List registered datasets.")
    datasets_list.set_defaults(func=cmd_datasets_list)
    datasets_add = datasets_sub.add_parser("add", help="Register a dataset directory.")
    datasets_add.add_argument("--file", type=Path, help="YAML file with name, domain, layout, root_path.")
    datasets_add.add_argument("--name")
    datasets_add.add_argument("--domain", choices=["simulated", "real"])
    datasets_add.add_argument("--path", help="Directory of audio or a folder that contains manifest.csv.")
    datasets_add.add_argument("--layout", choices=["class_folders", "csv"])
    datasets_add.add_argument("--description", default="")
    datasets_add.set_defaults(func=cmd_datasets_add)

    evaluate = sub.add_parser("eval", help="Run one model on one dataset and wait for the result.")
    evaluate.add_argument("--model", required=True)
    evaluate.add_argument("--dataset", required=True)
    evaluate.add_argument("--config", type=Path, help="YAML config. See config/example_eval.yaml.")
    evaluate.add_argument("--sample-rate", type=int)
    evaluate.add_argument("--split")
    evaluate.add_argument("--max-items", type=int)
    evaluate.add_argument("--max-seconds", type=float)
    evaluate.add_argument("--notes", default="")
    evaluate.add_argument(
        "--model-param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Model parameter. Repeat for more than one. Example: --model-param label=tone",
    )
    evaluate.set_defaults(func=cmd_eval)

    runs = sub.add_parser("runs", help="List recorded evaluation runs.")
    runs.add_argument("--limit", type=int, default=20)
    runs.set_defaults(func=cmd_runs)

    compare = sub.add_parser("compare", help="Compare a simulated run with a real run.")
    compare.add_argument("--sim", required=True, help="Run id recorded on simulated audio.")
    compare.add_argument("--real", required=True, help="Run id recorded on real audio.")
    compare.add_argument("--out", type=Path, help="Write the markdown report to this file.")
    compare.set_defaults(func=cmd_compare)

    show = sub.add_parser("show", help="Print one run as a markdown report.")
    show.add_argument("run_id")
    show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else str(exc)
        print(f"Error: {message}", file=sys.stderr)
        raise SystemExit(1) from exc


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from acousticbench.web.app import create_app

    root = _root(args)
    prepare_runtime(root)
    print(f"AcoustiBench at http://{args.host}:{args.port}")
    uvicorn.run(create_app(root), host=args.host, port=args.port)


def cmd_generate(args: argparse.Namespace) -> None:
    root = _root(args)
    records = generate_example_datasets(root, _store(root))
    print("Generated example datasets. These are synthetic and are not experimental results.")
    for record in records:
        print(f"- {record['id']}: {record['domain']} -> {record['root_path']}")


def cmd_simulate(args: argparse.Namespace) -> None:
    from acousticbench.sim.pyroom_dev import generate_pyroom_dataset

    record = generate_pyroom_dataset(_root(args), _store(_root(args)))
    print("Wrote the Pyroomacoustics development set. The t60 column is Sabine, not a measurement.")
    print(f"- {record['id']}: {record['domain']} -> {record['root_path']}")


def cmd_prepare_ace(args: argparse.Namespace) -> None:
    from acousticbench.ace_prepare import prepare_ace_dataset

    record = prepare_ace_dataset(_root(args), _store(_root(args)))
    print("Registered the local ACE impulse responses. Audio stays outside git.")
    print(f"- {record['id']}: {record['domain']} -> {record['root_path']}")
    print("Cite Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM TASLP, 2016.")


def cmd_demo(args: argparse.Namespace) -> None:
    from acousticbench.demo import run_recorded_demo

    written = run_recorded_demo(_root(args), _store(_root(args)))
    print("Wrote the development reports from completed runs.")
    for path in written.values():
        print(f"- {path}")


def cmd_datasets_list(args: argparse.Namespace) -> None:
    root = _root(args)
    rows = [_with_inventory(_store(root), row) for row in _store(root).list_datasets()]
    if not rows:
        print("No datasets registered. Run: acousticbench generate-examples")
        return
    for row in rows:
        inventory = row.get("inventory") or {}
        count = inventory.get("n_items", "unavailable")
        flags = []
        if row["is_example"]:
            flags.append("example")
        if row["synthetic_stand_in"]:
            flags.append("synthetic-stand-in")
        flag_text = f" [{', '.join(flags)}]" if flags else ""
        print(f"{row['id']}  {row['domain']}  items={count}  {row['name']}{flag_text}")


def cmd_datasets_add(args: argparse.Namespace) -> None:
    fields = {}
    if args.file:
        with args.file.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError("Dataset file must be a YAML mapping.")
        fields.update(loaded)
    if args.name:
        fields["name"] = args.name
    if args.domain:
        fields["domain"] = args.domain
    if args.path:
        fields["root_path"] = args.path
    if args.layout:
        fields["layout"] = args.layout
    if args.description:
        fields["description"] = args.description
    record = add_dataset(_store(_root(args)), fields)
    print(f"Registered {record['id']} ({record['domain']})")


def cmd_eval(args: argparse.Namespace) -> None:
    root = _root(args)
    prepare_runtime(root)
    raw = _load_config(args.config)
    if args.sample_rate is not None:
        raw["sample_rate"] = args.sample_rate
    if args.split:
        raw["split"] = args.split
    if args.max_items is not None:
        raw["max_items"] = args.max_items
    if args.max_seconds is not None:
        raw["max_seconds"] = args.max_seconds
    if args.notes:
        raw["notes"] = args.notes
    raw["model_params"] = _parse_model_params(args.model_param, raw.get("model_params") or {})
    store = _store(root)
    run = queue_run(
        store,
        root,
        model_id=args.model,
        dataset_id=args.dataset,
        raw_config=raw,
    )
    finished = execute_run(store, run["id"], root)
    print(run_report_markdown(finished))
    if finished["status"] != "completed":
        raise SystemExit(1)


def cmd_runs(args: argparse.Namespace) -> None:
    rows = _store(_root(args)).list_runs(limit=args.limit)
    if not rows:
        print("No runs yet.")
        return
    for row in rows:
        summary = row.get("summary") or {}
        accuracy = summary.get("accuracy")
        accuracy_text = f"{accuracy:.3f}" if isinstance(accuracy, float) else "-"
        print(
            f"{row['id']}  {row['status']:<10}  {row['dataset_domain']:<10}  "
            f"acc={accuracy_text}  {row['model_id']}  {row['dataset_id']}"
        )


def cmd_compare(args: argparse.Namespace) -> None:
    store = _store(_root(args))
    simulated = store.get_run(args.sim)
    real = store.get_run(args.real)
    report = compare_report_markdown(compare_runs(simulated, real), simulated, real)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(report)


def cmd_show(args: argparse.Namespace) -> None:
    print(run_report_markdown(_store(_root(args)).get_run(args.run_id)))


def _root(args: argparse.Namespace) -> Path:
    if args.root:
        return args.root.resolve()
    return find_project_root()


def _store(root: Path) -> Store:
    return Store(database_path(root))


def _with_inventory(store: Store, row: dict) -> dict:
    del store
    return dataset_summary(row)


def _load_config(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Evaluation config must be a YAML mapping.")
    return loaded


def _parse_model_params(pairs: list[str], existing: dict) -> dict:
    params = dict(existing)
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Model param '{pair}' must look like key=value.")
        key, raw_value = pair.split("=", 1)
        params[key.strip()] = _coerce(raw_value.strip())
    return params


def _coerce(value: str):
    if value[:1] in "[{":
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
