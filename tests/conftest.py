"""Register reusable mock fixtures for isolated poker tests."""

pytest_plugins = (
    "tests.mockups.game",
    "tests.mockups.models",
    "tests.mockups.console",
    "tests.mockups.play",
)
