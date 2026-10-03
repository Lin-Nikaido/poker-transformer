# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Typed poker actions and public action history."""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat


class ActionKind(StrEnum):
    """Actions available to a player on a betting turn."""

    FOLD = "f"
    CHECK = "x"
    BET = "b"
    CALL = "c"
    RAISE = "r"


class BetSize(StrEnum):
    """Pot fractions available for bets and raises."""

    POT_20 = "0.2"
    POT_50 = "0.5"
    POT_80 = "0.8"
    POT_100 = "1.0"
    POT_150 = "1.5"
    POT_200 = "2.0"


class Action(BaseModel):
    """An action selected by a player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    kind: ActionKind
    amount: ChipAmount | None = None
    bet_size: BetSize | None = None


class ActionHistoryEntry(BaseModel):
    """A public action together with its actor."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    actor: Seat
    action: Action


class ActionHistory(BaseModel):
    """Public actions grouped by betting street."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    preflop: list[ActionHistoryEntry] = Field(default_factory=list)
    flop: list[ActionHistoryEntry] = Field(default_factory=list)
    turn: list[ActionHistoryEntry] = Field(default_factory=list)
    river: list[ActionHistoryEntry] = Field(default_factory=list)
