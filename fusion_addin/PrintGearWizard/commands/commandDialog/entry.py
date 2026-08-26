"""PrintGearWizard command registration and standard dialog."""

import math
import os

import adsk.core
import adsk.fusion

from ... import config
from ...core import (
    GearStandard,
    GearTrainSpec,
    RotationDirection,
    StageInput,
    calculate_stage_results,
    calculate_total_ratio,
    has_errors,
    output_rotation_direction,
    validate_gear_train,
)
from ...lib import fusionAddInUtils as futil
from ...fusion import create_single_gear_body, hybrid_design_error
from ...version import VERSION


app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = f'PrintGearWizard {VERSION}'
CMD_Description = 'Create 3D-print-friendly spur gears and gear trains.'

IS_PROMOTED = True
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

MAX_STAGE_COUNT = 4
DEFAULT_DRIVER_TEETH = 15
DEFAULT_DRIVEN_TEETH = 45
PROFILE_BACKLASH_MM = {
    'FDM Standard': 0.20,
    'FDM Fine': 0.15,
    'Resin': 0.10,
    'Custom': 0.15,
}

local_handlers = []
backlash_manually_edited = False
updating_dialog = False


def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID,
        CMD_NAME,
        CMD_Description,
        ICON_FOLDER,
    )
    futil.add_handler(cmd_def.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def)
    control.isPromoted = IS_PROMOTED


def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')

    global backlash_manually_edited
    backlash_manually_edited = False

    command = args.command
    command.setDialogInitialSize(560, 720)
    command.setDialogMinimumSize(480, 600)
    inputs = command.commandInputs

    _add_basic_data_tab(inputs)
    _add_stages_tab(inputs)
    _add_construction_tab(inputs)
    _update_dialog(inputs)

    futil.add_handler(command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)


def _add_basic_data_tab(inputs: adsk.core.CommandInputs):
    tab = inputs.addTabCommandInput('basicTab', 'Basic data')
    tab_inputs = tab.children

    design_error = hybrid_design_error()
    compatibility = tab_inputs.addTextBoxCommandInput(
        'designCompatibility',
        '',
        (
            f'<b>Blocked:</b> {design_error}'
            if design_error
            else '<b>Document:</b> Compatible hybrid design.'
        ),
        3 if design_error else 1,
        True,
    )
    compatibility.isFullWidth = True

    tab_inputs.addIntegerSpinnerCommandInput(
        'stageCount',
        'Number of stages',
        1,
        MAX_STAGE_COUNT,
        1,
        2,
    )
    tab_inputs.addValueInput(
        'module',
        'Module',
        'mm',
        adsk.core.ValueInput.createByString('1.0 mm'),
    )
    pressure_angle = tab_inputs.addValueInput(
        'pressureAngle',
        'Pressure angle',
        'deg',
        adsk.core.ValueInput.createByString('20 deg'),
    )
    pressure_angle.isReadOnly = True
    tab_inputs.addValueInput(
        'faceWidth',
        'Gear width',
        'mm',
        adsk.core.ValueInput.createByString('8.0 mm'),
    )
    tab_inputs.addValueInput(
        'backlash',
        'Mesh backlash',
        'mm',
        adsk.core.ValueInput.createByString('0.15 mm'),
    )

    profile = tab_inputs.addDropDownCommandInput(
        'printProfile',
        'Print profile',
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    for name in PROFILE_BACKLASH_MM:
        profile.listItems.add(name, name == 'FDM Fine', '')


def _add_stages_tab(inputs: adsk.core.CommandInputs):
    tab = inputs.addTabCommandInput('stagesTab', 'Gear stages')
    tab_inputs = tab.children

    for stage_index in range(1, MAX_STAGE_COUNT + 1):
        group = tab_inputs.addGroupCommandInput(
            f'stageGroup_{stage_index}',
            f'Stage {stage_index}',
        )
        group.isExpanded = stage_index <= 2
        stage_inputs = group.children
        stage_inputs.addIntegerSpinnerCommandInput(
            f'driverTeeth_{stage_index}',
            'Driver gear teeth',
            4,
            400,
            1,
            DEFAULT_DRIVER_TEETH,
        )
        stage_inputs.addIntegerSpinnerCommandInput(
            f'drivenTeeth_{stage_index}',
            'Driven gear teeth',
            4,
            400,
            1,
            DEFAULT_DRIVEN_TEETH,
        )
        stage_inputs.addTextBoxCommandInput(
            f'stageRatio_{stage_index}',
            'Stage ratio',
            '',
            1,
            True,
        )
        stage_inputs.addTextBoxCommandInput(
            f'centerDistance_{stage_index}',
            'Center distance',
            '',
            1,
            True,
        )
        warning = stage_inputs.addTextBoxCommandInput(
            f'stageWarning_{stage_index}',
            'Warning',
            '',
            2,
            True,
        )
        warning.isVisible = False

    summary = tab_inputs.addGroupCommandInput('summaryGroup', 'Summary')
    summary_inputs = summary.children
    summary_inputs.addTextBoxCommandInput('totalRatio', 'Total ratio', '', 1, True)
    summary_inputs.addTextBoxCommandInput('physicalGearCount', 'Physical gears', '', 1, True)
    summary_inputs.addTextBoxCommandInput('shaftCount', 'Shafts', '', 1, True)
    summary_inputs.addTextBoxCommandInput(
        'outputDirection',
        'Output rotation',
        '',
        1,
        True,
    )
    validation_status = tab_inputs.addTextBoxCommandInput(
        'validationStatus',
        'Validation',
        '',
        4,
        True,
    )
    validation_status.isFullWidth = True


def _add_construction_tab(inputs: adsk.core.CommandInputs):
    tab = inputs.addTabCommandInput('constructionTab', 'Construction')
    tab_inputs = tab.children

    plane = tab_inputs.addSelectionInput(
        'constructionPlane',
        'Construction plane',
        'Select a construction plane or planar face.',
    )
    plane.addSelectionFilter('ConstructionPlanes')
    plane.addSelectionFilter('PlanarFaces')
    plane.setSelectionLimits(0, 1)

    design = adsk.fusion.Design.cast(app.activeProduct)
    if design:
        plane.addSelection(design.rootComponent.xYConstructionPlane)

    origin = tab_inputs.addSelectionInput(
        'startPoint',
        'Origin / start point',
        'Optional: select a point or vertex.',
    )
    origin.addSelectionFilter('SketchPoints')
    origin.addSelectionFilter('Vertices')
    origin.addSelectionFilter('ConstructionPoints')
    origin.setSelectionLimits(0, 1)

    layout = tab_inputs.addDropDownCommandInput(
        'layoutDirection',
        'Layout direction',
        adsk.core.DropDownStyles.TextListDropDownStyle,
    )
    layout.listItems.add('Horizontal', True, '')
    layout.listItems.add('Vertical', False, '')

    bores = tab_inputs.addGroupCommandInput('shaftBoresGroup', 'Shaft bores')
    bores.isExpanded = True
    for shaft_index in range(MAX_STAGE_COUNT + 1):
        bores.children.addValueInput(
            f'shaftBore_{shaft_index}',
            f'Shaft {shaft_index + 1} bore',
            'mm',
            adsk.core.ValueInput.createByString('5.0 mm'),
        )

    output_mode = tab_inputs.addTextBoxCommandInput(
        'outputMode',
        'Output mode',
        'Separate components',
        1,
        True,
    )
    output_mode.isFullWidth = False
    tab_inputs.addBoolValueInput('previewEnabled', 'Preview enabled', True, '', True)

    tab_inputs.addTextBoxCommandInput(
        'constructionStatus',
        'Status',
        f'Version {VERSION} creates one stage-1 driver body on confirmation.',
        2,
        True,
    )


def _millimetres(value_input: adsk.core.ValueCommandInput) -> float:
    units_manager = app.activeProduct.unitsManager
    return units_manager.convert(value_input.value, units_manager.internalUnits, 'mm')


def _input(inputs: adsk.core.CommandInputs, input_id: str):
    """Find an input recursively across tabs and groups."""

    direct_input = inputs.itemById(input_id)
    if direct_input:
        return direct_input

    for index in range(inputs.count):
        candidate = inputs.item(index)
        tab = adsk.core.TabCommandInput.cast(candidate)
        if tab:
            nested_input = _input(tab.children, input_id)
            if nested_input:
                return nested_input
            continue

        group = adsk.core.GroupCommandInput.cast(candidate)
        if group:
            nested_input = _input(group.children, input_id)
            if nested_input:
                return nested_input
    return None


def _active_stages(inputs: adsk.core.CommandInputs) -> tuple[StageInput, ...]:
    stage_count = _input(inputs, 'stageCount').value
    return tuple(
        StageInput(
            driver_teeth=_input(inputs, f'driverTeeth_{index}').value,
            driven_teeth=_input(inputs, f'drivenTeeth_{index}').value,
        )
        for index in range(1, stage_count + 1)
    )


def _value_expressions_are_valid(inputs: adsk.core.CommandInputs) -> bool:
    value_ids = ['module', 'pressureAngle', 'faceWidth', 'backlash']
    stage_count_input = _input(inputs, 'stageCount')
    if not stage_count_input:
        return False
    value_ids.extend(
        f'shaftBore_{index}' for index in range(stage_count_input.value + 1)
    )
    return all(_input(inputs, input_id).isValidExpression for input_id in value_ids)


def _dialog_spec(inputs: adsk.core.CommandInputs) -> GearTrainSpec:
    stage_count = _input(inputs, 'stageCount').value
    return GearTrainSpec(
        standard=GearStandard(
            module_mm=_millimetres(_input(inputs, 'module')),
            pressure_angle_rad=_input(inputs, 'pressureAngle').value,
            face_width_mm=_millimetres(_input(inputs, 'faceWidth')),
            backlash_mm=_millimetres(_input(inputs, 'backlash')),
        ),
        stages=_active_stages(inputs),
        shaft_bores_mm=tuple(
            _millimetres(_input(inputs, f'shaftBore_{index}'))
            for index in range(stage_count + 1)
        ),
    )


def _update_dialog(inputs: adsk.core.CommandInputs):
    global updating_dialog
    if updating_dialog:
        return

    updating_dialog = True
    try:
        stage_count = _input(inputs, 'stageCount').value
        if not _value_expressions_are_valid(inputs):
            validation_status = _input(inputs, 'validationStatus')
            validation_status.formattedText = (
                '<b>Error:</b> Complete all numeric values with valid expressions.'
            )
            return

        spec = _dialog_spec(inputs)
        stages = spec.stages
        results = calculate_stage_results(spec)

        for index in range(1, MAX_STAGE_COUNT + 1):
            active = index <= stage_count
            _input(inputs, f'stageGroup_{index}').isVisible = active
            _input(inputs, f'shaftBore_{index}').isVisible = index <= stage_count
            if not active:
                continue

            stage = stages[index - 1]
            result = results[index - 1]
            _input(inputs, f'stageRatio_{index}').formattedText = (
                f'{result.ratio:.4g} : 1'
            )
            _input(inputs, f'centerDistance_{index}').formattedText = (
                f'{result.center_distance_mm:.3f} mm'
            )
            warnings = []
            if stage.driver_teeth < 17:
                warnings.append('Driver has fewer than 17 teeth; undercut may occur.')
            if stage.driven_teeth < 17:
                warnings.append('Driven gear has fewer than 17 teeth; undercut may occur.')
            warning_input = _input(inputs, f'stageWarning_{index}')
            warning_input.formattedText = '<br>'.join(warnings)
            warning_input.isVisible = bool(warnings)

        _input(inputs, 'totalRatio').formattedText = (
            f'{calculate_total_ratio(stages):.5g} : 1'
        )
        _input(inputs, 'physicalGearCount').formattedText = str(2 * stage_count)
        _input(inputs, 'shaftCount').formattedText = str(stage_count + 1)
        direction = output_rotation_direction(stage_count)
        _input(inputs, 'outputDirection').formattedText = (
            'Same as input'
            if direction == RotationDirection.SAME
            else 'Opposite to input'
        )
        issues = validate_gear_train(spec)
        if issues:
            validation_lines = [
                f'<b>{issue.severity.value.title()}:</b> {issue.message}'
                for issue in issues
            ]
            _input(inputs, 'validationStatus').formattedText = '<br>'.join(
                validation_lines
            )
        else:
            _input(inputs, 'validationStatus').formattedText = (
                '<b>Ready:</b> All inputs are valid.'
            )
    finally:
        updating_dialog = False


def command_execute(args: adsk.core.CommandEventArgs):
    body = create_single_gear_body(_dialog_spec(args.command.commandInputs))
    futil.log(f'{CMD_NAME} created body {body.name}')


def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event — dialog preview only')


def command_input_changed(args: adsk.core.InputChangedEventArgs):
    global backlash_manually_edited, updating_dialog

    changed_input = args.input
    inputs = args.inputs
    futil.log(f'{CMD_NAME} Input Changed Event fired from {changed_input.id}')

    if changed_input.id == 'backlash' and not updating_dialog:
        backlash_manually_edited = True
    elif changed_input.id == 'printProfile' and not backlash_manually_edited:
        selected_profile = changed_input.selectedItem.name
        backlash_mm = PROFILE_BACKLASH_MM[selected_profile]
        updating_dialog = True
        try:
            _input(inputs, 'backlash').expression = f'{backlash_mm} mm'
        finally:
            updating_dialog = False

    _update_dialog(inputs)


def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # This event also fires when Fusion commits a value expression with Enter
    # or by moving focus, so refresh results without requiring a tab change.
    _update_dialog(args.inputs)
    if hybrid_design_error():
        args.areInputsValid = False
        return
    if not _value_expressions_are_valid(args.inputs):
        args.areInputsValid = False
        return
    args.areInputsValid = not has_errors(validate_gear_train(_dialog_spec(args.inputs)))


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
