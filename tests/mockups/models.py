"""Reusable deterministic poker test doubles."""

from __future__ import annotations

from decimal import Decimal

import pytest
import torch
from torch import Tensor
from torch import nn

from poker.core.ports.observation_encoder import BaseObservationEncoder
from poker.core.types.actions import ActionHistory
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.decisions import DecisionRequest
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street
from poker.core.types.table import PlayerObservation
from poker.core.types.table import TableState
from tests.mockups.ids import mock_uuid


@pytest.fixture
def stub_encoder() -> StubEncoder:
    """Create an encoder consuming only the player's observation."""
    return StubEncoder()


class StubEncoder(BaseObservationEncoder):
    def encode(self, *, observation: PlayerObservation) -> Tensor:
        return torch.tensor([observation.private_hand.cards[0].rank.to_num()])


class StubModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.logits = nn.Parameter(torch.arange(15, dtype=torch.float32))

    def forward(self, inputs: Tensor) -> Tensor:
        return self.logits + inputs.sum() * 0


def make_request(*, legal_kinds: tuple[ActionKind, ...]) -> DecisionRequest:
    return DecisionRequest(
        player_id=mock_uuid(1),
        hand_id=mock_uuid(100),
        revision=0,
        observation=PlayerObservation(
            seat=Seat.UTG,
            private_hand=Hand(
                cards=(
                    Card(rank=CardRank.ACE, suit=Suit.SPADES),
                    Card(rank=CardRank.KING, suit=Suit.SPADES),
                )
            ),
            public_state=TableState(
                street=Street.PREFLOP,
                pot=Decimal("1.5"),
                current_actor=Seat.UTG,
                players=tuple(
                    PublicPlayerState(seat=seat, stack=Decimal("100"))
                    for seat in Seat
                ),
                community_cards=(),
                action_history=ActionHistory(),
            ),
        ),
        legal_actions=LegalActions(action_kinds=legal_kinds),
    )
