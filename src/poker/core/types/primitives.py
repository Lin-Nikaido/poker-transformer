# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Shared poker values used by state and action types."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import Field


ChipAmount = Annotated[Decimal, Field(ge=Decimal("0"))]


class Seat(StrEnum):
    """A fixed seat in the six-player table order."""

    UTG = "UTG"
    MP = "MP"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class Street(StrEnum):
    """A betting street in a Hold'em hand."""

    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
