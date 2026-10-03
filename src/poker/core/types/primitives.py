"""Shared poker values used by state and action types."""

from decimal import Decimal
from enum import IntEnum
from enum import StrEnum
from typing import Annotated

from pydantic import Field


ChipAmount = Annotated[Decimal, Field(ge=Decimal("0"))]


class Seat(IntEnum):
    """A fixed seat in the six-player table order."""

    UTG = 0
    MP = 1
    CO = 2
    BTN = 3
    SB = 4
    BB = 5


class Street(StrEnum):
    """A betting street in a Hold'em hand."""

    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
