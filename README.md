# Planar Scan Registration

Offline tool that stitches multiple 2D rangefinder scans into a shared
planar coordinate frame using a known pose log. Pure Python standard
library; no localization or map optimization is performed.

## Coordinate Conventions

- Units: seconds and meters. Angles are degrees, counterclockwise
  positive, zero pointing along the +x axis.
- Frames: sensor -> body -> global. The sensor mount (translation +
  rotation, expressed in the body frame) is applied first, then the
  interpolated body pose. The two transforms are never swapped.
- Pose interpolation: position is linear between bracketing samples;
  heading follows the shortest angular difference, resolving an exact
  180-degree difference counterclockwise. Scan times outside the pose
  time range are rejected (no extrapolation, no nearest-pose fallback).
- Grid: cell index = floor((coordinate - origin) / cell_size), so
  negative coordinates floor away from zero (never truncated).

## Input Formats

Pose log (CSV, header required, times strictly increasing, all values
finite):

```csv
time,x,y,heading_deg
0.0,0.0,0.0,0.0
2.0,4.0,0.0,90.0
```

Scan records (JSONL, one object per line, all values finite):

```json
{"time": 1.0, "angle_deg": 45.0, "range_m": 1.2}
```

## Usage

```sh
python -m planar_scan_registration \
    --poses examples/poses.csv --scans examples/scans.jsonl \
    --out-dir out \
    --sensor-x 0.5 --sensor-y 0.0 --sensor-rotation-deg 0.0 \
    --range-min 0.1 --range-max 5.0 \
    --grid-origin-x 0.0 --grid-origin-y 0.0 --grid-cell-size 0.5
```

Installing the project also provides the `planar-scan-registration`
console script with identical options.

## Outputs

Written to `--out-dir`, deterministically sorted (points and rejections
by `(time, angle_deg, range_m)`, cells by `(ix, iy)`), so re-running on
the same input yields identical files:

- `points.csv` — accepted readings: global `x,y`, grid cell, and the
  source `time, angle_deg, range_m`.
- `rejected.csv` — dropped readings with the reason (out of pose time
  range or outside the valid range interval).
- `cells.csv` — per-cell point count and centroid.

Empty scans produce empty outputs, never fabricated points.

## Tests

```sh
python -m unittest discover -s tests
```

Covers interpolation across the 0/360-degree boundary, the 180-degree
tie rule, non-zero sensor mounting offsets, negative-coordinate grid
floor behavior, and rejection paths.
