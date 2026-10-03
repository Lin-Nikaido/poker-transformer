# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""check header"""

import sys
from pathlib import Path


HEADER = "# Copyright (c) 2026 YourIndependence."

failed = []

for path in Path(".").rglob("*.py"):
    if path.name == "__init__.py":
        continue

    text = path.read_text(encoding="utf-8")

    if not text.startswith(HEADER):
        failed.append(str(path))

if failed:
    print("Missing header:")
    for f in failed:
        print(f)
    sys.exit(1)

print("Header check passed")
