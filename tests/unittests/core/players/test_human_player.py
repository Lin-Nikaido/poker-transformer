import pytest

from poker.core.players.human_player import HumanPlayer
from poker.core.types.actions import ActionKind
from tests.mockups.console import FakeActionSource
from tests.mockups.models import make_request


@pytest.mark.asyncio
async def test_human_player_awaits_injected_input_without_model_trace(
    fake_action_source: FakeActionSource,
) -> None:
    source = fake_action_source
    player = HumanPlayer(player_id="learner", action_source=source)
    request = make_request(legal_kinds=(ActionKind.CALL,))

    decision = await player.select_action(request=request)

    assert source.requests == [request]
    assert decision.action.kind is ActionKind.CALL
    assert decision.policy_trace is None
