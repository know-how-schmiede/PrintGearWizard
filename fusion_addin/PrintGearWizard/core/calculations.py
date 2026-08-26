"""Pure calculations for external spur gears and linear gear trains."""

from __future__ import annotations

from math import cos, pi, prod

from .models import (
    GearGeometry,
    GearPlacement,
    GearSpec,
    GearTrainSpec,
    GearTrainLayout,
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
    """Return placements from the collision-aware axial layout plan."""

    return calculate_layout_plan(
        spec,
        vertical=vertical,
        axial_gap_mm=axial_gap_mm,
    ).placements


def calculate_layout_plan(
    spec: GearTrainSpec,
    *,
    vertical: bool = False,
    axial_gap_mm: float = AXIAL_GAP_MM,
) -> GearTrainLayout:
    """Prefer two planes and add fallback planes when addendum circles collide."""

    stage_results = calculate_stage_results(spec)
    shaft_offsets_mm = [0.0]
    for result in stage_results:
        shaft_offsets_mm.append(shaft_offsets_mm[-1] + result.center_distance_mm)

    gears = derive_gears(spec)
    plane_indices, warnings = _resolve_stage_planes(spec, gears, shaft_offsets_mm)
    placements = []
    for gear in gears:
        offset_mm = shaft_offsets_mm[gear.shaft_index]
        stage_plane_mm = plane_indices[gear.stage_index - 1] * (
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
    return GearTrainLayout(
        placements=tuple(placements),
        stage_plane_indices=plane_indices,
        warnings=warnings,
    )


def _resolve_stage_planes(
    spec: GearTrainSpec,
    gears: tuple[GearSpec, ...],
    shaft_offsets_mm: list[float],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    assigned_by_plane = {}
    plane_indices = []
    warnings = []

    for stage_index in range(1, len(spec.stages) + 1):
        stage_gears = tuple(
            gear for gear in gears if gear.stage_index == stage_index
        )
        rejected_collisions = []
        chosen_plane = None
        preferred_plane = (stage_index - 1) % 2
        candidate_planes = (preferred_plane,) + tuple(
            plane_index
            for plane_index in range(len(spec.stages))
            if plane_index != preferred_plane
        )
        for candidate_plane in candidate_planes:
            if plane_indices and candidate_plane == plane_indices[-1]:
                continue
            collision = _first_plane_collision(
                spec,
                stage_gears,
                assigned_by_plane.get(candidate_plane, ()),
                shaft_offsets_mm,
            )
            if collision:
                rejected_collisions.append(collision)
                continue
            chosen_plane = candidate_plane
            break

        if chosen_plane is None:
            raise ValueError(f'No collision-free plane found for stage {stage_index}.')
        plane_indices.append(chosen_plane)
        assigned_by_plane.setdefault(chosen_plane, []).extend(stage_gears)

        if chosen_plane != preferred_plane:
            reason = rejected_collisions[0] if rejected_collisions else 'compound-shaft overlap'
            warnings.append(
                f'Stage {stage_index} moved to axial plane {chosen_plane + 1}; '
                f'compact plane {preferred_plane + 1} would cause {reason}.'
            )

    return tuple(plane_indices), tuple(warnings)


def _first_plane_collision(
    spec: GearTrainSpec,
    new_gears: tuple[GearSpec, ...],
    existing_gears,
    shaft_offsets_mm: list[float],
) -> str:
    for new_gear in new_gears:
        new_radius_mm = calculate_gear_geometry(
            spec.standard.module_mm,
            new_gear.teeth,
            spec.standard.pressure_angle_rad,
        ).addendum_radius_mm
        for existing_gear in existing_gears:
            existing_radius_mm = calculate_gear_geometry(
                spec.standard.module_mm,
                existing_gear.teeth,
                spec.standard.pressure_angle_rad,
            ).addendum_radius_mm
            center_distance_mm = abs(
                shaft_offsets_mm[new_gear.shaft_index]
                - shaft_offsets_mm[existing_gear.shaft_index]
            )
            overlap_mm = new_radius_mm + existing_radius_mm - center_distance_mm
            if overlap_mm > 1e-9:
                return (
                    f'a {overlap_mm:.3f} mm collision between '
                    f'{existing_gear.id} and {new_gear.id}'
                )
    return ''
