"""Create Fusion sketches from the pure PrintGearWizard domain model."""

from __future__ import annotations

import adsk.core
import adsk.fusion

from ..core import (
    GearTrainSpec,
    build_gear_outline,
    calculate_gear_geometry,
    derive_gears,
)
from .design_context import require_hybrid_design


MM_TO_FUSION_LENGTH = 0.1
GEOMETRY_TOLERANCE_CM = 1e-4


def create_single_gear_body(spec: GearTrainSpec) -> adsk.fusion.BRepBody:
    """Create and extrude the stage-1 driver in a new component."""

    design = require_hybrid_design()

    gear = derive_gears(spec)[0]
    geometry = calculate_gear_geometry(
        spec.standard.module_mm,
        gear.teeth,
        spec.standard.pressure_angle_rad,
    )
    outline = build_gear_outline(
        geometry,
        gear.teeth,
        spec.standard.backlash_mm,
        spec.standard.involute_samples,
    )

    root_component = design.rootComponent
    train_occurrence = root_component.occurrences.addNewComponent(
        adsk.core.Matrix3D.create()
    )
    try:
        train_occurrence.component.name = 'PrintGearWizard Gear Train'
        gear_occurrence = train_occurrence.component.occurrences.addNewComponent(
            adsk.core.Matrix3D.create()
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
        distance = adsk.core.ValueInput.createByString(
            f'{spec.standard.face_width_mm} mm'
        )
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
            spec.standard.face_width_mm,
        )
        sketch.isVisible = False
        return body
    except Exception:
        train_occurrence.deleteMe()
        raise


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
    _require_close(
        actual_width_cm,
        expected_width_cm,
        f'{gear_id}: extruded width',
    )

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

    expected_bore_radius_cm = (
        bore_diameter_mm * MM_TO_FUSION_LENGTH / 2.0
    )
    cylindrical_radii_cm = []
    for index in range(body.faces.count):
        face = body.faces.item(index)
        cylinder = adsk.core.Cylinder.cast(face.geometry)
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
