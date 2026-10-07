# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""Game-engine port consumed by poker use cases."""

from abc import ABC
from abc import abstractmethod
from decimal import Decimal

from poker.core.types.actions import Action
from poker.core.types.legal_actions import LegalActions
from poker.core.types.primitives import Seat
from poker.core.types.table import PlayerObservation


class BaseGameEngine(ABC):
    """Execute one hand independently of seating and player behavior."""

    @abstractmethod
    def start_hand(
        self,
        *,
        starting_stacks: tuple[Decimal, ...],
    ) -> None:
        """Start a hand with stacks ordered by UTG, MP, CO, BTN, SB, BB."""
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
    def submit_action(
        self,
        *,
        action: Action,
    ) -> Action:
        """Apply a decision and return the actual action after sizing."""
        ...

    @abstractmethod
    def get_observation(self, *, seat: Seat) -> PlayerObservation:
        """Return public state and only the requested player's private hand."""
        ...

    @abstractmethod
    def get_stacks(self) -> tuple[Decimal, ...]:
        """Return current or settled stacks in position order."""
        ...
