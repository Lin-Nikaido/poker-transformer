"""Players that can participate in a game independently of its engine."""

from abc import ABC
from abc import abstractmethod
from uuid import UUID
from uuid import uuid4

from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


class BasePlayer(ABC):
    """A stable player identity and an asynchronous decision contract."""

    def __init__(self, *, player_id: UUID | None = None) -> None:
        self._player_id = player_id if player_id is not None else uuid4()

    @property
    def player_id(self) -> UUID:
        """Return the identity that remains stable across positions."""
        return self._player_id

    def validate_request(self, *, request: DecisionRequest) -> None:
        """Reject another player's decision request."""
        if request.player_id != self.player_id:
            raise ValueError("The decision request belongs to another player")

    @abstractmethod
    async def select_action(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        """Choose an action using only the supplied observation."""
        ...
