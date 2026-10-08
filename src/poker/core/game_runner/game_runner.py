"""A six-player game with stable identities and an injected hand engine."""

from decimal import Decimal
from uuid import UUID
from uuid import uuid4

from poker.core.game_engine.base_game_engine import BaseGameEngine
from poker.core.players.base_player import BasePlayer
from poker.core.ports.game_observer import BaseGameObserver
from poker.core.types.actions import Action
from poker.core.types.decisions import DecisionRequest
from poker.core.types.game import HandResult
from poker.core.types.game import PlayerHandResult
from poker.core.types.primitives import Seat


class GameRunner:
    """Own seating, position rotation, and consecutive hand lifecycles."""

    def __init__(self, *, engine: BaseGameEngine) -> None:
        self._engine = engine
        self._players: dict[int, BasePlayer] = {}
        self._stacks: dict[UUID, Decimal] = {}
        self._position_players: tuple[BasePlayer, ...] = ()
        self._starting_stacks: tuple[Decimal, ...] = ()
        self._hand_id: UUID | None = None
        self._revision = 0

    def seat_player(
        self,
        *,
        player: BasePlayer,
        table_seat: int,
        stack: Decimal = Decimal("100"),
    ) -> None:
        """Seat a player without starting a hand or assigning private cards."""
        if self._hand_id is not None:
            raise ValueError("Players can only be seated before a hand starts")
        if table_seat not in range(6) or table_seat in self._players:
            raise ValueError(
                "Each player requires a unique table seat from 0 to 5"
            )
        if player.player_id in self._stacks:
            raise ValueError("Each player must have a unique identity")
        if not stack.is_finite() or stack <= 0:
            raise ValueError("Starting stacks must be finite and positive")
        self._players[table_seat] = player
        self._stacks[player.player_id] = stack

    @property
    def is_terminal(self) -> bool:
        """Return whether the current hand has completed."""
        return self._hand_id is not None and self._engine.is_terminal

    def start_hand(self) -> None:
        """Preserve initial positions, then rotate and carry settled stacks."""
        if len(self._players) != 6:
            raise ValueError("A six-max game requires exactly six players")
        if self._hand_id is not None and not self.is_terminal:
            raise ValueError(
                "The current hand must finish before starting another"
            )
        stacks = self._stacks.copy()
        if self._hand_id is not None:
            for player, stack in zip(
                self._position_players,
                self._engine.get_stacks(),
                strict=True,
            ):
                stacks[player.player_id] = stack
            players = (*self._position_players[1:], self._position_players[0])
        else:
            players = tuple(self._players[index] for index in range(6))
        starting_stacks = tuple(stacks[player.player_id] for player in players)
        if any(stack <= 0 for stack in starting_stacks):
            raise ValueError(
                "A six-player session ends when a player has no chips"
            )
        hand_id = uuid4()
        self._engine.start_hand(starting_stacks=starting_stacks)
        self._stacks = stacks
        self._position_players = players
        self._starting_stacks = starting_stacks
        self._hand_id = hand_id
        self._revision = 0

    def get_player(self, *, seat: Seat) -> BasePlayer:
        """Resolve a hand position to its stable player object."""
        if self._hand_id is None:
            raise ValueError("Start a hand before resolving a position")
        return self._position_players[tuple(Seat).index(seat)]

    def get_decision_request(self) -> DecisionRequest | None:
        """Return an isolated observation for the next acting player."""
        if self._hand_id is None or self.is_terminal:
            return None
        seat = self._engine.acting_seat
        if seat is None:
            raise RuntimeError("A running hand must have an acting player")
        return DecisionRequest(
            player_id=self.get_player(seat=seat).player_id,
            hand_id=self._hand_id,
            revision=self._revision,
            observation=self._engine.get_observation(seat=seat).model_copy(
                deep=True
            ),
            legal_actions=self._engine.get_legal_actions().model_copy(
                deep=True
            ),
        )

    def submit_action(
        self, *, request: DecisionRequest, action: Action
    ) -> Action:
        """Reject stale or out-of-turn decisions before touching the engine."""
        seat = self._engine.acting_seat
        if self._hand_id is None or self.is_terminal or seat is None:
            raise ValueError("There is no acting player")
        if (
            request.hand_id != self._hand_id
            or request.revision != self._revision
            or request.player_id != self.get_player(seat=seat).player_id
            or request.observation.seat != seat
        ):
            raise ValueError(
                "The decision request is stale or belongs to another player"
            )
        applied_action = self._engine.submit_action(action=action)
        self._revision += 1
        return applied_action

    def get_hand_result(self) -> HandResult:
        """Attribute terminal chip profit to each player before rotating."""
        if not self.is_terminal or self._hand_id is None:
            raise ValueError("The hand must finish before reading its result")
        return HandResult(
            hand_id=self._hand_id,
            players=tuple(
                PlayerHandResult(
                    player_id=player.player_id,
                    seat=seat,
                    starting_stack=initial,
                    final_stack=final,
                )
                for player, seat, initial, final in zip(
                    self._position_players,
                    tuple(Seat),
                    self._starting_stacks,
                    self._engine.get_stacks(),
                    strict=True,
                )
            ),
        )

    async def run_hand(
        self, *, observer: BaseGameObserver | None = None
    ) -> HandResult:
        """Start and complete one hand using the seated players' behavior."""
        self.start_hand()
        while not self.is_terminal:
            request = self.get_decision_request()
            if request is None:
                raise RuntimeError(
                    "A running hand must expose a decision request"
                )
            player = self.get_player(seat=request.observation.seat)
            decision = await player.select_action(
                request=request.model_copy(deep=True)
            )
            applied_action = self.submit_action(
                request=request,
                action=decision.action,
            )
            if observer is not None:
                await observer.on_decision(
                    request=request,
                    decision=decision,
                    applied_action=applied_action,
                )
        return self.get_hand_result()
