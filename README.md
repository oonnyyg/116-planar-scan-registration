# Planar Scan Registration

Offline tool that stitches multiple scans from a mobile ranging sensor into
a common planar coordinate frame using a known pose log. Pure Python
standard library; no localization or map optimization is performed.

## Coordinate Conventions

- Units: seconds for time, meters for distance, degrees for angles.
- Heading zero points along the positive X axis; positive angles rotate
  counterclockwise.
- Transform chain per sample: polar sample -> body frame (mount rotation,
  then mount translation) -> global frame (pose rotation, then pose
  translation). The two transforms are never swapped.
- Grid binning: `cell = floor((coord - origin) / cell_size)`, so negative
  coordinates floor away from zero (no truncation toward zero).

## Input Formats

### Pose log (CSV)

Header `time,x,y,theta`; one pose per row. Times must be strictly
increasing and all values finite.

```csv
time,x,y,theta
0.0,0.0,0.0,0.0
1.0,1.0,0.0,90.0
```

### Scan records (JSONL)

One JSON object per line: `{"time": <s>, "points": [[angle_deg, range_m], ...]}`.
Empty `points` lists are allowed and produce no output points.

### Configuration (JSON)

```json
{
  "mount": {"x": 0.2, "y": 0.1, "rotation": 10.0},
  "range_min": 0.5,
  "range_max": 5.0,
  "grid_origin": [0.0, 0.0],
  "cell_size": 1.0
}
```

- `mount`: sensor translation (m) and rotation (deg) relative to the body.
- `range_min` / `range_max`: valid range as a closed interval; samples
  outside it are rejected with a recorded reason.
- `grid_origin`, `cell_size`: grid origin (m) and positive cell edge (m).

## Interpolation and Rejection Rules

- Scan times inside the pose time range interpolate position linearly and
  heading along the shortest angular difference; an exact 180 degree
  difference resolves counterclockwise.
- Scan times outside the pose range are rejected explicitly
  (`time outside pose range`); there is no extrapolation and no silent
  snapping to the nearest pose.

## Usage

```sh
python -m planar_scan_registration \
    --poses poses.csv --scans scans.jsonl --config config.json --out-dir out
```

Outputs in `--out-dir`:

- `points.csv`: one row per input point (stable input order) with global
  coordinates, grid cell, acceptance flag, and rejection reason.
- `cells.csv`: per-cell point count and centroid, sorted by
  `(cell_x, cell_y)`.

Processing is deterministic: the same inputs always produce identical
outputs.

## Tests

```sh
python -m unittest discover -s tests
```
