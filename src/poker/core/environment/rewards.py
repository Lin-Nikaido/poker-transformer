# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Per-hand reward calculation."""

from decimal import Decimal

from poker.core.types.hand_result import HandResult


def calculate_terminal_rewards(
    *,
    hand_result: HandResult,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Return each seat's stack change normalized by the initial big blind."""
    return tuple(
        (final - starting) / hand_result.initial_big_blind
        for starting, final in zip(
            hand_result.starting_stacks,
            hand_result.final_stacks,
            strict=True,
        )
    )
