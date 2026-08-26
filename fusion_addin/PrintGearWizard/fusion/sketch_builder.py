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
