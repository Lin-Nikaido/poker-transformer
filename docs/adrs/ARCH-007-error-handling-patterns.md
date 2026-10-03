---
id: ARCH-007
title: Error Handling Patterns (Fail Fast, Never Swallow)
domain: backend
status: active
date: 2026-05-08
rules: true
files:
  - 'src/poker/**/*.py'
  - 'tests/**/*.py'
---

## Context

Silently ignoring errors creates debugging nightmares. When exceptions are caught and suppressed without logging or re-raising, failures go unnoticed until they cause data corruption or incorrect behavior downstream.

In 2026, the Python community consensus is:
1. **Catch specific exceptions** — never catch bare `Exception` or `BaseException`
2. **Fail fast** — raise exceptions as soon as something goes wrong
3. **Raise low, catch high** — let lower-level functions raise, catch at the edges (CLI, web handler, event loop)
4. **EAFP style** — "Easier to Ask Forgiveness than Permission" (try/except over precondition checks)

## Decision

**Errors must not be silently ignored. If an unexpected error occurs, it is far better for the system to fail fast than to ignore the error silently.**

### Forbidden patterns:

```python
# ❌ NEVER do this
try:
    # do something
except Exception:  # Too broad
    pass  # Swallows all errors!

# ❌ NEVER do this
try:
    # do something
except:  # Bare except catches even KeyboardInterrupt!
    pass
```

### Required patterns:

**1. Catch only expected exceptions:**

```python
# ✅ Do this
try:
    value = int(user_input)
except ValueError as e:  # Specific exception only
    raise ValidationError(f"Invalid integer: {user_input}") from e
```

**2. For last-resort error boundaries (async tasks, background workers), log + alert:**

```python
# ✅ Do this (only at top-level error boundaries)
import logging
import traceback
from poker.exceptions.error_handler import send_error_alert

async def background_task(arg1: str, arg2: int) -> None:
    try:
        # do something risky
        await process_data(arg1, arg2)
    except Exception as e:
        # Log with full traceback
        logging.error(
            f"ERROR DETECTED! {traceback.format_exception_only(type(e), e)}\n"
            f"function: background_task\n"
            f"traceback:\n{traceback.format_exc()}",
        )
        # Send alert to developers
        await send_error_alert(func=background_task, e=e, kwargs={"arg1": arg1, "arg2": arg2})
        # DO NOT re-raise — this is a top-level boundary
```

**Key distinction:** This pattern is **only** allowed at top-level error boundaries (async task entry points, background workers, scheduled jobs). **Never** use this pattern in library functions or request handlers.

## Rationale

**Alternative: Catch `Exception` everywhere for safety**

This hides bugs. When errors are caught and logged but not re-raised, the caller assumes success. Silent failures are worse than loud crashes.

**Alternative: Use bare `except:` for compatibility**

Bare `except:` catches `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, which should never be caught. Python 3.11+ provides `ExceptionGroup` for better control.

**Alternative: Never catch `Exception` even at boundaries**

Too strict for production systems. Background tasks and async workers need last-resort error handling to prevent one failure from crashing the entire service. The key is to **log + alert**, not silently swallow.

## Consequences

- **Positive**: Bugs are caught immediately instead of propagating silently
- **Positive**: Developers are alerted to unexpected errors via logging + alerting
- **Positive**: Stack traces are preserved with full context
- **Negative**: Developers must identify specific exceptions to catch
- **Negative**: Top-level error boundaries require explicit logging + alerting setup

## Compliance

**Do:**

- Catch specific exceptions only (e.g., `ValueError`, `KeyError`, `FileNotFoundError`)
- Re-raise exceptions with `raise` or `raise ... from e` to preserve context
- Use `try/except` at error boundaries (top-level async tasks, CLI entry points) with logging + alerting
- Log errors with `traceback.format_exc()` for full stack traces
- Send alerts to developers using `send_error_alert()` at error boundaries

**Don't:**

- Catch bare `Exception` in library functions or request handlers
- Use bare `except:` (catches `KeyboardInterrupt` and `SystemExit`)
- Suppress errors with `pass` or `continue` without logging
- Catch `Exception` without logging or re-raising

**Allowed at error boundaries only:**

```python
# Top-level async task (OK)
async def scheduled_job() -> None:
    try:
        await process_batch()
    except Exception as e:
        logging.error(f"Scheduled job failed: {e}", exc_info=True)
        await send_error_alert(func=scheduled_job, e=e, kwargs={})
```

**Forbidden in library functions:**

```python
# ❌ Library function (NOT OK)
def process_user_data(user_id: str) -> dict:
    try:
        data = fetch_data(user_id)
        return transform(data)
    except Exception:  # WRONG! Caller assumes success even when it failed
        return {}
```

## References

- [docs/CODING_RULES.md](../CODING_RULES.md) — Section "Do not swallow errors"
- [The Ultimate Guide to Error Handling in Python (2026)](https://blog.miguelgrinberg.com/post/the-ultimate-guide-to-error-handling-in-python)
- [Python Exception Handling Best Practices (Real Python)](https://realpython.com/ref/best-practices/exception-handling/)
- [PEP 3134 — Exception Chaining](https://peps.python.org/pep-3134/)
