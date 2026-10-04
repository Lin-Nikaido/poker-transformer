# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

from collections import deque
from decimal import Decimal

import pytest
from pokerkit import Automation
from pokerkit import Card
from pokerkit import Deck
from pokerkit import NoLimitTexasHoldem

from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.actions import BetSize
from poker.core.types.primitives import Seat
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitEngine
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitHand


def _create_hand(
    *,
    starting_stacks: tuple[Decimal, ...] = (Decimal("100"),) * 6,
) -> PokerKitHand:
    state = NoLimitTexasHoldem.create_state(
        automations=tuple(Automation),
        ante_trimming_status=True,
        raw_antes=Decimal("0"),
        raw_blinds_or_straddles=(
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0.5"),
            Decimal("1"),
        ),
        min_bet=Decimal("1"),
        raw_starting_stacks=starting_stacks,
        player_count=6,
    )
    return PokerKitHand(state=state)


def _set_showdown_cards(
    *,
    hand: PokerKitHand,
    fixed_holes: tuple[tuple[str, str], ...],
) -> None:
    fixed_board = ("2d", "4d", "7h", "9s", "Jh")
    burn_and_board_cards = ("Qc", "2d", "4d", "7h", "Jc", "9s", "Ts", "Jh")
    holes = tuple(
        tuple(next(Card.parse(raw_card)) for raw_card in hole)
        for hole in fixed_holes
    )
    reserved_cards = {
        card
        for raw_card in (
            *fixed_board,
            *(card for hole in fixed_holes for card in hole),
        )
        for card in Card.parse(raw_card)
    }
    scripted_cards = tuple(
        next(Card.parse(raw_card)) for raw_card in burn_and_board_cards
    )
    remaining_cards = tuple(
        card
        for card in Deck.STANDARD.value
        if card not in reserved_cards and card not in scripted_cards
    )
    hand._state.hole_cards[:] = [list(hole) for hole in holes]
    hand._state.deck_cards = deque((*scripted_cards, *remaining_cards))


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


def test_observation_exposes_only_actor_cards_and_public_player_states() -> (
    None
):
    hand = PokerKitEngine().start_hand()

    observation = hand.get_observation()

    assert observation.seat is Seat.UTG
    assert observation.public_state.current_actor is Seat.UTG
    assert len(observation.private_hand.cards) == 2
    assert all(
        not hasattr(player, "hand")
        for player in observation.public_state.players
    )
    assert len(observation.public_state.players) == 6


def test_observation_records_actions_by_street() -> None:
    hand = PokerKitEngine().start_hand()

    hand.step(action=Action(kind=ActionKind.CALL))
    observation = hand.get_observation()

    assert len(observation.public_state.action_history.preflop) == 1
    entry = observation.public_state.action_history.preflop[0]
    assert entry.actor is Seat.UTG
    assert entry.action.kind is ActionKind.CALL


def test_result_is_terminal_and_reports_stacks_in_seat_order() -> None:
    hand = PokerKitEngine().start_hand()

    with pytest.raises(ValueError, match="only when terminal"):
        hand.get_result()
    for _ in range(5):
        hand.step(action=Action(kind=ActionKind.FOLD))

    result = hand.get_result()

    assert result.starting_stacks == (Decimal("100"),) * 6
    assert result.final_stacks == (
        Decimal("100"),
        Decimal("100"),
        Decimal("100"),
        Decimal("100"),
        Decimal("99.5"),
        Decimal("100.5"),
    )
    assert result.initial_big_blind == Decimal("1")


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
    assert hand._state.stacks[5] == Decimal("100.5")
    assert sum(hand._state.stacks) == Decimal("600")


def test_rejects_actions_outside_the_legal_action_set() -> None:
    hand = PokerKitEngine().start_hand()

    with pytest.raises(ValueError, match="is not legal"):
        hand.step(action=Action(kind=ActionKind.CHECK))


@pytest.mark.parametrize("kind", (ActionKind.FOLD, ActionKind.CALL))
def test_rejects_bet_size_on_non_betting_action(kind: ActionKind) -> None:
    hand = PokerKitEngine().start_hand()

    with pytest.raises(ValueError, match="only valid for bet and raise"):
        hand.step(action=Action(kind=kind, bet_size=BetSize.POT_80))


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


def test_explicit_raise_to_amount_is_preserved() -> None:
    hand = PokerKitEngine().start_hand()

    hand.step(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("2.25")),
    )

    assert hand._state.bets[0] == Decimal("2.25")


@pytest.mark.parametrize(
    ("bet_size", "expected_target"),
    (
        (BetSize.POT_20, Decimal("2")),
        (BetSize.POT_50, Decimal("2.25")),
        (BetSize.POT_80, Decimal("3")),
        (BetSize.POT_100, Decimal("3.5")),
        (BetSize.POT_150, Decimal("4.75")),
        (BetSize.POT_200, Decimal("6")),
    ),
)
def test_pot_sizing_resolves_to_legal_preflop_raise(
    bet_size: BetSize,
    expected_target: Decimal,
) -> None:
    hand = PokerKitEngine().start_hand()

    hand.step(
        action=Action(
            kind=ActionKind.RAISE,
            bet_size=bet_size,
        ),
    )

    assert hand._state.bets[0] == expected_target


@pytest.mark.parametrize("target_amount", (Decimal("40"), Decimal("50")))
def test_reraise_at_or_above_half_remaining_stack_becomes_all_in(
    target_amount: Decimal,
) -> None:
    hand = _create_hand(starting_stacks=(Decimal("80"),) * 6)

    hand.step(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("10")),
    )
    hand.step(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("20")),
    )
    hand.step(
        action=Action(kind=ActionKind.RAISE, amount=target_amount),
    )

    assert hand._state.bets[2] == Decimal("80")
    assert hand._state.stacks[2] == Decimal("0")


def test_showdown_awards_best_hand_and_preserves_all_chips() -> None:
    hand = _create_hand()
    fixed_holes = (
        ("As", "Ad"),
        ("Ks", "Kd"),
        ("2c", "3c"),
        ("4c", "5c"),
        ("6c", "7c"),
        ("8c", "9c"),
    )
    _set_showdown_cards(hand=hand, fixed_holes=fixed_holes)

    while not hand.is_terminal:
        legal_kinds = hand.get_legal_actions().action_kinds
        action_kind = (
            ActionKind.CALL
            if ActionKind.CALL in legal_kinds
            else ActionKind.CHECK
        )
        hand.step(action=Action(kind=action_kind))

    assert hand._state.stacks[0] == Decimal("105")
    assert sum(hand._state.stacks) == Decimal("600")


def test_main_and_side_pots_are_paid_to_eligible_winners() -> None:
    hand = _create_hand(
        starting_stacks=(
            Decimal("20"),
            Decimal("50"),
            Decimal("100"),
            Decimal("100"),
            Decimal("100"),
            Decimal("100"),
        ),
    )
    _set_showdown_cards(
        hand=hand,
        fixed_holes=(
            ("As", "Ad"),
            ("Ks", "Kd"),
            ("Qs", "Qd"),
            ("Tc", "Jc"),
            ("8s", "7s"),
            ("6h", "5h"),
        ),
    )

    hand.step(action=Action(kind=ActionKind.RAISE, amount=Decimal("20")))
    hand.step(action=Action(kind=ActionKind.RAISE, amount=Decimal("50")))
    hand.step(action=Action(kind=ActionKind.CALL))
    hand.step(action=Action(kind=ActionKind.FOLD))
    hand.step(action=Action(kind=ActionKind.FOLD))
    hand.step(action=Action(kind=ActionKind.FOLD))

    assert hand.is_terminal is True
    assert hand._state.stacks[0] == Decimal("61.5")
    assert hand._state.stacks[1] == Decimal("60")
    assert hand._state.stacks[2] == Decimal("50")
    assert sum(hand._state.stacks) == Decimal("470")
