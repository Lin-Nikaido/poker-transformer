# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.
"""version command"""

from importlib.metadata import version

import typer


app = typer.Typer(invoke_without_command=True)


@app.callback()
def show_version() -> None:
    """Show version"""
    typer.echo(version("poker-transformer"))
