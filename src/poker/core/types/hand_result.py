# Copyright (c) 2026 YourIndependence. All rights reserved.

"""Terminal chip stacks for one completed hand."""

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.primitives import ChipAmount


class HandResult(BaseModel):
    """Starting and ending stacks, in fixed seat order."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    starting_stacks: tuple[
        ChipAmount, ChipAmount, ChipAmount, ChipAmount, ChipAmount, ChipAmount
    ]
    final_stacks: tuple[
        ChipAmount, ChipAmount, ChipAmount, ChipAmount, ChipAmount, ChipAmount
    ]
    initial_big_blind: Decimal = Field(gt=Decimal("0"))
