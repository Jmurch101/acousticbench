"""Local FastAPI interface for datasets, runs, and sim-to-real comparisons."""

from __future__ import annotations

import csv
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from acousticbench import ADVISOR, EXAMPLE_CAVEAT, PROJECT_NAME, TEAM, __version__
from acousticbench.compare import compare_runs
from acousticbench.eval.runner import execute_run
from acousticbench.eval.store import Store
from acousticbench.examples_data import generate_example_datasets
from acousticbench.models.registry import list_models
from acousticbench.paths import database_path, find_project_root, prepare_runtime, runs_dir
from acousticbench.report import (
    compare_report_html,
    compare_report_markdown,
    run_report_html,
    run_report_markdown,
)
from acousticbench.service import (
    add_dataset,
    dataset_summary,
    queue_run,
    register_model,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(project_root: Path | None = None) -> FastAPI:
    root = (project_root or find_project_root()).resolve()
    prepare_runtime(root)
    store = Store(database_path(root))
    app = FastAPI(title=PROJECT_NAME, version=__version__)
    app.state.root = root
    app.state.store = store

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(ValueError)
    async def value_error(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(KeyError)
    async def missing(_request: Request, exc: KeyError) -> JSONResponse:
        message = exc.args[0] if exc.args else "Not found."
        return JSONResponse(status_code=404, content={"detail": str(message)})

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/overview")
    def overview() -> dict:
        datasets = store.list_datasets()
        runs = store.list_runs(limit=500)
        models = list_models(root, store.list_registered_models())
        return {
            "project": PROJECT_NAME,
            "version": __version__,
            "team": list(TEAM),
            "advisor": ADVISOR,
            "dataset_count": len(datasets),
            "run_count": len(runs),
            "model_count": len(models),
            "example_caveat": EXAMPLE_CAVEAT,
            "task": "T60 estimation is the first selected task. Classification is still available for room-size work.",
            "gap_definition": "gap = real - simulated",
        }

    @app.get("/api/datasets")
    def get_datasets() -> list[dict]:
        return [dataset_summary(row) for row in store.list_datasets()]

    @app.post("/api/datasets")
    def post_dataset(body: dict) -> dict:
        return dataset_summary(add_dataset(store, body))

    @app.delete("/api/datasets/{dataset_id}")
    def delete_dataset(dataset_id: str) -> dict:
        store.delete_dataset(dataset_id)
        return {"deleted": dataset_id}

    @app.post("/api/examples/generate")
    def post_examples() -> dict:
        records = generate_example_datasets(root, store)
        return {
            "datasets": [dataset_summary(row) for row in records],
            "caveat": EXAMPLE_CAVEAT,
        }

    @app.get("/api/models")
    def get_models() -> list[dict]:
        return [spec.to_dict() for spec in list_models(root, store.list_registered_models())]

    @app.post("/api/models")
    def post_model(body: dict) -> dict:
        registered = register_model(store, root, body)
        spec = next(
            item
            for item in list_models(root, store.list_registered_models())
            if item.model_id == registered["id"]
        )
        return spec.to_dict()

    @app.delete("/api/models/{model_id}")
    def delete_model(model_id: str) -> dict:
        specs = {spec.model_id: spec for spec in list_models(root, store.list_registered_models())}
        spec = specs.get(model_id)
        if spec is None:
            raise KeyError(f"Unknown model '{model_id}'.")
        if spec.source != "registered":
            raise ValueError("Only models registered from the interface can be removed here.")
        store.delete_registered_model(model_id)
        return {"deleted": model_id}

    @app.post("/api/evaluations")
    def post_evaluation(body: dict) -> dict:
        run = queue_run(
            store,
            root,
            model_id=str(body.get("model_id") or ""),
            dataset_id=str(body.get("dataset_id") or ""),
            raw_config=_eval_body(body),
        )
        _start(run["id"])
        return run

    @app.post("/api/evaluations/paired")
    def post_paired(body: dict) -> dict:
        group = uuid4().hex[:8]
        config = _eval_body(body)
        config["paired_group"] = group
        sim_id = str(body.get("sim_dataset_id") or "")
        real_id = str(body.get("real_dataset_id") or "")
        if not sim_id or not real_id:
            raise ValueError("Choose both a simulated dataset and a real dataset.")
        if sim_id == real_id:
            raise ValueError("The simulated and real datasets must be different.")
        simulated = queue_run(
            store, root, model_id=str(body.get("model_id") or ""), dataset_id=sim_id, raw_config=config
        )
        real = queue_run(
            store, root, model_id=str(body.get("model_id") or ""), dataset_id=real_id, raw_config=config
        )
        thread = threading.Thread(
            target=_run_pair,
            args=(store, root, simulated["id"], real["id"]),
            daemon=True,
        )
        thread.start()
        return {"paired_group": group, "simulated": simulated, "real": real}

    @app.get("/api/runs")
    def get_runs(limit: int = 200) -> list[dict]:
        return store.list_runs(limit=min(max(limit, 1), 500))

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        return store.get_run(run_id)

    @app.get("/api/runs/{run_id}/predictions")
    def get_predictions(run_id: str, limit: int = 50) -> dict:
        path = _predictions_file(root, store.get_run(run_id))
        rows = _read_predictions(path, limit=min(max(limit, 1), 500))
        return {"rows": rows, "limit": limit}

    @app.get("/api/runs/{run_id}/predictions.csv")
    def download_predictions(run_id: str) -> FileResponse:
        path = _predictions_file(root, store.get_run(run_id))
        return FileResponse(path, media_type="text/csv", filename=f"acousticbench-{run_id}-predictions.csv")

    @app.get("/api/runs/{run_id}/report.md")
    def download_run_md(run_id: str) -> Response:
        report = run_report_markdown(store.get_run(run_id))
        return _download(report, f"acousticbench-{run_id}.md", "text/markdown; charset=utf-8")

    @app.get("/api/runs/{run_id}/report.html")
    def view_run_html(run_id: str) -> HTMLResponse:
        return HTMLResponse(run_report_html(store.get_run(run_id)))

    @app.post("/api/compare")
    def post_compare(body: dict) -> dict:
        simulated = store.get_run(str(body.get("sim_run_id") or ""))
        real = store.get_run(str(body.get("real_run_id") or ""))
        comparison = compare_runs(simulated, real)
        comparison["simulated"] = _brief(simulated)
        comparison["real"] = _brief(real)
        return comparison

    @app.get("/api/compare/report.md")
    def download_compare_md(sim: str, real: str) -> Response:
        simulated = store.get_run(sim)
        actual = store.get_run(real)
        report = compare_report_markdown(compare_runs(simulated, actual), simulated, actual)
        return _download(report, f"acousticbench-compare-{sim}-{real}.md", "text/markdown; charset=utf-8")

    @app.get("/api/compare/report.html")
    def view_compare_html(sim: str, real: str) -> HTMLResponse:
        simulated = store.get_run(sim)
        actual = store.get_run(real)
        return HTMLResponse(compare_report_html(compare_runs(simulated, actual), simulated, actual))

    @app.get("/api/export/runs.json")
    def export_runs() -> JSONResponse:
        payload = {"project": PROJECT_NAME, "version": __version__, "runs": store.list_runs(limit=500)}
        return JSONResponse(
            payload,
            headers={"Content-Disposition": 'attachment; filename="acousticbench-runs.json"'},
        )

    def _start(run_id: str) -> None:
        thread = threading.Thread(target=execute_run, args=(store, run_id, root), daemon=True)
        thread.start()

    return app


def _run_pair(store: Store, root: Path, sim_run_id: str, real_run_id: str) -> None:
    execute_run(store, sim_run_id, root)
    execute_run(store, real_run_id, root)


def _eval_body(body: dict) -> dict:
    return {
        "sample_rate": body.get("sample_rate"),
        "split": body.get("split"),
        "max_items": body.get("max_items"),
        "max_seconds": body.get("max_seconds"),
        "notes": body.get("notes") or "",
        "model_params": body.get("model_params") or {},
        "paired_group": body.get("paired_group"),
    }


def _predictions_file(root: Path, run: dict) -> Path:
    raw = run.get("predictions_path")
    if not raw:
        raise ValueError("This run has no prediction file.")
    path = Path(raw).resolve()
    allowed = runs_dir(root).resolve()
    try:
        path.relative_to(allowed)
    except ValueError as exc:
        raise ValueError("Prediction file is outside the runs directory.") from exc
    if not path.is_file():
        raise ValueError("Prediction file is missing.")
    return path


def _read_predictions(path: Path, limit: int) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))[:limit]


def _brief(run: dict) -> dict:
    summary = run.get("summary") or {}
    return {
        "id": run["id"],
        "model_name": run["model_name"],
        "dataset_name": run["dataset_name"],
        "dataset_domain": run["dataset_domain"],
        "accuracy": summary.get("accuracy"),
        "macro_f1": summary.get("macro_f1"),
    }


def _download(content: str, filename: str, media_type: str) -> Response:
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
