# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""Legal betting decisions exposed by a poker engine."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.actions import ActionKind
from poker.core.types.primitives import ChipAmount


class LegalActions(BaseModel):
    """Actions available at one betting decision."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    action_kinds: tuple[ActionKind, ...]
    minimum_bet_or_raise_to: ChipAmount | None = Field(
        default=None, strict=True
    )
    maximum_bet_or_raise_to: ChipAmount | None = Field(
        default=None, strict=True
    )
