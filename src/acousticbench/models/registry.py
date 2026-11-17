"""Built-in models plus optional entries from config/models.yaml and the database."""

from __future__ import annotations

import importlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from acousticbench.models.base import AcousticModel
from acousticbench.models.constant import ConstantLabelModel
from acousticbench.models.example_spectral import ExampleSpectralClassifier

logger = logging.getLogger(__name__)

QUALIFIED_NAME = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$")

BUILTINS: dict[str, type[AcousticModel]] = {
    ExampleSpectralClassifier.model_id: ExampleSpectralClassifier,
    ConstantLabelModel.model_id: ConstantLabelModel,
}


@dataclass
class ModelSpec:
    model_id: str
    name: str
    qualified_name: str
    description: str
    params: dict
    source: str

    def to_dict(self) -> dict:
        return {
            "id": self.model_id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "description": self.description,
            "params": self.params,
            "source": self.source,
            "deletable": self.source == "registered",
        }


def list_models(project_root: Path, registered: list[dict] | None = None) -> list[ModelSpec]:
    specs: dict[str, ModelSpec] = {}
    for model_id, cls in BUILTINS.items():
        specs[model_id] = ModelSpec(
            model_id=model_id,
            name=cls.name,
            qualified_name=f"{cls.__module__}:{cls.__name__}",
            description=cls.description,
            params={},
            source="builtin",
        )
    for entry in _yaml_models(project_root / "config" / "models.yaml"):
        if entry.model_id in specs:
            logger.warning("Skipping config model '%s' because that id is already defined.", entry.model_id)
            continue
        specs[entry.model_id] = entry
    for row in registered or []:
        if row["id"] in specs:
            logger.warning("Skipping registered model '%s' because that id is already defined.", row["id"])
            continue
        specs[row["id"]] = ModelSpec(
            model_id=row["id"],
            name=row["name"],
            qualified_name=row["qualified_name"],
            description=row.get("description") or "",
            params=row.get("params") or {},
            source="registered",
        )
    return list(specs.values())


def get_model(project_root: Path, model_id: str, registered: list[dict] | None = None) -> ModelSpec:
    for spec in list_models(project_root, registered):
        if spec.model_id == model_id:
            return spec
    raise ValueError(f"Unknown model '{model_id}'.")


def instantiate(spec: ModelSpec, overrides: dict | None = None) -> AcousticModel:
    params = dict(spec.params)
    params.update(overrides or {})
    if spec.model_id in BUILTINS and spec.source == "builtin":
        cls = BUILTINS[spec.model_id]
    else:
        cls = import_model(spec.qualified_name)
    try:
        model = cls(**params)
    except TypeError as exc:
        raise ValueError(
            f"Could not construct model '{spec.model_id}' with params {sorted(params)}: {exc}"
        ) from exc
    if not isinstance(model, AcousticModel):
        raise ValueError(f"{spec.qualified_name} must be a subclass of AcousticModel.")
    return model


def import_model(qualified_name: str) -> type[AcousticModel]:
    if not QUALIFIED_NAME.match(qualified_name):
        raise ValueError(
            "Model path must look like 'package.module:ClassName'. "
            "Registering a model imports and runs local Python."
        )
    module_name, class_name = qualified_name.split(":")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ValueError(f"Could not import {module_name}: {exc}") from exc
    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise ValueError(f"{module_name} has no attribute {class_name}.") from exc
    return cls


def _yaml_models(path: Path) -> list[ModelSpec]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle) or {}
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a mapping.")
    entries = document.get("models") or []
    specs: list[ModelSpec] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"Each model entry in {path} must be a mapping.")
        model_id = str(entry.get("id") or "").strip()
        qualified = str(entry.get("qualified_name") or "").strip()
        if not model_id or not qualified:
            raise ValueError(f"Each model in {path} needs id and qualified_name.")
        params = entry.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError(f"Params for model '{model_id}' must be a mapping.")
        specs.append(
            ModelSpec(
                model_id=model_id,
                name=str(entry.get("name") or model_id),
                qualified_name=qualified,
                description=str(entry.get("description") or ""),
                params=params,
                source="config",
            )
        )
    return specs
