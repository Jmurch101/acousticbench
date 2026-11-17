"""SQLite records for datasets, user-registered models, and evaluation runs."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from uuid import uuid4

from acousticbench.util import utc_now

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL CHECK(domain IN ('simulated', 'real')),
    root_path TEXT NOT NULL,
    layout TEXT NOT NULL CHECK(layout IN ('class_folders', 'csv')),
    description TEXT NOT NULL DEFAULT '',
    is_example INTEGER NOT NULL DEFAULT 0,
    synthetic_stand_in INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS registered_models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    params_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_qualified_name TEXT NOT NULL,
    model_params_json TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    dataset_domain TEXT NOT NULL,
    status TEXT NOT NULL,
    config_json TEXT NOT NULL,
    summary_json TEXT,
    error TEXT,
    notes TEXT NOT NULL DEFAULT '',
    predictions_path TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);
"""


class Store:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connection() as connection:
            connection.executescript(SCHEMA)

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def upsert_dataset(self, dataset: dict) -> dict:
        row = {
            "id": dataset["id"],
            "name": dataset["name"],
            "domain": dataset["domain"],
            "root_path": str(dataset["root_path"]),
            "layout": dataset["layout"],
            "description": dataset.get("description") or "",
            "is_example": 1 if dataset.get("is_example") else 0,
            "synthetic_stand_in": 1 if dataset.get("synthetic_stand_in") else 0,
            "created_at": dataset.get("created_at") or utc_now(),
            "metadata_json": json.dumps(dataset.get("metadata") or {}),
        }
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO datasets (
                    id, name, domain, root_path, layout, description,
                    is_example, synthetic_stand_in, created_at, metadata_json
                ) VALUES (
                    :id, :name, :domain, :root_path, :layout, :description,
                    :is_example, :synthetic_stand_in, :created_at, :metadata_json
                )
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    domain=excluded.domain,
                    root_path=excluded.root_path,
                    layout=excluded.layout,
                    description=excluded.description,
                    is_example=excluded.is_example,
                    synthetic_stand_in=excluded.synthetic_stand_in,
                    metadata_json=excluded.metadata_json
                """,
                row,
            )
        return self.get_dataset(row["id"])

    def list_datasets(self) -> list[dict]:
        with self._lock, self._connection() as connection:
            rows = connection.execute("SELECT * FROM datasets ORDER BY created_at, name").fetchall()
        return [_dataset_from_row(row) for row in rows]

    def get_dataset(self, dataset_id: str) -> dict:
        with self._lock, self._connection() as connection:
            row = connection.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown dataset '{dataset_id}'.")
        return _dataset_from_row(row)

    def delete_dataset(self, dataset_id: str) -> None:
        with self._lock, self._connection() as connection:
            cursor = connection.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
        if cursor.rowcount == 0:
            raise KeyError(f"Unknown dataset '{dataset_id}'.")

    def list_registered_models(self) -> list[dict]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM registered_models ORDER BY created_at, name"
            ).fetchall()
        return [_model_from_row(row) for row in rows]

    def upsert_registered_model(self, model: dict) -> dict:
        row = {
            "id": model["id"],
            "name": model["name"],
            "qualified_name": model["qualified_name"],
            "description": model.get("description") or "",
            "params_json": json.dumps(model.get("params") or {}),
            "created_at": utc_now(),
        }
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO registered_models (
                    id, name, qualified_name, description, params_json, created_at
                ) VALUES (
                    :id, :name, :qualified_name, :description, :params_json, :created_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    qualified_name=excluded.qualified_name,
                    description=excluded.description,
                    params_json=excluded.params_json
                """,
                row,
            )
        return next(item for item in self.list_registered_models() if item["id"] == row["id"])

    def delete_registered_model(self, model_id: str) -> None:
        with self._lock, self._connection() as connection:
            cursor = connection.execute("DELETE FROM registered_models WHERE id = ?", (model_id,))
        if cursor.rowcount == 0:
            raise KeyError(f"Unknown registered model '{model_id}'.")

    def create_run(self, run: dict) -> dict:
        run_id = run.get("id") or uuid4().hex[:12]
        row = {
            "id": run_id,
            "model_id": run["model_id"],
            "model_name": run["model_name"],
            "model_qualified_name": run["model_qualified_name"],
            "model_params_json": json.dumps(run.get("model_params") or {}),
            "dataset_id": run["dataset_id"],
            "dataset_name": run["dataset_name"],
            "dataset_domain": run["dataset_domain"],
            "status": "queued",
            "config_json": json.dumps(run.get("config") or {}),
            "summary_json": None,
            "error": None,
            "notes": run.get("notes") or "",
            "predictions_path": None,
            "created_at": utc_now(),
            "started_at": None,
            "finished_at": None,
        }
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    id, model_id, model_name, model_qualified_name, model_params_json,
                    dataset_id, dataset_name, dataset_domain, status, config_json,
                    summary_json, error, notes, predictions_path, created_at, started_at, finished_at
                ) VALUES (
                    :id, :model_id, :model_name, :model_qualified_name, :model_params_json,
                    :dataset_id, :dataset_name, :dataset_domain, :status, :config_json,
                    :summary_json, :error, :notes, :predictions_path, :created_at, :started_at, :finished_at
                )
                """,
                row,
            )
        return self.get_run(run_id)

    def mark_running(self, run_id: str) -> None:
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE runs SET status = 'running', started_at = ?, error = NULL WHERE id = ?",
                (utc_now(), run_id),
            )

    def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        summary: dict | None = None,
        error: str | None = None,
        predictions_path: str | None = None,
    ) -> dict:
        with self._lock, self._connection() as connection:
            connection.execute(
                """
                UPDATE runs
                SET status = ?, summary_json = ?, error = ?, predictions_path = ?, finished_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    json.dumps(summary) if summary is not None else None,
                    error,
                    predictions_path,
                    utc_now(),
                    run_id,
                ),
            )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict:
        with self._lock, self._connection() as connection:
            row = connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown run '{run_id}'.")
        return _run_from_row(row)

    def list_runs(self, limit: int = 200) -> list[dict]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [_run_from_row(row) for row in rows]


def _dataset_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "domain": row["domain"],
        "root_path": row["root_path"],
        "layout": row["layout"],
        "description": row["description"],
        "is_example": bool(row["is_example"]),
        "synthetic_stand_in": bool(row["synthetic_stand_in"]),
        "created_at": row["created_at"],
        "metadata": json.loads(row["metadata_json"] or "{}"),
    }


def _model_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "qualified_name": row["qualified_name"],
        "description": row["description"],
        "params": json.loads(row["params_json"] or "{}"),
        "created_at": row["created_at"],
    }


def _run_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "model_id": row["model_id"],
        "model_name": row["model_name"],
        "model_qualified_name": row["model_qualified_name"],
        "model_params": json.loads(row["model_params_json"] or "{}"),
        "dataset_id": row["dataset_id"],
        "dataset_name": row["dataset_name"],
        "dataset_domain": row["dataset_domain"],
        "status": row["status"],
        "config": json.loads(row["config_json"] or "{}"),
        "summary": json.loads(row["summary_json"]) if row["summary_json"] else None,
        "error": row["error"],
        "notes": row["notes"],
        "predictions_path": row["predictions_path"],
        "created_at": row["created_at"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
    }


def new_dataset_id(name: str, existing: set[str]) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "dataset"
    if slug not in existing:
        return slug
    return f"{slug}-{uuid4().hex[:6]}"
