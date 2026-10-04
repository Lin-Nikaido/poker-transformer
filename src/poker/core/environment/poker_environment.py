# Copyright (c) 2026 YourIndependence. All rights reserved.

"""One-hand environment suitable for reinforcement-learning agents."""

from poker.core.environment.rewards import calculate_terminal_rewards
from poker.core.ports.game_engine import GameEngine
from poker.core.types.actions import Action
from poker.core.types.environment import EnvironmentState
from poker.core.types.environment import EnvironmentTransition


class PokerEnvironment:
    """Drive one poker hand through an injected game-engine port."""

    def __init__(
        self,
        *,
        game_engine: GameEngine,
    ) -> None:
        self._game_engine = game_engine
        self._game = None

    def reset(self) -> EnvironmentState:
        """Start a new hand and expose its first decision state."""
        self._game = self._game_engine.start_hand()
        if self._game.is_terminal:
            raise ValueError("A new hand cannot start in a terminal state")
        return self._get_state()

    def step(
        self,
        *,
        action: Action,
    ) -> EnvironmentTransition:
        """Apply one action and return the next state or terminal rewards."""
        if self._game is None:
            raise ValueError("Call reset before stepping the environment")
        if self._game.is_terminal:
            raise ValueError("Cannot step a terminal episode")

        acting_seat = self._game.acting_seat
        if acting_seat is None:
            raise ValueError("A nonterminal hand must have an acting player")
        self._game.step(action=action)

        if self._game.is_terminal:
            rewards = calculate_terminal_rewards(
                hand_result=self._game.get_result(),
            )
            return EnvironmentTransition(
                acting_seat=acting_seat,
                next_state=None,
                rewards=rewards,
                is_terminal=True,
            )

        return EnvironmentTransition(
            acting_seat=acting_seat,
            next_state=self._get_state(),
            rewards=None,
            is_terminal=False,
        )

    def _get_state(self) -> EnvironmentState:
        if self._game is None:
            raise ValueError("Call reset before reading environment state")
        if self._game.acting_seat is None:
            raise ValueError("A terminal hand has no decision state")
        return EnvironmentState(
            observation=self._game.get_observation(),
            legal_actions=self._game.get_legal_actions(),
        )
