"""Tests for spur-gear and gear-train calculations."""

import math
import unittest

from ..core import (
    GearStandard,
    GearTrainSpec,
    RotationDirection,
    StageInput,
    calculate_center_distance_mm,
    calculate_gear_geometry,
    calculate_placements,
    calculate_stage_results,
    calculate_total_ratio,
    derive_gears,
    output_rotation_direction,
)


def make_spec(stages, bores=None):
    stage_tuple = tuple(StageInput(*stage) for stage in stages)
    if bores is None:
        bores = (5.0,) * (len(stage_tuple) + 1)
    return GearTrainSpec(
        standard=GearStandard(
            module_mm=1.0,
            pressure_angle_rad=math.radians(20),
            face_width_mm=8.0,
            backlash_mm=0.15,
        ),
        stages=stage_tuple,
        shaft_bores_mm=tuple(bores),
    )


class GearGeometryTests(unittest.TestCase):
    def test_reference_radii_for_module_one_twenty_teeth(self):
        geometry = calculate_gear_geometry(1.0, 20, math.radians(20))

        self.assertAlmostEqual(geometry.pitch_radius_mm, 10.0)
        self.assertAlmostEqual(geometry.base_radius_mm, 10.0 * math.cos(math.radians(20)))
        self.assertAlmostEqual(geometry.addendum_radius_mm, 11.0)
        self.assertAlmostEqual(geometry.root_radius_mm, 8.75)

    def test_center_distance_for_twenty_and_forty_teeth(self):
        self.assertAlmostEqual(calculate_center_distance_mm(1.0, 20, 40), 30.0)

    def test_reference_outside_diameter_is_twenty_two_millimetres(self):
        geometry = calculate_gear_geometry(1.0, 20, math.radians(20))

        self.assertAlmostEqual(2 * geometry.addendum_radius_mm, 22.0)


class GearTrainCalculationTests(unittest.TestCase):
    def test_single_stage_ratio_and_direction(self):
        spec = make_spec(((20, 40),))

        self.assertAlmostEqual(calculate_stage_results(spec)[0].ratio, 2.0)
        self.assertAlmostEqual(calculate_total_ratio(spec.stages), 2.0)
        self.assertEqual(output_rotation_direction(1), RotationDirection.OPPOSITE)

    def test_two_stage_ratio_and_direction(self):
        spec = make_spec(((15, 45), (18, 54)))

        self.assertAlmostEqual(calculate_total_ratio(spec.stages), 9.0)
        self.assertEqual(output_rotation_direction(2), RotationDirection.SAME)

    def test_gear_and_shaft_count_for_one_through_four_stages(self):
        for stage_count in range(1, 5):
            with self.subTest(stage_count=stage_count):
                spec = make_spec(((20, 40),) * stage_count)
                gears = derive_gears(spec)

                self.assertEqual(len(gears), 2 * stage_count)
                self.assertEqual(
                    {gear.shaft_index for gear in gears},
                    set(range(stage_count + 1)),
                )

    def test_compound_gears_share_intermediate_shaft(self):
        gears = derive_gears(make_spec(((15, 45), (18, 54))))

        self.assertEqual(gears[1].shaft_index, 1)
        self.assertEqual(gears[2].shaft_index, 1)
        self.assertEqual(gears[1].bore_diameter_mm, gears[2].bore_diameter_mm)

    def test_generated_gear_names_are_stable(self):
        gears = derive_gears(make_spec(((15, 45),)))

        self.assertEqual(gears[0].id, 'PGW_S1_Driver_Z15')
        self.assertEqual(gears[1].id, 'PGW_S1_Driven_Z45')


class PlacementTests(unittest.TestCase):
    def test_horizontal_placement_uses_center_distances(self):
        placements = calculate_placements(make_spec(((15, 45), (18, 54))))

        self.assertEqual((placements[0].x_mm, placements[0].y_mm), (0.0, 0.0))
        self.assertEqual((placements[1].x_mm, placements[1].y_mm), (30.0, 0.0))
        self.assertEqual((placements[2].x_mm, placements[2].y_mm), (30.0, 0.0))
        self.assertEqual((placements[3].x_mm, placements[3].y_mm), (66.0, 0.0))

    def test_vertical_placement_uses_y_axis(self):
        placements = calculate_placements(make_spec(((20, 40),)), vertical=True)

        self.assertEqual((placements[1].x_mm, placements[1].y_mm), (0.0, 30.0))

    def test_successive_stages_use_separate_axial_planes(self):
        placements = calculate_placements(make_spec(((15, 45), (18, 54))))

        self.assertEqual(placements[0].z_mm, 0.0)
        self.assertEqual(placements[1].z_mm, 0.0)
        self.assertEqual(placements[2].z_mm, 9.0)
        self.assertEqual(placements[3].z_mm, 9.0)


if __name__ == '__main__':
    unittest.main()
