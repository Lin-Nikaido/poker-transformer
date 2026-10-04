# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Typed state and transitions for one-hand poker environments."""

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators

from poker.core.types.legal_actions import LegalActions
from poker.core.types.primitives import Seat
from poker.core.types.table import PlayerObservation


class EnvironmentState(BaseModel):
    """Decision state visible to the player whose turn it is."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    observation: PlayerObservation
    legal_actions: LegalActions


class EnvironmentTransition(BaseModel):
    """Outcome of one action in a one-hand episode."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    acting_seat: Seat
    next_state: EnvironmentState | None
    rewards: tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal] | None
    is_terminal: bool
