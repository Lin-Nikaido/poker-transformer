"""Players that can participate in a game independently of its engine."""

from abc import ABC
from abc import abstractmethod
from decimal import Decimal
from uuid import UUID
from uuid import uuid4

from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision


class BasePlayer(ABC):
    """A stable player identity and an asynchronous decision contract."""

    def __init__(self, *, player_id: UUID | None = None) -> None:
        self._player_id = player_id if player_id is not None else uuid4()

    @property
    def player_id(self) -> UUID:
        """Return the identity that remains stable across positions."""
        return self._player_id

    def validate_request(self, *, request: DecisionRequest) -> None:
        """Reject another player's decision request."""
        if request.player_id != self.player_id:
            raise ValueError("The decision request belongs to another player")

    async def select_action(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        """Choose an action and resolve betting targets from the observation."""
        self.validate_request(request=request)
        decision = await self._select_action_impl(request=request)
        if decision.action.kind not in (ActionKind.BET, ActionKind.RAISE):
            return decision
        return decision.model_copy(
            update={
                "action": Action(
                    kind=decision.action.kind,
                    amount=self._resolve_bet_amount(
                        action=decision.action, request=request
                    ),
                ),
            },
        )

    @abstractmethod
    async def _select_action_impl(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        """Choose an action using only the supplied observation."""
        ...

    def _resolve_bet_amount(
        self, *, action: Action, request: DecisionRequest
    ) -> Decimal:
        if action.kind not in (ActionKind.BET, ActionKind.RAISE):
            raise ValueError(
                "Bet targets are only valid for bet and raise actions"
            )
        if action.amount is not None and action.bet_size is not None:
            raise ValueError(
                "Specify either an amount or a bet size, not both"
            )
        if action.amount is None and action.bet_size is None:
            raise ValueError(
                "Bet and raise actions require a target or bet size"
            )

        minimum_amount = request.legal_actions.minimum_bet_or_raise_to
        maximum_amount = request.legal_actions.maximum_bet_or_raise_to
        if minimum_amount is None or maximum_amount is None:
            raise ValueError(
                "Bet and raise actions are not currently available"
            )

        public_state = request.observation.public_state
        actor = next(
            (
                player
                for player in public_state.players
                if player.seat == request.observation.seat
            ),
            None,
        )
        if actor is None:
            raise ValueError(
                "The observation does not contain the acting player"
            )

        if action.bet_size is None:
            bet_amount = Decimal(str(action.amount))
        else:
            amount_to_call = min(
                actor.stack,
                max(player.street_bet for player in public_state.players)
                - actor.street_bet,
            )
            pot_after_call = public_state.pot + amount_to_call
            bet_amount = (
                actor.street_bet
                + amount_to_call
                + pot_after_call * Decimal(action.bet_size.value)
            )
            bet_amount = max(bet_amount, minimum_amount)
            bet_amount = min(bet_amount, maximum_amount)

        if bet_amount >= actor.stack / Decimal("2"):
            return maximum_amount
        return bet_amount
