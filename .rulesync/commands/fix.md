---
name: fix
description: "Fixes a bug in the TRUST backend from a GitHub Issue through a 6-phase workflow: bug analysis, root cause identification, clarification, solution design, plan (with user approval gate), minimal implementation, and quality review with draft PR creation."
targets: ["*"]
claudecode:
  skills:
    - fetching-github-issue
    - exploring-codebase
    - investigating-bugs
    - quality-gate
    - record-architectural-decision
    - review-with-adrs
  allowed-tools: Read, Write, Edit, Bash(gh issue view *), Bash(gh issue list *), Bash(gh pr create *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git status *), Bash(git log *), Bash(git diff *), Bash(uv run pytest *), Bash(uv run ruff *), Bash(archgate *), Bash(grep *), Bash(find *), Bash(ls *)
  disable-model-invocation: true
---

# Fix

Fixes a bug from a GitHub Issue through a structured workflow.

**Phases 1-4 are read-only. File changes begin only in Phase 5 after explicit user approval.**

## Usage

```
/fix <issue-number>
/fix <natural language description of the bug or unexpected behavior>
/fix --auto <issue-number>
```

## Autonomous mode (`--auto`)

If `$ARGUMENTS` contains the `--auto` flag, run **non-interactively** (used by
CI). Strip the flag before parsing the issue number, then:

- **Skip every user-approval gate** (Phases 1, 3, 4, 5). Do not stop to wait for
  confirmation at any "Do not proceed until the user ..." step.
- **Never call `AskUserQuestion`.** For each clarifying question, choose the most
  reasonable default and record it in the PR body under an `## Assumptions`
  section instead of asking.
- Still perform all read-only analysis (Phases 1-4) and the full quality gate
  (Phase 7) -- only the human gates are bypassed.
- Proceed straight through to branch creation and draft PR creation.
- **Stop instead of guessing when no safe default exists.** If a critical design
  decision has no defensible recommendation (mutually exclusive options with
  materially different outcomes), or if the root cause / requirements stay too
  ambiguous to produce a concrete Phase 5 implementation plan, do NOT write code
  or open a PR. Instead, post the blocking questions as a comment on the issue
  with `gh issue comment <number>` and end the command. Prefer asking over
  shipping a guess when the choice is consequential.

Without `--auto`, behave exactly as documented below, honoring every gate.

## Procedure

### Phase 1: Bug Analysis

**If `$ARGUMENTS` is an issue number**: Apply **fetching-github-issue** and present the structured summary.

**If `$ARGUMENTS` is a natural language description**: Synthesize the report into the same structured format:

```
## Bug Summary

- **Symptom**: <extracted from description>
- **Trigger**: <extracted -- what action or input causes it>
- **Expected behavior**: <extracted>

### Open Questions
- <ambiguities not resolved by the description>
```

Present the summary and confirm with the user before proceeding. _(Skipped in `--auto` mode.)_

Extract from the issue or description:

- **Symptom**: exact error message, exception class, or incorrect behavior
- **Trigger**: what action or input produces the failure
- **Expected behavior**: what should happen instead

**Infer the affected test scope** from the issue or description (do NOT run the full suite yet):

- Map mentioned module names, class names, or error keywords to their `tests/unittests/` counterparts.
  - e.g., issue mentions `AgentOrchestrator` -> scope is `tests/unittests/core/agents/`
  - e.g., error is `KeyError` in `infrastructure/` -> scope is `tests/unittests/infrastructure/`
- Record the inferred scope as `<BASELINE_SCOPE>`. If the scope cannot be inferred, mark it as `UNKNOWN` and defer to Phase 2.

If the request is a **new feature** (not a bug), stop and recommend:
> This appears to be a feature request. Use `/build` instead.

### Phase 2: Root Cause Investigation

Run **in parallel**:

1. Apply **exploring-codebase** focused on the modules mentioned in the error.
2. Search for the error in the codebase:
   ```bash
   grep -r "<ErrorClass or key phrase>" src/trust --include="*.py" -n
   ```

Then apply **investigating-bugs** using the issue summary and context report.

Present the root cause report: exact file, line, why it's wrong, call path, and downstream impact.

**Capture the targeted test baseline** once the affected module is confirmed:

```bash
uv run pytest <BASELINE_SCOPE> -v --tb=short 2>&1 | tail -30
```

Where `<BASELINE_SCOPE>` is the `tests/unittests/<affected-layer>/<affected-module>/` directory identified above. Save this output -- it will be compared against Phase 6 results.

> If `<BASELINE_SCOPE>` was `UNKNOWN` in Phase 1, resolve it now from the root cause report before running.

### Phase 3: Clarifying Questions

Compile all ambiguities into a single list and ask the user:

- Confirm the root cause is the expected bug (not a deeper issue)
- For fixes requiring interface changes: confirm acceptable scope
- Environment-specific behavior: does it reproduce everywhere or only in one environment?
- Is there an existing test that should have caught this? Should a regression test be added?

**Do not proceed to Phase 4 until all blocking questions are answered.** _(In `--auto` mode, do not ask: assume reasonable defaults and record them under `## Assumptions` in the PR body.)_

### Phase 4: Solution Design

Based on the investigation and clarifications:

**Primary fix**: the recommended minimal change (Option 1 from investigating-bugs).

**Fallback / workaround**: if a full fix is blocked (e.g., requires external service change), document Option 2.

**Test plan**:

| Test              | Command                                          | Expected Result |
| ----------------- | ------------------------------------------------ | --------------- |
| Regression test   | `uv run pytest tests/unittests/<path>/ -v`       | No failures     |
| Targeted fix test | `uv run pytest tests/unittests/<new-test>.py -v` | Passes          |
| Ruff clean        | `uv run ruff check src/trust/<file>.py`          | No issues       |

Unit tests in the plan must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets. If the bug can be reproduced only with a real cloud service, put that test under `tests/integration/` and add the appropriate marker (`real_aws`, and `ecs` for ECS dispatch).

Present the solution and test plan. Wait for user confirmation before proceeding. _(In `--auto` mode, select the primary fix and note the choice under `## Assumptions`.)_

### Phase 5: Implementation Plan

Produce the precise, minimal plan. Present it and require explicit user approval before writing any file.

**Exact Changes Required:**

| File                  | Location            | Before      | After     |
| --------------------- | ------------------- | ----------- | --------- |
| `src/trust/<path>.py` | `<function>:<line>` | `<current>` | `<fixed>` |

Show before/after snippet:

```python
# BEFORE
def broken_function(...):
    ...wrong logic...

# AFTER
def fixed_function(...):
    ...correct logic...
```

**Scope Confirmation:**

- Only the root cause is changed -- no unrelated refactoring
- Callers affected: <list or "none">
- New regression test required: yes/no

**Do not write any files until the user approves this plan.** _(Skipped in `--auto` mode: proceed directly to Phase 6.)_

### Phase 6: TDD Implementation

**Step 1 -- Write the regression test first (🔴 RED)**

Write a test that directly exercises the broken behavior and names the bug symptom:

```python
# tests/unittests/<same-path>/test_<module>.py
@pytest.mark.asyncio
async def test_<function>_<bug_symptom>():
    # currently FAILS -- will pass after the fix
    ...
```

Run it and confirm it **FAILS**:

```bash
uv run pytest tests/unittests/<path>/test_<module>.py::test_<name> -v
```

-> Must be 🔴 RED. If it is already GREEN: the test does not reproduce the bug -- rewrite it before continuing.

**Step 2 -- Apply the fix (🟢 GREEN)**

Make only the exact changes specified in the approved Phase 5 plan. No other modifications.

Run the regression test and confirm it **PASSES**:

```bash
uv run pytest tests/unittests/<path>/test_<module>.py::test_<name> -v
```

-> Must be 🟢 GREEN.

**Step 3 -- Refactor if needed**

Refactor the fix for clarity if the minimum change is hard to read. Run tests again to confirm GREEN is maintained.

**Step 4 -- Lint**

```bash
uv run ruff check src/trust/<changed-file>.py
```

Fix any issues before proceeding to Phase 7.

Do not rename, refactor, or clean up code outside the approved scope.

### Phase 7: Quality Review

Apply **quality-gate** for the affected module. All three steps below are **mandatory** -- do not skip any.

**Step 7a -- Format & Lint**

```bash
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
```

**Step 7b -- Targeted unit tests (affected module only)**

```bash
uv run pytest <BASELINE_SCOPE> -v
```

Compare against the Phase 2 baseline:

- The specific error must no longer appear
- No new failures introduced
- Pass count for the affected module must not decrease

Run the full suite **only if** the fix touches shared infrastructure (e.g., base classes, middleware, config) or the root cause report flagged cross-module impact:

```bash
uv run pytest tests/unittests/ -n auto --dist loadscope -m "not libreoffice" -v
```

**Step 7c -- ADR compliance (required)**

```bash
archgate check
```

Report every violation as a blocking issue. The quality gate is **not passed** until `archgate check` exits with no errors.

If any check fails:
1. Fix the issue
2. Re-run the failing check (and any subsequent checks)
3. Repeat until all three steps pass

**ADR compliance review**: Apply **review-with-adrs** to supplement the automated archgate results with a manual review of human-only ADR sections.

**Architectural decisions**: If the fix reveals an unwritten architectural rule, apply **record-architectural-decision** to capture it before creating the PR.

Once all checks pass, create a branch, commit changes, and draft PR:

```bash
git checkout -b fix/issue-<NUMBER>-<kebab-case-title>
git add <changed files>
git commit -m "fix: <what was wrong and what was corrected>"
```

Create a PR using the project's bugfix template:

```bash
# Create PR with the bugfix template
# The template will be auto-populated from .github/PULL_REQUEST_TEMPLATE/bugfix.md
gh pr create --draft --base dev \
  --title "fix: <issue title>"
```

**After PR creation**, guide the user to fill out the template:

- **Bug Description**: close #<ISSUE_NUMBER>
- **Root Cause**: <2-3 sentence technical explanation>
- **Fix Implementation**: <what was changed and why>
- **Testing Plan**: Commands and screenshots showing all tests pass

Report the PR URL to the user.

## Important Considerations

- **Read-only phases**: Phases 1-4 make zero file changes. Only Phase 5+ writes files.
- **Plan gate**: Phase 5 requires explicit user approval before implementation begins.
- **Baseline first**: Capture the targeted test baseline at the end of Phase 2, once the affected module is confirmed. Do not run the full suite.
- **Minimal diff**: Fix only the root cause. No cleanup, no refactoring outside scope.
- **Regression test**: Always add a test that would have caught the bug, unless one exists.
- **Feature redirect**: If the issue is a feature request, stop and recommend `/build`.
- **ADR gate**: Before creating the PR, always run `review-with-adrs`. If the fix reveals an unwritten architectural rule, record it with `record-architectural-decision`.
