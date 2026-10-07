# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Resolve domain bet actions to legal target amounts."""

from decimal import Decimal

from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.legal_actions import LegalActions


def resolve_bet_target(
    *,
    action: Action,
    current_street_bet: Decimal,
    amount_to_call: Decimal,
    total_pot: Decimal,
    remaining_stack: Decimal,
    legal_actions: LegalActions,
) -> Decimal:
    """Resolve a bet or raise action without depending on an engine."""
    if action.kind not in (ActionKind.BET, ActionKind.RAISE):
        raise ValueError(
            "Bet targets are only valid for bet and raise actions"
        )
    if action.amount is not None and action.bet_size is not None:
        raise ValueError("Specify either an amount or a bet size, not both")
    if action.amount is None and action.bet_size is None:
        raise ValueError("Bet and raise actions require a target or bet size")

    minimum_amount = legal_actions.minimum_bet_or_raise_to
    maximum_amount = legal_actions.maximum_bet_or_raise_to
    if minimum_amount is None or maximum_amount is None:
        raise ValueError("Bet and raise actions are not currently available")

    if action.bet_size is None:
        target_amount = Decimal(str(action.amount))
    else:
        pot_after_call = total_pot + amount_to_call
        target_amount = (
            current_street_bet
            + amount_to_call
            + pot_after_call * Decimal(action.bet_size.value)
        )
        target_amount = max(target_amount, minimum_amount)
        target_amount = min(target_amount, maximum_amount)

    if target_amount >= remaining_stack / Decimal("2"):
        return maximum_amount
    return target_amount
