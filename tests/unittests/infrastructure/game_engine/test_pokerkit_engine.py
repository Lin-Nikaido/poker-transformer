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
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitGameEngine


def _create_hand(
    *,
    starting_stacks: tuple[Decimal, ...] = (Decimal("100"),) * 6,
) -> PokerKitGameEngine:
    game = PokerKitGameEngine()
    game.start_hand(starting_stacks=starting_stacks)
    return game


def _set_showdown_cards(
    *,
    hand: PokerKitGameEngine,
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
    hand = _create_hand()

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
    hand = _create_hand()
    hand._state = state

    legal_actions = hand.get_legal_actions()

    assert legal_actions.minimum_bet_or_raise_to == Decimal("4")
    assert legal_actions.maximum_bet_or_raise_to == Decimal("100")
    assert isinstance(legal_actions.minimum_bet_or_raise_to, Decimal)
    assert isinstance(legal_actions.maximum_bet_or_raise_to, Decimal)


def test_fold_ends_hand_when_one_player_remains() -> None:
    hand = _create_hand()

    for _ in range(5):
        hand.submit_action(action=Action(kind=ActionKind.FOLD))

    assert hand.is_terminal is True
    assert hand.acting_seat is None
    assert hand.get_legal_actions().action_kinds == ()
    assert hand._state.stacks[5] == Decimal("100.5")
    assert sum(hand._state.stacks) == Decimal("600")


def test_observations_hide_other_hands_and_do_not_mutate_with_play() -> None:
    engine = _create_hand()
    first = engine.get_observation(seat=Seat.UTG)
    assert all(
        not hasattr(player, "hand") for player in first.public_state.players
    )
    assert len(first.private_hand.cards) == 2
    assert first.public_state.players[4].committed == Decimal("0.5")
    assert first.public_state.players[5].committed == Decimal("1")

    applied = engine.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("3"))
    )
    second = engine.get_observation(seat=Seat.MP)
    assert applied.amount == Decimal("3")
    assert second.public_state.players[0].stack == Decimal("97")
    assert second.public_state.players[0].committed == Decimal("3")
    assert second.public_state.action_history.preflop[
        0
    ].action.amount == Decimal("3")
    assert first.public_state.players[0].stack == Decimal("100")
    assert first.public_state.action_history.preflop == []

    second.public_state.players[0].stack = Decimal("1")
    second.public_state.action_history.preflop.clear()
    assert engine.get_observation(seat=Seat.MP).public_state.players[
        0
    ].stack == Decimal("97")
    assert (
        len(
            engine.get_observation(
                seat=Seat.MP
            ).public_state.action_history.preflop
        )
        == 1
    )


def test_flop_snapshot_contains_only_revealed_board_and_grouped_history() -> (
    None
):
    engine = _create_hand()
    for _ in range(6):
        kind = (
            ActionKind.CALL
            if ActionKind.CALL in engine.get_legal_actions().action_kinds
            else ActionKind.CHECK
        )
        engine.submit_action(action=Action(kind=kind))
    observation = engine.get_observation(seat=Seat.SB)
    assert observation.public_state.street.value == "flop"
    assert len(observation.public_state.community_cards) == 3
    assert len(observation.public_state.action_history.preflop) == 6
    assert observation.public_state.action_history.flop == []


def test_engine_requires_valid_six_stacks_and_does_not_restart_active_hand() -> (
    None
):
    engine = PokerKitGameEngine()
    with pytest.raises(ValueError, match="exactly six"):
        engine.start_hand(starting_stacks=(Decimal("100"),) * 5)
    with pytest.raises(ValueError, match="finite and positive"):
        engine.start_hand(starting_stacks=(Decimal("0"),) * 6)
    engine.start_hand(starting_stacks=(Decimal("100"),) * 6)
    with pytest.raises(ValueError, match="must finish"):
        engine.start_hand(starting_stacks=(Decimal("100"),) * 6)


def test_rejects_actions_outside_the_legal_action_set() -> None:
    hand = _create_hand()

    with pytest.raises(ValueError, match="is not legal"):
        hand.submit_action(action=Action(kind=ActionKind.CHECK))


@pytest.mark.parametrize("kind", (ActionKind.FOLD, ActionKind.CALL))
def test_rejects_bet_size_on_non_betting_action(kind: ActionKind) -> None:
    hand = _create_hand()

    with pytest.raises(ValueError, match="only valid for bet and raise"):
        hand.submit_action(action=Action(kind=kind, bet_size=BetSize.POT_80))


def test_raise_to_amount_advances_to_the_next_actor() -> None:
    hand = _create_hand()

    hand.submit_action(
        action=Action(
            kind=ActionKind.RAISE,
            amount=Decimal("2"),
        ),
    )

    assert hand.acting_seat is Seat.MP
    assert ActionKind.CALL in hand.get_legal_actions().action_kinds


def test_explicit_raise_to_amount_is_preserved() -> None:
    hand = _create_hand()

    hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("2.25")),
    )

    assert hand._state.bets[0] == Decimal("2.25")


@pytest.mark.parametrize(
    "action",
    (
        Action(kind=ActionKind.RAISE),
        Action(kind=ActionKind.RAISE, bet_size=BetSize.POT_80),
        Action(
            kind=ActionKind.RAISE, amount=Decimal("3"), bet_size=BetSize.POT_80
        ),
    ),
)
def test_rejects_unresolved_betting_targets_without_advancing(
    action: Action,
) -> None:
    hand = _create_hand()

    with pytest.raises(ValueError, match="resolved target amount"):
        hand.submit_action(action=action)

    assert hand.acting_seat is Seat.UTG
    assert hand._state.bets[0] == Decimal("0")
    assert (
        hand.get_observation(seat=Seat.UTG).public_state.action_history.preflop
        == []
    )


@pytest.mark.parametrize("target_amount", (Decimal("40"), Decimal("50")))
def test_engine_preserves_explicit_targets_at_half_remaining_stack(
    target_amount: Decimal,
) -> None:
    hand = _create_hand(starting_stacks=(Decimal("80"),) * 6)
    hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("10"))
    )
    hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("20"))
    )

    applied = hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=target_amount),
    )

    assert applied.amount == target_amount
    assert hand._state.bets[2] == target_amount
    assert hand._state.stacks[2] == Decimal("80") - target_amount


@pytest.mark.parametrize("amount", (Decimal("1.5"), Decimal("101")))
def test_engine_rejects_targets_outside_legal_bounds(amount: Decimal) -> None:
    hand = _create_hand()

    with pytest.raises(ValueError):
        hand.submit_action(action=Action(kind=ActionKind.RAISE, amount=amount))

    assert hand.acting_seat is Seat.UTG
    assert hand._state.bets[0] == Decimal("0")


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
        hand.submit_action(action=Action(kind=action_kind))

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

    hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("20"))
    )
    hand.submit_action(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("50"))
    )
    hand.submit_action(action=Action(kind=ActionKind.CALL))
    hand.submit_action(action=Action(kind=ActionKind.FOLD))
    hand.submit_action(action=Action(kind=ActionKind.FOLD))
    hand.submit_action(action=Action(kind=ActionKind.FOLD))

    assert hand.is_terminal is True
    assert hand._state.stacks[0] == Decimal("61.5")
    assert hand._state.stacks[1] == Decimal("60")
    assert hand._state.stacks[2] == Decimal("50")
    assert sum(hand._state.stacks) == Decimal("470")
