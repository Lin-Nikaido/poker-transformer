from decimal import Decimal

import pytest

from poker.core.game.game import Game
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.primitives import Seat
from tests.mockups.game import FakeEngine
from tests.mockups.game import ScriptedPlayer
from tests.mockups.game import make_game


def test_game_seats_players_without_starting_or_rotating_first_hand(
    fake_engine: FakeEngine,
) -> None:
    engine = fake_engine
    game = make_game(engine=engine)

    assert engine.starts == []
    game.start_hand()

    assert engine.starts == [tuple(Decimal(100 + index) for index in range(6))]
    assert game.get_player(seat=Seat.UTG).player_id == "player-0"
    assert game.get_player(seat=Seat.BTN).player_id == "player-3"


def finish_hand(*, game: Game) -> None:
    for _ in range(5):
        request = game.get_decision_request()
        assert request is not None
        game.submit_action(
            request=request, action=Action(kind=ActionKind.FOLD)
        )


def test_next_hand_rotates_players_and_carries_profit_by_identity(
    fake_engine: FakeEngine,
) -> None:
    engine = fake_engine
    game = make_game(engine=engine)
    game.start_hand()
    finish_hand(game=game)
    result = game.get_hand_result()

    assert result.players[4].net_profit == Decimal("-0.5")
    assert result.players[5].player_id == "player-5"
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
    assert game.get_player(seat=Seat.UTG).player_id == "player-1"
    assert result.players[5].seat is Seat.BB


def test_rejects_duplicate_seats_and_identities_without_changing_roster(
    fake_engine: FakeEngine,
) -> None:
    game = Game(engine=fake_engine)
    game.seat_player(player=ScriptedPlayer(player_id="one"), table_seat=0)
    with pytest.raises(ValueError, match="unique table seat"):
        game.seat_player(player=ScriptedPlayer(player_id="two"), table_seat=0)
    with pytest.raises(ValueError, match="unique identity"):
        game.seat_player(player=ScriptedPlayer(player_id="one"), table_seat=1)
    with pytest.raises(ValueError, match="exactly six"):
        game.start_hand()


def test_rejects_active_hand_restart_and_late_seating(
    fake_engine: FakeEngine,
) -> None:
    game = make_game(engine=fake_engine)
    game.start_hand()
    with pytest.raises(ValueError, match="must finish"):
        game.start_hand()
    with pytest.raises(ValueError, match="before a hand"):
        game.seat_player(player=ScriptedPlayer(player_id="late"), table_seat=0)
    with pytest.raises(ValueError, match="must finish"):
        game.get_hand_result()


def test_rejects_stale_decision_without_advancing_engine(
    fake_engine: FakeEngine,
) -> None:
    engine = fake_engine
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
    fake_engine: FakeEngine,
) -> None:
    game = make_game(engine=fake_engine)
    game.start_hand()
    request = game.get_decision_request()
    assert request is not None
    forged_request = request.model_copy(update={"player_id": "player-1"})
    with pytest.raises(ValueError, match="another player"):
        game.submit_action(
            request=forged_request, action=Action(kind=ActionKind.FOLD)
        )
    assert fake_engine.actions == []
    finish_hand(game=game)
    game.start_hand()
    with pytest.raises(ValueError, match="stale"):
        game.submit_action(
            request=request, action=Action(kind=ActionKind.FOLD)
        )
    assert fake_engine.actions == []


@pytest.mark.parametrize(
    "stack", (Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity"))
)
def test_rejects_invalid_initial_stacks(
    stack: Decimal, fake_engine: FakeEngine
) -> None:
    game = Game(engine=fake_engine)
    with pytest.raises(ValueError, match="finite and positive"):
        game.seat_player(
            player=ScriptedPlayer(player_id="one"), table_seat=0, stack=stack
        )
