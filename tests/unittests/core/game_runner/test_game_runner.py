from decimal import Decimal

import pytest
from pytest_mock import MockerFixture

from poker.core.game_runner.game_runner import GameRunner
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.primitives import Seat
from tests.mockups.game import MockGameEngine
from tests.mockups.game import ScriptedPlayer
from tests.mockups.game import make_game
from tests.mockups.ids import mock_uuid
from tests.mockups.play import Recorder


@pytest.mark.asyncio
async def test_run_hand_passes_original_request_to_player_and_observer(
    mock_game_engine: MockGameEngine,
    recorder: Recorder,
    mocker: MockerFixture,
) -> None:
    game = GameRunner(engine=mock_game_engine)
    players = tuple(
        ScriptedPlayer(player_id=mock_uuid(index)) for index in range(6)
    )
    selections = tuple(
        mocker.spy(player, "select_action") for player in players
    )
    for index, player in enumerate(players):
        game.seat_player(player=player, table_seat=index)

    await game.run_hand(observer=recorder)

    assert len(recorder.decisions) == 5
    for index, (request, _) in enumerate(recorder.decisions):
        selections[index].assert_called_once()
        assert selections[index].call_args.kwargs["request"] is request
    selections[-1].assert_not_called()


def test_game_seats_players_without_starting_or_rotating_first_hand(
    mock_game_engine: MockGameEngine,
) -> None:
    engine = mock_game_engine
    game = make_game(engine=engine)

    assert engine.starts == []
    game.start_hand()

    assert engine.starts == [tuple(Decimal(100 + index) for index in range(6))]
    assert game.get_player(seat=Seat.UTG).player_id == mock_uuid(0)
    assert game.get_player(seat=Seat.BTN).player_id == mock_uuid(3)


def finish_hand(*, game: GameRunner) -> None:
    for _ in range(5):
        request = game.get_decision_request()
        assert request is not None
        game.submit_action(
            request=request, action=Action(kind=ActionKind.FOLD)
        )


def test_next_hand_rotates_players_and_carries_profit_by_identity(
    mock_game_engine: MockGameEngine,
) -> None:
    engine = mock_game_engine
    game = make_game(engine=engine)
    game.start_hand()
    finish_hand(game=game)
    result = game.get_hand_result()

    assert result.players[4].net_profit == Decimal("-0.5")
    assert result.players[5].player_id == mock_uuid(5)
    assert result.players[5].net_profit == Decimal("0.5")
    assert sum(player.net_profit for player in result.players) == 0

    game.start_hand()

    assert engine.starts[-1] == (
        Decimal("101"),
        Decimal("102"),
        Decimal("103"),
        Decimal("103.5"),
        Decimal("105.5"),
        Decimal("100"),
    )
    assert game.get_player(seat=Seat.UTG).player_id == mock_uuid(1)
    assert result.players[5].seat is Seat.BB


def test_rejects_duplicate_seats_and_identities_without_changing_roster(
    mock_game_engine: MockGameEngine,
) -> None:
    game = GameRunner(engine=mock_game_engine)
    game.seat_player(
        player=ScriptedPlayer(player_id=mock_uuid(10)), table_seat=0
    )
    with pytest.raises(ValueError, match="unique table seat"):
        game.seat_player(
            player=ScriptedPlayer(player_id=mock_uuid(11)), table_seat=0
        )
    with pytest.raises(ValueError, match="unique identity"):
        game.seat_player(
            player=ScriptedPlayer(player_id=mock_uuid(10)), table_seat=1
        )
    with pytest.raises(ValueError, match="exactly six"):
        game.start_hand()


def test_rejects_active_hand_restart_and_late_seating(
    mock_game_engine: MockGameEngine,
) -> None:
    game = make_game(engine=mock_game_engine)
    game.start_hand()
    with pytest.raises(ValueError, match="must finish"):
        game.start_hand()
    with pytest.raises(ValueError, match="before a hand"):
        game.seat_player(
            player=ScriptedPlayer(player_id=mock_uuid(12)), table_seat=0
        )
    with pytest.raises(ValueError, match="must finish"):
        game.get_hand_result()


def test_rejects_stale_decision_without_advancing_engine(
    mock_game_engine: MockGameEngine,
) -> None:
    engine = mock_game_engine
    game = make_game(engine=engine)
    game.start_hand()
    request = game.get_decision_request()
    assert request is not None
    game.submit_action(request=request, action=Action(kind=ActionKind.FOLD))

    with pytest.raises(ValueError, match="stale"):
        game.submit_action(
            request=request, action=Action(kind=ActionKind.FOLD)
        )
    assert len(engine.actions) == 1


def test_rejects_wrong_identity_and_previous_hand_requests(
    mock_game_engine: MockGameEngine,
) -> None:
    game = make_game(engine=mock_game_engine)
    game.start_hand()
    request = game.get_decision_request()
    assert request is not None
    forged_request = request.model_copy(update={"player_id": mock_uuid(1)})
    with pytest.raises(ValueError, match="another player"):
        game.submit_action(
            request=forged_request, action=Action(kind=ActionKind.FOLD)
        )
    assert mock_game_engine.actions == []
    finish_hand(game=game)
    game.start_hand()
    with pytest.raises(ValueError, match="stale"):
        game.submit_action(
            request=request, action=Action(kind=ActionKind.FOLD)
        )
    assert mock_game_engine.actions == []


@pytest.mark.parametrize(
    "stack", (Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity"))
)
def test_rejects_invalid_initial_stacks(
    stack: Decimal, mock_game_engine: MockGameEngine
) -> None:
    game = GameRunner(engine=mock_game_engine)
    with pytest.raises(ValueError, match="finite and positive"):
        game.seat_player(
            player=ScriptedPlayer(player_id=mock_uuid(10)),
            table_seat=0,
            stack=stack,
        )
