"""Pose interpolation within the logged time range."""

from __future__ import annotations

import bisect

from .poses import Pose


def _angle_delta_ccw_deg(start: float, end: float) -> float:
    """Shortest signed angular difference end - start in (-180, 180].

    A difference of exactly 180 degrees resolves to +180 (counterclockwise).
    """
    delta = (end - start) % 360.0
    if delta > 180.0:
        delta -= 360.0
    return delta


def interpolate_pose(poses: list[Pose], time: float) -> Pose:
    """Interpolate the pose at ``time`` between bracketing samples.

    Position is linear; heading follows the shortest angular difference,
    counterclockwise when the samples differ by exactly 180 degrees.
    Times outside the logged range are rejected (no extrapolation).
    """
    if not poses:
        raise ValueError("no poses available")
    if time < poses[0].time or time > poses[-1].time:
        raise ValueError(
            f"time {time} outside pose range "
            f"[{poses[0].time}, {poses[-1].time}]"
        )
    times = [p.time for p in poses]
    idx = bisect.bisect_left(times, time)
    if times[idx] == time:
        return poses[idx]
    before, after = poses[idx - 1], poses[idx]
    span = after.time - before.time
    ratio = (time - before.time) / span
    x = before.x + ratio * (after.x - before.x)
    y = before.y + ratio * (after.y - before.y)
    delta = _angle_delta_ccw_deg(before.heading_deg, after.heading_deg)
    heading = before.heading_deg + ratio * delta
    return Pose(time=time, x=x, y=y, heading_deg=heading)
