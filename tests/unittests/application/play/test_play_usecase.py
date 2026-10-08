from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from poker.application.play.play_usecase import play_usecase
from poker.core.game_runner.game_runner import GameRunner
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.game import HandResult
from poker.core.types.game import PlayerHandResult
from poker.core.types.primitives import Seat
from tests.mockups.game import MockGameEngine
from tests.mockups.ids import mock_uuid


@pytest.mark.asyncio
async def test_play_usecase_propagates_core_result(
    mock_game_engine: MockGameEngine,
    recorder: BaseGameObserver,
) -> None:
    game = GameRunner(engine=mock_game_engine)
    expected_output = HandResult(
        hand_id=mock_uuid(100),
        players=tuple(
            PlayerHandResult(
                player_id=mock_uuid(index),
                seat=seat,
                starting_stack=100,
                final_stack=100,
            )
            for index, seat in enumerate(Seat)
        ),
    )
    with patch.object(
        game,
        "run_hand",
        new=AsyncMock(return_value=expected_output),
    ) as run_hand:
        result = await play_usecase(game_runner=game, observer=recorder)

    assert result is expected_output
    run_hand.assert_awaited_once_with(observer=recorder)


@pytest.mark.asyncio
async def test_play_usecase_propagates_core_failure(
    mock_game_engine: MockGameEngine,
) -> None:
    failure = ValueError("Game cannot start")
    game = GameRunner(engine=mock_game_engine)
    with patch.object(game, "run_hand", new=AsyncMock(side_effect=failure)):
        with pytest.raises(ValueError) as caught:
            await play_usecase(game_runner=game)
    assert caught.value is failure
