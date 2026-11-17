"""Small shared helpers."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def jsonable(value):
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.floating):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value
