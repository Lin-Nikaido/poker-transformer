---
id: ARCH-013
title: Core-Owned One-Hand Poker Environment
domain: architecture
status: active
date: 2026-10-04
rules: false
---

## Context

Step 06 needs a one-hand environment that exposes legal decisions and player
observations, then returns each seat's normalized terminal result. The same
contract must work with different game engines and prevent private cards from
other seats from reaching a policy.

## Decision

Own the synchronous one-hand environment and reward calculation in `core/`.
Extend the game-engine port with an actor-only observation and a terminal
`HandResult`. Keep PokerKit state conversion in
`infrastructure/game_engine/`. Return no intermediate reward; at hand end,
return each fixed-order seat's final stack change divided by the initial big
blind.

## Rationale

Environment transitions and normalized poker rewards are domain behavior. The
core environment depends only on the game-engine port, while an adapter is
responsible for translating a concrete engine state into the player's
observation and terminal stack result.

## Consequences

- **Positive**: collection and training can drive a consistent environment
  without depending on PokerKit types.
- **Positive**: the engine adapter provides a narrow boundary for hidden cards.
- **Negative**: each engine adapter must implement actor-only observations and
  terminal results in fixed seat order.

## Compliance

**Do:**

- Keep RL environment orchestration and normalized rewards in `core/`.
- Return only the current actor's private hand alongside public table state.
- Return terminal rewards in UTG, MP, CO, BTN, SB, BB order.

**Don't:**

- Expose the engine's full state or another player's private hand to the policy.
- Emit intermediate rewards in the one-hand environment.

## References

- [ARCH-001](./ARCH-001-clean-architecture.md)
- [ARCH-012](./ARCH-012-pokerkit-game-engine.md)
