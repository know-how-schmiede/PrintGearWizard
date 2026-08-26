"""Synchronize static project files with the canonical add-in version."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "fusion_addin" / "PrintGearWizard" / "version.py"
MANIFEST_FILE = ROOT / "fusion_addin" / "PrintGearWizard" / "PrintGearWizard.manifest"
README_FILE = ROOT / "README.md"


def read_version() -> str:
    match = re.fullmatch(
        r"\s*VERSION\s*=\s*['\"]([^'\"]+)['\"]\s*",
        VERSION_FILE.read_text(encoding="utf-8"),
    )
    if not match:
        raise ValueError(f"Could not read VERSION from {VERSION_FILE}")
    return match.group(1)


def expected_content() -> dict[Path, str]:
    version = read_version()

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"

    readme = README_FILE.read_text(encoding="utf-8")
    readme_text, replacements = re.subn(
        r"(?m)^# PrintGearWizard(?:\s+\S+)?$",
        f"# PrintGearWizard {version}",
        readme,
        count=1,
    )
    if replacements != 1:
        raise ValueError(f"Could not find the README title in {README_FILE}")

    return {MANIFEST_FILE: manifest_text, README_FILE: readme_text}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="report stale files without changing them",
    )
    args = parser.parse_args()

    stale = []
    for path, expected in expected_content().items():
        if path.read_text(encoding="utf-8") == expected:
            continue
        stale.append(path)
        if not args.check:
            path.write_text(expected, encoding="utf-8", newline="\n")

    if stale:
        action = "Out of date" if args.check else "Updated"
        print(f"{action}: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
        return 1 if args.check else 0

    print(f"Version {read_version()} is synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
