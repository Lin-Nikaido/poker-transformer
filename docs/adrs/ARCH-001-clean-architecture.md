---
id: ARCH-001
title: 4-Layer Clean Architecture (apis / application / core / infrastructure)
domain: architecture
status: active
date: 2026-05-05
rules: true
files:
  - 'src/**/*.py'
  - 'tests/**/*.py'
---

## Context

The TRUST backend is an AI-agent platform built on FastAPI + Google ADK. It integrates with diverse external systems — LLM backends, vector stores, document pipelines, and external SaaS APIs. Without explicit separation of concerns, the codebase becomes difficult to test and change over time.

## Decision

The `src/trust/` directory is organized into **4 layers**:

| Layer             | Path                        | Responsibility                                                                           |
| ----------------- | --------------------------- | ---------------------------------------------------------------------------------------- |
| `apis/`           | `src/trust/apis/`           | HTTP boundary: FastAPI routers, Pydantic request/response schemas                        |
| `application/`    | `src/trust/application/`    | Use-case orchestration: coordinates core + infrastructure, no framework dependencies     |
| `core/`           | `src/trust/core/`           | Domain logic: abstract base classes, registries, agents, preprocessors, type definitions |
| `infrastructure/` | `src/trust/infrastructure/` | External I/O: DB adapters, external API clients, session services                        |

Dependency direction: `apis/ → application/ → core/ ← infrastructure/`

`infrastructure/` registers concrete implementations into `core/` registries at startup time. `application/` and `core/` depend only on abstract interfaces resolved through the registry.

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
- Registry-based DI is a lightweight DI mechanism for Python — no heavy DI framework required
- Centralizing use cases in `application/` allows unit testing completely decoupled from FastAPI

## Registry Pattern (DI Mechanism)

Registries are defined in the core layer; concrete implementations are registered at startup.

| Registry                         | Defined in                      | Registered by              |
| -------------------------------- | ------------------------------- | -------------------------- |
| `database_registry`              | `core/database/`                | `infrastructure/database/` |
| `store_registry`                 | `core/store/`                   | startup script             |
| `dataloader_registry`            | `core/dataloader/`              | startup script             |
| `preprocessor_strategy_registry` | `core/preprocessor/strategies/` | startup script             |
| `chunker_registry`               | `core/preprocessor/chunker/`    | startup script             |
| `agent_registry`                 | `core/agents/agent_registry.py` | startup script             |
| `tool_registry`                  | `core/tools/tool_registry.py`   | `core/tools/*_tool.py`, `core/tools/*_tools.py`, and `core/agents/*/tools.py` modules |

Tool registration follows the dedicated Tool Registry initialization pattern defined in [ARCH-013](./ARCH-013-tool-registry-pattern.md). Shared tool modules under `core/tools/` expose `initialize()` and register tools through `tool_registry` during startup. Agent-specific tool modules under `core/agents/*/tools.py` expose `initialize(prefix: str)` so tools can be registered with an agent-specific prefix.

## Known Deviations

See [known-deviations.md](./known-deviations.md) for the full list of accepted compromises. Key items:

- Several `core/agents/*/tools.py` files import `OpenAiLlmClient` directly from `infrastructure/`. The abstract `BaseLlmClient` in `core/external_clients_interface/` exists but is not yet applied. Gradual migration to Registry injection is planned (technical debt).
- `apis/auth/auth.py` directly imports from `infrastructure/external_clients/ms_clients/`. To be resolved in an auth middleware refactor.

## Consequences

- **Positive**: Each layer can be tested independently (`infrastructure/` can be replaced with `core/` ABC stubs)
- **Positive**: Adding new DB, store, or agent, or tool requires only a registry registration
- **Negative**: New features require creating files across multiple layers (responsibility is unambiguous, but there is more boilerplate)
- **Negative**: Registry singletons are global state; parallel tests require explicit cleanup (`registry.clear()` in teardown)

## Compliance

**Do:**

- Add new external clients in `infrastructure/external_clients/` and implement the ABC from `core/external_clients_interface/`
- Create new DB adapters in `infrastructure/database/*_database.py` with an `initialize()` function (auto-detected)
- Resolve dependencies in `application/` through registry functions (`get_database()`, `get_store_instance_by_name()`, etc.)
- Add shared tools in `core/tools/*_tool.py` or `core/tools/*_tools.py` with an `initialize()` function as defined in [ARCH-013](./ARCH-013-tool-registry-pattern.md)
- Add agent-specific tools in `core/agents/*/tools.py` with an `initialize(prefix: str)` function as defined in [ARCH-013](./ARCH-013-tool-registry-pattern.md)

**Don't:**

- Import from `application/` or `apis/` inside `infrastructure/`
- Import `apis/` Pydantic schemas inside `application/` (use `core/types/` instead)
- Import concrete `infrastructure/` implementations directly inside `core/` (inject via Registry)
- Register tools at module import time; use the Tool Registry initialization lifecycle instead

## References

- [ARCH-010: Google ADK Patterns and Best Practices](./ARCH-010-google-adk-patterns.md)
- [ARCH-013: Tool Registry and Initialization Pattern](./ARCH-013-tool-registry-pattern.md)
- [Archgate ADR guide](https://cli.archgate.dev/)
- [.rulesync/rules/architecture.md](../../.rulesync/rules/architecture.md)
