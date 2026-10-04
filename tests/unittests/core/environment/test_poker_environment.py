from decimal import Decimal

import pytest

from poker.core.environment.poker_environment import PokerEnvironment
from poker.core.ports.game_engine import GameEngine
from poker.core.ports.game_engine import PokerGame
from poker.core.types.actions import Action
from poker.core.types.actions import ActionHistory
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.hand_result import HandResult
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import Seat
from poker.core.types.table import PlayerObservation
from poker.core.types.table import TableState


class FakeGameEngine(GameEngine):
    def __init__(self) -> None:
        self.started_hands = 0

    def start_hand(self) -> PokerGame:
        self.started_hands += 1
        return FakePokerGame()


class FakePokerGame(PokerGame):
    def __init__(self) -> None:
        super().__init__()
        self._step_count = 0

    @property
    def acting_seat(self) -> Seat | None:
        if self.is_terminal:
            return None
        return Seat.UTG if self._step_count == 0 else Seat.MP

    @property
    def is_terminal(self) -> bool:
        return self._step_count == 2

    def get_legal_actions(self) -> LegalActions:
        return LegalActions(
            action_kinds=(ActionKind.CALL, ActionKind.CHECK),
        )

    def get_observation(self) -> PlayerObservation:
        acting_seat = self.acting_seat
        if acting_seat is None:
            raise ValueError("A terminal hand has no player observation")
        players = tuple(
            PublicPlayerState(seat=seat, stack=Decimal("100")) for seat in Seat
        )
        return PlayerObservation(
            seat=acting_seat,
            private_hand=Hand(
                cards=(
                    Card(rank=CardRank.ACE, suit=Suit.SPADES),
                    Card(rank=CardRank.KING, suit=Suit.SPADES),
                ),
            ),
            public_state=TableState(
                street="preflop",
                pot=Decimal("1.5"),
                current_actor=acting_seat,
                players=players,
                community_cards=(),
                action_history=ActionHistory(),
            ),
        )

    def get_result(self) -> HandResult:
        if not self.is_terminal:
            raise ValueError("A hand result is available only when terminal")
        return HandResult(
            starting_stacks=(Decimal("100"),) * 6,
            final_stacks=(
                Decimal("100.5"),
                Decimal("99.5"),
                Decimal("100"),
                Decimal("100"),
                Decimal("100"),
                Decimal("100"),
            ),
            initial_big_blind=Decimal("1"),
        )

    def step(self, *, action: Action) -> None:
        if self.is_terminal:
            raise ValueError("The hand is already terminal")
        if action.kind not in self.get_legal_actions().action_kinds:
            raise ValueError("The action is not legal")
        self._step_count += 1


def test_reset_returns_only_the_current_players_observation() -> None:
    engine = FakeGameEngine()
    environment = PokerEnvironment(game_engine=engine)

    state = environment.reset()

    assert engine.started_hands == 1
    assert state.observation.seat is Seat.UTG
    assert state.observation.public_state.current_actor is Seat.UTG
    assert state.legal_actions.action_kinds == (
        ActionKind.CALL,
        ActionKind.CHECK,
    )


def test_step_returns_terminal_zero_sum_rewards_only_at_hand_end() -> None:
    environment = PokerEnvironment(game_engine=FakeGameEngine())
    environment.reset()

    first_step = environment.step(action=Action(kind=ActionKind.CALL))
    terminal_step = environment.step(action=Action(kind=ActionKind.CHECK))

    assert first_step.acting_seat is Seat.UTG
    assert first_step.is_terminal is False
    assert first_step.rewards is None
    assert first_step.next_state is not None
    assert first_step.next_state.observation.seat is Seat.MP
    assert terminal_step.acting_seat is Seat.MP
    assert terminal_step.is_terminal is True
    assert terminal_step.next_state is None
    assert terminal_step.rewards == (
        Decimal("0.5"),
        Decimal("-0.5"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
    )
    assert sum(terminal_step.rewards) == Decimal("0")


def test_reset_starts_a_new_hand_and_terminal_episode_rejects_steps() -> None:
    engine = FakeGameEngine()
    environment = PokerEnvironment(game_engine=engine)
    environment.reset()
    environment.step(action=Action(kind=ActionKind.CALL))
    environment.step(action=Action(kind=ActionKind.CHECK))

    with pytest.raises(ValueError, match="terminal episode"):
        environment.step(action=Action(kind=ActionKind.CALL))

    assert environment.reset().observation.seat is Seat.UTG
    assert engine.started_hands == 2
