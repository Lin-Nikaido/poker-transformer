# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Typed playing-card values."""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators


class CardRank(StrEnum):
    """Rank of a standard playing card."""

    DEUCE = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

    def to_num(self) -> int:
        """Return the rank's numeric value from two through fourteen."""
        return "23456789TJQKA".index(self.value) + 2


class Suit(StrEnum):
    """Suit of a standard playing card."""

    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Card(BaseModel):
    """A standard playing card."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    rank: CardRank
    suit: Suit
