"""Fusion-independent involute sampling for one external spur-gear tooth."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, sin, sqrt

from .models import GearGeometry


@dataclass(frozen=True)
class Point2D:
    """A two-dimensional point in millimetres."""

    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class ToothFlanks:
    """Sampled left and right involute flanks from root region to addendum."""

    left: tuple[Point2D, ...]
    right: tuple[Point2D, ...]


@dataclass(frozen=True)
class GearOutline:
    """A closed outer gear contour represented by ordered line endpoints."""

    points: tuple[Point2D, ...]


def involute_parameter_at_radius(base_radius_mm: float, radius_mm: float) -> float:
    """Return the involute parameter at a requested radius."""

    if base_radius_mm <= 0:
        raise ValueError('Base radius must be greater than zero.')
    if radius_mm < base_radius_mm:
        raise ValueError('Requested radius cannot be smaller than the base radius.')
    return sqrt((radius_mm / base_radius_mm) ** 2 - 1.0)


def involute_point(base_radius_mm: float, parameter: float) -> Point2D:
    """Return a point on the unrotated involute curve."""

    return Point2D(
        x_mm=base_radius_mm * (
            cos(parameter) + parameter * sin(parameter)
        ),
        y_mm=base_radius_mm * (
            sin(parameter) - parameter * cos(parameter)
        ),
    )


def rotate_point(point: Point2D, angle_rad: float) -> Point2D:
    """Rotate a point counter-clockwise around the origin."""

    return Point2D(
        x_mm=point.x_mm * cos(angle_rad) - point.y_mm * sin(angle_rad),
        y_mm=point.x_mm * sin(angle_rad) + point.y_mm * cos(angle_rad),
    )


def sample_involute(
    base_radius_mm: float,
    start_radius_mm: float,
    end_radius_mm: float,
    sample_count: int,
) -> tuple[Point2D, ...]:
    """Sample an involute between two radii, including both endpoints."""

    if sample_count < 2:
        raise ValueError('At least two involute samples are required.')
    if end_radius_mm < start_radius_mm:
        raise ValueError('End radius cannot be smaller than start radius.')

    start_parameter = involute_parameter_at_radius(base_radius_mm, start_radius_mm)
    end_parameter = involute_parameter_at_radius(base_radius_mm, end_radius_mm)
    parameter_step = (end_parameter - start_parameter) / (sample_count - 1)
    return tuple(
        involute_point(base_radius_mm, start_parameter + index * parameter_step)
        for index in range(sample_count)
    )


def build_tooth_flanks(
    geometry: GearGeometry,
    teeth: int,
    backlash_mm: float,
    sample_count: int = 12,
) -> ToothFlanks:
    """Build symmetric flanks using per-gear tooth-thickness reduction.

    ``backlash_mm`` is the total circular tooth-thickness reduction assigned to
    this generated gear. It is applied symmetrically to both tooth flanks.
    """

    if teeth <= 0:
        raise ValueError('Tooth count must be greater than zero.')
    if backlash_mm < 0:
        raise ValueError('Backlash cannot be negative.')

    start_radius_mm = max(geometry.root_radius_mm, geometry.base_radius_mm)
    raw_flank = sample_involute(
        geometry.base_radius_mm,
        start_radius_mm,
        geometry.addendum_radius_mm,
        sample_count,
    )
    pitch_parameter = involute_parameter_at_radius(
        geometry.base_radius_mm,
        geometry.pitch_radius_mm,
    )
    pitch_point = involute_point(geometry.base_radius_mm, pitch_parameter)
    pitch_point_angle = atan2(pitch_point.y_mm, pitch_point.x_mm)

    corrected_half_angle = (
        pi / (2 * teeth)
        - backlash_mm / (2 * geometry.pitch_radius_mm)
    )
    if corrected_half_angle <= 0:
        raise ValueError('Backlash removes the complete tooth thickness.')

    # The unrotated involute winds counter-clockwise as its radius grows. It
    # therefore represents the right flank: after placing its pitch point at
    # the negative half-tooth angle, the addendum point moves toward the tooth
    # centerline. Mirroring that curve produces the left flank.
    rotation_rad = -corrected_half_angle - pitch_point_angle
    right = tuple(rotate_point(point, rotation_rad) for point in raw_flank)
    left = tuple(Point2D(point.x_mm, -point.y_mm) for point in right)
    return ToothFlanks(left=left, right=right)


def point_radius_mm(point: Point2D) -> float:
    """Return the distance of a point from the origin."""

    return hypot(point.x_mm, point.y_mm)


def build_gear_outline(
    geometry: GearGeometry,
    teeth: int,
    backlash_mm: float,
    involute_samples: int = 12,
    arc_segments: int = 4,
) -> GearOutline:
    """Build one counter-clockwise, closed, polygonal gear outline.

    Version 1 uses radial transitions between the root circle and involute.
    Circular root and addendum regions are sampled into short line segments.
    The final point repeats the first point to make closure explicit.
    """

    if arc_segments < 1:
        raise ValueError('At least one arc segment is required.')

    flanks = build_tooth_flanks(
        geometry,
        teeth,
        backlash_mm,
        involute_samples,
    )
    tooth_pitch_rad = 2 * pi / teeth
    right_start_angle = atan2(flanks.right[0].y_mm, flanks.right[0].x_mm)
    left_start_angle = atan2(flanks.left[0].y_mm, flanks.left[0].x_mm)
    right_tip_angle = atan2(flanks.right[-1].y_mm, flanks.right[-1].x_mm)
    left_tip_angle = atan2(flanks.left[-1].y_mm, flanks.left[-1].x_mm)

    points = []
    for tooth_index in range(teeth):
        center_angle = tooth_index * tooth_pitch_rad
        root_right = _polar_point(
            geometry.root_radius_mm,
            center_angle + right_start_angle,
        )
        if not points:
            points.append(root_right)

        points.extend(
            rotate_point(point, center_angle) for point in flanks.right
        )
        points.extend(
            _sample_arc(
                geometry.addendum_radius_mm,
                center_angle + right_tip_angle,
                center_angle + left_tip_angle,
                arc_segments,
            )[1:]
        )
        points.extend(
            rotate_point(point, center_angle)
            for point in reversed(flanks.left[:-1])
        )
        root_left = _polar_point(
            geometry.root_radius_mm,
            center_angle + left_start_angle,
        )
        points.append(root_left)

        next_right_angle = center_angle + tooth_pitch_rad + right_start_angle
        points.extend(
            _sample_arc(
                geometry.root_radius_mm,
                center_angle + left_start_angle,
                next_right_angle,
                arc_segments,
            )[1:]
        )

    points[-1] = points[0]
    deduplicated = [points[0]]
    for point in points[1:]:
        previous = deduplicated[-1]
        if hypot(point.x_mm - previous.x_mm, point.y_mm - previous.y_mm) > 1e-9:
            deduplicated.append(point)
    if deduplicated[-1] != deduplicated[0]:
        deduplicated.append(deduplicated[0])
    return GearOutline(points=tuple(deduplicated))


def _polar_point(radius_mm: float, angle_rad: float) -> Point2D:
    return Point2D(radius_mm * cos(angle_rad), radius_mm * sin(angle_rad))


def _sample_arc(
    radius_mm: float,
    start_angle_rad: float,
    end_angle_rad: float,
    segment_count: int,
) -> tuple[Point2D, ...]:
    angle_step = (end_angle_rad - start_angle_rad) / segment_count
    return tuple(
        _polar_point(radius_mm, start_angle_rad + index * angle_step)
        for index in range(segment_count + 1)
    )
