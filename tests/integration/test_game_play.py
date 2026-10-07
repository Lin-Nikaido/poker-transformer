from decimal import Decimal

import pytest

from poker.application.play.play_usecase import play_usecase
from poker.core.game.game import Game
from poker.core.players.human_player import HumanPlayer
from poker.core.players.model_player import ModelPlayer
from poker.core.types.primitives import Seat
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitGameEngine
from tests.mockups.models import StubEncoder
from tests.mockups.play import FoldInput
from tests.mockups.play import FoldModel
from tests.mockups.play import Recorder


@pytest.mark.asyncio
async def test_human_and_five_models_share_engine_and_preserve_identity_across_hands(
    fold_input: FoldInput, recorder: Recorder, stub_encoder: StubEncoder
) -> None:
    model = FoldModel().eval()
    game = Game(engine=PokerKitGameEngine())
    game.seat_player(
        player=HumanPlayer(player_id="human", action_source=fold_input),
        table_seat=0,
    )
    for index in range(1, 6):
        game.seat_player(
            player=ModelPlayer(
                player_id=f"model-{index}",
                model=model,
                encoder=stub_encoder,
                seed=index,
            ),
            table_seat=index,
        )
    recorder = recorder

    first = await play_usecase(game=game, observer=recorder)
    assert first.players[5].net_profit == Decimal("0.5")
    assert recorder.decisions[0][1].policy_trace is None
    assert all(
        decision.policy_trace is not None
        for _, decision in recorder.decisions[1:]
    )
    assert all(
        not hasattr(player, "hand")
        for request, _ in recorder.decisions
        for player in request.observation.public_state.players
    )

    second = await play_usecase(game=game)
    assert second.hand_id == 2
    assert second.players[0].player_id == "model-1"
    assert second.players[5].player_id == "human"
    assert game.get_player(seat=Seat.BB).player_id == "human"
    assert sum(player.final_stack for player in second.players) == Decimal(
        "600"
    )
    assert sum(player.net_profit for player in second.players) == 0
    assert model.training is False
