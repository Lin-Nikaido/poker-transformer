---
id: ARCH-004
title: Layered Testing Strategy
domain: testing
status: active
date: 2026-07-11
rules: true
files:
  - 'tests/**/*.py'
---

## Context

The project uses FastAPI, asynchronous Python code, and AWS integrations. Tests
must distinguish unit-level behavior from component integration while remaining
deterministic in CI.

## Decision

Tests must have a clear purpose and layer responsibility. Use the minimum set
of tests that protects observable behavior.

### Test Layers

| Test type | Location | Responsibility |
| --- | --- | --- |
| Unit | `tests/unittests/` | Verify one function, class, or adapter with in-process doubles |
| Integration | `tests/integration/` | Verify wiring between application components and HTTP boundaries |

Unit tests must not require real AWS resources, repository secrets, or external
network access. Use fakes, `botocore.stub.Stubber`, `moto`, or shared mockups.

Integration tests should exercise real component wiring. Collaborator
replacement rules are defined in [ARCH-011](./ARCH-011-test-implementation.md).

### Async Test Declaration

Every `async def test_*` function must have `@pytest.mark.asyncio` on the
function or its enclosing class. Without the marker, pytest may collect the
coroutine without executing its body.

```python
@pytest.mark.asyncio
async def test_get_user(client):
    ...
```

This requirement is enforced as an `error` by
`async-test-needs-asyncio-mark`.

## Rationale

Separating test responsibilities makes failures easier to diagnose and keeps
unit tests fast and reproducible. Explicit async markers prevent silent false
passes in pytest's strict asyncio mode.

## Compliance

**Do:**

- Give every test a behavior or regression purpose
- Keep unit tests independent of AWS credentials and external services
- Add `@pytest.mark.asyncio` to every asynchronous test
- Use integration tests for component wiring rather than replacing the wiring
- Keep implementation-level test rules in [ARCH-011](./ARCH-011-test-implementation.md)

**Don't:**

- Add tests solely to increase coverage metrics
- Make unit tests call real cloud services or external URLs
- Define asynchronous tests without the asyncio marker

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md)
- [ARCH-011](./ARCH-011-test-implementation.md)
