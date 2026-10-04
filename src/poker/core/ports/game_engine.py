# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""Game-engine port consumed by poker use cases."""

from abc import ABC
from abc import abstractmethod

from poker.core.types.actions import Action
from poker.core.types.hand_result import HandResult
from poker.core.types.legal_actions import LegalActions
from poker.core.types.primitives import Seat
from poker.core.types.table import PlayerObservation


class PokerGame(ABC):
    """A player-safe game session exposed by an engine adapter."""

    @abstractmethod
    def __init__(self, **kwargs) -> None: ...

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
    def get_observation(self) -> PlayerObservation:
        """Return the observation for the acting player only."""
        ...

    @abstractmethod
    def get_result(self) -> HandResult:
        """Return terminal stacks after a completed hand."""
        ...

    @abstractmethod
    def step(
        self,
        *,
        action: Action,
    ) -> None:
        """Apply one legal action to the game session."""
        ...


class GameEngine(ABC):
    """Factory contract for starting one poker hand."""

    @abstractmethod
    def start_hand(self) -> PokerGame:
        """Create a new hand session."""
        ...
