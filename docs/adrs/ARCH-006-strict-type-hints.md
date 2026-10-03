---
id: ARCH-006
title: Strict Type Hints (No Bare Any)
domain: backend
status: active
date: 2026-05-08
rules: true
files:
  - 'src/trust/**/*.py'
---

## Context

Python's `typing.Any` defeats the purpose of type hints. When used without justification, it allows any type to pass through, eliminating static analysis benefits and IDE auto-completion. Type checkers like mypy and Pyright cannot catch errors when `Any` is used.

In 2026, the Python typing community consensus is:
- For arguments, prefer abstract types (`Mapping`, `Sequence`, `Iterable`)
- For return values, prefer concrete types (`list`, `dict`)
- If an argument accepts literally any value, use `object` instead of `Any`
- Reserve `Any` only for external system boundaries with explicit justification

## Decision

**All function signatures must use proper type hints. `Any` is allowed only at external system boundaries with explicit justification.**

| Case                                      | Type to use                                                |
| ----------------------------------------- | ---------------------------------------------------------- |
| Function accepts any mapping              | `Mapping[str, Any]` or `dict[str, Any]`                    |
| Function accepts any sequence             | `Sequence[T]` or `list[T]`                                 |
| Function truly accepts any value          | `object` (not `Any`)                                       |
| External API response (untyped JSON)      | `Any` with comment justifying boundary                     |
| boto3 / third-party SDK with no type stub | `Any` with comment referencing missing stub               |
| Gradual migration from untyped code       | `Any` with TODO comment and issue reference for fix target |

**Examples:**

**✅ Do this:**

```python
from collections.abc import Mapping, Sequence

def process_config(config: Mapping[str, object]) -> dict[str, str]:
    """Process configuration dictionary."""
    return {k: str(v) for k, v in config.items()}

def filter_items(items: Sequence[str], predicate: Callable[[str], bool]) -> list[str]:
    """Filter items by predicate."""
    return [item for item in items if predicate(item)]

# At external boundary (boto3 response has no type stub)
def get_s3_object(bucket: str, key: str) -> Any:  # boto3 GetObject response lacks type stub
    """Fetch S3 object. Returns boto3 response dict."""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response
```

**❌ Don't do this:**

```python
def process_config(config: Any) -> Any:  # Too loose — defeats type checking
    return {k: str(v) for k, v in config.items()}

def filter_items(items: Any, predicate: Any) -> Any:  # No type safety
    return [item for item in items if predicate(item)]
```

## Rationale

**Alternative: Allow `Any` freely for convenience**

This abandons type safety. The entire purpose of type hints is defeated. IDE auto-completion stops working, and type checkers cannot catch bugs.

**Alternative: Use `object` everywhere instead of `Any`**

This is too strict for external boundaries. When integrating with untyped third-party libraries (e.g., boto3 without stubs), `Any` is the pragmatic choice with proper documentation.

**Alternative: Use `dict` and `list` for all cases**

This is too specific. When accepting arguments, abstract types (`Mapping`, `Sequence`) allow callers to pass any compatible type, improving flexibility.

## Consequences

- **Positive**: Type errors are caught at analysis time (mypy / Pyright / Ruff)
- **Positive**: IDE auto-completion works correctly
- **Positive**: Refactoring is safer — type checkers detect breaking changes
- **Negative**: Developers must understand abstract vs. concrete types
- **Negative**: External integrations require explicit `Any` with justification comments

## Compliance

**Do:**

- Use `Mapping[K, V]` or `Sequence[T]` for function arguments
- Use `list[T]` or `dict[K, V]` for return values
- Use `object` when a function truly accepts any value
- Add a justifying comment when using `Any` at external boundaries
- Use Pydantic models for structured data (see ARCH-002)

**Don't:**

- Use `Any` for internal function signatures
- Use `Any` for arguments that could be `Mapping` or `Sequence`
- Use `Any` for return values that could be `list` or `dict`
- Leave `Any` without a comment explaining why it's necessary

**External boundary justification template:**

```python
def fetch_external_data(endpoint: str) -> Any:  # Third-party API returns unstructured JSON
    """Fetch data from external API."""
    ...
```

**Gradual migration template:**

```python
def legacy_function(data: Any) -> Any:  # TODO(issue-123): Add proper types during validation refactor
    """Legacy function pending type migration."""
    ...
```

## References

- [ARCH-002](./ARCH-002-pydantic-first-type-system.md) — Pydantic-First Type System
- [Python Typing Best Practices (2026)](https://typing.python.org/en/latest/reference/best_practices.html)
- [PEP 484 — Type Hints](https://peps.python.org/pep-0484/)
- [docs/CLAUDE.md](../AGENT.md) — "No bare `Any`" rule
