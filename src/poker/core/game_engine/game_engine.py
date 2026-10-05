# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""Game-engine port consumed by poker use cases."""

from abc import ABC
from abc import abstractmethod

from poker.core.types.actions import Action
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PlayerState
from poker.core.types.primitives import Seat


class BasePokerGame(ABC):
    """A player-safe game session exposed by an engine adapter."""

    @abstractmethod
    def seat_player(
        self,
        *,
        players: list[PlayerState],
    ) -> None:
        """Assign the supplied players to seats without starting a hand."""
        ...

    @abstractmethod
    def start_hand(self) -> None:
        """Advance the button and begin a hand with blinds and hole cards."""
        ...

    @property
    @abstractmethod
    def acting_seat(self) -> Seat | None:
        """Return the seat that must act next, if one exists."""
        ...

    @property
    @abstractmethod
    def is_terminal(self) -> bool:
        """Return whether the hand is complete."""
        ...

    @abstractmethod
    def get_legal_actions(self) -> LegalActions:
        """Return legal decisions for the acting player."""
        ...

    @abstractmethod
    def step(
        self,
        *,
        action: Action,
    ) -> None:
        """Apply one legal action to the game session."""
        ...

