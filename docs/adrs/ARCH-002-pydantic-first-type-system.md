---
id: ARCH-002
title: Pydantic-First Type System (core/types/ as SSOT)
domain: architecture
status: active
date: 2026-05-05
rules: true
files:
  - 'src/**/*.py'
---

## Context

`core/types/` is the designated location for domain type definitions shared across all layers. When independent Pydantic `BaseModel` classes are defined inside `application/` or `infrastructure/`, the same structure ends up in multiple places. Changes to one copy are not propagated to the other, creating type drift that becomes a source of runtime errors.

A concrete example: a `ResponseSchema(BaseModel)` was defined inside `application/validation/` for HTTP responses, making the boundary between it and `core/types/` ambiguous.

## Decision

**Domain types shared across multiple layers must use `core/types/` as the Single Source of Truth.**

| Case                                       | Where to define the type                                                      |
| ------------------------------------------ | ----------------------------------------------------------------------------- |
| Domain types shared across multiple layers | `src/trust/core/types/` (Pydantic model)                                      |
| Fields specific to HTTP input validation   | `apis/schemas/request_schemas.py` (composes `core/types/`)                    |
| Fields specific to HTTP response shaping   | `apis/schemas/response_schemas.py` (composes `core/types/`)                   |
| Structures used only inside `application/` | Python `dataclass` or `TypedDict` (when no external I/O validation is needed) |

**No new Pydantic `BaseModel` subclasses should be defined in `application/` or `infrastructure/`.**

## Rationale

**Alternative: Each layer defines its own Pydantic models**
Allows slim, layer-specific models but introduces DRY violations. The same fields appear in multiple places and changes in one location are not reflected in another, creating a breeding ground for runtime errors.

**Alternative: Pass data as `Any` / `dict`**
Abandons type strictness. Loses the benefits of Pydantic validation and IDE auto-completion.

## Consequences

- **Positive**: Field changes are centralized in `core/types/`, eliminating the risk of missed updates
- **Positive**: Reading `core/types/` alone gives a complete picture of the domain data structures
- **Positive**: Type errors are caught at analysis time (mypy / Pyright)
- **Negative**: HTTP-specific validation (alias config, pagination-only fields, etc.) must remain in `apis/schemas/`

## Compliance

**Do:**

- Add new domain types to `src/trust/core/types/` as Pydantic models
- In `apis/schemas/`, wrap or compose types imported from `core/types/`
- When a data structure is needed inside `application/` with no external I/O validation, use Python `dataclass` or `TypedDict`

**Don't:**

- Define `class Xxx(BaseModel):` in `application/` (put it in `core/types/`)
- Define `class Xxx(BaseModel):` in `infrastructure/` (same rule)
- Re-define a model that already exists in `core/types/` in another layer

## References

- [ARCH-001](./ARCH-001-clean-architecture.md) — 4-layer Clean Architecture
- `src/trust/core/types/` — canonical list of domain types
