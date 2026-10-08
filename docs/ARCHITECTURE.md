# Architecture

## Project structure

The installable Python package is `poker`, located under `src/poker/`. The
repository is being built as a poker AI, so the structure below describes both
the modules that exist now and the ownership rules for modules added by the MVP.

```text
src/poker/
  cli/             Typer command-line boundary
  application/     Training, inference, and evaluation use cases
  core/            Poker domain types, rules, policy interfaces, and algorithms
  infrastructure/ External engines, checkpoint files, and other adapters
  config/          Configuration loading and validation
tests/
  unittests/       Fast isolated tests mirroring src/poker/
  integration/     Tests across adapters and system boundaries
```

## Layer responsibilities

| Layer | Owns | May depend on |
| --- | --- | --- |
| `cli/` | Parse command-line input, call an application use case, render output | `application/`, `config/` |
| `application/` | Function-only use cases connecting Core methods and injected I/O ports | `core/` and injected ports |
| `core/` | Game lifecycle, players, observations, legal actions, model computation, learning state and algorithms, and port definitions | Standard library and domain-level dependencies, including PyTorch |
| `infrastructure/` | Concrete game engine, storage, external service, and file adapters | `core/` |
| `config/` | Parse and validate settings at the process boundary | Configuration libraries |

Dependencies point inward: command-line and infrastructure adapters connect to
application/core contracts; domain logic does not import CLI, application, or
infrastructure modules. ModelPlayer directly holds its PyTorch `nn.Module` in
`core/`. Application functions do not retain state in classes, globals, or closures.
GameRunner and future SelfPlayTrainer/RolloutCollector/PPOUpdater objects own domain and
learning state in Core. Application connects their methods with save/report ports.
Inject dependencies explicitly; do not introduce shared mutable game registries.

## Game and player ownership

`core/game_runner/GameRunner` seats six `BasePlayer` objects and owns stable
identities, initial positions, later button rotation, and hand revisions. `BaseGameEngine` executes a
single hand; `infrastructure/game_engine/PokerKitGameEngine` adapts native state,
legal actions, snapshots, and payouts. Engine and behavioral player lifecycles are
separate. The first hand keeps its initial seating; later hands carry settled
stacks and rotate positions. Physical table indices differ from hand positions.

`HumanPlayer` awaits an injected input port. `ModelPlayer.model` is the supplied
`nn.Module`, shared if desired by five opponents, with a separate sampling
generator per player. Its encoder is injected and is shared with future training.
Action selection applies a legal mask to 15 logits and preserves sampling metadata.
`GameRunner.run_hand()` drives both player kinds and owns the sequential hand
lifecycle.
`play_usecase` is a thin asynchronous function that delegates to this method.
Optional observers can record private player-local decisions but must not render
those records as public game output.

## Training ownership and remaining work

The planned `poker learn` command calls a function-only `learn_usecase`. Core
`SelfPlayTrainer` will hold the learner ModelPlayer and training counters;
`RolloutCollector` will collect one current learner against five frozen opponents;
`PPOUpdater` will update the same `learner.model` parameters. The first opponents
are random, and later opponents use a distinct frozen copy from the previous
epoch. Application functions handle checkpoint I/O and reporting via injected
ports. These components, the actual encoder/Transformer/value head, terminal RL
rewards, checkpoint handling, and the `learn`/`play` CLI are still roadmap work.

The completed gameplay foundation already supports one HumanPlayer and five
ModelPlayer objects with injected input and encoder adapters. Integration tests
exercise that combination against PokerKit without an interactive terminal.

## I/O and async boundary

All external I/O is owned by `infrastructure/` and exposed through injected
interfaces. Database, network, and asynchronous file operations use `async def`
and are awaited by application use cases. Do not call `asyncio.run()` from an
async request path. CPU-bound PyTorch inference and training are synchronous
computation; keep them out of async I/O adapters and use an explicit worker
boundary if a future async service must invoke long-running model work.

The current MVP is a local CLI and does not need an HTTP API, database, cloud
service, or distributed worker. Add adapters only when a use case needs them.

## Tests

Unit tests mirror source paths under `tests/unittests/` and use fakes for ports.
They do not depend on LocalStack, real cloud services, or repository secrets.
Cross-boundary tests belong under `tests/integration/`. See
`docs/CONTRIBUTING.md` for local commands.

## Architecture Decision Records

| ADR | Decision |
| --- | --- |
| [ARCH-012](adrs/ARCH-012-pokerkit-game-engine.md) | Keep seating, hand lifecycle, and bet sizing in the core game contract; adapt PokerKit in infrastructure. |
| [ARCH-013](adrs/ARCH-013-game-player-and-training-ownership.md) | Keep GameRunner, players, and learning state in Core; directly hold models in ModelPlayer and expose function-only application use cases. |


