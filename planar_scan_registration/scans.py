"""Loading and validation of JSONL scan records."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanPoint:
    """One polar range reading: time (s), angle (deg, CCW from +x), range (m)."""

    time: float
    angle_deg: float
    range_m: float


def _finite_field(record: dict, key: str, line: int) -> float:
    if key not in record:
        raise ValueError(f"line {line}: scan record missing field {key!r}")
    try:
        value = float(record[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"line {line}: scan field {key!r} is not a number: {record[key]!r}"
        ) from exc
    if not math.isfinite(value):
        raise ValueError(
            f"line {line}: scan field {key!r} is not finite: {value!r}"
        )
    return value


def load_scans(path: str | Path) -> list[ScanPoint]:
    """Read scan points from JSONL, one ``{"time","angle_deg","range_m"}`` per line."""
    points: list[ScanPoint] = []
    with open(path, encoding="utf-8") as handle:
        for line, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"line {line}: scan record must be an object")
            points.append(
                ScanPoint(
                    time=_finite_field(record, "time", line),
                    angle_deg=_finite_field(record, "angle_deg", line),
                    range_m=_finite_field(record, "range_m", line),
                )
            )
    return points
