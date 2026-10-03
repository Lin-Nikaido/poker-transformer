# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""insert header"""

from __future__ import annotations

import sys
from pathlib import Path


HEADER = """# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""

TARGET_SUFFIXES = {".py"}


def _has_header(text: str) -> bool:
    return text.startswith("# Copyright (c) 2026 YourIndependence. All rights reserved.")


def _insert_header(text: str) -> str:
    if _has_header(text):
        return text

    if text.startswith("#!"):
        lines = text.splitlines(keepends=True)
        if len(lines) >= 2 and "coding" in lines[1]:
            return lines[0] + lines[1] + HEADER + "".join(lines[2:])
        return lines[0] + HEADER + "".join(lines[1:])

    lines = text.splitlines(keepends=True)
    if lines and "coding" in lines[0]:
        return lines[0] + HEADER + "".join(lines[1:])

    return HEADER + text


def _process_file(path: Path) -> bool:
    if path.suffix not in TARGET_SUFFIXES:
        return False
    if not path.exists() or not path.is_file():
        return False

    original = path.read_text(encoding="utf-8")
    updated = _insert_header(original)

    if updated != original:
        path.write_text(updated, encoding="utf-8", newline="")
        print(f"updated: {path}")
        return True
    return False


def main() -> int:
    """Main."""
    changed = False
    for arg in sys.argv[1:]:
        if _process_file(Path(arg)):
            changed = True
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
