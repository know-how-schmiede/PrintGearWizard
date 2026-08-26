"""Validation rules for PrintGearWizard domain input."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi

from .calculations import calculate_gear_geometry, calculate_layout_plan
from .models import GearTrainSpec


MIN_STAGE_COUNT = 1
MAX_STAGE_COUNT = 4
MIN_TEETH = 4
RECOMMENDED_MIN_TEETH = 17
MIN_WALL_MM = 1.2


class ValidationSeverity(str, Enum):
    """Severity of a validation issue."""

    ERROR = 'error'
    WARNING = 'warning'


@dataclass(frozen=True)
class ValidationIssue:
    """One actionable validation result."""

    severity: ValidationSeverity
    message: str
    field_id: str = ''


def validate_gear_train(spec: GearTrainSpec) -> tuple[ValidationIssue, ...]:
    """Return blocking errors and non-blocking warnings for a normalized spec."""

    issues = []
    stage_count = len(spec.stages)
    if not MIN_STAGE_COUNT <= stage_count <= MAX_STAGE_COUNT:
        _error(issues, 'Number of stages must be between 1 and 4.', 'stageCount')

    standard = spec.standard
    if standard.module_mm <= 0:
        _error(issues, 'Module must be greater than zero.', 'module')
    if not 0 < standard.pressure_angle_rad < pi / 2:
        _error(issues, 'Pressure angle must be between 0 and 90 degrees.', 'pressureAngle')
    if standard.face_width_mm <= 0:
        _error(issues, 'Gear width must be greater than zero.', 'faceWidth')
    if standard.backlash_mm < 0:
        _error(issues, 'Backlash cannot be negative.', 'backlash')
    if standard.involute_samples < 2:
        _error(issues, 'At least two involute samples are required.')

    expected_bore_count = stage_count + 1
    if len(spec.shaft_bores_mm) != expected_bore_count:
        _error(
            issues,
            f'Exactly {expected_bore_count} shaft bore values are required.',
        )

    if standard.module_mm > 0:
        if standard.module_mm < 0.5:
            _warning(issues, 'Module below 0.5 mm may be difficult to print.', 'module')
        if standard.backlash_mm < 0.05:
            _warning(issues, 'Backlash below 0.05 mm may be too small for printing.', 'backlash')
        if standard.backlash_mm > 0.5 * standard.module_mm:
            _warning(issues, 'Backlash is unusually large for the selected module.', 'backlash')

    for shaft_index, bore_mm in enumerate(spec.shaft_bores_mm):
        if bore_mm <= 0:
            _error(
                issues,
                f'Shaft {shaft_index + 1} bore must be greater than zero.',
                f'shaftBore_{shaft_index}',
            )

    for stage_index, stage in enumerate(spec.stages, start=1):
        _validate_gear(
            issues,
            spec,
            stage_index,
            'driver',
            stage.driver_teeth,
            stage_index - 1,
        )
        _validate_gear(
            issues,
            spec,
            stage_index,
            'driven',
            stage.driven_teeth,
            stage_index,
        )

    if not any(issue.severity == ValidationSeverity.ERROR for issue in issues):
        for message in calculate_layout_plan(spec).warnings:
            _warning(issues, message, 'layoutDirection')

    return tuple(issues)


def has_errors(issues: tuple[ValidationIssue, ...]) -> bool:
    """Return whether a validation result contains a blocking issue."""

    return any(issue.severity == ValidationSeverity.ERROR for issue in issues)


def _validate_gear(
    issues: list[ValidationIssue],
    spec: GearTrainSpec,
    stage_index: int,
    role: str,
    teeth: int,
    shaft_index: int,
):
    field_id = f'{role}Teeth_{stage_index}'
    label = f'Stage {stage_index} {role}'
    if teeth < MIN_TEETH:
        _error(issues, f'{label} must have at least {MIN_TEETH} teeth.', field_id)
        return
    if teeth < RECOMMENDED_MIN_TEETH:
        _warning(
            issues,
            f'{label} has fewer than {RECOMMENDED_MIN_TEETH} teeth; undercut may occur.',
            field_id,
        )

    standard = spec.standard
    if standard.module_mm <= 0 or not 0 < standard.pressure_angle_rad < pi / 2:
        return

    geometry = calculate_gear_geometry(
        standard.module_mm,
        teeth,
        standard.pressure_angle_rad,
    )
    if geometry.root_radius_mm <= 0:
        _error(issues, f'{label} has a non-positive root radius.', field_id)
        return
    if geometry.addendum_radius_mm < geometry.base_radius_mm:
        _error(issues, f'{label} has no real involute endpoint.', field_id)

    pitch_half_angle = pi / (2 * teeth)
    corrected_half_angle = pitch_half_angle - (
        standard.backlash_mm / (2 * geometry.pitch_radius_mm)
    )
    if corrected_half_angle <= 0:
        _error(issues, f'{label} backlash removes the complete tooth thickness.', 'backlash')

    if shaft_index >= len(spec.shaft_bores_mm):
        return
    bore_radius_mm = spec.shaft_bores_mm[shaft_index] / 2.0
    safety_wall_mm = max(MIN_WALL_MM, 1.5 * standard.module_mm)
    if bore_radius_mm + safety_wall_mm >= geometry.root_radius_mm:
        _error(
            issues,
            f'{label} bore leaves less than {safety_wall_mm:.2f} mm wall at the root.',
            f'shaftBore_{shaft_index}',
        )

    if 2 * geometry.addendum_radius_mm > 300:
        _warning(issues, f'{label} outside diameter exceeds 300 mm.', field_id)


def _error(issues: list[ValidationIssue], message: str, field_id: str = ''):
    issues.append(ValidationIssue(ValidationSeverity.ERROR, message, field_id))


def _warning(issues: list[ValidationIssue], message: str, field_id: str = ''):
    issues.append(ValidationIssue(ValidationSeverity.WARNING, message, field_id))
