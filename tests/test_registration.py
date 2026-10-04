import math
import unittest

from planar_scan_registration.poses import Pose
from planar_scan_registration.registration import (
    RegistrationConfig,
    register_scans,
)
from planar_scan_registration.scans import ScanPoint


def stationary_pose(x=0.0, y=0.0, heading=0.0):
    return [
        Pose(time=0.0, x=x, y=y, heading_deg=heading),
        Pose(time=10.0, x=x, y=y, heading_deg=heading),
    ]


class RegistrationTest(unittest.TestCase):
    def test_identity_transform(self):
        result = register_scans(
            stationary_pose(),
            [ScanPoint(time=5.0, angle_deg=90.0, range_m=2.0)],
            RegistrationConfig(),
        )
        self.assertEqual(len(result.points), 1)
        point = result.points[0]
        self.assertAlmostEqual(point.x, 0.0, places=9)
        self.assertAlmostEqual(point.y, 2.0)

    def test_sensor_offset_and_rotation_applied_before_pose(self):
        config = RegistrationConfig(
            sensor_x=1.0, sensor_y=0.0, sensor_rotation_deg=90.0
        )
        result = register_scans(
            stationary_pose(x=10.0, y=0.0, heading=90.0),
            [ScanPoint(time=5.0, angle_deg=0.0, range_m=2.0)],
            config,
        )
        # Sensor frame: (2, 0). Mount rotation 90 deg -> body (0, 2);
        # mount translation -> body (1, 2). Pose heading 90 deg ->
        # global (10 - 2, 0 + 1) = (8, 1).
        point = result.points[0]
        self.assertAlmostEqual(point.x, 8.0)
        self.assertAlmostEqual(point.y, 1.0)

    def test_range_gate_rejects_with_reason(self):
        config = RegistrationConfig(range_min=0.5, range_max=3.0)
        result = register_scans(
            stationary_pose(),
            [
                ScanPoint(time=5.0, angle_deg=0.0, range_m=0.4),
                ScanPoint(time=5.0, angle_deg=0.0, range_m=3.1),
                ScanPoint(time=5.0, angle_deg=0.0, range_m=0.5),
                ScanPoint(time=5.0, angle_deg=0.0, range_m=3.0),
            ],
            config,
        )
        self.assertEqual(len(result.points), 2)
        self.assertEqual(len(result.rejected), 2)
        self.assertIn("range", result.rejected[0].reason)

    def test_out_of_pose_range_rejected(self):
        result = register_scans(
            stationary_pose(),
            [ScanPoint(time=11.0, angle_deg=0.0, range_m=1.0)],
            RegistrationConfig(),
        )
        self.assertEqual(len(result.points), 0)
        self.assertEqual(len(result.rejected), 1)
        self.assertIn("outside pose range", result.rejected[0].reason)

    def test_negative_coordinates_floor_not_truncate(self):
        config = RegistrationConfig(grid_cell_size=1.0)
        result = register_scans(
            stationary_pose(),
            [ScanPoint(time=5.0, angle_deg=225.0, range_m=math.sqrt(0.5))],
            config,
        )
        # Global (-0.5, -0.5) must fall into cell (-1, -1), not (0, 0).
        self.assertEqual(result.points[0].cell, (-1, -1))

    def test_grid_origin_and_cell_stats(self):
        config = RegistrationConfig(
            grid_origin_x=1.0, grid_origin_y=1.0, grid_cell_size=2.0
        )
        result = register_scans(
            stationary_pose(),
            [
                ScanPoint(time=5.0, angle_deg=0.0, range_m=2.0),
                ScanPoint(time=5.0, angle_deg=0.0, range_m=3.0),
            ],
            config,
        )
        # Points at (2, 0) and (3, 0): offsets (1, -1) and (2, -1).
        cells = {p.cell for p in result.points}
        self.assertEqual(cells, {(0, -1), (1, -1)})
        self.assertEqual(len(result.cells), 2)
        for stats in result.cells:
            self.assertEqual(stats.count, 1)

    def test_empty_scans_produce_no_points(self):
        result = register_scans(stationary_pose(), [], RegistrationConfig())
        self.assertEqual(result.points, [])
        self.assertEqual(result.rejected, [])
        self.assertEqual(result.cells, [])

    def test_deterministic_repeat_and_sorted_output(self):
        scans = [
            ScanPoint(time=6.0, angle_deg=0.0, range_m=1.0),
            ScanPoint(time=5.0, angle_deg=90.0, range_m=1.0),
            ScanPoint(time=5.0, angle_deg=0.0, range_m=1.0),
        ]
        first = register_scans(stationary_pose(), scans, RegistrationConfig())
        second = register_scans(stationary_pose(), scans, RegistrationConfig())
        self.assertEqual(first.points, second.points)
        times = [p.time for p in first.points]
        self.assertEqual(times, sorted(times))


if __name__ == "__main__":
    unittest.main()
