"""Stable model action indices shared across players and training."""

from poker.core.types.actions import Action
from poker.core.types.actions import ActionKind
from poker.core.types.actions import BetSize
from poker.core.types.legal_actions import LegalActions


def get_action_options() -> tuple[Action, ...]:
    """Return fold, check, call, six bets, and six raises in fixed order."""
    return (
        Action(kind=ActionKind.FOLD),
        Action(kind=ActionKind.CHECK),
        Action(kind=ActionKind.CALL),
        *(Action(kind=ActionKind.BET, bet_size=size) for size in BetSize),
        *(Action(kind=ActionKind.RAISE, bet_size=size) for size in BetSize),
    )


def get_action_mask(*, legal_actions: LegalActions) -> tuple[bool, ...]:
    """Mask model indices using the current engine's legal decisions."""
    return tuple(
        action.kind in legal_actions.action_kinds
        for action in get_action_options()
    )
