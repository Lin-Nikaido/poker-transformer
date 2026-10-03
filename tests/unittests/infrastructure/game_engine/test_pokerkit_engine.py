from decimal import Decimal

import pytest
from pokerkit import Automation
from pokerkit import NoLimitTexasHoldem

from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.primitives import Seat
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitEngine
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitHand


def test_start_hand_uses_agreed_six_max_configuration() -> None:
    hand = PokerKitEngine().start_hand()

    assert hand.acting_seat is Seat.UTG
    assert hand.is_terminal is False
    legal_actions = hand.get_legal_actions()
    assert legal_actions.action_kinds == (
        ActionKind.FOLD,
        ActionKind.CALL,
        ActionKind.RAISE,
    )
    assert isinstance(legal_actions.minimum_bet_or_raise_to, Decimal)
    assert isinstance(legal_actions.maximum_bet_or_raise_to, Decimal)
    assert legal_actions.minimum_bet_or_raise_to == Decimal("2")
    assert legal_actions.maximum_bet_or_raise_to == Decimal("100")


def test_legal_action_amounts_convert_integer_engine_values() -> None:
    state = NoLimitTexasHoldem.create_state(
        automations=tuple(Automation),
        ante_trimming_status=True,
        raw_antes=0,
        raw_blinds_or_straddles=(0, 0, 0, 0, 1, 2),
        min_bet=2,
        raw_starting_stacks=(100,) * 6,
        player_count=6,
    )
    assert isinstance(state.min_completion_betting_or_raising_to_amount, int)
    assert isinstance(state.max_completion_betting_or_raising_to_amount, int)
    hand = PokerKitHand(state=state)

    legal_actions = hand.get_legal_actions()

    assert legal_actions.minimum_bet_or_raise_to == Decimal("4")
    assert legal_actions.maximum_bet_or_raise_to == Decimal("100")
    assert isinstance(legal_actions.minimum_bet_or_raise_to, Decimal)
    assert isinstance(legal_actions.maximum_bet_or_raise_to, Decimal)


def test_fold_ends_hand_when_one_player_remains() -> None:
    hand = PokerKitEngine().start_hand()

    for _ in range(5):
        hand.step(action=Action(kind=ActionKind.FOLD))

    assert hand.is_terminal is True
    assert hand.acting_seat is None
    assert hand.get_legal_actions().action_kinds == ()


def test_rejects_actions_outside_the_legal_action_set() -> None:
    hand = PokerKitEngine().start_hand()

    with pytest.raises(ValueError, match="is not legal"):
        hand.step(action=Action(kind=ActionKind.CHECK))


def test_raise_to_amount_advances_to_the_next_actor() -> None:
    hand = PokerKitEngine().start_hand()

    hand.step(
        action=Action(
            kind=ActionKind.RAISE,
            amount=Decimal("2"),
        ),
    )

    assert hand.acting_seat is Seat.MP
    assert ActionKind.CALL in hand.get_legal_actions().action_kinds
