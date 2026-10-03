"""Typed public state and player-specific observations."""

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.actions import ActionHistory
from poker.core.types.cards import Card
from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street


class PrivateHand(BaseModel):
    """The two private cards visible to one player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    cards: tuple[Card, Card]


class PublicPlayerState(BaseModel):
    """Public chip and participation state for one seat."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        revalidate_instances="always",
    )

    seat: Seat
    stack: ChipAmount
    committed: ChipAmount = Decimal("0")
    is_folded: bool = False
    is_all_in: bool = False


class PlayerState(PublicPlayerState):
    """Complete state for one player, including private cards."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    hand: PrivateHand | None = None

    def get_public_state(self) -> PublicPlayerState:
        """Return public player fields with private cards removed."""
        return PublicPlayerState.model_validate(self)


class PublicGameState(BaseModel):
    """Game state containing only information visible to every player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    street: Street
    pot: ChipAmount
    current_actor: Seat
    players: tuple[
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
        PublicPlayerState,
    ]
    community_cards: tuple[Card, ...] = Field(max_length=5)
    action_history: ActionHistory


class PlayerObservation(BaseModel):
    """Public game state combined with the observing player's private hand."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    seat: Seat
    private_hand: PrivateHand
    public_state: PublicGameState
