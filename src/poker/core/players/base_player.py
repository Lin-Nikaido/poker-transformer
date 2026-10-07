"""Players that can participate in a game independently of its engine."""

from abc import ABC
from abc import abstractmethod

from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


class BasePlayer(ABC):
    """A stable player identity and an asynchronous decision contract."""

    def __init__(self, *, player_id: str) -> None:
        if not player_id.strip():
            raise ValueError("Player identity must not be empty")
        self._player_id = player_id

    @property
    def player_id(self) -> str:
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
