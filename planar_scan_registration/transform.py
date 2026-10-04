"""Coordinate transforms: sensor -> body -> global."""

from __future__ import annotations

import math
from typing import Tuple

from .model import Pose, SensorMount


def sensor_to_body(
    angle_deg: float, distance: float, mount: SensorMount
) -> Tuple[float, float]:
    """Convert a polar ranging sample into body-frame coordinates.

    Applies the mount rotation first, then the mount translation.
    """
    heading = math.radians(angle_deg + mount.rotation)
    x = mount.x + distance * math.cos(heading)
    y = mount.y + distance * math.sin(heading)
    return x, y


def body_to_global(x: float, y: float, pose: Pose) -> Tuple[float, float]:
    """Apply the interpolated body pose: rotate by heading, then translate."""
    heading = math.radians(pose.theta)
    cos_h = math.cos(heading)
    sin_h = math.sin(heading)
    gx = pose.x + x * cos_h - y * sin_h
    gy = pose.y + x * sin_h + y * cos_h
    return gx, gy


def sensor_to_global(
    angle_deg: float, distance: float, mount: SensorMount, pose: Pose
) -> Tuple[float, float]:
    """Full chain: polar sample -> body frame -> global frame."""
    bx, by = sensor_to_body(angle_deg, distance, mount)
    return body_to_global(bx, by, pose)
