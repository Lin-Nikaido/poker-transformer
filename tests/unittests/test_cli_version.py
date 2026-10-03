from typer.testing import CliRunner

from poker.cli.__main__ import app


def test_version_option_displays_package_version() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"
