# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

from decimal import Decimal

import pytest

from poker.core.environment.bet_sizing import resolve_bet_target
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.actions import BetSize
from poker.core.types.legal_actions import LegalActions


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
def test_resolves_pot_fraction_after_call(
    bet_size: BetSize,
    expected_target: Decimal,
) -> None:
    target = resolve_bet_target(
        action=Action(kind=ActionKind.RAISE, bet_size=bet_size),
        current_street_bet=Decimal("0"),
        amount_to_call=Decimal("1"),
        total_pot=Decimal("1.5"),
        remaining_stack=Decimal("100"),
        legal_actions=LegalActions(
            action_kinds=(ActionKind.RAISE,),
            minimum_bet_or_raise_to=Decimal("2"),
            maximum_bet_or_raise_to=Decimal("100"),
        ),
    )

    assert target == expected_target


def test_converts_half_stack_sized_target_to_maximum_legal_target() -> None:
    target = resolve_bet_target(
        action=Action(kind=ActionKind.RAISE, amount=Decimal("40")),
        current_street_bet=Decimal("0"),
        amount_to_call=Decimal("1"),
        total_pot=Decimal("1.5"),
        remaining_stack=Decimal("80"),
        legal_actions=LegalActions(
            action_kinds=(ActionKind.RAISE,),
            minimum_bet_or_raise_to=Decimal("2"),
            maximum_bet_or_raise_to=Decimal("80"),
        ),
    )

    assert target == Decimal("80")


def test_clamps_size_based_target_to_legal_bounds() -> None:
    target = resolve_bet_target(
        action=Action(kind=ActionKind.RAISE, bet_size=BetSize.POT_20),
        current_street_bet=Decimal("0"),
        amount_to_call=Decimal("1"),
        total_pot=Decimal("1.5"),
        remaining_stack=Decimal("100"),
        legal_actions=LegalActions(
            action_kinds=(ActionKind.RAISE,),
            minimum_bet_or_raise_to=Decimal("3"),
            maximum_bet_or_raise_to=Decimal("5"),
        ),
    )

    assert target == Decimal("3")
