"""Typed playing-card values."""

from enum import IntEnum
from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators


class CardRank(IntEnum):
    """Rank of a standard playing card."""

    DEUCE = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


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
