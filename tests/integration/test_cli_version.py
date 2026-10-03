# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import asyncio
import os
import sys
from importlib.metadata import version

import pytest


@pytest.mark.asyncio
async def test_version_command_displays_installed_package_version() -> None:
    command_name = "poker.exe" if sys.platform == "win32" else "poker"
    command_path = os.path.join(os.path.dirname(sys.executable), command_name)
    process = await asyncio.create_subprocess_exec(
        command_path,
        "version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    assert process.returncode == 0, stderr.decode()
    assert stdout.decode().strip() == version("poker-transformer")
