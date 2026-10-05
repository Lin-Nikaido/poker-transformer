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
application/     <- Use cases: orchestrate core + infra, no framework imports
core/            <- Domain logic: agents, preprocessors, stores, model_registry, types
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

