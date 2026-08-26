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


MM_TO_FUSION_LENGTH = 0.1


def create_single_gear_sketch(spec: GearTrainSpec) -> adsk.fusion.Sketch:
    """Create the stage-1 driver outline and bore in a new component."""

    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError('An active Fusion design is required.')

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
        return sketch
    except Exception:
        train_occurrence.deleteMe()
        raise


def _fusion_point(point):
    return adsk.core.Point3D.create(
        point.x_mm * MM_TO_FUSION_LENGTH,
        point.y_mm * MM_TO_FUSION_LENGTH,
        0,
    )
