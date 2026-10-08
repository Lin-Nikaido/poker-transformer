"""Deterministic UUID v4 values for tests."""

from uuid import UUID


def mock_uuid(index: int) -> UUID:
    """Return a stable UUID with version 4 bits for the supplied test index."""
    return UUID(int=index, version=4)
