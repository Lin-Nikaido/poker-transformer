---
id: ARCH-003
title: tests/mockups/ as the Sole Source of Mock Implementations
domain: testing
status: active
date: 2026-07-11
rules: true
files:
  - 'tests/**/*.py'
---

## Context

Reusable mock implementations for core abstract interfaces should be shared
across tests. Defining the same implementation inside individual test files
causes duplication and makes interface changes harder to propagate.

## Decision

Mock classes that implement core `Base*` ABCs must be placed in
`tests/mockups/`. Test files should consume them through pytest fixtures rather
than defining those implementations inline.

```python
# tests/mockups/mock_database.py
class MockDatabase(BaseDatabase):
    async def get(self, key: str) -> dict[str, object]:
        return {"key": key}

@pytest.fixture
def mock_database() -> MockDatabase:
    return MockDatabase()
```

```python
# tests/unittests/test_service.py
def test_service(mock_database):
    ...
```

Private duck-typed stubs that do not inherit a `Base*` ABC may remain local to
a test file when they are genuinely file-scoped.

## Rationale

Centralizing ABC implementations keeps tests reusable and ensures that mock
implementations continue to satisfy the same interface as production code.

## Compliance

**Do:**

- Define reusable `Base*` mock classes in `tests/mockups/`
- Expose them through pytest fixtures
- Register shared mockup modules through the project test configuration

**Don't:**

- Define `Base*` mock implementations inline in test files
- Duplicate the same mock implementation across test modules

## Automated Enforcement

`no-base-mock-class-in-test-file` scans `tests/**/*.py`, excludes
`tests/mockups/` and `conftest.py`, and reports inline classes matching the
`class Xxx(BaseSomething):` pattern as an `error`.

## References

- [ARCH-011](./ARCH-011-test-implementation.md)
