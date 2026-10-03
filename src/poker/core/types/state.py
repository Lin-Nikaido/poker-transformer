"""Typed public state and player-specific observations."""

from collections.abc import Sequence
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from poker.core.types.actions import ActionHistoryEntry
from poker.core.types.cards import Card
from poker.core.types.primitives import ChipAmount
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street


class PrivateHand(BaseModel):
    """The two private cards visible to one player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
    )

    cards: tuple[Card, Card]


class PublicPlayerState(BaseModel):
    """Public chip and participation state for one seat."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
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
        frozen=True,
    )

    hand: PrivateHand | None = None

    def get_public_state(self) -> PublicPlayerState:
        """Return public player fields with private cards removed."""
        return PublicPlayerState.model_validate(self)


class StackVector(BaseModel):
    """Six stack amounts in UTG, MP, CO, BTN, SB, BB order."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
    )

    values: tuple[
        ChipAmount,
        ChipAmount,
        ChipAmount,
        ChipAmount,
        ChipAmount,
        ChipAmount,
    ]

    @classmethod
    def from_players(
        cls,
        *,
        players: Sequence[PlayerState],
    ) -> "StackVector":
        """Build the model stack input from one state per seat."""
        players_by_seat = {player.seat: player for player in players}
        if len(players_by_seat) != len(Seat) or set(players_by_seat) != set(
            Seat
        ):
            raise ValueError("Expected exactly one player per seat")

        return cls(values=tuple(players_by_seat[seat].stack for seat in Seat))


class PublicGameState(BaseModel):
    """Game state containing only information visible to every player."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
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
    action_history: tuple[ActionHistoryEntry, ...]


class PlayerObservation(BaseModel):
    """Public game state combined with the observing player's private hand."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        frozen=True,
    )

    seat: Seat
    private_hand: PrivateHand
    public_state: PublicGameState
