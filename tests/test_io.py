import tempfile
import unittest
from pathlib import Path

from planar_scan_registration.poses import load_poses
from planar_scan_registration.scans import load_scans


def write_tmp(text):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".tmp", delete=False, encoding="utf-8"
    )
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


class PoseLoadTest(unittest.TestCase):
    def test_valid_poses(self):
        path = write_tmp("time,x,y,heading_deg\n0,0,0,0\n1,1.5,2,90\n")
        poses = load_poses(path)
        self.assertEqual(len(poses), 2)
        self.assertEqual(poses[1].heading_deg, 90.0)

    def test_non_increasing_times_rejected(self):
        path = write_tmp("time,x,y,heading_deg\n0,0,0,0\n0,1,1,1\n")
        with self.assertRaises(ValueError):
            load_poses(path)

    def test_non_finite_rejected(self):
        path = write_tmp("time,x,y,heading_deg\n0,nan,0,0\n")
        with self.assertRaises(ValueError):
            load_poses(path)


class ScanLoadTest(unittest.TestCase):
    def test_valid_scans(self):
        path = write_tmp('{"time": 0.5, "angle_deg": 10, "range_m": 1.2}\n')
        scans = load_scans(path)
        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0].range_m, 1.2)

    def test_non_finite_rejected(self):
        path = write_tmp('{"time": 0.5, "angle_deg": 10, "range_m": "inf"}\n')
        with self.assertRaises(ValueError):
            load_scans(path)

    def test_missing_field_rejected(self):
        path = write_tmp('{"time": 0.5, "angle_deg": 10}\n')
        with self.assertRaises(ValueError):
            load_scans(path)


if __name__ == "__main__":
    unittest.main()
