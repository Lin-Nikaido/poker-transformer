# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

from decimal import Decimal

from poker.core.types.actions import ActionHistory
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.player import PlayerState
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street
from poker.core.types.table import TableState


def test_player_state_public_projection_hides_hand() -> None:
    hand = Hand(
        cards=(
            Card(rank=CardRank.DEUCE, suit=Suit.CLUBS),
            Card(rank=CardRank.ACE, suit=Suit.HEARTS),
        )
    )
    player = PlayerState(seat=Seat.UTG, stack=Decimal("80"), hand=hand)

    public_state = player.get_public_state()

    assert public_state.seat == player.seat
    assert public_state.stack == player.stack
    assert type(public_state) is PublicPlayerState
    assert not hasattr(public_state, "hand")
    assert player.hand == hand


def test_public_game_state_revalidates_player_subclasses() -> None:
    hand = Hand(
        cards=(
            Card(rank=CardRank.DEUCE, suit=Suit.CLUBS),
            Card(rank=CardRank.ACE, suit=Suit.HEARTS),
        )
    )
    players = tuple(
        PlayerState(
            seat=seat,
            stack=Decimal("80"),
            hand=hand if seat is Seat.UTG else None,
        )
        for seat in Seat
    )

    public_state = TableState(
        street=Street.PREFLOP,
        pot=Decimal("1.5"),
        current_actor=Seat.UTG,
        players=players,
        community_cards=(),
        action_history=ActionHistory(),
    )

    assert type(public_state.players[0]) is PublicPlayerState
    assert not hasattr(public_state.players[0], "hand")
