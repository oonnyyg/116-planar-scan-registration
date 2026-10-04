"""Core processing: register scans into the global frame and bin to a grid."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .interpolate import interpolate_pose
from .model import Config, Pose, Scan
from .transform import sensor_to_global


@dataclass(frozen=True)
class PointRecord:
    """Per-point output row. Rejected points keep their reason."""

    scan_index: int
    point_index: int
    time: float
    angle: float
    distance: float
    accepted: bool
    x: Optional[float] = None
    y: Optional[float] = None
    cell_x: Optional[int] = None
    cell_y: Optional[int] = None
    reason: str = ""


@dataclass
class CellStats:
    count: int = 0
    sum_x: float = 0.0
    sum_y: float = 0.0

    @property
    def centroid(self) -> Tuple[float, float]:
        return self.sum_x / self.count, self.sum_y / self.count


@dataclass
class Result:
    points: List[PointRecord] = field(default_factory=list)
    cells: Dict[Tuple[int, int], CellStats] = field(default_factory=dict)


def grid_cell(x: float, y: float, config: Config) -> Tuple[int, int]:
    """Bin a global point; floor division handles negative coordinates."""
    cell_x = math.floor((x - config.grid_origin_x) / config.cell_size)
    cell_y = math.floor((y - config.grid_origin_y) / config.cell_size)
    return cell_x, cell_y


def process(poses: List[Pose], scans: List[Scan], config: Config) -> Result:
    result = Result()
    for scan_index, scan in enumerate(scans):
        pose = interpolate_pose(poses, scan.time)
        for point_index, point in enumerate(scan.points):
            base = dict(
                scan_index=scan_index,
                point_index=point_index,
                time=scan.time,
                angle=point.angle,
                distance=point.distance,
            )
            if pose is None:
                result.points.append(
                    PointRecord(
                        accepted=False,
                        reason="time outside pose range",
                        **base,
                    )
                )
                continue
            if not (config.range_min <= point.distance <= config.range_max):
                result.points.append(
                    PointRecord(
                        accepted=False,
                        reason=(
                            f"range {point.distance} outside "
                            f"[{config.range_min}, {config.range_max}]"
                        ),
                        **base,
                    )
                )
                continue
            gx, gy = sensor_to_global(
                point.angle, point.distance, config.mount, pose
            )
            cell_x, cell_y = grid_cell(gx, gy, config)
            result.points.append(
                PointRecord(
                    accepted=True,
                    x=gx,
                    y=gy,
                    cell_x=cell_x,
                    cell_y=cell_y,
                    **base,
                )
            )
            stats = result.cells.setdefault((cell_x, cell_y), CellStats())
            stats.count += 1
            stats.sum_x += gx
            stats.sum_y += gy
    return result
