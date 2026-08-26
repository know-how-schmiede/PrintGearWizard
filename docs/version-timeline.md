# PrintGearWizard version timeline

This file records all user-visible and technical project changes by release.

## 0.2.3 — 2026-08-26

- Added pre-generation collision planning based on addendum-circle clearance.
- Checked non-mating gears assigned to the same axial plane before creating Fusion geometry.
- Preserved the compact alternating two-plane layout whenever it is collision-free.
- Automatically assigned a stage to the next free axial plane when its preferred plane would collide.
- Added collision messages containing the affected gear IDs and calculated overlap in millimetres.
- Displayed the resolved layout and fallback warnings live on the construction tab and in validation results.
- Used the same resolved collision-free placements during final body generation.
- Added regression tests for both collision-free two-plane layouts and automatic third-plane fallback.
- Updated the project guide with the preferred-plane and fallback rules.

## 0.2.2 — 2026-08-26

- Replaced continuously stacked stage planes with a compact two-plane axial layout.
- Assigned odd-numbered stages to the first axial plane at `z = 0`.
- Assigned even-numbered stages to the second plane at `z = face width + 1 mm`.
- Returned stages 3 and 4 to the first and second planes respectively.
- Preserved a common plane for both mating gears within each stage.
- Preserved alternating planes for the two compound gears on every intermediate shaft.
- Added a four-stage regression test that verifies only two unique Z positions are used.
- Updated the project guide to make the two-plane rule explicit.

## 0.2.1 — 2026-08-26

- Documented the top-level `PrintGearWizard Gear Train` component as the required container for all generated gear components.
- Preserved the container hierarchy so the complete generated train can be moved, hidden, or removed as one occurrence.
- Collected all component, sketch, and extrusion operations created by one command run into one Fusion timeline group.
- Named timeline groups with the generated gear count and collapsed them after successful creation.
- Treated timeline grouping as part of the atomic generation operation and rolled back if grouping fails.

## 0.2.0 — 2026-08-26

- Added generation of two separate physical gear components for every active stage.
- Positioned shafts at cumulative calculated center distances in horizontal or vertical layouts.
- Placed both gears of each mesh on the same axial stage plane.
- Placed compound gears of adjacent stages on their shared intermediate-shaft coordinates.
- Stacked successive stage planes by gear width plus the internal 1 mm axial gap.
- Added driven-gear phase rotation so a tooth gap faces the corresponding driver tooth.
- Extruded and dimensionally verified every generated gear body.
- Verified the final body count against twice the configured stage count.
- Retained all-or-nothing cleanup if any gear fails during generation.
- Kept selected construction-plane/origin placement and preview cleanup for later versions.

## 0.1.9 — 2026-08-26

- Added post-extrusion verification before generated geometry is accepted.
- Verified that Fusion created a solid body with positive volume.
- Compared the resulting body width with the configured gear width.
- Compared the maximum body-vertex radius with the calculated addendum radius.
- Located the cylindrical bore face and compared its radius with the configured shaft bore.
- Added explicit dimensional error messages with actual and expected values.
- Rolled back the generated component tree whenever a dimensional check fails.
- Added a 20-tooth, module-1 reference test for the expected 22 mm outside diameter.
- Completed the single-gear geometry milestone; multi-stage creation remains disabled.

## 0.1.8 — 2026-08-26

- Selected the largest closed sketch region and verified that it contains the bore loop.
- Added a one-sided positive extrusion using the configured gear width.
- Created exactly one new solid body for the stage-1 driver.
- Added stable names for the profile sketch, extrusion feature, and resulting body.
- Hid the source sketch after successful extrusion.
- Added actionable errors for missing profiles, missing bore loops, invalid extents, or unexpected body counts.
- Retained automatic removal of the complete generated component tree after an extrusion failure.
- Kept selected-plane placement and additional gears for later versions.

## 0.1.7 — 2026-08-26

- Added a centralized active-document and Fusion design-intent compatibility check.
- Allowed internal gear components only in writable hybrid designs.
- Blocked part designs because they cannot contain child components.
- Blocked assembly designs because generated parts would need to be external components.
- Blocked read-only configuration documents and Fusion versions that cannot report design intent.
- Added a visible compatibility status at the top of the basic-data tab.
- Repeated the compatibility check immediately before geometry creation to prevent bypasses.
- Isolated use of Fusion's preview design-intent API behind one integration module.

## 0.1.6 — 2026-08-26

- Added complete counter-clockwise gear-outline construction from sampled involute flanks.
- Added polygonal addendum and root arcs plus controlled radial root transitions.
- Removed consecutive duplicate points and made contour closure explicit.
- Added a Fusion integration boundary that converts millimetres only when creating sketch geometry.
- Added creation of a top-level gear-train component and a stable stage-1 driver component.
- Added a closed stage-1 driver profile sketch and separate round bore on the component XY plane.
- Added outline closure, radius-bound, and zero-length-segment tests.
- Corrected the involute flank orientation so teeth narrow toward the addendum instead of widening outward.
- Kept extrusion, selected-plane placement, preview geometry, and additional gears for later versions.

## 0.1.5 — 2026-08-26

- Refreshed calculated dialog results when Fusion commits a value with Enter or a focus change.
- Updated read-only result fields through their formatted-text API for immediate repainting.
- Added validation-time refresh as a fallback, removing the need to switch dialog tabs.
- Added Fusion-independent involute parameter, point, rotation, and sampling calculations.
- Added symmetric tooth-flank generation with documented per-gear backlash semantics.
- Added automated tests for involute endpoint radii, flank symmetry, and backlash reduction.
- Kept version 0.1.5 non-destructive; sampled tooth curves are not yet written into Fusion sketches.

## 0.1.4 — 2026-08-26

- Added automated unit tests using Python's standard `unittest` framework.
- Added reference tests for gear radii, center distance, stage ratios, and total ratios.
- Added gear-count, shaft-assignment, stable-name, and compound-shaft tests for one to four stages.
- Added horizontal, vertical, and axial placement tests.
- Added validation tests for stage count, module, bore count, bore wall, backlash, and warnings.
- Kept the test suite independent of Autodesk Fusion and external test dependencies.

## 0.1.3 — 2026-08-26

- Added Fusion-independent blocking validation and non-blocking warning results.
- Added checks for stage count, positive dimensions, pressure angle, involute sampling, and shaft bore count.
- Added minimum tooth-count, positive root-radius, real involute, tooth-thickness, and bore-wall checks.
- Added printability warnings for low tooth counts, small modules, unusual backlash, and large diameters.
- Added a live validation summary to the gear-stages tab.
- Disabled command confirmation whenever blocking errors or invalid numeric expressions are present.
- Kept version 0.1.3 non-destructive; successful confirmation still creates no geometry.

## 0.1.2 — 2026-08-26

- Added the standard three-tab command dialog for basic data, gear stages, and construction.
- Added common module, pressure-angle, width, backlash, and print-profile inputs.
- Added four persistent stage groups whose visibility follows the selected stage count.
- Added live stage ratios, center distances, total ratio, gear count, shaft count, and rotation direction.
- Added undercut warnings for gears with fewer than 17 teeth.
- Added optional construction-plane and start-point selections.
- Added horizontal/vertical layout selection and dynamically visible bore inputs for all shafts.
- Added the fixed separate-component output mode and preview option.
- Kept command execution non-destructive; version 0.1.2 does not create geometry.

## 0.1.1 — 2026-08-26

- Added pure calculations for standard gear radii and external-gear center distances.
- Added stage and total transmission-ratio calculations.
- Added deterministic physical-gear and shaft assignment for one to four stages.
- Added odd/even output rotation-direction derivation.
- Added horizontal and vertical linear placement with a 1 mm axial gap between stage planes.
- Kept all calculation code independent of the Autodesk Fusion API.

## 0.1.0 — 2026-08-26

- Established `fusion_addin/PrintGearWizard/version.py` as the canonical version source.
- Displayed version 0.1.0 in the Fusion command and dialog title.
- Set the add-in manifest version to 0.1.0.
- Displayed version 0.1.0 in the root README heading.
- Added a version synchronization tool for the manifest and README.
- Reduced the generated Autodesk sample to one PrintGearWizard command.
- Registered the command in **Design > Solid > Create**.
- Added the initial status-only dialog; it intentionally creates no geometry yet.
- Replaced the generated sample command icons with the PrintGearWizard project icons.
- Kept start/stop registration and event cleanup from the generated Fusion add-in skeleton.
- Updated `.gitignore` for conflict-free local Fusion testing while retaining required manifest and runtime helper sources.
- Added immutable, Fusion-independent domain models for standards, stages, gears, calculated geometry, results, and placement.
