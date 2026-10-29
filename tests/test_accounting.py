"""Scientific identities and failure boundaries, not source-specific expected outcomes."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from accounting import decompose, logarithmic_mean


class AccountingIdentities(unittest.TestCase):
    def test_equal_energy_mean(self):
        self.assertEqual(logarithmic_mean(17, 17), 17)
        self.assertAlmostEqual(logarithmic_mean(17, 17.00000001), 17.000000005)

    def test_activity_only(self):
        r = decompose([10, 20], [12, 24], [5, 10], [6, 12])
        self.assertAlmostEqual(r['activity_tj'], 6)
        self.assertAlmostEqual(r['structure_tj'], 0)
        self.assertAlmostEqual(r['intensity_tj'], 0)

    def test_structure_only(self):
        r = decompose([10, 40], [20, 20], [10, 20], [20, 10])
        self.assertAlmostEqual(r['structure_tj'], -10)
        self.assertAlmostEqual(r['activity_tj'], 0)
        self.assertAlmostEqual(r['intensity_tj'], 0)

    def test_intensity_only(self):
        r = decompose([10, 20], [5, 10], [5, 10], [5, 10])
        self.assertAlmostEqual(r['intensity_tj'], -15)
        self.assertAlmostEqual(r['activity_tj'] + r['structure_tj'], 0)

    def test_energy_unit_scaling_and_order(self):
        original = decompose([10, 40, 5], [15, 32, 6], [5, 10, 2], [8, 9, 3])
        scaled = decompose([100, 400, 50], [150, 320, 60], [5, 10, 2], [8, 9, 3])
        reverse = decompose([5, 40, 10], [6, 32, 15], [2, 10, 5], [3, 9, 8])
        for field in original:
            self.assertAlmostEqual(scaled[field], 10 * original[field])
            self.assertAlmostEqual(reverse[field], original[field])

    def test_output_unit_invariance(self):
        a = decompose([10, 20], [12, 15], [5, 10], [6, 9])
        b = decompose([10, 20], [12, 15], [5000, 10000], [6000, 9000])
        for field in a:
            self.assertAlmostEqual(a[field], b[field])

    def test_invalid_values_and_shapes(self):
        for v in (0, -1, math.nan, math.inf):
            with self.subTest(v=v), self.assertRaises(ValueError):
                decompose([v], [1], [1], [1])
        for a in (([], [], [], []), ([1], [1, 2], [1], [1])):
            with self.assertRaises(ValueError):
                decompose(*a)


if __name__ == '__main__':
    unittest.main()
