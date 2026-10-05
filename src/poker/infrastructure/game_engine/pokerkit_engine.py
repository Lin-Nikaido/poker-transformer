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

from poker.core.environment.bet_sizing import resolve_bet_target
from poker.core.game_engine.game_engine import BasePokerGame
from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.cards import Card
from poker.core.types.cards import CardRank
from poker.core.types.cards import Hand
from poker.core.types.cards import Suit
from poker.core.types.legal_actions import LegalActions
from poker.core.types.player import PlayerState
from poker.core.types.primitives import Seat


SEATS = tuple(Seat)
AUTOMATIONS = tuple(automation for automation in Automation)
SUITS = {
    "c": Suit.CLUBS,
    "d": Suit.DIAMONDS,
    "h": Suit.HEARTS,
    "s": Suit.SPADES,
}


class PokerKitGame(BasePokerGame):
    """Run consecutive six-max Hold'em hands through PokerKit."""

    def __init__(self) -> None:
        self._state: State | None = None
        self._players: list[PlayerState] = []

    def seat_player(
        self,
        *,
        players: list[PlayerState],
    ) -> None:
        """Place the six players without initializing a hand."""
        if self._state is not None:
            raise ValueError("Players can only be seated before a hand starts")
        if len(players) != len(SEATS):
            raise ValueError("A six-max game requires exactly six players")

        players_by_seat = {player.seat: player for player in players}
        if len(players_by_seat) != len(SEATS):
            raise ValueError("Each player must occupy a unique seat")
        self._players = [
            players_by_seat[seat].model_copy(deep=True) for seat in SEATS
        ]

    def start_hand(self) -> None:
        """Move the button, post blinds, deal cards, and activate UTG."""
        if not self._players:
            raise ValueError("Seat players before starting a hand")
        if self._state is not None and not self.is_terminal:
            raise ValueError(
                "The current hand must finish before starting another"
            )

        players = self._players
        if self._state is not None:
            players = [
                player.model_copy(
                    update={
                        "stack": Decimal(str(self._state.stacks[index])),
                        "hand": None,
                        "committed": Decimal("0"),
                        "is_folded": False,
                        "is_all_in": False,
                    },
                )
                for index, player in enumerate(players)
            ]
        players = [*players[1:], players[0]]
        self._players = [
            player.model_copy(update={"seat": seat, "hand": None})
            for seat, player in zip(SEATS, players, strict=True)
        ]
        self._state = NoLimitTexasHoldem.create_state(
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
            raw_starting_stacks=tuple(
                player.stack for player in self._players
            ),
            player_count=len(SEATS),
        )
        for index, player in enumerate(self._players):
            player.hand = Hand(
                cards=tuple(
                    self._convert_card(card)
                    for card in self._state.hole_cards[index]
                ),
            )

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
    ) -> None:
        """Submit one domain action to the underlying PokerKit state."""
        if self._state is None:
            raise ValueError("Start a hand before applying actions")
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

        if action.kind is ActionKind.FOLD:
            self._state.fold()
            return
        if action.kind in (ActionKind.CHECK, ActionKind.CALL):
            self._state.check_or_call()
            return
        actor_index = self._state.actor_index
        if actor_index is None:
            raise ValueError("There is no acting player")
        amount_to_call = self._state.checking_or_calling_amount
        target_amount = resolve_bet_target(
            action=action,
            current_street_bet=Decimal(str(self._state.bets[actor_index])),
            amount_to_call=Decimal(str(amount_to_call or 0)),
            total_pot=Decimal(str(self._state.total_pot_amount)),
            remaining_stack=Decimal(str(self._state.stacks[actor_index])),
            legal_actions=legal_actions,
        )
        self._state.complete_bet_or_raise_to(target_amount)

    @staticmethod
    def _convert_card(card: PokerKitCard) -> Card:
        return Card(
            rank=CardRank(str(card.rank)),
            suit=SUITS[str(card.suit)],
        )
