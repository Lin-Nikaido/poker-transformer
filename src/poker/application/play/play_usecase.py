"""Function-only application entry point for an injected game."""

from poker.core.game.game import Game
from poker.core.game.game_runner import run_hand
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.game import HandResult


async def play_usecase(
    *,
    game: Game,
    observer: BaseGameObserver | None = None,
) -> HandResult:
    """Play a hand without retaining application-layer state."""
    return await run_hand(game=game, observer=observer)
