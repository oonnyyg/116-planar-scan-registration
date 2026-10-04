import unittest

from planar_scan_registration.model import Config, Pose, Scan, ScanPoint, SensorMount
from planar_scan_registration.pipeline import grid_cell, process


def make_config(**overrides):
    config = Config(
        mount=SensorMount(),
        range_min=0.5,
        range_max=10.0,
        grid_origin_x=0.0,
        grid_origin_y=0.0,
        cell_size=1.0,
    )
    return Config(**{**config.__dict__, **overrides})


POSES = [
    Pose(time=0.0, x=0.0, y=0.0, theta=0.0),
    Pose(time=1.0, x=1.0, y=0.0, theta=0.0),
]


class GridCellTest(unittest.TestCase):
    def test_negative_coordinates_floor_not_truncate(self):
        config = make_config()
        self.assertEqual(grid_cell(-0.1, -1.5, config), (-1, -2))
        self.assertEqual(grid_cell(0.0, 0.0, config), (0, 0))
        self.assertEqual(grid_cell(0.999, 1.0, config), (0, 1))

    def test_origin_offset(self):
        config = make_config(grid_origin_x=10.0, grid_origin_y=-5.0, cell_size=2.0)
        self.assertEqual(grid_cell(10.0, -5.0, config), (0, 0))
        self.assertEqual(grid_cell(9.999, -5.001, config), (-1, -1))


class PipelineTest(unittest.TestCase):
    def test_valid_point_registered(self):
        scans = [Scan(time=0.5, points=(ScanPoint(angle=0.0, distance=2.0),))]
        result = process(POSES, scans, make_config())
        record = result.points[0]
        self.assertTrue(record.accepted)
        self.assertAlmostEqual(record.x, 2.5)
        self.assertAlmostEqual(record.y, 0.0)
        self.assertEqual(result.cells[(2, 0)].count, 1)

    def test_out_of_range_distance_rejected_with_reason(self):
        scans = [
            Scan(
                time=0.5,
                points=(
                    ScanPoint(angle=0.0, distance=0.1),
                    ScanPoint(angle=0.0, distance=99.0),
                ),
            )
        ]
        result = process(POSES, scans, make_config())
        self.assertFalse(result.points[0].accepted)
        self.assertIn("range", result.points[0].reason)
        self.assertFalse(result.points[1].accepted)
        self.assertEqual(len(result.cells), 0)

    def test_scan_outside_pose_range_rejected(self):
        scans = [Scan(time=5.0, points=(ScanPoint(angle=0.0, distance=1.0),))]
        result = process(POSES, scans, make_config())
        self.assertFalse(result.points[0].accepted)
        self.assertIn("pose range", result.points[0].reason)

    def test_empty_scan_makes_no_points(self):
        scans = [Scan(time=0.5, points=())]
        result = process(POSES, scans, make_config())
        self.assertEqual(result.points, [])
        self.assertEqual(result.cells, {})

    def test_deterministic_repeat(self):
        scans = [
            Scan(time=0.25, points=(ScanPoint(angle=30.0, distance=3.0),)),
            Scan(time=0.75, points=(ScanPoint(angle=-45.0, distance=1.5),)),
        ]
        config = make_config()
        first = process(POSES, scans, config)
        second = process(POSES, scans, config)
        self.assertEqual(first.points, second.points)
        self.assertEqual(first.cells, second.cells)

    def test_centroid(self):
        scans = [
            Scan(
                time=0.0,
                points=(
                    ScanPoint(angle=0.0, distance=1.0),
                    ScanPoint(angle=0.0, distance=3.0),
                ),
            )
        ]
        result = process(POSES, scans, make_config(cell_size=10.0))
        stats = result.cells[(0, 0)]
        self.assertEqual(stats.count, 2)
        cx, cy = stats.centroid
        self.assertAlmostEqual(cx, 2.0)
        self.assertAlmostEqual(cy, 0.0)


if __name__ == "__main__":
    unittest.main()
