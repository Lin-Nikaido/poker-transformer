from decimal import Decimal

import pytest

from poker.application.play.play_usecase import play_usecase
from poker.core.game_runner.game_runner import GameRunner
from poker.core.players.human_player import HumanPlayer
from poker.core.players.model_player import ModelPlayer
from poker.core.types.primitives import Seat
from poker.infrastructure.game_engine.pokerkit_engine import PokerKitGameEngine
from tests.mockups.models import MockEncoder
from tests.mockups.play import FoldInput
from tests.mockups.play import FoldModel
from tests.mockups.play import Recorder


@pytest.mark.asyncio
async def test_human_and_five_models_share_engine_and_preserve_identity_across_hands(
    fold_input: FoldInput, recorder: Recorder, mock_encoder: MockEncoder
) -> None:
    model = FoldModel().eval()
    game = GameRunner(engine=PokerKitGameEngine())
    human = HumanPlayer(action_source=fold_input)
    game.seat_player(
        player=human,
        table_seat=0,
    )
    model_players: list[ModelPlayer] = []
    for index in range(1, 6):
        model_player = ModelPlayer(
            model=model,
            encoder=mock_encoder,
            seed=index,
        )
        model_players.append(model_player)
        game.seat_player(
            player=model_player,
            table_seat=index,
        )
    recorder = recorder

    first = await play_usecase(game_runner=game, observer=recorder)
    assert first.hand_id.version == 4
    assert human.player_id.version == 4
    assert all(player.player_id.version == 4 for player in model_players)
    assert (
        len({human.player_id, *(player.player_id for player in model_players)})
        == 6
    )
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

    second = await play_usecase(game_runner=game)
    assert second.hand_id.version == 4
    assert second.hand_id != first.hand_id
    assert second.players[0].player_id == model_players[0].player_id
    assert second.players[5].player_id == human.player_id
    assert game.get_player(seat=Seat.BB).player_id == human.player_id
    assert sum(player.final_stack for player in second.players) == Decimal(
        "600"
    )
    assert sum(player.net_profit for player in second.players) == 0
    assert model.training is False
