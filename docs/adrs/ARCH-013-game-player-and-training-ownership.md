---
id: ARCH-013
title: Core Game and Player Ownership with Function-only Use Cases
domain: architecture
status: active
date: 2026-10-08
rules: true
files:
  - 'src/poker/**/*.py'
---

## Context

The previous engine adapter owned seating, player-state copies, button rotation,
and hand execution together. There was no behavioral player contract. The agreed
application design requires state to remain outside application objects and
requires ModelPlayer to hold a PyTorch nn.Module directly.

## Decision

Core Game owns a six-player roster, stable player identities, hand revisions,
position rotation, and consecutive-hand lifecycle. BaseGameEngine defines the
single-hand execution contract; PokerKitGameEngine implements it in infrastructure.
The engine owns native cards, stacks, legal transitions, and payouts. Game reads
snapshots through that contract rather than duplicating native rules.

BasePlayer defines asynchronous select_action. HumanPlayer uses an injected
BaseActionSource; ModelPlayer directly holds the supplied nn.Module, an observation
encoder, and its own sampling generator. It never owns an optimizer. Multiple
ModelPlayer instances may share a module while keeping identities and sampling
state separate. Module mode and updates are managed by the caller, not by each turn.

```python
player = ModelPlayer(
    player_id="learner",
    model=model,
    encoder=encoder,
    seed=42,
)
game.seat_player(player=player, table_seat=0)
```

Application contains use-case functions only. Inject Core objects and I/O ports
through keyword arguments. Do not retain state in application classes, global
variables, or closures. Function-local references to returned progress are allowed.
Core run_hand is the common sequential execution function used by play_usecase
and future rollout collection; no stateful runner class is needed.

```python
async def play_usecase(*, game: Game) -> HandResult:
    return await run_hand(game=game)
```

For later learning steps, Core SelfPlayTrainer will hold the learner ModelPlayer,
training counters, and frozen opponents. Core RolloutCollector will generate games
and collect player-local trajectories. Core PPOUpdater will hold optimizer state
and update the same learner.model instance. Application learn_usecase will call
these methods and injected save/report ports. These learning components are design
commitments, not implemented PPO functionality in this change.

## Implementation Boundary

The initial hand preserves explicitly assigned positions. Subsequent hands rotate
positions and carry settled stacks by PlayerId. Table seats are physical indices;
Seat represents UTG/MP/CO/BTN/SB/BB positions. A six-player session stops when a
player has no chips. Learning will create fresh 100 BB hands rather than making
automatic replenishment a universal Game rule.

The current ModelPlayer adapter expects a one-dimensional Tensor with 15 logits:
fold, check, call, six bets, six raises. The injected encoder remains a port; the
Transformer encoder and value head belong to later roadmap steps. Selection
returns the original action index, log probability, and policy version. Sizes are
resolved through the existing core sizing function and recorded as applied amounts.

## Rationale

**Alternative: application service objects**
They place game and learning state in the layer the user explicitly requires to
remain function-only.

**Alternative: Game calls players and owns optimization**
It combines poker state, asynchronous interaction, trajectory collection, and PPO
updates, making isolated rule tests and shared inference harder.

**Alternative: a mandatory Policy object between Player and Module**
It adds an ownership indirection that is unnecessary for the approved design.
ModelPlayer performs the inference adaptation around its directly held module.

## Consequences

- Positive: human and model players share one game and engine contract.
- Positive: native rules remain in PokerKit; unit tests can inject isolated engines.
- Positive: shared weights do not imply shared identity or sampling generators.
- Negative: BasePokerGame/PokerKitGame callers must migrate to Game/BaseGameEngine/
  PokerKitGameEngine. This is an intentional internal API change before release.
- Negative: learning must preserve the inference action order and add the PPO
  value/trajectory contract explicitly in later steps.

## Compliance

**Do:**

- Keep Game, players, and future stateful learning components in Core.
- Use function-only application entry points and inject dependencies.
- Keep PokerKit imports in infrastructure and PyTorch computation in Core.
- Pass only player-local observation snapshots to Player implementations.
- Attribute results and trajectories to stable player identities.
- Keep a frozen opponent's weights independent from the updated learner's weights.

**Don't:**

- Define application-layer classes or mutable module-level state.
- Require ModelPlayer to obtain its model through a Policy wrapper.
- Duplicate stacks or private cards inside behavioral Player objects.
- Mutate shared model mode or weights during action selection.
- Expose native engine state or an observer's private records as public UI output.

## References

- [ARCH-001](ARCH-001-clean-architecture.md)
- [ARCH-012](ARCH-012-pokerkit-game-engine.md)
- [Architecture](../ARCHITECTURE.md)
- [Roadmap](../../INSTRUCTION.md)
