"""Command line entry point for planar scan registration."""

from __future__ import annotations

import argparse
import json
import sys

from .export import export_all
from .io import load_poses, load_scans
from .model import Config
from .pipeline import process


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="planar-scan-registration",
        description=(
            "Stitch mobile ranger scans into a common planar frame using "
            "known poses (offline, no localization or map optimization)."
        ),
    )
    parser.add_argument("--poses", required=True, help="pose CSV log")
    parser.add_argument("--scans", required=True, help="scan JSONL records")
    parser.add_argument("--config", required=True, help="JSON configuration")
    parser.add_argument("--out-dir", required=True, help="output directory")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with open(args.config, encoding="utf-8") as handle:
            config = Config.from_dict(json.load(handle))
        poses = load_poses(args.poses)
        scans = load_scans(args.scans)
        result = process(poses, scans, config)
        export_all(result, args.out_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    accepted = sum(1 for p in result.points if p.accepted)
    rejected = len(result.points) - accepted
    print(
        f"processed {len(result.points)} points "
        f"({accepted} accepted, {rejected} rejected), "
        f"{len(result.cells)} occupied cells"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
