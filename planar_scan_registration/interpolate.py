"""Pose interpolation along a strictly increasing time series."""

from __future__ import annotations

import bisect
from typing import List, Optional

from .model import Pose


def shortest_angle_delta(start: float, end: float) -> float:
    """Shortest signed delta in degrees from start to end, in (-180, 180].

    An exact 180 degree difference resolves to the counterclockwise
    (positive) direction.
    """
    delta = (end - start) % 360.0
    if delta > 180.0:
        delta -= 360.0
    return delta


def interpolate_pose(poses: List[Pose], time: float) -> Optional[Pose]:
    """Interpolate the pose at `time`, or None if outside the pose range.

    Position is linear in time; heading follows the shortest angular
    difference. No extrapolation is performed.
    """
    if not poses or time < poses[0].time or time > poses[-1].time:
        return None
    times = [pose.time for pose in poses]
    index = bisect.bisect_left(times, time)
    if times[index] == time:
        return poses[index]
    before = poses[index - 1]
    after = poses[index]
    span = after.time - before.time
    ratio = (time - before.time) / span
    x = before.x + ratio * (after.x - before.x)
    y = before.y + ratio * (after.y - before.y)
    delta = shortest_angle_delta(before.theta, after.theta)
    theta = before.theta + ratio * delta
    return Pose(time=time, x=x, y=y, theta=theta)
