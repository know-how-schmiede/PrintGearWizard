"""Create Fusion components and bodies from the PrintGearWizard domain model."""

from __future__ import annotations

import adsk.core
import adsk.fusion

from ..core import (
    GearPlacement,
    GearSpec,
    GearStandard,
    GearTrainSpec,
    build_gear_outline,
    calculate_gear_geometry,
    calculate_placements,
    derive_gears,
)
from .design_context import require_hybrid_design


MM_TO_FUSION_LENGTH = 0.1
GEOMETRY_TOLERANCE_CM = 1e-4


def create_gear_train_bodies(
    spec: GearTrainSpec,
    *,
    vertical: bool = False,
) -> tuple[adsk.fusion.BRepBody, ...]:
    """Create every derived gear as a positioned internal component."""

    design = require_hybrid_design()
    gears = derive_gears(spec)
    placements = calculate_placements(spec, vertical=vertical)
    if len(gears) != len(placements):
        raise RuntimeError('Gear derivation and placement counts do not match.')

    train_occurrence = design.rootComponent.occurrences.addNewComponent(
        adsk.core.Matrix3D.create()
    )
    try:
        train_component = train_occurrence.component
        train_component.name = 'PrintGearWizard Gear Train'
        bodies = tuple(
            _create_gear_body(train_component, gear, placement, spec.standard)
            for gear, placement in zip(gears, placements)
        )
        if len(bodies) != 2 * len(spec.stages):
            raise RuntimeError('Generated body count does not match the stage count.')
        return bodies
    except Exception:
        train_occurrence.deleteMe()
        raise


def _create_gear_body(
    train_component: adsk.fusion.Component,
    gear: GearSpec,
    placement: GearPlacement,
    standard: GearStandard,
) -> adsk.fusion.BRepBody:
    geometry = calculate_gear_geometry(
        standard.module_mm,
        gear.teeth,
        standard.pressure_angle_rad,
    )
    outline = build_gear_outline(
        geometry,
        gear.teeth,
        standard.backlash_mm,
        standard.involute_samples,
    )

    gear_occurrence = train_component.occurrences.addNewComponent(
        _placement_transform(placement)
    )
    gear_component = gear_occurrence.component
    gear_component.name = gear.id

    sketch = gear_component.sketches.add(gear_component.xYConstructionPlane)
    sketch.name = f'{gear.id}_Profile'
    sketch.isComputeDeferred = True
    try:
        lines = sketch.sketchCurves.sketchLines
        for start, end in zip(outline.points, outline.points[1:]):
            lines.addByTwoPoints(_fusion_point(start), _fusion_point(end))
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            gear.bore_diameter_mm * MM_TO_FUSION_LENGTH / 2.0,
        )
    finally:
        sketch.isComputeDeferred = False

    if sketch.profiles.count < 2:
        raise RuntimeError(
            f'{gear.id}: expected a gear profile and bore profile, '
            f'but Fusion found {sketch.profiles.count}.'
        )
    gear_profile = max(
        (sketch.profiles.item(index) for index in range(sketch.profiles.count)),
        key=lambda profile: profile.areaProperties().area,
    )
    if gear_profile.profileLoops.count < 2:
        raise RuntimeError(f'{gear.id}: the selected profile does not contain the bore.')

    extrudes = gear_component.features.extrudeFeatures
    extrude_input = extrudes.createInput(
        gear_profile,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    distance = adsk.core.ValueInput.createByString(f'{standard.face_width_mm} mm')
    distance_extent = adsk.fusion.DistanceExtentDefinition.create(distance)
    if not extrude_input.setOneSideExtent(
        distance_extent,
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
    ):
        raise RuntimeError(f'{gear.id}: could not define the extrusion extent.')

    extrude = extrudes.add(extrude_input)
    extrude.name = f'{gear.id}_Extrude'
    if extrude.bodies.count != 1:
        raise RuntimeError(f'{gear.id}: extrusion did not create exactly one body.')
    body = extrude.bodies.item(0)
    body.name = f'{gear.id}_Body'
    _verify_created_body(
        body,
        gear.id,
        geometry.addendum_radius_mm,
        gear.bore_diameter_mm,
        standard.face_width_mm,
    )
    sketch.isVisible = False
    return body


def _placement_transform(placement: GearPlacement) -> adsk.core.Matrix3D:
    transform = adsk.core.Matrix3D.create()
    transform.setToRotation(
        placement.rotation_rad,
        adsk.core.Vector3D.create(0, 0, 1),
        adsk.core.Point3D.create(0, 0, 0),
    )
    transform.translation = adsk.core.Vector3D.create(
        placement.x_mm * MM_TO_FUSION_LENGTH,
        placement.y_mm * MM_TO_FUSION_LENGTH,
        placement.z_mm * MM_TO_FUSION_LENGTH,
    )
    return transform


def _fusion_point(point):
    return adsk.core.Point3D.create(
        point.x_mm * MM_TO_FUSION_LENGTH,
        point.y_mm * MM_TO_FUSION_LENGTH,
        0,
    )


def _verify_created_body(
    body: adsk.fusion.BRepBody,
    gear_id: str,
    addendum_radius_mm: float,
    bore_diameter_mm: float,
    face_width_mm: float,
):
    """Verify critical dimensions at the Fusion API boundary."""

    if not body.isSolid:
        raise RuntimeError(f'{gear_id}: extrusion did not create a solid body.')
    if body.volume <= 0:
        raise RuntimeError(f'{gear_id}: generated body has no positive volume.')

    bounding_box = body.boundingBox
    actual_width_cm = bounding_box.maxPoint.z - bounding_box.minPoint.z
    expected_width_cm = face_width_mm * MM_TO_FUSION_LENGTH
    _require_close(actual_width_cm, expected_width_cm, f'{gear_id}: extruded width')

    expected_outer_radius_cm = addendum_radius_mm * MM_TO_FUSION_LENGTH
    actual_outer_radius_cm = max(
        (
            body.vertices.item(index).geometry.x ** 2
            + body.vertices.item(index).geometry.y ** 2
        ) ** 0.5
        for index in range(body.vertices.count)
    )
    _require_close(
        actual_outer_radius_cm,
        expected_outer_radius_cm,
        f'{gear_id}: outside radius',
    )

    expected_bore_radius_cm = bore_diameter_mm * MM_TO_FUSION_LENGTH / 2.0
    cylindrical_radii_cm = []
    for index in range(body.faces.count):
        cylinder = adsk.core.Cylinder.cast(body.faces.item(index).geometry)
        if cylinder:
            cylindrical_radii_cm.append(cylinder.radius)
    if not any(
        abs(radius_cm - expected_bore_radius_cm) <= GEOMETRY_TOLERANCE_CM
        for radius_cm in cylindrical_radii_cm
    ):
        raise RuntimeError(
            f'{gear_id}: expected bore radius {expected_bore_radius_cm:.6f} cm '
            f'was not found in the generated body.'
        )


def _require_close(actual: float, expected: float, label: str):
    if abs(actual - expected) > GEOMETRY_TOLERANCE_CM:
        raise RuntimeError(
            f'{label} is {actual:.6f} cm; expected {expected:.6f} cm.'
        )
