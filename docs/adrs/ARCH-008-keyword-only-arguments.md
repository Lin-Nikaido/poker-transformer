---
id: ARCH-008
title: Keyword-Only Arguments (Explicit Function Calls)
domain: backend
status: active
date: 2026-05-08
rules: true
files:
  - 'src/trust/**/*.py'
---

## Context

Functions that allow both positional and keyword arguments create ambiguity and increase cognitive load. When refactoring, changing parameter order breaks code that uses positional arguments. Type checkers cannot catch these errors at analysis time.

In 2026, the Python community consensus (PEP 3102) recommends:
- Use keyword-only arguments for functions with 2+ parameters
- Force callers to use explicit parameter names
- Improve readability at the call site

## Decision

**Functions must clearly define whether arguments are positional or keyword-only. Prefer explicit keyword-only arguments for clarity.**

All functions with **2 or more parameters** should use the `*` separator to make parameters keyword-only, unless they are truly positional by nature (e.g., mathematical operations like `max(a, b)`).

### Examples

**✅ Do this (keyword-only parameters):**

```python
def some_function(
    agent_name: str,
    prompts: list[str],
    *,
    config: Config | None = None,
) -> int:
    """Process agent with prompts."""
    # impl

# When calling
result = some_function(
    agent_name="trust",
    prompts=["Hi", "hello"],
    config=my_config,
)
```

**✅ Do this (required keyword-only parameters):**

```python
def send_email(
    *,
    to: str,
    subject: str,
    body: str,
) -> None:
    """Send email with explicit parameters."""
    # impl

# When calling — parameter names are required
send_email(
    to="user@example.com",
    subject="Greeting",
    body="Hello!",
)
```

**❌ Don't do this (ambiguous positional/keyword mix):**

```python
def some_function(agent_name, prompts, config=None):
    # impl

# When calling — unclear what each argument means
result = some_function("trust", ["Hi", "hello"], my_config)
```

**❌ Don't do this (positional arguments are fragile):**

```python
# If parameter order changes, this breaks silently
send_email("user@example.com", "Greeting", "Hello!")
```

## Rationale

**Alternative: Allow positional arguments for brevity**

This sacrifices readability and safety. When reading code, positional arguments require consulting the function signature to understand what each value represents. Keyword arguments are self-documenting.

**Alternative: Use positional-only arguments (/ separator)**

Python 3.8+ supports positional-only parameters with `/`, but this is rarely needed except for built-in functions like `len(obj)` or `pow(x, y)`. For domain code, keyword-only is clearer.

**Alternative: No enforcement, rely on developer discipline**

Without enforcement, codebases drift. Some functions use positional, others use keyword-only, creating inconsistency.

## Consequences

- **Positive**: Function calls are self-documenting — no need to look up parameter order
- **Positive**: Refactoring is safer — changing parameter order doesn't break calls
- **Positive**: Type checkers catch mismatched arguments at analysis time
- **Negative**: Function calls are more verbose (must type parameter names)
- **Negative**: Developers must remember to add `*` separator

## Compliance

**Do:**

- Use `*` separator to make parameters keyword-only for functions with 2+ parameters
- Use required keyword-only parameters (no default value) when parameters are not optional
- Use descriptive parameter names (e.g., `user_principal` instead of `up`)
- Call functions with explicit keyword arguments

**Don't:**

- Define functions allowing both positional and keyword arguments (unless naturally positional, like `max(a, b)`)
- Call functions with positional arguments when keyword arguments are available
- Use single-letter parameter names (except for mathematical operations: `x`, `y`, `z`)

**Syntax for keyword-only parameters:**

```python
def function_name(
    required_param: str,           # Positional or keyword (OK for 1-parameter functions)
    *,                             # Everything after this is keyword-only
    keyword_only: int,             # Required keyword-only
    optional: str | None = None,   # Optional keyword-only
) -> ReturnType:
    ...
```

**When to allow positional arguments:**

- Single-parameter functions: `def process(data: str) -> str:`
- Mathematical operations: `def add(x: int, y: int) -> int:`
- Built-in replacements: `def len_utf8(s: str) -> int:`

## References

- [docs/CODING_RULES.md](../CODING_RULES.md) — Section "Avoid ambiguous arguments"
- [PEP 3102 — Keyword-Only Arguments](https://peps.python.org/pep-3102/)
- [Python Function Arguments Best Practices (2026)](https://thepythoncodingbook.com/2022/12/11/positional-only-and-keyword-only-arguments-in-python/)
