"""Command line entry point for offline scan registration."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .poses import load_poses
from .registration import RegistrationConfig, register_scans
from .scans import load_scans


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="planar-scan-registration",
        description="Stitch planar rangefinder scans into a shared global frame.",
    )
    parser.add_argument("--poses", required=True, help="CSV pose log")
    parser.add_argument("--scans", required=True, help="JSONL scan records")
    parser.add_argument("--out-dir", required=True, help="output directory")
    parser.add_argument("--sensor-x", type=float, default=0.0,
                        help="sensor translation along body x (m)")
    parser.add_argument("--sensor-y", type=float, default=0.0,
                        help="sensor translation along body y (m)")
    parser.add_argument("--sensor-rotation-deg", type=float, default=0.0,
                        help="sensor rotation relative to body (deg, CCW)")
    parser.add_argument("--range-min", type=float, default=0.0,
                        help="minimum valid range (m, inclusive)")
    parser.add_argument("--range-max", type=float, default=float("inf"),
                        help="maximum valid range (m, inclusive)")
    parser.add_argument("--grid-origin-x", type=float, default=0.0,
                        help="grid origin x (m)")
    parser.add_argument("--grid-origin-y", type=float, default=0.0,
                        help="grid origin y (m)")
    parser.add_argument("--grid-cell-size", type=float, default=1.0,
                        help="grid cell edge length (m, positive)")
    return parser


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = RegistrationConfig(
        sensor_x=args.sensor_x,
        sensor_y=args.sensor_y,
        sensor_rotation_deg=args.sensor_rotation_deg,
        range_min=args.range_min,
        range_max=args.range_max,
        grid_origin_x=args.grid_origin_x,
        grid_origin_y=args.grid_origin_y,
        grid_cell_size=args.grid_cell_size,
    )
    try:
        poses = load_poses(args.poses)
        scans = load_scans(args.scans)
        result = register_scans(poses, scans, config)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        out_dir / "points.csv",
        ["time", "angle_deg", "range_m", "x", "y", "cell_ix", "cell_iy"],
        [[p.time, p.angle_deg, p.range_m, p.x, p.y, p.cell[0], p.cell[1]]
         for p in result.points],
    )
    _write_csv(
        out_dir / "rejected.csv",
        ["time", "angle_deg", "range_m", "reason"],
        [[r.time, r.angle_deg, r.range_m, r.reason] for r in result.rejected],
    )
    _write_csv(
        out_dir / "cells.csv",
        ["cell_ix", "cell_iy", "count", "centroid_x", "centroid_y"],
        [[c.cell[0], c.cell[1], c.count, c.centroid_x, c.centroid_y]
         for c in result.cells],
    )
    print(
        f"registered {len(result.points)} points, "
        f"rejected {len(result.rejected)}, "
        f"{len(result.cells)} occupied cells -> {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
