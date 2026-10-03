# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Typed public state and player-specific observations."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.actions import ActionHistory
from poker.core.types.cards import Card
from poker.core.types.cards import Hand
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street


class TableState(BaseModel):
    """Game state containing only information visible to every player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    street: Street
    pot: ChipAmount
    current_actor: Seat
    players: tuple[
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
    ]
    community_cards: tuple[Card, ...] = Field(max_length=5)
    action_history: ActionHistory


class PlayerObservation(BaseModel):
    """Public game state combined with the observing player's private hand."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    seat: Seat
    private_hand: Hand
    public_state: TableState
