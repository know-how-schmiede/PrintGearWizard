# PrintGearWizard version timeline

This file records all user-visible and technical project changes by release.

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
