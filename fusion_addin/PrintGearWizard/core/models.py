"""Immutable domain models used by calculations and Fusion integration.

This module deliberately does not import ``adsk``. Domain calculations use
millimetres and radians; conversion to Fusion database units belongs at the
Fusion API boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RotationDirection(str, Enum):
    """Output rotation direction relative to the input shaft."""

    SAME = 'same'
    OPPOSITE = 'opposite'


@dataclass(frozen=True)
class GearStandard:
    """Parameters shared by every gear in a gear train."""

    module_mm: float
    pressure_angle_rad: float
    face_width_mm: float
    backlash_mm: float
    involute_samples: int = 12


@dataclass(frozen=True)
class StageInput:
    """User-supplied tooth counts for one external gear stage."""

    driver_teeth: int
    driven_teeth: int


@dataclass(frozen=True)
class GearSpec:
    """Specification of one physical gear before geometry is generated."""

    id: str
    stage_index: int
    role: str
    teeth: int
    shaft_index: int
    bore_diameter_mm: float


@dataclass(frozen=True)
class GearTrainSpec:
    """Complete normalized input for a gear-train calculation."""

    standard: GearStandard
    stages: tuple[StageInput, ...]
    shaft_bores_mm: tuple[float, ...]


@dataclass(frozen=True)
class GearGeometry:
    """Calculated reference radii for one gear, in millimetres."""

    pitch_radius_mm: float
    base_radius_mm: float
    addendum_radius_mm: float
    root_radius_mm: float


@dataclass(frozen=True)
class StageResult:
    """Calculated transmission values for one stage."""

    ratio: float
    center_distance_mm: float


@dataclass(frozen=True)
class GearPlacement:
    """Calculated gear position in millimetres and radians."""

    gear_id: str
    x_mm: float
    y_mm: float
    z_mm: float
    rotation_rad: float
