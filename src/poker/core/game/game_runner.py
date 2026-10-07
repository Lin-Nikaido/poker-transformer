"""Shared hand execution for interactive play and future rollout collection."""

from poker.core.game.game import Game
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.game import HandResult


async def run_hand(
    *,
    game: Game,
    observer: BaseGameObserver | None = None,
) -> HandResult:
    """Start and complete one hand using the seated players' behavior."""
    game.start_hand()
    while not game.is_terminal:
        request = game.get_decision_request()
        if request is None:
            raise RuntimeError("A running hand must expose a decision request")
        player = game.get_player(seat=request.observation.seat)
        decision = await player.select_action(
            request=request.model_copy(deep=True)
        )
        applied_action = game.submit_action(
            request=request, action=decision.action
        )
        if observer is not None:
            await observer.on_decision(
                request=request,
                decision=decision,
                applied_action=applied_action,
            )
    return game.get_hand_result()
