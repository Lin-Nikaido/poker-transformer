---
id: ARCH-001
title: Clean Architecture with Injected Core Contracts
domain: architecture
status: active
date: 2026-10-08
rules: true
files:
  - 'src/**/*.py'
  - 'tests/**/*.py'
---

## Context

This project is transformer model develop and leaning system.

## Decision

The `src/poker/` directory is organized into **4 layers**:

| Layer             | Path                        | Responsibility                                                                           |
| ----------------- | --------------------------- | ---------------------------------------------------------------------------------------- |
| `apis/`           | `src/poker/apis/`           | HTTP boundary: FastAPI routers, Pydantic request/response schemas                        |
| `application/`    | `src/poker/application/`    | Function-only use cases that call Core methods and injected I/O ports |
| `core/`           | `src/poker/core/`           | Game, players, model computation, learning state, types and abstract ports |
| `infrastructure/` | `src/poker/infrastructure/` | External I/O: DB adapters, external API clients, session services                        |

Dependency direction: `apis/ → application/ → core/ ← infrastructure/`

Application use cases are functions that receive Core objects and abstract I/O
ports explicitly. Infrastructure implements those ports. State belongs to Core
objects or native adapter resources rather than application service instances.
Construct concrete adapters at the process boundary and inject them. A global
registry is not required for the local CLI. See ARCH-013 for game/player ownership.

### Auxiliary Modules

| Module         | Responsibility                                                  |
| -------------- | --------------------------------------------------------------- |
| `config/`      | Environment variables and settings (accessible from all layers) |
| `exceptions/`  | Custom exceptions (accessible from all layers)                  |
| `task_runner/` | Background task management                                      |

## Rationale

**Alternative: Feature-Sliced Design**
Organizes directories by feature domain. As feature count grows, cross-cutting concerns like LLM clients and DB connections scatter across multiple features, making dependency graphs complex and hard to reason about.

**Alternative: Flat structure**
Works at small scale but loses control of inter-component dependencies quickly. Test isolation also becomes difficult.

**Adopted because:**
- Port (core/ ABC) + Adapter (infrastructure/ concrete class) pattern makes external system replacement straightforward
- Explicit dependency injection keeps state ownership visible without a DI framework
- Centralizing use cases in `application/` allows unit testing completely decoupled from FastAPI

## Dependency Injection

Define replaceable contracts in Core. Pass implementations through keyword-only
constructor or function arguments. Keep concrete infrastructure imports outside
Core and Application. This replaces the inherited registry requirement for the
current CLI; unrelated database, ADK, and tool registries are not project modules.

```python
game = Game(engine=engine)
result = await play_usecase(game=game)
```

## Consequences

- **Positive**: Each layer can be tested independently (`infrastructure/` can be replaced with `core/` ABC stubs)
- **Positive**: Each game can receive a separate adapter instance without global registration
- **Negative**: New features require creating files across multiple layers (responsibility is unambiguous, but there is more boilerplate)
- **Negative**: The process boundary must assemble dependencies explicitly

## Compliance

**Do:**

- Put concrete external adapters in infrastructure and implement their Core contracts
- Construct adapters at the process boundary and pass them into Core objects
- Inject Core capabilities and abstract ports into application functions
- Keep domain and training state in Core objects, including directly held models

**Don't:**

- Import from `application/` or `apis/` inside `infrastructure/`
- Import `apis/` Pydantic schemas inside `application/` (use `core/types/` instead)
- Import concrete `infrastructure/` implementations directly inside `core/` (inject through its contracts)
- Register tools at module import time; use the Tool Registry initialization lifecycle instead

## References

- [ARCH-013: Game, Player, and Training Ownership](./ARCH-013-game-player-and-training-ownership.md)
- [Archgate ADR guide](https://cli.archgate.dev/)
- [.rulesync/rules/architecture.md](../../.rulesync/rules/architecture.md)
