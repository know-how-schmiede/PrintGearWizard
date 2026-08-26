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
    'RotationDirection',
    'StageInput',
    'StageResult',
]
