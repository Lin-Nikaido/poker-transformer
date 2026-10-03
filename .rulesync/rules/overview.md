---
root: true
targets: ["*"]
description: "Poker transformer AI"
globs: ["**/*"]
---

# Project Overview
Poker AI transformer model develop

## Critical Rules

- **Respond in Japanese** -- ALL responses to the user MUST be in Japanese. Code, identifiers, commit messages, and `.rulesync/` files stay in English.
- **No bare `Any`** -- use proper type hints; `Any` is allowed only at external system boundaries with explicit justification.
- **Async-first** -- all I/O must be `async def`; never call `asyncio.run()` inside an async request path.


## Repository Layout

```
src/poker/
  cli/              # Typer command-line boundary
  application/      # Training, inference, and evaluation use cases
  core/             # Poker domain types, rules, policies, and algorithms
  infrastructure/   # Game engine, checkpoint, and external adapters
  config/           # Configuration loading and validation
tests/
  unittests/        # Fast unit tests, mirroring src/ layer structure
  integration/      # End-to-end tests against real or mocked services
```

## Required reading

Before making implementation changes, read the relevant documents under `/docs`.

Primary documents:
- `README.md`
  - Overview
  - Major design decisions

- `docs/ARCHITECTURE.md`
  - System architecture
  - Layer responsibilities
  - Dependency direction

- `docs/CONTRIBUTING.md`
  - Development workflow
  - How to set up developing environment
  - How to run checks before submission

- `docs/CODING_RULES.md`
  - Coding conventions
  - Branch / PR rules
  - Testing expectations
  - Style and maintainability guidelines


## Working rules

1. Do not implement based only on local assumptions.
2. Check the relevant document in `/docs` before changing code.
3. Read `/docs/CODING_RULES.md` and follow its **Coding Guide**
3. Follow existing architecture and coding rules.
4. Prefer minimal, consistent changes over broad rewrites.
5. Do not bypass existing abstractions.
6. If documentation and implementation conflict, report the conflict before making a broad change.
7. When changing behavior, update tests accordingly.
8. When adding new behavior, follow the existing test structure.
9. Keep unit tests independent from LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, and repository secrets.
10. Mark real cloud integration tests with `real_aws`; mark ECS dispatch tests with both `real_aws` and `ecs`.


## General principle

- Structure first. Implementation second.
- Do not solve a local problem by introducing a global inconsistency.


## Workflow

- **Plan first**: Present an implementation plan and wait for user approval before making significant changes.
- **Verify**: After implementation, run `uv run ruff format --check src/ tests/ && uv run ruff check src/ tests/ && uv run pytest tests/unittests/ -v`.
- **Testing boundary**: Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets. Use fakes, `botocore.stub.Stubber`, `moto`, or `tests/mockups/`.
- **Multi-phase**: Significant tasks use `/build` (features) or `/fix` (bugs), which define phase gates and require explicit approval at each step.

## Language & Communication

- **Responses**: All responses and descriptions to the user MUST be in **Japanese**. This is VERY IMPORTANT!
- **Code comments**: Write in English, except variable/function names and commit messages (those stay in English).
- **Human-in-the-loop**: When asking for permission or clarification, use clear and polite Japanese.
