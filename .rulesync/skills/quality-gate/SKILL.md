---
name: quality-gate
description: Runs ruff (format + lint), pytest (unit + integration where available), and archgate for the affected module, reports results, and blocks PR creation if any check fails. Use after implementing any change.
---

# Running Quality Checks

Validates code quality before creating a PR.

> **All steps are MANDATORY. Do NOT skip any step -- especially `archgate check`.
> The quality gate is only passed when ALL steps report success.**

## Instructions

### Step 1: Format & Lint

```bash
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
```

Fix any issues:

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
```

### Step 2: Run Unit Tests

Targeted (default -- run this first):

```bash
uv run pytest tests/unittests/<module-path>/ -v
```

Full unit suite (run only if cross-module impact is suspected):

```bash
uv run pytest tests/unittests/ -n auto --dist loadscope -m "not libreoffice" -v
```

Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets. If a test needs those resources, it belongs in `tests/integration/` with explicit skip guards or markers.

### Step 3: Run Integration Tests (environment-dependent)

First, determine whether services are available by probing MySQL:

```bash
nc -z mysql 3306 2>/dev/null && echo "reachable via docker network" \
  || nc -z localhost 3306 2>/dev/null && echo "reachable on localhost" \
  || echo "services not reachable"
```

**If services are reachable** (devcontainer / LOCAL_CONTAINER, or host with compose running):

```bash
bash scripts/run-integration-tests.sh
```

The script auto-detects endpoints (Docker-network hostnames or localhost), overrides `ENV=CI`, starts Docker Compose if needed, and runs the LocalStack-backed profile. Pass extra pytest flags after `--`:

```bash
bash scripts/run-integration-tests.sh -k test_greeting -v
```

When `AWS_ENDPOINT_URL` points to LocalStack, `tests/integration/conftest.py` skips `real_aws` tests automatically. From a credentialed environment such as an EC2 bastion, the default integration command includes real AWS tests:

```bash
uv run pytest -q tests/integration/
uv run pytest -q -m "real_aws and ecs" tests/integration/task_runner/
```

**If services are NOT reachable** (ENV=LOCAL -- GitHub Codespaces, EC2 without compose):

Integration tests will be auto-skipped via `testing_utils.skip_local()`. Report this as "Skipped (services unavailable)" in the results -- this is not a blocking failure.

### Step 4: ADR Compliance (REQUIRED -- do not skip)

```bash
archgate check
```

This step is **not optional**. Run it every time. Report each violation as a blocking issue.

### Step 5: Report Results

```
## Quality Gate

### Ruff
- Format: ✅ / ❌ <issues>
- Lint:   ✅ / ❌ <issues>

### Unit Tests (pytest)
- Passed: <N>
- Failed: <N> -- <list failures>

### Integration Tests
- Status: ✅ Passed / ❌ Failed / ⚠️ Skipped (services unavailable)
- Passed: <N>
- Failed: <N> -- <list failures>

### Archgate
- Rules:  <N> passed / <N> failed
- Errors: <list rule violations>

### Verdict
✅ All checks passed -- ready for PR
❌ Blocking issues -- fix before creating PR
```

Do not create a PR if any check fails. Skipped integration tests (due to unavailable services) are not a blocker.
