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

    rotation_rad = corrected_half_angle - pitch_point_angle
    left = tuple(rotate_point(point, rotation_rad) for point in raw_flank)
    right = tuple(Point2D(point.x_mm, -point.y_mm) for point in left)
    return ToothFlanks(left=left, right=right)


def point_radius_mm(point: Point2D) -> float:
    """Return the distance of a point from the origin."""

    return hypot(point.x_mm, point.y_mm)
