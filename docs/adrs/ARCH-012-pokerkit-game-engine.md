---
id: ARCH-012
title: PokerKit as the Poker Game Engine
domain: architecture
status: active
date: 2026-10-08
rules: false
---

## Context

The MVP requires a six-player no-limit Texas Hold'em engine that provides legal
betting transitions, terminal states, and hand payouts. Implementing these
rules locally would increase the risk of incorrect betting and side-pot logic.

## Decision

Use PokerKit's predefined `NoLimitTexasHoldem` state as the concrete engine.
Keep BaseGameEngine in `core/game_engine/` and PokerKitGameEngine configuration
and state adaptation in `infrastructure/game_engine/`. Core GameRunner in
`core/game_runner/` owns player seating and consecutive-hand lifecycle.
`seat_player` assigns a
BasePlayer to a physical seat without starting a hand. The initial hand preserves
that position order; later hands rotate the button and carry settled stacks by
stable player identity. The engine starts one supplied hand, posts blinds, deals
hole cards, and executes legal decisions. It does not seat behavioral players.
GameRunner validates the acting identity and decision revision before
submitting actions.

Resolve discrete bet sizes through `BasePlayer._resolve_bet_target` before
submitting a selected action to the engine. The adapter supplies public
`street_bet` values separately from cumulative `committed` amounts and exposes
legal target bounds. For pot fraction `s`, the target is the actor's current street bet
plus the amount to call plus `s` times the total pot after calling. Clamp
size-based targets to the legal range. Convert a target at least half the
actor's remaining stack into the maximum legal target, making the action
all-in. Explicit target amounts remain unchanged unless the all-in threshold
applies.

The engine accepts resolved target amounts and validates their legality through
PokerKit. It rejects unresolved `BetSize` values and does not apply player sizing
or all-in policy to explicit engine inputs.

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
- **Positive**: the core game contract remains independent of PokerKit and
  exposes seating and hand-start operations on one game object.
- **Negative**: the adapter must translate between PokerKit values and project
  domain types, and the core sizing rule must be verified against PokerKit
  transitions in Step 05.

## Compliance

**Do:**

- Keep PokerKit imports in `infrastructure/game_engine/`.
- Keep the engine contract in `core/game_engine/` and seating/lifecycle in
  `core/game_runner/`.
- Keep PokerKit state creation and adaptation in
  `infrastructure/game_engine/`.
- Resolve `BetSize` values into legal targets in the private BasePlayer method
  using the supplied observation and legal target bounds.
- Expose current street bets separately from cumulative commitments.
- Verify all-in transitions, hand ranking, payouts, and chip conservation in
  Step 05.

**Don't:**

- Import PokerKit from `core/` or `application/`.
- Treat the engine's native state as a player observation.
- Own seating or button rotation inside the PokerKit adapter.
- Resolve player bet sizes or apply the half-stack policy inside the engine.

## References

- [ARCH-001](./ARCH-001-clean-architecture.md)
- [ARCH-013](./ARCH-013-game-player-and-training-ownership.md)
- [PokerKit simulation documentation](https://pokerkit.readthedocs.io/en/stable/simulation.html)
- [RLCard no-limit Hold'em documentation](https://rlcard.org/rlcard.games.nolimitholdem.html)

