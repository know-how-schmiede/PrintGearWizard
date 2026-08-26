"""Checks for the Fusion document context required by PrintGearWizard."""

from __future__ import annotations

import adsk.core
import adsk.fusion


HYBRID_REQUIRED_MESSAGE = (
    'PrintGearWizard currently requires a hybrid design because it creates '
    'internal child components.'
)


def hybrid_design_error() -> str:
    """Return an actionable error, or an empty string for a writable hybrid design."""

    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return 'Open or create a Fusion design before running PrintGearWizard.'
    if design.isConfiguration:
        return 'The active configuration is read-only and cannot receive generated gears.'

    intent_types = getattr(adsk.fusion, 'DesignIntentTypes', None)
    if intent_types is None or not hasattr(design, 'designIntent'):
        return (
            'This Fusion version cannot report the active design intent. '
            'Update Fusion before generating components.'
        )

    intent = design.designIntent
    if intent == intent_types.HybridDesignIntentType:
        return ''
    if intent == intent_types.PartDesignIntentType:
        return (
            'The active document is a part design. ' + HYBRID_REQUIRED_MESSAGE
        )
    if intent == intent_types.AssemblyDesignIntentType:
        return (
            'The active document is an assembly design, where generated parts '
            'must be external components. ' + HYBRID_REQUIRED_MESSAGE
        )
    return 'The active Fusion design intent is not supported.'


def require_hybrid_design() -> adsk.fusion.Design:
    """Return the active design or raise before any geometry is changed."""

    error = hybrid_design_error()
    if error:
        raise RuntimeError(error)
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
