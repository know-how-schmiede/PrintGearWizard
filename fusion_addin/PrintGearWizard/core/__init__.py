"""Fusion-independent domain logic for PrintGearWizard."""

from .calculations import (
    calculate_center_distance_mm,
    calculate_gear_geometry,
    calculate_placements,
    calculate_stage_result,
    calculate_stage_results,
    calculate_total_ratio,
    derive_gears,
    output_rotation_direction,
)
from .models import (
    GearGeometry,
    GearPlacement,
    GearSpec,
    GearStandard,
    GearTrainSpec,
    RotationDirection,
    StageInput,
    StageResult,
)
from .involute import (
    Point2D,
    ToothFlanks,
    build_tooth_flanks,
    involute_parameter_at_radius,
    involute_point,
    point_radius_mm,
    rotate_point,
    sample_involute,
)
from .validation import (
    ValidationIssue,
    ValidationSeverity,
    has_errors,
    validate_gear_train,
)

__all__ = [
    'calculate_center_distance_mm',
    'calculate_gear_geometry',
    'calculate_placements',
    'calculate_stage_result',
    'calculate_stage_results',
    'calculate_total_ratio',
    'derive_gears',
    'GearGeometry',
    'GearPlacement',
    'GearSpec',
    'GearStandard',
    'GearTrainSpec',
    'output_rotation_direction',
    'Point2D',
    'ToothFlanks',
    'build_tooth_flanks',
    'involute_parameter_at_radius',
    'involute_point',
    'point_radius_mm',
    'rotate_point',
    'sample_involute',
    'RotationDirection',
    'StageInput',
    'StageResult',
    'ValidationIssue',
    'ValidationSeverity',
    'has_errors',
    'validate_gear_train',
]
