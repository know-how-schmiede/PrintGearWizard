"""Tests for Fusion-independent involute sampling."""

import math
import unittest

from ..core import (
    build_tooth_flanks,
    calculate_gear_geometry,
    involute_parameter_at_radius,
    involute_point,
    point_radius_mm,
    sample_involute,
)


class InvoluteTests(unittest.TestCase):
    def setUp(self):
        self.geometry = calculate_gear_geometry(1.0, 20, math.radians(20))

    def test_parameter_reaches_requested_radius(self):
        parameter = involute_parameter_at_radius(
            self.geometry.base_radius_mm,
            self.geometry.addendum_radius_mm,
        )
        point = involute_point(self.geometry.base_radius_mm, parameter)

        self.assertAlmostEqual(
            point_radius_mm(point),
            self.geometry.addendum_radius_mm,
        )

    def test_sample_endpoints_lie_on_requested_radii(self):
        start_radius = max(
            self.geometry.root_radius_mm,
            self.geometry.base_radius_mm,
        )
        points = sample_involute(
            self.geometry.base_radius_mm,
            start_radius,
            self.geometry.addendum_radius_mm,
            12,
        )

        self.assertEqual(len(points), 12)
        self.assertAlmostEqual(point_radius_mm(points[0]), start_radius)
        self.assertAlmostEqual(
            point_radius_mm(points[-1]),
            self.geometry.addendum_radius_mm,
        )

    def test_generated_flanks_are_symmetric(self):
        flanks = build_tooth_flanks(self.geometry, 20, 0.15)

        for left, right in zip(flanks.left, flanks.right):
            self.assertAlmostEqual(left.x_mm, right.x_mm)
            self.assertAlmostEqual(left.y_mm, -right.y_mm)

    def test_backlash_reduces_pitch_circle_tooth_thickness(self):
        without_backlash = build_tooth_flanks(self.geometry, 20, 0.0)
        with_backlash = build_tooth_flanks(self.geometry, 20, 0.15)
        pitch_index = min(
            range(len(with_backlash.left)),
            key=lambda index: abs(
                point_radius_mm(with_backlash.left[index])
                - self.geometry.pitch_radius_mm
            ),
        )

        self.assertLess(
            abs(math.atan2(
                with_backlash.left[pitch_index].y_mm,
                with_backlash.left[pitch_index].x_mm,
            )),
            abs(math.atan2(
                without_backlash.left[pitch_index].y_mm,
                without_backlash.left[pitch_index].x_mm,
            )),
        )

    def test_radius_below_base_is_rejected(self):
        with self.assertRaises(ValueError):
            involute_parameter_at_radius(
                self.geometry.base_radius_mm,
                self.geometry.base_radius_mm - 0.01,
            )


if __name__ == '__main__':
    unittest.main()
