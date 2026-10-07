"""Player decisions and reproducible decision requests."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.actions import Action
from poker.core.types.legal_actions import LegalActions
from poker.core.types.table import PlayerObservation


class DecisionRequest(BaseModel):
    """An observation belonging to one player and one game revision."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    player_id: str = Field(min_length=1)
    hand_id: int = Field(ge=1)
    revision: int = Field(ge=0)
    observation: PlayerObservation
    legal_actions: LegalActions


class PolicyTrace(BaseModel):
    """Sampling information retained independently of the game engine."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    action_index: int = Field(ge=0)
    log_probability: float = Field(allow_inf_nan=False)
    policy_version: str


class PlayerDecision(BaseModel):
    """A selected action and optional model sampling information."""

    model_config = ConfigDict(
        frozen=True,
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    action: Action
    policy_trace: PolicyTrace | None = None
