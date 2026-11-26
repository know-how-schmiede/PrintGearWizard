# PrintGearWizard 0.2.6

<img src="images/PrintGearWizard_TitelLogo.png" alt="PrintGear Wizard Logo" width="420">

PrintGearWizard is an open-source Autodesk Fusion add-in for creating configurable, 3D-print-friendly spur gears and simple multi-stage gear trains.

The first release focuses on standard external involute spur gears and one to four reduction stages. Users enter the common gear parameters and the tooth counts for each stage; the add-in calculates the gear geometry, ratios, center distances, shaft assignments, rotation directions, and Fusion component placement.

## Planned first release

- One to four gear stages
- Standard 20-degree involute external spur gears
- Shared module, pressure angle, face width, backlash, and safety clearance
- Automatic compound intermediate shafts
- Automatic ratio and center-distance calculation
- Separate Fusion components for every gear
- Configurable round shaft bores
- Print-oriented backlash defaults
- Live validation and preview
- English user interface with German documentation added later

## Project status

Version 0.2.6 provides the executable Fusion add-in skeleton, the first
Fusion-independent gear-train calculation core, and the standard three-tab
configuration dialog with live input validation and automated core tests. It
can create and dimensionally verify every configured gear as a separate,
positioned component on a selected planar construction reference in a compatible
hybrid design. The add-in registers a
PrintGearWizard command under **Design > Solid > Create**, displays the project
icon, and opens the initial dialog without modifying the active design.

## Documentation

- [Codex implementation guide](docs/CODEX_PROJECT_GUIDE.md)
- [GitHub repository setup](docs/GITHUB_SETUP.md)
- [Screenshots](docs/screenshots.md)
- [Version timeline](docs/version-timeline.md)

## Trademark notice

Autodesk and Autodesk Fusion are registered trademarks or trademarks of Autodesk, Inc. PrintGearWizard is an independent project and is not affiliated with or endorsed by Autodesk.

## Packaging a Fusion add-in release

From the repository root, check out the release commit and run this command with Git (Bash or Git Bash). It packages the tracked runtime files under the folder name Fusion expects.

```sh
git archive --format=zip --prefix=PrintGearWizard/ --output=PrintGearWizard-universal.zip --add-file=LICENSE HEAD:fusion_addin/PrintGearWizard -- PrintGearWizard.manifest PrintGearWizard.py AddInIcon.svg commands config.py core fusion lib version.py
```

Upload `PrintGearWizard-universal.zip` as an asset of a stable GitHub Release. Use a numeric tag such as `v0.2.6` matching the version in `PrintGearWizard.manifest`.
