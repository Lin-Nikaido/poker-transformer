---
root: false
targets: ["*"]
description: "Tech stack and architecture patterns for this project"
globs: ["src/**", "tests/**", "cli/**"]
---

# Architecture

## Tech Stack

| Concern          | Technology                                                 |
| ---------------- | ---------------------------------------------------------- |
| framwork         | pytorch                                                    |
| AI Model         | Transformer                                                |
| Package manager  | uv                                                         |
| Lint / format    | Ruff                                                       |
| Testing          | pytest + pytest-asyncio; moto for AWS mocking              |
| Git hooks        | lefthook (gitleaks secret scan on commit/push)             |

## Clean Architecture Layers

```
apis/            <- HTTP boundary: FastAPI routers, Pydantic request/response schemas
application/     <- Function-only use cases: call Core methods and injected I/O ports
core/            <- GameRunner, players, directly held models, learning state, types and ports
infrastructure/  <- External I/O: DB sessions, boto3 clients, third-party APIs, File systems
```

## Async Convention

All I/O -- database, HTTP, external APIs, files -- must be async. FastAPI endpoints are `async def`. Never call `asyncio.run()` inside an async context.

## Testing Conventions

- Unit tests: `tests/unittests/<same-path-as-src>/`
- Run a single file: `uv run pytest tests/unittests/path/to/test_file.py -v`
- Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets
- Async tests: decorate with `@pytest.mark.asyncio`
- Format + lint before committing: `uv run ruff format src/ tests/ && uv run ruff check src/ tests/`

## Architecture Decision Records

| ADR | Decision |
| --- | --- |
| [ARCH-012](docs/adrs/ARCH-012-pokerkit-game-engine.md) | Keep player seating and hand lifecycle in the core game contract; adapt PokerKit in infrastructure. |
| [ARCH-013](docs/adrs/ARCH-013-game-player-and-training-ownership.md) | Keep state in Core, hold nn.Module directly in ModelPlayer, and use application functions only. |

GameRunner owns seating, rotation, and the asynchronous run_hand method that drives
seated players through one hand; BaseGameEngine executes the poker rules for that
hand. HumanPlayer uses an async input port. ModelPlayer owns a reference to
nn.Module and an injected encoder. Future SelfPlayTrainer, RolloutCollector and PPOUpdater belong in Core.
BasePlayer.select_action validates identity, awaits the subclass's _select_action_impl,
and resolves betting targets in its private _resolve_bet_amount method. Observations
expose current street_bet separately from cumulative committed chips. Engines
validate and execute resolved amounts without applying player sizing policy.
Model sampling metadata retains the original discrete action index and probability.
Application has no stateful classes or mutable globals. Inject adapters explicitly
instead of storing games or models in a global registry.

