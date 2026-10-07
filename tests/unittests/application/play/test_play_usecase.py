from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from poker.application.play.play_usecase import play_usecase
from poker.core.game.game import Game
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.game import HandResult
from poker.core.types.game import PlayerHandResult
from poker.core.types.primitives import Seat
from tests.mockups.game import FakeEngine


@pytest.mark.asyncio
async def test_play_usecase_propagates_core_result(
    fake_engine: FakeEngine,
    recorder: BaseGameObserver,
) -> None:
    game = Game(engine=fake_engine)
    expected_output = HandResult(
        hand_id=1,
        players=tuple(
            PlayerHandResult(
                player_id=f"player-{index}",
                seat=seat,
                starting_stack=100,
                final_stack=100,
            )
            for index, seat in enumerate(Seat)
        ),
    )
    with patch(
        "poker.application.play.play_usecase.run_hand",
        new=AsyncMock(return_value=expected_output),
    ) as run_hand:
        result = await play_usecase(game=game, observer=recorder)

    assert result is expected_output
    run_hand.assert_awaited_once_with(game=game, observer=recorder)


@pytest.mark.asyncio
async def test_play_usecase_propagates_core_failure(
    fake_engine: FakeEngine,
) -> None:
    failure = ValueError("Game cannot start")
    with patch(
        "poker.application.play.play_usecase.run_hand",
        new=AsyncMock(side_effect=failure),
    ):
        with pytest.raises(ValueError) as caught:
            await play_usecase(game=Game(engine=fake_engine))
    assert caught.value is failure
