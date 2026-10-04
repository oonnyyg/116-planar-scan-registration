"""Transform scans into the global frame and bin them into a grid."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .interpolate import interpolate_pose
from .poses import Pose
from .scans import ScanPoint


@dataclass(frozen=True)
class RegistrationConfig:
    """Sensor mounting, valid range gate, and grid parameters.

    The sensor offset is expressed in the body frame; angles are degrees,
    counterclockwise positive, zero pointing along +x.
    """

    sensor_x: float = 0.0
    sensor_y: float = 0.0
    sensor_rotation_deg: float = 0.0
    range_min: float = 0.0
    range_max: float = math.inf
    grid_origin_x: float = 0.0
    grid_origin_y: float = 0.0
    grid_cell_size: float = 1.0

    def __post_init__(self) -> None:
        for name in (
            "sensor_x",
            "sensor_y",
            "sensor_rotation_deg",
            "range_min",
            "grid_origin_x",
            "grid_origin_y",
            "grid_cell_size",
        ):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"config field {name!r} must be finite")
        if math.isnan(self.range_max) or self.range_max == -math.inf:
            raise ValueError("config field 'range_max' must not be NaN or -inf")
        if self.range_min > self.range_max:
            raise ValueError("range_min must not exceed range_max")
        if self.grid_cell_size <= 0.0:
            raise ValueError("grid_cell_size must be positive")


@dataclass(frozen=True)
class RegisteredPoint:
    """A valid reading transformed into the global frame."""

    time: float
    angle_deg: float
    range_m: float
    x: float
    y: float
    cell: tuple[int, int]


@dataclass(frozen=True)
class RejectedPoint:
    """A reading that was dropped, with the reason."""

    time: float
    angle_deg: float
    range_m: float
    reason: str


@dataclass(frozen=True)
class CellStats:
    """Point count and centroid for one grid cell."""

    cell: tuple[int, int]
    count: int
    centroid_x: float
    centroid_y: float


@dataclass
class RegistrationResult:
    points: list[RegisteredPoint] = field(default_factory=list)
    rejected: list[RejectedPoint] = field(default_factory=list)
    cells: list[CellStats] = field(default_factory=list)


def _to_body_frame(point: ScanPoint, config: RegistrationConfig) -> tuple[float, float]:
    """Sensor-frame polar reading -> body-frame Cartesian (sensor mount first)."""
    angle = math.radians(point.angle_deg)
    sx = point.range_m * math.cos(angle)
    sy = point.range_m * math.sin(angle)
    mount = math.radians(config.sensor_rotation_deg)
    cos_m, sin_m = math.cos(mount), math.sin(mount)
    bx = config.sensor_x + cos_m * sx - sin_m * sy
    by = config.sensor_y + sin_m * sx + cos_m * sy
    return bx, by


def _to_global_frame(bx: float, by: float, pose: Pose) -> tuple[float, float]:
    """Body-frame point -> global frame using the interpolated pose."""
    heading = math.radians(pose.heading_deg)
    cos_h, sin_h = math.cos(heading), math.sin(heading)
    gx = pose.x + cos_h * bx - sin_h * by
    gy = pose.y + sin_h * bx + cos_h * by
    return gx, gy


def _cell_for(x: float, y: float, config: RegistrationConfig) -> tuple[int, int]:
    """Grid cell via floor of the offset divided by cell size (negatives included)."""
    ix = math.floor((x - config.grid_origin_x) / config.grid_cell_size)
    iy = math.floor((y - config.grid_origin_y) / config.grid_cell_size)
    return ix, iy


def register_scans(
    poses: list[Pose], scans: list[ScanPoint], config: RegistrationConfig
) -> RegistrationResult:
    """Register every scan point and aggregate per-cell statistics.

    Outputs are deterministically sorted: points and rejections by
    ``(time, angle_deg, range_m)``, cells by ``(ix, iy)``. Empty scans
    produce no points. Re-running on the same input gives identical output.
    """
    result = RegistrationResult()
    for point in scans:
        try:
            pose = interpolate_pose(poses, point.time)
        except ValueError as exc:
            result.rejected.append(
                RejectedPoint(point.time, point.angle_deg, point.range_m, str(exc))
            )
            continue
        if not (config.range_min <= point.range_m <= config.range_max):
            result.rejected.append(
                RejectedPoint(
                    point.time,
                    point.angle_deg,
                    point.range_m,
                    f"range {point.range_m} outside "
                    f"[{config.range_min}, {config.range_max}]",
                )
            )
            continue
        bx, by = _to_body_frame(point, config)
        gx, gy = _to_global_frame(bx, by, pose)
        result.points.append(
            RegisteredPoint(
                time=point.time,
                angle_deg=point.angle_deg,
                range_m=point.range_m,
                x=gx,
                y=gy,
                cell=_cell_for(gx, gy, config),
            )
        )
    result.points.sort(key=lambda p: (p.time, p.angle_deg, p.range_m))
    result.rejected.sort(key=lambda p: (p.time, p.angle_deg, p.range_m))
    sums: dict[tuple[int, int], list[float]] = {}
    for point in result.points:
        acc = sums.setdefault(point.cell, [0.0, 0.0, 0.0])
        acc[0] += 1.0
        acc[1] += point.x
        acc[2] += point.y
    result.cells = [
        CellStats(cell=cell, count=int(total[0]),
                  centroid_x=total[1] / total[0],
                  centroid_y=total[2] / total[0])
        for cell, total in sorted(sums.items())
    ]
    return result
