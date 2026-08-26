"""Tests for Fusion-independent involute sampling."""

import math
import unittest

from ..core import (
    build_tooth_flanks,
    build_gear_outline,
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

    def test_tooth_becomes_narrower_toward_addendum(self):
        flanks = build_tooth_flanks(self.geometry, 20, 0.15)
        corrected_pitch_half_angle = (
            math.pi / 40
            - 0.15 / (2 * self.geometry.pitch_radius_mm)
        )
        addendum_half_angle = abs(math.atan2(
            flanks.left[-1].y_mm,
            flanks.left[-1].x_mm,
        ))

        self.assertLess(addendum_half_angle, corrected_pitch_half_angle)

    def test_radius_below_base_is_rejected(self):
        with self.assertRaises(ValueError):
            involute_parameter_at_radius(
                self.geometry.base_radius_mm,
                self.geometry.base_radius_mm - 0.01,
            )

    def test_complete_outline_is_explicitly_closed(self):
        outline = build_gear_outline(self.geometry, 20, 0.15)

        self.assertGreater(len(outline.points), 20 * 20)
        self.assertEqual(outline.points[0], outline.points[-1])

    def test_outline_stays_between_root_and_addendum_radii(self):
        outline = build_gear_outline(self.geometry, 20, 0.15)

        radii = [point_radius_mm(point) for point in outline.points]
        self.assertGreaterEqual(min(radii), self.geometry.root_radius_mm - 1e-9)
        self.assertLessEqual(max(radii), self.geometry.addendum_radius_mm + 1e-9)

    def test_outline_has_no_zero_length_segments(self):
        outline = build_gear_outline(self.geometry, 20, 0.15)

        for start, end in zip(outline.points, outline.points[1:]):
            segment_length = math.hypot(
                end.x_mm - start.x_mm,
                end.y_mm - start.y_mm,
            )
            self.assertGreater(segment_length, 1e-9)


if __name__ == '__main__':
    unittest.main()
