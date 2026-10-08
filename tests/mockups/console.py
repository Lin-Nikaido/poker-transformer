"""Reusable deterministic poker test doubles."""

from __future__ import annotations

import pytest

from poker.core.actions.action_source import BaseActionSource
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.decisions import DecisionRequest


@pytest.fixture
def mock_action_source() -> MockActionSource:
    """Create asynchronous input without reading a real terminal."""
    return MockActionSource()


class MockActionSource(BaseActionSource):
    def __init__(self, *, action: Action | None = None) -> None:
        self.action = (
            action if action is not None else Action(kind=ActionKind.CALL)
        )
        self.requests: list[DecisionRequest] = []

    async def read_action(self, *, request: DecisionRequest) -> Action:
        self.requests.append(request)
        return self.action
