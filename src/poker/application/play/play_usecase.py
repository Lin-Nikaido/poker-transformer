"""Function-only application entry point for an injected game."""

from poker.core.game_runner.game_runner import GameRunner
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.game import HandResult


async def play_usecase(
    *,
    game_runner: GameRunner,
    observer: BaseGameObserver | None = None,
) -> HandResult:
    """Play a hand without retaining application-layer state."""
    return await game_runner.run_hand(observer=observer)
