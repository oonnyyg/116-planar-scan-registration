"""Deterministic CSV export of point records and grid statistics."""

from __future__ import annotations

import csv
import os

from .pipeline import Result

POINT_FIELDS = (
    "scan_index",
    "point_index",
    "time",
    "angle_deg",
    "range_m",
    "accepted",
    "x",
    "y",
    "cell_x",
    "cell_y",
    "reason",
)

CELL_FIELDS = ("cell_x", "cell_y", "count", "centroid_x", "centroid_y")


def _format(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


def export_points(result: Result, path: str) -> None:
    """Write one row per input point, in input order (stable)."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(POINT_FIELDS)
        for record in result.points:
            writer.writerow(
                [
                    record.scan_index,
                    record.point_index,
                    _format(record.time),
                    _format(record.angle),
                    _format(record.distance),
                    "1" if record.accepted else "0",
                    _format(record.x),
                    _format(record.y),
                    _format(record.cell_x),
                    _format(record.cell_y),
                    record.reason,
                ]
            )


def export_cells(result: Result, path: str) -> None:
    """Write per-cell count and centroid, sorted by (cell_x, cell_y)."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CELL_FIELDS)
        for (cell_x, cell_y) in sorted(result.cells):
            stats = result.cells[(cell_x, cell_y)]
            centroid_x, centroid_y = stats.centroid
            writer.writerow(
                [
                    cell_x,
                    cell_y,
                    stats.count,
                    _format(centroid_x),
                    _format(centroid_y),
                ]
            )


def export_all(result: Result, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    export_points(result, os.path.join(out_dir, "points.csv"))
    export_cells(result, os.path.join(out_dir, "cells.csv"))
