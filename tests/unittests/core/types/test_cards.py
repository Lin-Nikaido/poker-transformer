# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from poker.core.types.cards import CardRank


@pytest.mark.parametrize(
    ("rank", "expected"),
    [
        (CardRank.DEUCE, 2),
        (CardRank.THREE, 3),
        (CardRank.FOUR, 4),
        (CardRank.FIVE, 5),
        (CardRank.SIX, 6),
        (CardRank.SEVEN, 7),
        (CardRank.EIGHT, 8),
        (CardRank.NINE, 9),
        (CardRank.TEN, 10),
        (CardRank.JACK, 11),
        (CardRank.QUEEN, 12),
        (CardRank.KING, 13),
        (CardRank.ACE, 14),
    ],
)
def test_card_rank_to_num(rank: CardRank, expected: int) -> None:
    assert rank.to_num() == expected
