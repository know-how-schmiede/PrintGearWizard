"""Tests for blocking and advisory gear-train validation."""

import math
import unittest

from ..core import (
    GearStandard,
    GearTrainSpec,
    StageInput,
    ValidationSeverity,
    has_errors,
    validate_gear_train,
)


def make_spec(
    *,
    module_mm=1.0,
    backlash_mm=0.15,
    stages=((20, 40),),
    bores=(5.0, 5.0),
):
    return GearTrainSpec(
        standard=GearStandard(
            module_mm=module_mm,
            pressure_angle_rad=math.radians(20),
            face_width_mm=8.0,
            backlash_mm=backlash_mm,
        ),
        stages=tuple(StageInput(*stage) for stage in stages),
        shaft_bores_mm=tuple(bores),
    )


class ValidationTests(unittest.TestCase):
    def assert_error_contains(self, spec, text):
        errors = [
            issue.message
            for issue in validate_gear_train(spec)
            if issue.severity == ValidationSeverity.ERROR
        ]
        self.assertTrue(any(text in message for message in errors), errors)

    def test_reference_spec_is_valid(self):
        issues = validate_gear_train(make_spec())

        self.assertFalse(has_errors(issues), issues)

    def test_stage_count_outside_one_to_four_is_rejected(self):
        self.assert_error_contains(make_spec(stages=(), bores=(5.0,)), 'between 1 and 4')

    def test_non_positive_module_is_rejected(self):
        self.assert_error_contains(make_spec(module_mm=0.0), 'greater than zero')

    def test_incorrect_bore_count_is_rejected(self):
        self.assert_error_contains(make_spec(bores=(5.0,)), 'bore values')

    def test_oversized_bore_is_rejected(self):
        self.assert_error_contains(make_spec(bores=(20.0, 5.0)), 'wall at the root')

    def test_excessive_backlash_is_rejected(self):
        self.assert_error_contains(
            make_spec(backlash_mm=2.0),
            'complete tooth thickness',
        )

    def test_low_tooth_count_warns_but_remains_executable(self):
        issues = validate_gear_train(make_spec(stages=((15, 40),)))

        self.assertFalse(has_errors(issues))
        self.assertTrue(
            any(
                issue.severity == ValidationSeverity.WARNING
                and 'fewer than 17 teeth' in issue.message
                for issue in issues
            )
        )

    def test_small_module_produces_printability_warning(self):
        issues = validate_gear_train(
            make_spec(module_mm=0.4, bores=(1.0, 1.0))
        )

        self.assertTrue(any('difficult to print' in issue.message for issue in issues))

    def test_shaft_clearance_intruding_into_unrelated_gear_is_rejected(self):
        spec = make_spec(
            stages=((20, 100), (20, 20)),
            bores=(5.0, 5.0, 5.0),
        )

        self.assert_error_contains(spec, 'Shaft 3 plus 1.0 mm clearance intrudes')


if __name__ == '__main__':
    unittest.main()
