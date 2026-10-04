"""Readers for pose CSV logs and scan JSONL records."""

from __future__ import annotations

import csv
import json
from typing import List

from .model import Pose, Scan, ScanPoint, require_finite

POSE_FIELDS = ("time", "x", "y", "theta")


def load_poses(path: str) -> List[Pose]:
    """Read poses from CSV with header time,x,y,theta (deg).

    Times must be strictly increasing; all values must be finite.
    """
    poses: List[Pose] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [f for f in POSE_FIELDS if f not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"pose CSV missing columns: {', '.join(missing)}")
        for line_no, row in enumerate(reader, start=2):
            try:
                pose = Pose.from_values(
                    float(row["time"]),
                    float(row["x"]),
                    float(row["y"]),
                    float(row["theta"]),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"pose CSV line {line_no}: {exc}") from exc
            if poses and pose.time <= poses[-1].time:
                raise ValueError(
                    f"pose CSV line {line_no}: time {pose.time} is not strictly "
                    f"greater than previous {poses[-1].time}"
                )
            poses.append(pose)
    if not poses:
        raise ValueError("pose CSV contains no poses")
    return poses


def load_scans(path: str) -> List[Scan]:
    """Read scans from JSONL.

    Each line: {"time": <seconds>, "points": [[angle_deg, range_m], ...]}.
    """
    scans: List[Scan] = []
    with open(path, encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"scan JSONL line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"scan JSONL line {line_no}: record must be an object")
            if "time" not in record or "points" not in record:
                raise ValueError(
                    f"scan JSONL line {line_no}: record needs 'time' and 'points'"
                )
            time = require_finite(record["time"], f"scan JSONL line {line_no} time")
            raw_points = record["points"]
            if not isinstance(raw_points, list):
                raise ValueError(f"scan JSONL line {line_no}: 'points' must be a list")
            points = []
            for index, item in enumerate(raw_points):
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise ValueError(
                        f"scan JSONL line {line_no} point {index}: "
                        "expected [angle_deg, range_m]"
                    )
                angle = require_finite(
                    item[0], f"scan JSONL line {line_no} point {index} angle"
                )
                distance = require_finite(
                    item[1], f"scan JSONL line {line_no} point {index} range"
                )
                points.append(ScanPoint(angle=angle, distance=distance))
            scans.append(Scan(time=time, points=tuple(points)))
    return scans
