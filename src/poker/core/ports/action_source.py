"""Asynchronous input boundary for human players."""

from abc import ABC
from abc import abstractmethod

from poker.core.types.actions import Action
from poker.core.types.decisions import DecisionRequest


class BaseActionSource(ABC):
    """Read one human action without coupling a player to a terminal."""

    @abstractmethod
    async def read_action(self, *, request: DecisionRequest) -> Action:
        """Read an action for the supplied player-safe request."""
        ...
