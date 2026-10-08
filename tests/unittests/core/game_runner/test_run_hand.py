import pytest

from tests.mockups.game import MockGameEngine
from tests.mockups.game import make_game
from tests.mockups.ids import mock_uuid
from tests.mockups.play import Recorder


@pytest.mark.asyncio
async def test_game_run_hand_records_only_applied_decisions_with_stable_requests(
    mock_game_engine: MockGameEngine,
    recorder: Recorder,
) -> None:
    game = make_game(engine=mock_game_engine)
    result = await game.run_hand(observer=recorder)

    assert result.hand_id.version == 4
    assert len(recorder.decisions) == 5
    assert [request.revision for request, _ in recorder.decisions] == list(
        range(5)
    )
    assert [request.player_id for request, _ in recorder.decisions] == [
        mock_uuid(index) for index in range(5)
    ]
    assert all(
        decision.policy_trace is None for _, decision in recorder.decisions
    )
    assert game.is_terminal


@pytest.mark.asyncio
async def test_game_run_hand_rejects_restarting_an_unfinished_hand(
    mock_game_engine: MockGameEngine,
) -> None:
    game = make_game(engine=mock_game_engine)
    game.start_hand()
    with pytest.raises(ValueError, match="must finish"):
        await game.run_hand()
    assert mock_game_engine.actions == []
