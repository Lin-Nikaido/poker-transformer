from decimal import Decimal

import pytest

from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Suit
from poker.core.types.state import PlayerState
from poker.core.types.state import PrivateHand
from poker.core.types.state import Seat
from poker.core.types.state import StackVector


def test_player_state_public_projection_hides_hand() -> None:
    hand = PrivateHand(
        cards=(
            Card(rank=CardRank.DEUCE, suit=Suit.CLUBS),
            Card(rank=CardRank.ACE, suit=Suit.HEARTS),
        )
    )
    player = PlayerState(seat=Seat.UTG, stack=Decimal("80"), hand=hand)

    public_state = player.get_public_state()

    assert public_state.seat == player.seat
    assert public_state.stack == player.stack
    assert public_state.hand is None
    assert player.hand == hand


def test_stack_vector_orders_player_stacks_by_seat() -> None:
    players = tuple(
        PlayerState(seat=seat, stack=Decimal(seat.value + 1))
        for seat in reversed(tuple(Seat))
    )

    stack_vector = StackVector.from_players(players=players)

    assert stack_vector.values == tuple(
        Decimal(seat.value + 1) for seat in Seat
    )


def test_stack_vector_rejects_missing_seat() -> None:
    players = tuple(
        PlayerState(seat=seat, stack=Decimal(seat.value + 1))
        for seat in tuple(Seat)[:-1]
    )

    with pytest.raises(ValueError, match="exactly one player per seat"):
        StackVector.from_players(players=players)


def test_stack_vector_rejects_duplicate_seat() -> None:
    players = tuple(
        PlayerState(seat=seat, stack=Decimal(seat.value + 1)) for seat in Seat
    )
    players_with_duplicate = (*players[:-1], players[0])

    with pytest.raises(ValueError, match="exactly one player per seat"):
        StackVector.from_players(players=players_with_duplicate)
