"""Pure calculations for external spur gears and linear gear trains."""

from __future__ import annotations

from math import cos, pi, prod

from .models import (
    GearGeometry,
    GearPlacement,
    GearSpec,
    GearTrainSpec,
    RotationDirection,
    StageInput,
    StageResult,
)


AXIAL_GAP_MM = 1.0


def calculate_gear_geometry(
    module_mm: float,
    teeth: int,
    pressure_angle_rad: float,
) -> GearGeometry:
    """Return the standard reference radii for one external spur gear."""

    pitch_radius_mm = module_mm * teeth / 2.0
    return GearGeometry(
        pitch_radius_mm=pitch_radius_mm,
        base_radius_mm=pitch_radius_mm * cos(pressure_angle_rad),
        addendum_radius_mm=pitch_radius_mm + module_mm,
        root_radius_mm=pitch_radius_mm - 1.25 * module_mm,
    )


def calculate_center_distance_mm(
    module_mm: float,
    driver_teeth: int,
    driven_teeth: int,
) -> float:
    """Return the center distance of two external gears with equal module."""

    return module_mm * (driver_teeth + driven_teeth) / 2.0


def calculate_stage_result(module_mm: float, stage: StageInput) -> StageResult:
    """Return ratio and center distance for one stage."""

    return StageResult(
        ratio=stage.driven_teeth / stage.driver_teeth,
        center_distance_mm=calculate_center_distance_mm(
            module_mm,
            stage.driver_teeth,
            stage.driven_teeth,
        ),
    )


def calculate_stage_results(spec: GearTrainSpec) -> tuple[StageResult, ...]:
    """Calculate all stages without reading Fusion command inputs."""

    return tuple(
        calculate_stage_result(spec.standard.module_mm, stage)
        for stage in spec.stages
    )


def calculate_total_ratio(stages: tuple[StageInput, ...]) -> float:
    """Return the product of all stage ratios."""

    return prod(stage.driven_teeth / stage.driver_teeth for stage in stages)


def output_rotation_direction(stage_count: int) -> RotationDirection:
    """Return output direction relative to input for external gear meshes."""

    if stage_count % 2 == 0:
        return RotationDirection.SAME
    return RotationDirection.OPPOSITE


def derive_gears(spec: GearTrainSpec) -> tuple[GearSpec, ...]:
    """Derive two physical gears per stage and assign them to shafts."""

    gears = []
    for stage_index, stage in enumerate(spec.stages, start=1):
        driver_shaft_index = stage_index - 1
        driven_shaft_index = stage_index
        gears.extend(
            (
                GearSpec(
                    id=f'PGW_S{stage_index}_Driver_Z{stage.driver_teeth}',
                    stage_index=stage_index,
                    role='driver',
                    teeth=stage.driver_teeth,
                    shaft_index=driver_shaft_index,
                    bore_diameter_mm=spec.shaft_bores_mm[driver_shaft_index],
                ),
                GearSpec(
                    id=f'PGW_S{stage_index}_Driven_Z{stage.driven_teeth}',
                    stage_index=stage_index,
                    role='driven',
                    teeth=stage.driven_teeth,
                    shaft_index=driven_shaft_index,
                    bore_diameter_mm=spec.shaft_bores_mm[driven_shaft_index],
                ),
            )
        )
    return tuple(gears)


def calculate_placements(
    spec: GearTrainSpec,
    *,
    vertical: bool = False,
    axial_gap_mm: float = AXIAL_GAP_MM,
) -> tuple[GearPlacement, ...]:
    """Place shafts linearly and stack successive mesh planes along Z."""

    stage_results = calculate_stage_results(spec)
    shaft_offsets_mm = [0.0]
    for result in stage_results:
        shaft_offsets_mm.append(shaft_offsets_mm[-1] + result.center_distance_mm)

    placements = []
    for gear in derive_gears(spec):
        offset_mm = shaft_offsets_mm[gear.shaft_index]
        # Alternate stages between two axial planes. This keeps compound gears
        # on separate planes while limiting the complete train to two layers.
        stage_plane_mm = ((gear.stage_index - 1) % 2) * (
            spec.standard.face_width_mm + axial_gap_mm
        )
        tooth_pitch_rad = 2 * pi / gear.teeth
        rotation_rad = 0.0
        if gear.role == 'driven':
            # Put a tooth gap, rather than a tooth center, on the line of
            # centers opposite the stage driver.
            rotation_rad = (pi - tooth_pitch_rad / 2.0) % tooth_pitch_rad
        placements.append(
            GearPlacement(
                gear_id=gear.id,
                x_mm=0.0 if vertical else offset_mm,
                y_mm=offset_mm if vertical else 0.0,
                z_mm=stage_plane_mm,
                rotation_rad=rotation_rad,
            )
        )
    return tuple(placements)
