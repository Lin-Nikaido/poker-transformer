"""Typed poker actions and public action history."""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators

from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street


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
        frozen=True,
    )

    kind: ActionKind
    amount: ChipAmount | None = None
    bet_size: BetSize | None = None


class ActionHistoryEntry(BaseModel):
    """A public action together with its actor and betting street."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
    )

    actor: Seat
    street: Street
    action: Action
