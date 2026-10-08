"""Reusable deterministic poker test doubles."""

from __future__ import annotations

from decimal import Decimal

import pytest

from poker.core.game.game import Game
from poker.core.game_engine.base_game_engine import BaseGameEngine
from poker.core.players.base_player import BasePlayer
from poker.core.types.actions import Action
from poker.core.types.actions import ActionHistory
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street
from poker.core.types.table import PlayerObservation
from poker.core.types.table import TableState


@pytest.fixture
def fake_engine() -> FakeEngine:
    """Create a fresh isolated six-player engine."""
    return FakeEngine()


class ScriptedPlayer(BasePlayer):
    async def select_action(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        self.validate_request(request=request)
        return PlayerDecision(action=Action(kind=ActionKind.FOLD))


class FakeEngine(BaseGameEngine):
    def __init__(self) -> None:
        self.starts: list[tuple[Decimal, ...]] = []
        self.actions: list[Action] = []

    def start_hand(self, *, starting_stacks: tuple[Decimal, ...]) -> None:
        self.starts.append(starting_stacks)
        self.actions = []

    @property
    def acting_seat(self) -> Seat | None:
        return (
            tuple(Seat)[len(self.actions)]
            if self.starts and not self.is_terminal
            else None
        )

    @property
    def is_terminal(self) -> bool:
        return bool(self.starts) and len(self.actions) == 5

    def get_legal_actions(self) -> LegalActions:
        return LegalActions(action_kinds=(ActionKind.FOLD,))

    def get_observation(self, *, seat: Seat) -> PlayerObservation:
        return PlayerObservation(
            seat=seat,
            private_hand=Hand(
                cards=(
                    Card(rank=CardRank.ACE, suit=Suit.SPADES),
                    Card(rank=CardRank.KING, suit=Suit.SPADES),
                )
            ),
            public_state=TableState(
                street=Street.PREFLOP,
                pot=Decimal("1.5"),
                current_actor=self.acting_seat,
                players=tuple(
                    PublicPlayerState(seat=position, stack=stack)
                    for position, stack in zip(
                        Seat, self.get_stacks(), strict=True
                    )
                ),
                community_cards=(),
                action_history=ActionHistory(),
            ),
        )

    def get_stacks(self) -> tuple[Decimal, ...]:
        if self.is_terminal:
            return (
                *self.starts[-1][:4],
                self.starts[-1][4] - Decimal("0.5"),
                self.starts[-1][5] + Decimal("0.5"),
            )
        return self.starts[-1]

    def submit_action(self, *, action: Action) -> Action:
        self.actions.append(action)
        return action


def make_game(*, engine: BaseGameEngine) -> Game:
    game = Game(engine=engine)
    for index in range(6):
        game.seat_player(
            player=ScriptedPlayer(player_id=f"player-{index}"),
            table_seat=index,
            stack=Decimal(100 + index),
        )
    return game
