# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""Game-engine port consumed by poker use cases."""

from typing import Protocol

from poker.core.types.actions import Action
from poker.core.types.legal_actions import LegalActions
from poker.core.types.primitives import Seat


class PokerGame(Protocol):
    """A player-safe game session exposed by an engine adapter."""

    @property
    def acting_seat(self) -> Seat | None:
        """Return the seat that must act next, if one exists."""
        ...

    @property
    def is_terminal(self) -> bool:
        """Return whether the hand is complete."""
        ...

    def get_legal_actions(self) -> LegalActions:
        """Return legal decisions for the acting player."""
        ...

    def step(
        self,
        *,
        action: Action,
    ) -> None:
        """Apply one legal action to the game session."""
        ...


class GameEngine(Protocol):
    """Factory contract for starting one poker hand."""

    def start_hand(self) -> PokerGame:
        """Create a new hand session."""
        ...
