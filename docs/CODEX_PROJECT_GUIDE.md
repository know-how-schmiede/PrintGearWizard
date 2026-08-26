# PrintGearWizard — project specification and Codex implementation guide

## 1. Codex role

Implement PrintGearWizard incrementally from the empty Autodesk Fusion Python add-in created by the project owner. Preserve the generated add-in entry points and manifest unless a change is necessary and explained. Keep each milestone executable inside Fusion. Do not implement later milestones before the current milestone passes its tests and acceptance criteria.

Use English for source code, identifiers, comments, logs, commits, issues, and primary documentation. German documentation will be added later under `docs/de/`.

## 2. Product goal

PrintGearWizard is an open-source Autodesk Fusion add-in that generates configurable, 3D-print-friendly external spur gears and simple multi-stage gear trains.

The standard version must let a beginner define one to four gear stages without manually assigning every gear to a shaft. From the stage definitions, the add-in derives the individual gears, compound intermediate shafts, ratios, center distances, rotation directions, and component positions.

The first release is a geometric generator, not a certified gear-strength calculation system. Calculated torque values, if added later, must be clearly labeled as estimates.

## 3. Scope of the first release

### Included

- Standard external involute spur gears
- One to four gear stages
- Two gears per stage
- Automatic compound intermediate shafts
- Common module for the complete train
- Common pressure angle, default 20 degrees
- Common face width
- Configurable backlash/tooth-thickness reduction
- Configurable round bore for every shaft
- Automatic pitch, base, addendum, and root diameters
- Automatic center distances
- Stage and total transmission ratios
- Input/output rotation-direction display
- One Fusion component per physical gear
- Automatic positioning in one plane
- Input validation and preview
- Documented, testable geometry functions independent of Fusion where practical

### Explicitly excluded from version 1

- Internal gears
- Planetary gears
- Helical, herringbone, bevel, worm, and rack gears
- True manufacturing trochoids
- Automatic strength or lifetime calculation
- Gearbox housing generation
- Bearings, keys, splines, D-bores, set screws, and clamping hubs
- Arbitrary free-positioned gear networks
- Profile shift as a user-facing standard parameter
- Automatic tooth-count optimization from a requested ratio

These exclusions must not prevent later extension. Use enums and clear interfaces where they reduce future migration cost, but do not build unused abstraction layers.

## 4. Standard user workflow

1. Start the PrintGearWizard command in the Design workspace.
2. Select the number of stages from one to four.
3. Enter common gear parameters.
4. Enter driver and driven tooth counts for every visible stage.
5. Enter the bore diameter for input, intermediate, and output shafts.
6. Review calculated stage ratios, total ratio, center distances, warnings, and preview.
7. Confirm the command.
8. Receive a root component containing one component per gear with clear names and generated parameters.

For a two-stage train, the add-in automatically creates four gears on three shafts:

- Gear 1: stage 1 driver on input shaft
- Gear 2: stage 1 driven gear on intermediate shaft 1
- Gear 3: stage 2 driver on intermediate shaft 1
- Gear 4: stage 2 driven gear on output shaft

## 5. Command dialog

Use three `TabCommandInput` pages.

### 5.1 Basic data

Visible standard inputs:

| ID | Label | Type | Default | Range |
| --- | --- | --- | --- | --- |
| `stageCount` | Number of stages | Integer spinner | 2 | 1–4 |
| `module` | Module | Value input, mm | 1.0 mm | > 0 |
| `pressureAngle` | Pressure angle | Angle input | 20 deg | initially fixed or read-only |
| `faceWidth` | Gear width | Value input, mm | 8.0 mm | > 0 |
| `backlash` | Mesh backlash | Value input, mm | 0.15 mm | >= 0 |
| `printProfile` | Print profile | Dropdown | FDM Fine | FDM Standard, FDM Fine, Resin, Custom |

The print profile supplies defaults only. Changing a profile may update backlash until the user manually edits the backlash field. Do not silently overwrite a manually changed value.

### 5.2 Gear stages

Create four `GroupCommandInput` objects at command creation time. Toggle their `isVisible` property when `stageCount` changes. Do not delete and recreate them because hidden stage values should survive temporary stage-count changes.

Each stage contains:

| ID pattern | Label | Type |
| --- | --- | --- |
| `driverTeeth_N` | Driver gear teeth | Integer spinner |
| `drivenTeeth_N` | Driven gear teeth | Integer spinner |
| `stageRatio_N` | Stage ratio | Read-only text |
| `centerDistance_N` | Center distance | Read-only text |
| `stageWarning_N` | Warning | Read-only text, hidden when empty |

Recommended defaults per stage: 15 driver teeth and 45 driven teeth. Accept a wider technical input range, but warn below the recommended minimum.

Below the groups display:

- Total ratio
- Number of physical gears
- Number of shafts
- Output rotation direction relative to input

### 5.3 Construction

Standard inputs:

- Construction plane selection, default XY plane when possible
- Origin or start-point selection, optional with component origin fallback
- Layout direction: horizontal or vertical
- Bore diameter for every generated shaft
- Output mode fixed to separate components for version 1
- Preview enabled checkbox

Keep advanced parameters out of the standard dialog.

## 6. Data model

Do not read Fusion command inputs throughout the geometry code. Convert them once into typed domain objects.

Suggested model:

```python
@dataclass(frozen=True)
class GearStandard:
    module_mm: float
    pressure_angle_rad: float
    face_width_mm: float
    backlash_mm: float
    involute_samples: int = 12


@dataclass(frozen=True)
class StageInput:
    driver_teeth: int
    driven_teeth: int


@dataclass(frozen=True)
class GearSpec:
    id: str
    stage_index: int
    role: str
    teeth: int
    shaft_index: int
    bore_diameter_mm: float


@dataclass(frozen=True)
class GearTrainSpec:
    standard: GearStandard
    stages: tuple[StageInput, ...]
    shaft_bores_mm: tuple[float, ...]
```

Derived results must be separate from user input:

```python
@dataclass(frozen=True)
class GearGeometry:
    pitch_radius_mm: float
    base_radius_mm: float
    addendum_radius_mm: float
    root_radius_mm: float


@dataclass(frozen=True)
class StageResult:
    ratio: float
    center_distance_mm: float


@dataclass(frozen=True)
class GearPlacement:
    gear_id: str
    x_mm: float
    y_mm: float
    z_mm: float
    rotation_rad: float
```

## 7. Gear-train derivation

For `s` stages:

- Physical gear count: `2 * s`
- Shaft count: `s + 1`
- Stage `n` driver belongs to shaft `n`
- Stage `n` driven gear belongs to shaft `n + 1`
- The driven gear of stage `n` and driver gear of stage `n + 1` share the same shaft but remain separate components

Stage ratio:

```text
i_n = z_driven,n / z_driver,n
```

Total ratio:

```text
i_total = product(i_n)
```

Each external mesh reverses rotation. Therefore the output rotates in the same direction as the input for an even number of stages and in the opposite direction for an odd number of stages.

## 8. Standard gear geometry

For module `m`, tooth count `z`, and pressure angle `alpha`:

```text
pitch_radius    r  = m * z / 2
addendum_radius ra = r + m
root_radius     rf = r - 1.25 * m
base_radius     rb = r * cos(alpha)
```

For two external gears with the same module:

```text
center_distance a = m * (z1 + z2) / 2
```

Version 1 uses a radial or controlled fillet transition between the root circle and involute. It does not claim to reproduce a cutting-tool trochoid.

## 9. Involute profile algorithm

Generate one tooth and rotate it around the center for all teeth, or generate the complete closed contour mathematically before creating one Fusion sketch. Prefer the complete-contour approach if performance testing confirms it is more stable.

Parametric involute from base radius `rb`:

```text
x(t) = rb * (cos(t) + t * sin(t))
y(t) = rb * (sin(t) - t * cos(t))
```

Parameter at a target radius `rx`:

```text
t(rx) = sqrt((rx / rb)^2 - 1)
```

Algorithm:

1. Calculate pitch, addendum, root, and base radii.
2. Set the involute start radius to `max(root_radius, base_radius)`.
3. Calculate start and end involute parameters.
4. Sample 10–16 points; default 12.
5. Calculate the involute point at the pitch circle.
6. Rotate the flank so its pitch-circle point lies at the required half-tooth angle.
7. Reduce tooth thickness symmetrically to implement backlash.
8. Mirror the first flank around the tooth centerline.
9. Connect the flanks with an addendum-circle arc.
10. Connect the involute to the root region using the version-1 root transition.
11. Rotate the tooth by `2*pi/z` for every tooth.
12. Join adjacent teeth with root-circle arcs.
13. Verify a closed, non-self-intersecting contour.
14. Add the bore as a separate closed circle.
15. Create one extrusion for the gear component.

The half-tooth angle without backlash is:

```text
theta_half = pi / (2*z)
```

If `backlash_mm` means the total clearance assigned to a single generated gear's tooth thickness, use:

```text
theta_half_corrected = pi/(2*z) - backlash_mm/(2*r)
```

Document the chosen backlash semantics explicitly and test mating pairs. Do not mix total pair backlash with per-gear tooth-thickness reduction.

## 10. Placement algorithm

Version 1 uses a deterministic linear layout. Place the input shaft at the selected origin. For every stage, place the next shaft at the previous shaft position plus that stage's center distance along the selected layout axis.

Compound gears on the same intermediate shaft share X and Y coordinates. They may use an axial Z offset if necessary to represent successive stages without unintended body collision. Define the axial layout rule explicitly before implementation. A simple first rule is:

- Stage 1 mesh plane at `z = 0`
- Stage 2 mesh plane at `z = face_width + axial_gap`
- Stage 3 first attempts to return to `z = 0`; later stages continue alternating when collision-free
- Before creation, detect addendum-circle overlap between non-mating gears on the same plane
- If a preferred plane would collide, warn the user and assign the stage to the next collision-free axial plane
- The two gears sharing an intermediate shaft occupy their respective stage planes

Use a small configurable internal axial gap, initially 1 mm, but do not expose it in the standard UI unless required.

## 11. Fusion object structure

Create a top-level occurrence/component named `PrintGearWizard Gear Train`. Create child components with stable names:

```text
PGW_S1_Driver_Z15
PGW_S1_Driven_Z45
PGW_S2_Driver_Z18
PGW_S2_Driven_Z54
```

Inside each gear component:

- One profile sketch with a descriptive name
- One extrusion feature
- Optional construction circles only when useful and hidden after creation
- User parameters or model parameters with collision-safe names

All temporary preview objects must be deleted or rolled back when the command is cancelled. Do not leave partial geometry after failed validation or exceptions.

Fusion uses internal database units. Keep all domain calculations in explicitly named millimeter values and convert only at the Fusion API boundary.

## 12. Suggested source structure

Adapt this to the empty add-in structure rather than replacing working generated files blindly.

```text
PrintGearWizard/
  PrintGearWizard.py
  PrintGearWizard.manifest
  commands/
    create_gear_train/
      entry.py
      dialog.py
      handlers.py
  core/
    models.py
    validation.py
    calculations.py
    involute.py
    placement.py
  fusion/
    sketch_builder.py
    component_builder.py
    preview.py
    units.py
  resources/
    PrintGearWizard-logo.png
    16x16.png
    32x32.png
    64x64.png
    128x128.png
  tests/
    test_calculations.py
    test_involute.py
    test_validation.py
    test_placement.py
  docs/
    en/
    de/
```

Pure calculation modules must not import `adsk`. This allows unit tests to run outside Fusion.

## 13. Validation rules

Block execution when:

- Stage count is outside 1–4
- Module, face width, or bore is invalid
- Tooth count is below the hard geometric minimum
- Root radius is non-positive
- Bore radius plus a safety wall exceeds the root radius
- Backlash produces zero or negative tooth thickness
- Involute parameters are not real
- The final profile is open or self-intersecting

Warn but allow execution when:

- Tooth count is below approximately 17 at a 20-degree pressure angle without profile shift
- A very small module is selected for the current print profile
- The selected backlash is unusually small or large
- The gear diameter becomes unusually large

Use `validateInputs` for blocking conditions and `inputChanged` for live calculations and warnings. Keep expensive geometry rebuilding in preview handling rather than every text update where possible.

## 14. Error handling and logging

- Wrap Fusion event handlers at the API boundary.
- Log exceptions with a traceback to a project-specific log where appropriate.
- Show concise actionable messages to the user.
- Never swallow an exception silently.
- On failure, preserve the original design and remove temporary preview geometry.
- Include the failing gear or stage identifier in geometry errors.

## 15. Tests

### Pure unit tests

At minimum test:

- Radii for known module/tooth-count examples
- Center distance for known pairs
- Single- and multi-stage ratios
- Shaft assignment for one through four stages
- Rotation direction for odd/even stage counts
- Involute endpoints lie on their requested radii within tolerance
- Mirrored flanks are symmetric
- Backlash reduces tooth thickness correctly
- Placement produces shared intermediate-shaft coordinates
- Invalid bore and backlash are rejected

### Fusion integration checks

Manually verify at least:

1. One stage: 20/40 teeth, module 1
2. Two stages: 15/45 and 18/54 teeth, module 1
3. Four stages with valid moderate tooth counts
4. Change stage count from four to one and back; hidden values survive
5. Cancel preview; no geometry remains
6. Confirm creation; all gears are separate named components
7. Inspect a mating pair at the calculated center distance
8. Export representative gears and slice them to check contour integrity

## 16. Milestones

### Milestone 0 — Inspect and preserve the generated skeleton

- Inspect all files in the empty Fusion add-in
- Identify entry points, manifest, command registration, and resource conventions
- Run the untouched add-in once
- Record the Fusion version and Python/API assumptions

Acceptance: the empty command loads and unloads without errors.

### Milestone 1 — Pure calculation core

- Add data models
- Add radius, ratio, center-distance, shaft, and placement calculations
- Add validation
- Add automated unit tests

Acceptance: tests pass without launching Fusion.

### Milestone 2 — Single-gear geometry

- Implement involute sampling
- Create one closed profile and bore
- Create one component and extrusion
- Validate against known dimensions

Acceptance: one valid external spur gear is created reliably.

### Milestone 3 — Standard command dialog

- Create the three tabs
- Add one to four dynamic stage groups
- Add live calculated values and warnings
- Add validation

Acceptance: dialog behavior matches the specification and retains hidden values.

### Milestone 4 — Multi-stage generation

- Derive physical gears and shafts
- Position gear pairs and compound shafts
- Create separate named components
- Add preview and cancel cleanup

Acceptance: one- through four-stage examples generate without overlap or orphan preview objects.

### Milestone 5 — Packaging and documentation

- Finalize resources and icons
- Add installation instructions
- Add examples and screenshots
- Add license and contribution guidance
- Add German documentation links when translations exist

Acceptance: a new user can install and create the documented example from a clean checkout.

## 17. Codex working rules

When implementation begins:

1. Inspect the repository and any `AGENTS.md` before editing.
2. Do not overwrite unrelated user changes.
3. Propose the smallest milestone-sized plan.
4. Implement pure calculations before Fusion-bound geometry.
5. Keep `adsk` imports out of testable core modules.
6. Use explicit units in variable names.
7. Avoid magic constants; document standard-derived values.
8. Run available tests after every material change.
9. Report exactly what was changed, tested, and not yet verified in Fusion.
10. Do not claim mechanical strength, standards compliance, or manufacturability that has not been validated.

## 18. Version-1 completion criteria

Version 1 is complete when a user can create a valid one- to four-stage external spur-gear train using the standard dialog, obtain correctly named separate Fusion components at calculated shaft positions, see accurate ratios and warnings, cancel without residue, and reproduce the documented reference examples.
