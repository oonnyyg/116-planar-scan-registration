"""Loading and validation of the CSV pose log."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pose:
    """Body pose: time (s), planar position (m), heading (degrees, CCW from +x)."""

    time: float
    x: float
    y: float
    heading_deg: float


def _finite(value: float, field: str, line: int) -> float:
    if not math.isfinite(value):
        raise ValueError(f"line {line}: pose field {field!r} is not finite: {value!r}")
    return value


def load_poses(path: str | Path) -> list[Pose]:
    """Read poses from CSV with header ``time,x,y,heading_deg``.

    Times must be strictly increasing and every value finite.
    """
    poses: list[Pose] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"time", "x", "y", "heading_deg"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"pose CSV missing columns: {sorted(missing)}")
        for line, row in enumerate(reader, start=2):
            try:
                pose = Pose(
                    time=_finite(float(row["time"]), "time", line),
                    x=_finite(float(row["x"]), "x", line),
                    y=_finite(float(row["y"]), "y", line),
                    heading_deg=_finite(
                        float(row["heading_deg"]), "heading_deg", line
                    ),
                )
            except (TypeError, ValueError) as exc:
                if isinstance(exc, ValueError) and "not finite" in str(exc):
                    raise
                raise ValueError(f"line {line}: invalid pose row {row!r}: {exc}")
            if poses and pose.time <= poses[-1].time:
                raise ValueError(
                    f"line {line}: pose times must be strictly increasing "
                    f"({pose.time} <= {poses[-1].time})"
                )
            poses.append(pose)
    if not poses:
        raise ValueError("pose CSV contains no poses")
    return poses
