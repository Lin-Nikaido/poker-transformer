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

from poker.core.ports.game_engine import GameEngine
from poker.core.ports.game_engine import PokerGame
from poker.core.types.actions import Action
from poker.core.types.actions import ActionHistory
from poker.core.types.actions import ActionHistoryEntry
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.hand_result import HandResult
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


class PokerKitHand(PokerGame):
    """Adapt one PokerKit state to the core game-session contract."""

    def __init__(
        self,
        *,
        state: State,
    ) -> None:
        super().__init__()
        self._state = state
        self._action_history = ActionHistory()

    @property
    def acting_seat(self) -> Seat | None:
        """Return the seat whose betting action is next."""
        actor_index = self._state.actor_index
        if actor_index is None:
            return None
        return SEATS[actor_index]

    @property
    def is_terminal(self) -> bool:
        """Return whether PokerKit has completed the hand."""
        return not self._state.status

    def get_legal_actions(self) -> LegalActions:
        """Return the current betting choices and legal raise bounds."""
        if self.is_terminal:
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

    def get_observation(self) -> PlayerObservation:
        """Build an observation containing only the actor's private cards."""
        actor_index = self._state.actor_index
        if actor_index is None:
            raise ValueError("A terminal hand has no player observation")
        street = tuple(Street)[self._state.street_index]
        players = tuple(
            PublicPlayerState(
                seat=SEATS[index],
                stack=Decimal(str(self._state.stacks[index])),
                committed=Decimal(str(-self._state.payoffs[index])),
                is_folded=not self._state.statuses[index],
                is_all_in=(
                    self._state.statuses[index]
                    and self._state.stacks[index] == 0
                ),
            )
            for index in range(len(SEATS))
        )
        return PlayerObservation(
            seat=SEATS[actor_index],
            private_hand=Hand(
                cards=tuple(
                    self._convert_card(card)
                    for card in self._state.hole_cards[actor_index]
                )
            ),
            public_state=TableState(
                street=street,
                pot=Decimal(str(self._state.total_pot_amount)),
                current_actor=SEATS[actor_index],
                players=players,
                community_cards=tuple(
                    self._convert_card(card)
                    for card in self._state.board_cards
                ),
                action_history=self._action_history,
            ),
        )

    def get_result(self) -> HandResult:
        """Return starting and final stacks after the hand is complete."""
        if not self.is_terminal:
            raise ValueError("A hand result is available only when terminal")
        return HandResult(
            starting_stacks=tuple(
                Decimal(str(stack)) for stack in self._state.starting_stacks
            ),
            final_stacks=tuple(
                Decimal(str(stack)) for stack in self._state.stacks
            ),
            initial_big_blind=Decimal(
                str(self._state.blinds_or_straddles[-1])
            ),
        )

    def step(
        self,
        *,
        action: Action,
    ) -> None:
        """Apply one domain action to the underlying PokerKit state."""
        legal_actions = self.get_legal_actions()
        if action.kind not in legal_actions.action_kinds:
            raise ValueError(f"Action {action.kind} is not legal")
        if action.bet_size is not None and action.kind not in (
            ActionKind.BET,
            ActionKind.RAISE,
        ):
            raise ValueError(
                "Bet sizes are only valid for bet and raise actions"
            )

        actor = self.acting_seat
        street_index = self._state.street_index
        if action.kind is ActionKind.FOLD:
            self._state.fold()
            recorded_action = action
        elif action.kind in (ActionKind.CHECK, ActionKind.CALL):
            self._state.check_or_call()
            recorded_action = action
        else:
            target_amount = self._get_bet_or_raise_to(action=action)
            self._state.complete_bet_or_raise_to(target_amount)
            recorded_action = Action(kind=action.kind, amount=target_amount)
        if actor is not None:
            self._record_action(
                street_index=street_index,
                entry=ActionHistoryEntry(actor=actor, action=recorded_action),
            )

    def _record_action(
        self,
        *,
        street_index: int,
        entry: ActionHistoryEntry,
    ) -> None:
        history = self._action_history
        if street_index == 0:
            history.preflop.append(entry)
        elif street_index == 1:
            history.flop.append(entry)
        elif street_index == 2:
            history.turn.append(entry)
        elif street_index == 3:
            history.river.append(entry)

    @staticmethod
    def _convert_card(card: PokerKitCard) -> Card:
        return Card(
            rank=CardRank(str(card.rank)),
            suit=SUITS[str(card.suit)],
        )

    def _get_bet_or_raise_to(
        self,
        *,
        action: Action,
    ) -> Decimal:
        if action.amount is not None and action.bet_size is not None:
            raise ValueError(
                "Specify either an amount or a bet size, not both"
            )

        actor_index = self._state.actor_index
        if actor_index is None:
            raise ValueError("There is no acting player")

        if action.bet_size is None:
            if action.amount is None:
                raise ValueError(
                    "Bet and raise actions require a target amount"
                )
            target_amount = Decimal(str(action.amount))
        else:
            amount_to_call = self._state.checking_or_calling_amount
            if amount_to_call is None:
                amount_to_call = 0
            pot_after_call = self._state.total_pot_amount + amount_to_call
            target_amount = (
                self._state.bets[actor_index]
                + amount_to_call
                + pot_after_call * Decimal(action.bet_size.value)
            )

        legal_actions = self.get_legal_actions()
        minimum_amount = legal_actions.minimum_bet_or_raise_to
        maximum_amount = legal_actions.maximum_bet_or_raise_to
        if minimum_amount is None or maximum_amount is None:
            raise ValueError(
                "Bet and raise actions are not currently available"
            )

        if action.bet_size is not None:
            target_amount = max((target_amount, minimum_amount))
            target_amount = min((target_amount, maximum_amount))
        remaining_stack = Decimal(str(self._state.stacks[actor_index]))
        if target_amount >= remaining_stack / Decimal("2"):
            target_amount = maximum_amount
        return target_amount


class PokerKitEngine(GameEngine):
    """Create six-max No-Limit Texas Hold'em hands with PokerKit."""

    def start_hand(self) -> PokerKitHand:
        """Create a hand with the MVP table configuration."""
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
            raw_starting_stacks=(Decimal("100"),) * len(SEATS),
            player_count=len(SEATS),
        )
        return PokerKitHand(state=state)
