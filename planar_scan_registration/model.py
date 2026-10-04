"""Data model and validation for poses, scans and configuration."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


def require_finite(value, what: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{what} must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{what} must be finite, got {value!r}")
    return value


@dataclass(frozen=True)
class Pose:
    """Body pose: time in seconds, position in meters, heading in degrees."""

    time: float
    x: float
    y: float
    theta: float

    @staticmethod
    def from_values(time, x, y, theta) -> "Pose":
        return Pose(
            time=require_finite(time, "pose time"),
            x=require_finite(x, "pose x"),
            y=require_finite(y, "pose y"),
            theta=require_finite(theta, "pose theta"),
        )


@dataclass(frozen=True)
class ScanPoint:
    """One polar ranging sample: angle in degrees, range in meters."""

    angle: float
    distance: float


@dataclass(frozen=True)
class Scan:
    """One scan record with its timestamp in seconds."""

    time: float
    points: Tuple[ScanPoint, ...]


@dataclass(frozen=True)
class SensorMount:
    """Ranger pose relative to the body frame (meters, degrees)."""

    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0


@dataclass(frozen=True)
class Config:
    mount: SensorMount
    range_min: float
    range_max: float
    grid_origin_x: float
    grid_origin_y: float
    cell_size: float

    @staticmethod
    def from_dict(data: dict) -> "Config":
        if not isinstance(data, dict):
            raise ValueError("config must be a JSON object")
        mount_data = data.get("mount", {})
        if not isinstance(mount_data, dict):
            raise ValueError("config 'mount' must be an object")
        mount = SensorMount(
            x=require_finite(mount_data.get("x", 0.0), "mount.x"),
            y=require_finite(mount_data.get("y", 0.0), "mount.y"),
            rotation=require_finite(mount_data.get("rotation", 0.0), "mount.rotation"),
        )
        range_min = require_finite(data.get("range_min", 0.0), "range_min")
        range_max = require_finite(data.get("range_max", math.inf), "range_max")
        if range_min > range_max:
            raise ValueError("range_min must not exceed range_max")
        origin = data.get("grid_origin", [0.0, 0.0])
        if not isinstance(origin, (list, tuple)) or len(origin) != 2:
            raise ValueError("grid_origin must be a [x, y] pair")
        cell_size = require_finite(data.get("cell_size", 1.0), "cell_size")
        if cell_size <= 0.0:
            raise ValueError("cell_size must be positive")
        return Config(
            mount=mount,
            range_min=range_min,
            range_max=range_max,
            grid_origin_x=require_finite(origin[0], "grid_origin[0]"),
            grid_origin_y=require_finite(origin[1], "grid_origin[1]"),
            cell_size=cell_size,
        )
