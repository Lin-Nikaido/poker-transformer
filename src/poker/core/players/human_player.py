"""Human decision behavior with injected asynchronous input."""

from poker.core.players.base_player import BasePlayer
from poker.core.ports.action_source import BaseActionSource
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


class HumanPlayer(BasePlayer):
    """A player whose decisions come from an input adapter."""

    def __init__(
        self, *, player_id: str, action_source: BaseActionSource
    ) -> None:
        super().__init__(player_id=player_id)
        self.action_source = action_source

    async def select_action(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        """Delegate human input through the asynchronous boundary."""
        self.validate_request(request=request)
        return PlayerDecision(
            action=await self.action_source.read_action(request=request),
        )
