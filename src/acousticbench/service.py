"""Shared checks used by the command line and the local web app."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from acousticbench.datasets.manifest import AudioItem, load_items, summarize_items
from acousticbench.eval.store import Store, new_dataset_id
from acousticbench.models.base import AcousticModel
from acousticbench.models.registry import get_model, import_model, instantiate, list_models

DOMAINS = {"simulated", "real"}
LAYOUTS = {"class_folders", "csv"}


def normalize_eval_config(raw: dict | None) -> dict:
    raw = raw or {}
    sample_rate = int(raw.get("sample_rate") or 16000)
    if sample_rate < 8000 or sample_rate > 48000:
        raise ValueError("sample_rate must be between 8000 and 48000.")
    split = str(raw.get("split") or "all").strip().lower()
    if split not in {"all", "train", "val", "valid", "validation", "test"}:
        raise ValueError("split must be all, train, val, or test.")
    if split in {"val", "valid", "validation"}:
        split = "val"
    max_items = raw.get("max_items")
    if max_items in ("", None):
        max_items = None
    else:
        max_items = int(max_items)
        if max_items < 1:
            raise ValueError("max_items must be at least 1.")
    max_seconds = raw.get("max_seconds", 30)
    if max_seconds in ("", None):
        max_seconds = None
    else:
        max_seconds = float(max_seconds)
        if max_seconds <= 0 or max_seconds > 120:
            raise ValueError("max_seconds must be greater than 0 and at most 120.")
    notes = str(raw.get("notes") or "").strip()
    model_params = raw.get("model_params") or {}
    if not isinstance(model_params, dict):
        raise ValueError("model_params must be an object.")
    return {
        "sample_rate": sample_rate,
        "split": split,
        "max_items": max_items,
        "max_seconds": max_seconds,
        "notes": notes,
        "model_params": model_params,
        "paired_group": raw.get("paired_group"),
    }


def dataset_items(dataset: dict, config: dict) -> list[AudioItem]:
    items = load_items(Path(dataset["root_path"]), dataset["layout"])
    split = (config or {}).get("split") or "all"
    if split != "all":
        items = [item for item in items if (item.split or "").lower() in _split_aliases(split)]
    max_items = (config or {}).get("max_items")
    if max_items:
        items = items[: int(max_items)]
    return items


def dataset_summary(dataset: dict) -> dict:
    payload = dict(dataset)
    try:
        items = load_items(Path(dataset["root_path"]), dataset["layout"])
        payload["inventory"] = summarize_items(items)
        payload["inventory_error"] = None
    except Exception as exc:
        payload["inventory"] = None
        payload["inventory_error"] = str(exc)
    return payload


def add_dataset(store: Store, fields: dict, *, allow_example_flags: bool = False) -> dict:
    name = str(fields.get("name") or "").strip()
    domain = str(fields.get("domain") or "").strip().lower()
    layout = str(fields.get("layout") or "").strip()
    root = Path(str(fields.get("root_path") or "")).expanduser()
    description = str(fields.get("description") or "").strip()
    if not name:
        raise ValueError("Dataset name is required.")
    if domain not in DOMAINS:
        raise ValueError("Domain must be simulated or real.")
    if layout not in LAYOUTS:
        raise ValueError("Layout must be class_folders or csv.")
    if not root.exists():
        raise ValueError(f"Dataset path does not exist: {root}")
    load_items(root, layout)
    existing_ids = {item["id"] for item in store.list_datasets()}
    dataset_id = str(fields.get("id") or "").strip() or new_dataset_id(name, existing_ids)
    record = {
        "id": dataset_id,
        "name": name,
        "domain": domain,
        "root_path": str(root.resolve()),
        "layout": layout,
        "description": description,
        "is_example": bool(fields.get("is_example")) if allow_example_flags else False,
        "synthetic_stand_in": bool(fields.get("synthetic_stand_in")) if allow_example_flags else False,
        "metadata": fields.get("metadata") or {},
    }
    if not allow_example_flags:
        record["metadata"] = {
            **record["metadata"],
            "source": "user",
        }
    try:
        return store.upsert_dataset(record)
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"A dataset named '{name}' already exists.") from exc


def register_model(store: Store, project_root: Path, fields: dict) -> dict:
    model_id = str(fields.get("id") or "").strip()
    name = str(fields.get("name") or model_id).strip()
    qualified_name = str(fields.get("qualified_name") or "").strip()
    description = str(fields.get("description") or "").strip()
    params = fields.get("params") or {}
    if not model_id or not name:
        raise ValueError("Model id and name are required.")
    if not isinstance(params, dict):
        raise ValueError("Model params must be an object.")
    known = {spec.model_id for spec in list_models(project_root, store.list_registered_models())}
    if model_id in known and model_id not in {row["id"] for row in store.list_registered_models()}:
        raise ValueError(f"Model id '{model_id}' is already used by a built-in or config model.")
    cls = import_model(qualified_name)
    if not isinstance(cls, type) or not issubclass(cls, AcousticModel):
        raise ValueError(f"{qualified_name} must be a subclass of AcousticModel.")
    instantiate_spec_check(cls, params)
    return store.upsert_registered_model(
        {
            "id": model_id,
            "name": name,
            "qualified_name": qualified_name,
            "description": description,
            "params": params,
        }
    )


def instantiate_spec_check(cls: type[AcousticModel], params: dict) -> None:
    try:
        model = cls(**params)
    except TypeError as exc:
        raise ValueError(f"Could not construct {cls.__name__}: {exc}") from exc
    if not isinstance(model, AcousticModel):
        raise ValueError(f"{cls.__name__} must be a subclass of AcousticModel.")


def queue_run(
    store: Store,
    project_root: Path,
    *,
    model_id: str,
    dataset_id: str,
    raw_config: dict | None,
) -> dict:
    config = normalize_eval_config(raw_config)
    try:
        dataset = store.get_dataset(dataset_id)
    except KeyError as exc:
        raise ValueError(exc.args[0] if exc.args else "Unknown dataset.") from exc
    try:
        spec = get_model(project_root, model_id, store.list_registered_models())
    except ValueError:
        raise
    params = config.pop("model_params")
    notes = config.pop("notes")
    model = instantiate(spec, params)
    metadata = dataset.get("metadata") or {}
    config["task"] = getattr(model, "task", "classification")
    config["dataset_flags"] = {
        "is_example": dataset["is_example"],
        "synthetic_stand_in": dataset["synthetic_stand_in"],
        "synthetic": bool(metadata.get("synthetic")),
    }
    return store.create_run(
        {
            "model_id": spec.model_id,
            "model_name": spec.name,
            "model_qualified_name": spec.qualified_name,
            "model_params": params,
            "dataset_id": dataset["id"],
            "dataset_name": dataset["name"],
            "dataset_domain": dataset["domain"],
            "config": config,
            "notes": notes,
        }
    )


def _split_aliases(split: str) -> set[str]:
    if split == "val":
        return {"val", "valid", "validation"}
    return {split}
