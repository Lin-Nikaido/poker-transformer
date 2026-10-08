"""An observation boundary for recording applied player decisions."""

from abc import ABC
from abc import abstractmethod

from poker.core.types.actions import Action
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


class BaseGameObserver(ABC):
    """Observe decisions independently of rules and player implementations."""

    @abstractmethod
    async def on_decision(
        self,
        *,
        request: DecisionRequest,
        decision: PlayerDecision,
        applied_action: Action,
    ) -> None:
        """Record one applied decision and its private, player-local context."""
        ...
