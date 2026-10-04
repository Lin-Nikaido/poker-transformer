---
id: ARCH-012
title: PokerKit as the Poker Game Engine
domain: architecture
status: active
date: 2026-10-04
rules: false
---

## Context

The MVP requires a six-player no-limit Texas Hold'em engine that provides legal
betting transitions, terminal states, and hand payouts. Implementing these
rules locally would increase the risk of incorrect betting and side-pot logic.

## Decision

Use PokerKit's predefined `NoLimitTexasHoldem` state as the concrete engine.
Keep the engine port and its public contract in `core/`, and keep PokerKit
configuration and state adaptation in `infrastructure/game_engine/`. Resolve
discrete bet sizes into legal PokerKit targets in the adapter. For pot fraction
`s`, the target is the actor's current street bet plus the amount to call plus
`s` times the total pot after calling. Clamp size-based targets to the legal
range. Convert a target at least half the actor's remaining stack into the
maximum legal target, making the action all-in. Explicit target amounts remain
unchanged unless the all-in threshold applies.

```python
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
    raw_starting_stacks=(Decimal("100"),) * 6,
    player_count=6,
)
```

## Rationale

PokerKit provides the required no-limit Hold'em variant and supports player
counts and stack configurations supplied at state creation. Its state API
exposes legal betting operations, hand completion, and payouts, while the
adapter keeps the dependency outside the domain layer.

**Alternative: RLCard**
Its documented no-limit Hold'em environment supports two players, while this
MVP requires six.

**Alternative: implement a local engine**
This would duplicate complex betting, all-in, showdown, and payout rules before
the MVP can collect training experience.

## Consequences

- **Positive**: the project can build on a maintained, tested poker rules engine.
- **Positive**: the core contract remains independent of PokerKit.
- **Negative**: the adapter must translate between PokerKit values and project
  domain types, and betting-size semantics must be verified against PokerKit
  transitions in Step 05.

## Compliance

**Do:**

- Keep PokerKit imports in `infrastructure/game_engine/`.
- Implement the core game-engine port without importing PokerKit.
- Convert `BetSize` values into legal target amounts in the PokerKit adapter.
- Verify all-in transitions, hand ranking, payouts, and chip conservation in
  Step 05.

**Don't:**

- Import PokerKit from `core/` or `application/`.
- Treat the engine's native state as a player observation.

## References

- [ARCH-001](./ARCH-001-clean-architecture.md)
- [PokerKit simulation documentation](https://pokerkit.readthedocs.io/en/stable/simulation.html)
- [RLCard no-limit Hold'em documentation](https://rlcard.org/rlcard.games.nolimitholdem.html)

