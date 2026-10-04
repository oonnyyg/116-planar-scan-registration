import unittest

from planar_scan_registration.model import Pose, SensorMount
from planar_scan_registration.transform import sensor_to_global


class TransformTest(unittest.TestCase):
    def test_identity(self):
        mount = SensorMount()
        pose = Pose(time=0.0, x=0.0, y=0.0, theta=0.0)
        gx, gy = sensor_to_global(0.0, 2.0, mount, pose)
        self.assertAlmostEqual(gx, 2.0)
        self.assertAlmostEqual(gy, 0.0)

    def test_nonzero_mount_offset_and_rotation(self):
        # Ranger mounted 0.5 m ahead, rotated +90 deg; body at (1, 2),
        # heading 0. Sample at sensor angle 0, range 1.
        mount = SensorMount(x=0.5, y=0.0, rotation=90.0)
        pose = Pose(time=0.0, x=1.0, y=2.0, theta=0.0)
        gx, gy = sensor_to_global(0.0, 1.0, mount, pose)
        self.assertAlmostEqual(gx, 1.5)
        self.assertAlmostEqual(gy, 3.0)

    def test_transform_order_matters(self):
        # Mount offset is rotated by the body heading, not added after.
        mount = SensorMount(x=1.0, y=0.0, rotation=0.0)
        pose = Pose(time=0.0, x=0.0, y=0.0, theta=90.0)
        gx, gy = sensor_to_global(0.0, 1.0, mount, pose)
        # Body-frame point (2, 0) rotated by +90 deg -> (0, 2).
        self.assertAlmostEqual(gx, 0.0, places=12)
        self.assertAlmostEqual(gy, 2.0, places=12)

    def test_body_rotation_applies_to_sample(self):
        mount = SensorMount()
        pose = Pose(time=0.0, x=1.0, y=1.0, theta=180.0)
        gx, gy = sensor_to_global(0.0, 1.0, mount, pose)
        self.assertAlmostEqual(gx, 0.0, places=12)
        self.assertAlmostEqual(gy, 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
