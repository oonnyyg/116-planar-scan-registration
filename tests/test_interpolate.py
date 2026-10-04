import unittest

from planar_scan_registration.interpolate import (
    interpolate_pose,
    shortest_angle_delta,
)
from planar_scan_registration.model import Pose


def make_poses():
    return [
        Pose(time=0.0, x=0.0, y=0.0, theta=350.0),
        Pose(time=2.0, x=4.0, y=-2.0, theta=10.0),
    ]


class ShortestDeltaTest(unittest.TestCase):
    def test_wraps_across_zero(self):
        self.assertAlmostEqual(shortest_angle_delta(350.0, 10.0), 20.0)
        self.assertAlmostEqual(shortest_angle_delta(10.0, 350.0), -20.0)

    def test_exact_180_goes_counterclockwise(self):
        self.assertAlmostEqual(shortest_angle_delta(0.0, 180.0), 180.0)
        self.assertAlmostEqual(shortest_angle_delta(180.0, 0.0), 180.0)
        self.assertAlmostEqual(shortest_angle_delta(90.0, 270.0), 180.0)


class InterpolateTest(unittest.TestCase):
    def test_midpoint_across_angle_boundary(self):
        pose = interpolate_pose(make_poses(), 1.0)
        self.assertAlmostEqual(pose.x, 2.0)
        self.assertAlmostEqual(pose.y, -1.0)
        self.assertAlmostEqual(pose.theta, 360.0)  # 350 + 0.5 * 20

    def test_exact_pose_times(self):
        poses = make_poses()
        self.assertEqual(interpolate_pose(poses, 0.0), poses[0])
        self.assertEqual(interpolate_pose(poses, 2.0), poses[1])

    def test_out_of_range_rejected(self):
        poses = make_poses()
        self.assertIsNone(interpolate_pose(poses, -0.001))
        self.assertIsNone(interpolate_pose(poses, 2.001))

    def test_180_tie_uses_counterclockwise(self):
        poses = [
            Pose(time=0.0, x=0.0, y=0.0, theta=0.0),
            Pose(time=1.0, x=0.0, y=0.0, theta=180.0),
        ]
        pose = interpolate_pose(poses, 0.5)
        self.assertAlmostEqual(pose.theta, 90.0)


if __name__ == "__main__":
    unittest.main()
