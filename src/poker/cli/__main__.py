# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""cli entrypoint."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterable
from pathlib import Path

import typer


app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="poker ai CLI",
)


def _iter_command_module_names() -> Iterable[str]:
    pkg_name = __package__
    if not pkg_name:
        return

    pkg = importlib.import_module(pkg_name)
    pkg_path = Path(pkg.__file__).parent  # src/cli

    for m in pkgutil.iter_modules([str(pkg_path)]):
        name = m.name
        if name in {"__main__", "__init__"}:
            continue
        if name.startswith("_"):
            continue
        yield name


def _register_subcommands() -> None:
    for mod_name in _iter_command_module_names():
        mod = importlib.import_module(
            f"{__package__}.{mod_name}"
        )  # cli.<mod_name>
        sub_app = getattr(mod, "app", None)
        if sub_app is None:
            continue

        command_name = getattr(mod, "COMMAND_NAME", mod_name)
        app.add_typer(sub_app, name=command_name)


_register_subcommands()


def main() -> None:
    """Main command."""
    app()


if __name__ == "__main__":
    main()
