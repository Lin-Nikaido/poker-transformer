# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Typed public state and player-specific observations."""

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators

from poker.core.types.cards import Hand
from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat


class PublicPlayerState(BaseModel):
    """Public chip and participation state for one seat."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        revalidate_instances="always",
    )

    seat: Seat
    stack: ChipAmount
    committed: ChipAmount = Decimal("0")
    street_bet: ChipAmount = Decimal("0")
    is_folded: bool = False
    is_all_in: bool = False


class PlayerState(PublicPlayerState):
    """Complete state for one player, including private cards."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    hand: Hand | None = None

    def get_public_state(self) -> PublicPlayerState:
        """Return public player fields with private cards removed."""
        return PublicPlayerState.model_validate(self)
