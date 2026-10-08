"""Hand results attributed to stable player identities."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat


class PlayerHandResult(BaseModel):
    """Starting and settled stacks for one participant."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    player_id: UUID
    seat: Seat
    starting_stack: ChipAmount
    final_stack: ChipAmount

    @property
    def net_profit(self) -> Decimal:
        """Return signed profit including blind contributions."""
        return self.final_stack - self.starting_stack


class HandResult(BaseModel):
    """A complete hand without exposing any private cards."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    hand_id: UUID
    players: tuple[PlayerHandResult, ...] = Field(min_length=6, max_length=6)
