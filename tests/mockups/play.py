"""Reusable deterministic poker test doubles."""

from __future__ import annotations

import pytest
import torch
from torch import Tensor
from torch import nn

from poker.core.ports.action_source import BaseActionSource
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


@pytest.fixture
def fold_input() -> FoldInput:
    """Create input for a human who folds each requested hand."""
    return FoldInput()


@pytest.fixture
def recorder() -> Recorder:
    """Create an isolated recorder of decisions and model traces."""
    return Recorder()


class FoldInput(BaseActionSource):
    async def read_action(self, *, request: DecisionRequest) -> Action:
        assert request.player_id.version == 4
        return Action(kind=ActionKind.FOLD)


class FoldModel(nn.Module):
    def forward(self, inputs: Tensor) -> Tensor:
        logits = torch.full((15,), -1000.0)
        logits[0] = inputs.sum() * 0
        return logits


class Recorder(BaseGameObserver):
    def __init__(self) -> None:
        self.decisions: list[tuple[DecisionRequest, PlayerDecision]] = []

    async def on_decision(
        self,
        *,
        request: DecisionRequest,
        decision: PlayerDecision,
        applied_action: Action,
    ) -> None:
        assert applied_action.kind is ActionKind.FOLD
        self.decisions.append((request, decision))
