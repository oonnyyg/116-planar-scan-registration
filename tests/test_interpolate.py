import unittest

from planar_scan_registration.interpolate import (
    _angle_delta_ccw_deg,
    interpolate_pose,
)
from planar_scan_registration.poses import Pose


def make_poses():
    return [
        Pose(time=0.0, x=0.0, y=0.0, heading_deg=0.0),
        Pose(time=1.0, x=2.0, y=4.0, heading_deg=90.0),
        Pose(time=2.0, x=4.0, y=4.0, heading_deg=180.0),
    ]


class AngleDeltaTest(unittest.TestCase):
    def test_wraps_across_boundary_shortest_way(self):
        self.assertAlmostEqual(_angle_delta_ccw_deg(350.0, 10.0), 20.0)
        self.assertAlmostEqual(_angle_delta_ccw_deg(10.0, 350.0), -20.0)

    def test_exactly_180_resolves_counterclockwise(self):
        self.assertAlmostEqual(_angle_delta_ccw_deg(0.0, 180.0), 180.0)
        self.assertAlmostEqual(_angle_delta_ccw_deg(180.0, 0.0), 180.0)


class InterpolatePoseTest(unittest.TestCase):
    def test_linear_position_and_heading(self):
        pose = interpolate_pose(make_poses(), 0.5)
        self.assertAlmostEqual(pose.x, 1.0)
        self.assertAlmostEqual(pose.y, 2.0)
        self.assertAlmostEqual(pose.heading_deg, 45.0)

    def test_exact_sample_returned(self):
        pose = interpolate_pose(make_poses(), 1.0)
        self.assertEqual(pose, make_poses()[1])

    def test_heading_wraps_across_zero(self):
        poses = [
            Pose(time=0.0, x=0.0, y=0.0, heading_deg=350.0),
            Pose(time=1.0, x=0.0, y=0.0, heading_deg=10.0),
        ]
        pose = interpolate_pose(poses, 0.5)
        self.assertAlmostEqual(pose.heading_deg % 360.0, 0.0)

    def test_180_degree_difference_goes_counterclockwise(self):
        poses = [
            Pose(time=0.0, x=0.0, y=0.0, heading_deg=0.0),
            Pose(time=1.0, x=0.0, y=0.0, heading_deg=180.0),
        ]
        pose = interpolate_pose(poses, 0.5)
        self.assertAlmostEqual(pose.heading_deg, 90.0)

    def test_out_of_range_rejected(self):
        poses = make_poses()
        with self.assertRaises(ValueError):
            interpolate_pose(poses, -0.001)
        with self.assertRaises(ValueError):
            interpolate_pose(poses, 2.001)


if __name__ == "__main__":
    unittest.main()
