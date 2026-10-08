# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, use or distribution is prohibited.

"""PokerKit-backed six-max Hold'em engine adapter."""

from __future__ import annotations

from decimal import Decimal

from pokerkit import Automation
from pokerkit import Card as PokerKitCard
from pokerkit import NoLimitTexasHoldem
from pokerkit.state import State

from poker.core.game_engine.base_game_engine import BaseGameEngine
from poker.core.types.actions import Action
from poker.core.types.actions import ActionHistory
from poker.core.types.actions import ActionHistoryEntry
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PublicPlayerState
from poker.core.types.primitives import Seat
from poker.core.types.primitives import Street
from poker.core.types.table import PlayerObservation
from poker.core.types.table import TableState


SEATS = tuple(Seat)
AUTOMATIONS = tuple(automation for automation in Automation)
SUITS = {
    "c": Suit.CLUBS,
    "d": Suit.DIAMONDS,
    "h": Suit.HEARTS,
    "s": Suit.SPADES,
}


class PokerKitGameEngine(BaseGameEngine):
    """Execute a six-max hand without owning players or rotating the button."""

    def __init__(self) -> None:
        self._state: State | None = None
        self._history = ActionHistory()
        self._folded: set[Seat] = set()
        self._street = Street.PREFLOP

    def start_hand(
        self,
        *,
        starting_stacks: tuple[Decimal, ...],
    ) -> None:
        """Start exactly the supplied position order and post blinds."""
        if self._state is not None and not self.is_terminal:
            raise ValueError(
                "The current hand must finish before starting another"
            )

        if len(starting_stacks) != len(SEATS):
            raise ValueError("A six-max engine requires exactly six stacks")
        if any(
            not stack.is_finite() or stack <= 0 for stack in starting_stacks
        ):
            raise ValueError("Starting stacks must be finite and positive")
        state = NoLimitTexasHoldem.create_state(
            automations=AUTOMATIONS,
            ante_trimming_status=True,
            raw_antes=Decimal("0"),
            raw_blinds_or_straddles=(
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0.5"),
                Decimal("1"),
            ),
            min_bet=Decimal("1"),
            raw_starting_stacks=starting_stacks,
            player_count=len(SEATS),
        )
        self._state = state
        self._history = ActionHistory()
        self._folded = set()
        self._street = Street.PREFLOP

    @property
    def acting_seat(self) -> Seat | None:
        """Return the seat whose betting action is next."""
        if self._state is None:
            return None
        actor_index = self._state.actor_index
        if actor_index is None:
            return None
        return SEATS[actor_index]

    @property
    def is_terminal(self) -> bool:
        """Return whether PokerKit has completed the hand."""
        return self._state is not None and not self._state.status

    def get_legal_actions(self) -> LegalActions:
        """Return the current betting choices and legal raise bounds."""
        if self._state is None or self.is_terminal:
            return LegalActions(action_kinds=())

        action_kinds: list[ActionKind] = []
        if self._state.can_fold():
            action_kinds.append(ActionKind.FOLD)
        if self._state.can_check_or_call():
            action_kinds.append(
                ActionKind.CALL
                if self._state.checking_or_calling_amount
                else ActionKind.CHECK
            )

        minimum_bet_or_raise_to = None
        maximum_bet_or_raise_to = None
        if self._state.can_complete_bet_or_raise_to():
            action_kinds.append(
                ActionKind.RAISE if any(self._state.bets) else ActionKind.BET
            )
            minimum_bet_or_raise_to = (
                self._state.min_completion_betting_or_raising_to_amount
            )
            maximum_bet_or_raise_to = (
                self._state.max_completion_betting_or_raising_to_amount
            )
            if minimum_bet_or_raise_to is not None:
                minimum_bet_or_raise_to = Decimal(str(minimum_bet_or_raise_to))
            if maximum_bet_or_raise_to is not None:
                maximum_bet_or_raise_to = Decimal(str(maximum_bet_or_raise_to))
        return LegalActions(
            action_kinds=tuple(action_kinds),
            minimum_bet_or_raise_to=minimum_bet_or_raise_to,
            maximum_bet_or_raise_to=maximum_bet_or_raise_to,
        )

    def submit_action(
        self,
        *,
        action: Action,
    ) -> Action:
        """Submit one domain action to the underlying PokerKit state."""
        if self._state is None:
            raise ValueError("Start a hand before applying actions")
        legal_actions = self.get_legal_actions()
        if action.kind not in legal_actions.action_kinds:
            raise ValueError(f"Action {action.kind} is not legal")
        if (
            action.bet_size is not None or action.amount is not None
        ) and action.kind not in (
            ActionKind.BET,
            ActionKind.RAISE,
        ):
            raise ValueError(
                "Amounts and bet sizes are only valid for bet and raise actions"
            )
        actor_index = self._state.actor_index
        if actor_index is None:
            raise ValueError("There is no acting player")
        street = tuple(Street)[self._state.street_index]
        if action.kind is ActionKind.FOLD:
            self._state.fold()
            self._folded.add(SEATS[actor_index])
            applied_action = Action(kind=action.kind)
        elif action.kind in (ActionKind.CHECK, ActionKind.CALL):
            committed = Decimal(
                str(self._state.checking_or_calling_amount or 0)
            )
            self._state.check_or_call()
            applied_action = Action(
                kind=action.kind, amount=committed if committed else None
            )
        else:
            if action.bet_size is not None or action.amount is None:
                raise ValueError(
                    "Bet and raise actions require a resolved target amount"
                )
            target_amount = action.amount
            self._state.complete_bet_or_raise_to(target_amount)
            applied_action = Action(kind=action.kind, amount=target_amount)
        getattr(self._history, street.value).append(
            ActionHistoryEntry(
                actor=SEATS[actor_index],
                action=applied_action.model_copy(deep=True),
            ),
        )
        self._street = (
            street
            if self._state.street_index is None
            else tuple(Street)[self._state.street_index]
        )
        return applied_action

    def get_stacks(self) -> tuple[Decimal, ...]:
        """Return settled or current stacks without revealing private cards."""
        if self._state is None:
            raise ValueError("Start a hand before reading stacks")
        return tuple(Decimal(str(stack)) for stack in self._state.stacks)

    def get_observation(self, *, seat: Seat) -> PlayerObservation:
        """Project native state into an independent player-safe snapshot."""
        if self._state is None or self.is_terminal:
            raise ValueError("Observations require an active hand")
        index = SEATS.index(seat)
        cards = tuple(
            self._convert_card(card) for card in self._state.hole_cards[index]
        )
        if len(cards) != 2:
            raise ValueError("The player no longer has a private hand")
        return PlayerObservation(
            seat=seat,
            private_hand=Hand(cards=cards),
            public_state=TableState(
                street=self._street,
                pot=Decimal(str(self._state.total_pot_amount)),
                current_actor=self.acting_seat,
                players=tuple(
                    PublicPlayerState(
                        seat=position,
                        stack=stack,
                        committed=Decimal(
                            str(self._state.starting_stacks[player_index])
                        )
                        - stack,
                        street_bet=Decimal(
                            str(self._state.bets[player_index])
                        ),
                        is_folded=position in self._folded,
                        is_all_in=stack == 0 and position not in self._folded,
                    )
                    for player_index, (position, stack) in enumerate(
                        zip(SEATS, self.get_stacks(), strict=True)
                    )
                ),
                community_cards=tuple(
                    self._convert_card(card)
                    for board in self._state.board_cards
                    for card in board
                ),
                action_history=self._history.model_copy(deep=True),
            ),
        )

    @staticmethod
    def _convert_card(card: PokerKitCard) -> Card:
        return Card(
            rank=CardRank(str(card.rank)),
            suit=SUITS[str(card.suit)],
        )
