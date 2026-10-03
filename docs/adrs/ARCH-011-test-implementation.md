---
id: ARCH-011
title: Test Implementation Rules
domain: testing
status: active
date: 2026-09-20
rules: true
files:
  - 'tests/**/*.py'
---

## Context

Test implementation details can undermine the layer boundaries defined by
ARCH-004. In particular, replacing integration collaborators, creating
expensive fixtures repeatedly, or allowing real outbound HTTP calls makes the
test suite misleading or nondeterministic.

## Decision

Tests must preserve the distinction between integration and unit behavior.
Reusable abstract-class mocks belong in `tests/mockups/`; integration tests
must keep real component wiring; and unit tests must use in-process doubles for
external boundaries. Every API endpoint must have a corresponding test in
`tests/integration/`. In CI, where `ENV=CI` is injected, integration tests use
the `mock_infrastracture_injection_when_ci` fixture to replace external
infrastructure with in-memory doubles while preserving the application wiring.

### 1. Shared Mock Implementations

Classes implementing a `Base*` ABC must be defined in `tests/mockups/`, not in
individual test files. See [ARCH-003](./ARCH-003-mockups-as-mock-layer.md) for
the complete mock placement policy.

### 2. Integration Collaborators

Integration tests must not use `@patch` or `monkeypatch.setattr()` to replace
services, agents, stores, or I/O collaborators. FastAPI dependency overrides
and environment configuration through `monkeypatch.setenv()` or
`monkeypatch.setitem()` are allowed.

### 3. Fixture Scope

Fixtures that create expensive resources such as HTTP clients, database
tables, or indexes must use `module` or `session` scope when sharing the
resource is safe. Avoid recreating those resources for every test.

Asynchronous fixtures must use `@pytest_asyncio.fixture`, not
`@pytest.fixture`.

### 4. Unit Test Network Isolation

Unit tests must not make real outbound HTTPS calls. Use a fake client or mock
the HTTP client at the import binding. If a test genuinely requires a network
service, it belongs in the integration layer with an explicit environment
policy.

### 5. Private Attribute Patching

Before using `monkeypatch.setattr(obj, "_attribute", value)`, verify that the
attribute exists on the target object. When a collaborator is instantiated
inside a method, patch the class at its import binding instead of an instance
attribute that may not exist.

### 6. Application Use-Case Tests

Application use cases are responsible for orchestration and delegation. When a
use case delegates to a core function, its unit test should isolate the core
collaborator and verify only the application-layer contract:

1. The core collaborator is called once with the intended arguments.
2. The value returned by the core collaborator is returned unchanged by the
   use case.

Application tests should not duplicate core-layer domain behavior, such as
project construction, authorization rules, scene generation, or persistence
serialization. Those behaviors belong in core-layer tests. Persistence and
component wiring belong in integration tests when they need to be verified
together.

Patch the collaborator at the import binding used by the application module,
not necessarily at the collaborator's definition module. For example:

```python
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from application.foo import hoge_usecase


@pytest.mark.asyncio
async def test_hoge_usecase_delegates_to_core():
    expected_output = object()
    with patch(
        "application.foo.hoge_function",
        new=AsyncMock(return_value=expected_output),
    ) as mock_hoge_function:
        result = await hoge_usecase(
            key_1="val_1",
            key_2="val_2",
        )

    mock_hoge_function.assert_awaited_once_with(
        key_1="val_1",
        key_2="val_2",
    )
    assert result is expected_output
```

### 7. AWS Resource Cleanup

Integration tests outside CI may access real AWS resources. Tests that create
temporary AWS resources or data must clean them up reliably. Temporary AWS
resource names must use the `it_` prefix so that test-owned resources are
identifiable and safe to remove.

Each test module must inject the data required for its own responsibility and
remove it after the test completes. Use the `fixture + yield + cleanup`
pattern so cleanup runs even when assertions fail:

```python
@pytest_asyncio.fixture
async def integration_data(database):
    item = {
        "id": "it_example",
        "data": "mock_data"
    }
    await database.put_item(item)
    
    yield
    with suppress(Exception):
        await database.delete_item({"id": item["id"]})
```

Cleanup coverage for every temporary AWS resource and injected test datum is a
manual review requirement. It is intentionally not enforced by Archgate,
because the complete lifecycle cannot be reliably determined from static
source inspection.

## Automated Enforcement

The following implementation rules are active:

- `every-application-usecase-has-unit-test`
- `application-usecase-must-patch-core-collaborator`
- `application-usecase-must-propagate-mock-output`
- `every-api-endpoint-has-integration-test`
- `no-patch-in-integration-tests`
- `no-monkeypatch-setattr-component-in-integration`
- `async-fixture-must-use-pytest-asyncio-fixture`
- `mock-abc-class-must-be-in-mockups-dir`
- `expensive-fixture-must-not-use-function-scope`
- `unit-test-must-not-make-real-http-calls`
- `monkeypatch-setattr-underscore-attribute`

All listed rules use `error` severity and block the Archgate check when
violated.

## Compliance

**Do:**

- Put reusable `Base*` mock implementations in `tests/mockups/`
- Keep integration tests connected to real collaborators
- Use `@pytest_asyncio.fixture` for asynchronous fixtures
- Use `module` or `session` scope for expensive shared fixtures
- Mock outbound HTTP in unit tests
- In application use-case unit tests, isolate core collaborators and verify
  intended calls and unchanged return-value propagation
- Verify private attributes before patching them
- Prefix temporary AWS resource names with `it_`
- Inject module-owned test data and clean it up with `fixture + yield + cleanup`
- Manually verify that every temporary AWS resource and test datum is cleaned up

**Don't:**

- Patch services, agents, stores, or I/O in integration tests
- Define reusable `Base*` mock classes inside test files
- Recreate database tables, HTTP clients, or indexes per test unnecessarily
- Make unit tests call real external URLs
- Duplicate core-layer domain behavior in application use-case tests
- Assume a private attribute exists merely because it has an underscore prefix
- Leave temporary AWS resources or injected test data behind after integration tests

## References

- [ARCH-003](./ARCH-003-mockups-as-mock-layer.md)
- [ARCH-004](./ARCH-004-testing-strategy.md)
