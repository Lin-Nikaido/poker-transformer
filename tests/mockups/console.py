"""Reusable deterministic poker test doubles."""

from __future__ import annotations

import pytest

from poker.core.ports.action_source import BaseActionSource
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.decisions import DecisionRequest


@pytest.fixture
def fake_action_source() -> FakeActionSource:
    """Create asynchronous input without reading a real terminal."""
    return FakeActionSource()


class FakeActionSource(BaseActionSource):
    def __init__(self) -> None:
        self.requests: list[DecisionRequest] = []

    async def read_action(self, *, request: DecisionRequest) -> Action:
        self.requests.append(request)
        return Action(kind=ActionKind.CALL)
