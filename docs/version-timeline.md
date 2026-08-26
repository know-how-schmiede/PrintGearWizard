# PrintGearWizard version timeline

This file records all user-visible and technical project changes by release.

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
