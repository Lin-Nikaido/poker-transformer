import pytest

from poker.core.game.game_runner import run_hand
from tests.mockups.game import FakeEngine
from tests.mockups.game import make_game
from tests.mockups.play import Recorder


@pytest.mark.asyncio
async def test_runner_records_only_applied_decisions_with_stable_requests(
    fake_engine: FakeEngine,
    recorder: Recorder,
) -> None:
    game = make_game(engine=fake_engine)
    result = await run_hand(game=game, observer=recorder)

    assert result.hand_id == 1
    assert len(recorder.decisions) == 5
    assert [request.revision for request, _ in recorder.decisions] == list(
        range(5)
    )
    assert [request.player_id for request, _ in recorder.decisions] == [
        f"player-{index}" for index in range(5)
    ]
    assert all(
        decision.policy_trace is None for _, decision in recorder.decisions
    )
    assert game.is_terminal


@pytest.mark.asyncio
async def test_runner_rejects_restarting_an_unfinished_hand(
    fake_engine: FakeEngine,
) -> None:
    game = make_game(engine=fake_engine)
    game.start_hand()
    with pytest.raises(ValueError, match="must finish"):
        await run_hand(game=game)
    assert fake_engine.actions == []
