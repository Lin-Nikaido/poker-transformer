---
name: hotfix
description: "Fixes critical production bugs through a 7-phase workflow: bug analysis, root cause investigation, clarification, solution design, plan approval, minimal implementation, and quality review, ending at a draft PR into staging. The actual release is handled separately by the /release skill."
targets: ["*"]
claudecode:
  skills:
    - fetching-github-issue
    - exploring-codebase
    - investigating-bugs
    - quality-gate
    - record-architectural-decision
    - review-with-adrs
  allowed-tools: Read, Write, Edit, Bash(gh issue view *), Bash(gh issue list *), Bash(gh pr create *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git status *), Bash(git log *), Bash(git diff *), Bash(git checkout *), Bash(git push *), Bash(git branch *), Bash(uv run pytest *), Bash(uv run ruff *), Bash(archgate *), Bash(grep *), Bash(find *), Bash(ls *)
  disable-model-invocation: true
---

# Hotfix

Fixes critical production bugs through a structured workflow.

**Phases 1-4 are read-only. File changes begin only in Phase 5 after explicit user approval.**

## Usage

```
/hotfix <issue-number>
/hotfix <natural language description of the critical production issue>
/hotfix --auto <issue-number>
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
- Proceed straight through to creating the hotfix branch and a **draft PR into
  `staging`**. As always, the flow stops there: never merge, tag, push to
  shared branches, or delete branches -- the release is handled by `/release`.
- **Stop instead of guessing when no safe default exists.** If a critical design
  decision has no defensible recommendation (mutually exclusive options with
  materially different outcomes), or if the root cause / requirements stay too
  ambiguous to produce a concrete Phase 5 implementation plan, do NOT write code
  or open a PR. Instead, post the blocking questions as a comment on the issue
  with `gh issue comment <number>` and end the command. Prefer asking over
  shipping a guess when the choice is consequential.

Without `--auto`, behave exactly as documented below, honoring every gate.

## Prerequisites

- **Critical impact in production** (for non-critical bugs, use `/fix`)
- **Immediate action required** (cannot wait for next release cycle)
- Clear scope of impact

## Procedure

### Phase 1: Bug Analysis

**If `$ARGUMENTS` is an issue number**: Apply **fetching-github-issue** and present the structured summary.

**If `$ARGUMENTS` is a natural language description**: Synthesize the report into the same structured format:

```
## Bug Summary

- **Symptom**: <extracted from description>
- **Trigger**: <extracted -- what action or input causes it>
- **Expected behavior**: <extracted>
- **Production impact**: <scope and severity in production environment>

### Open Questions
- <ambiguities not resolved by the description>
```

Present the summary and confirm with the user before proceeding. _(Skipped in `--auto` mode.)_

Extract from the issue or description:

- **Symptom**: exact error message, exception class, or incorrect behavior
- **Trigger**: what action or input produces the failure
- **Expected behavior**: what should happen instead
- **Production impact**: scope and severity in production environment

Capture the current test baseline:

```bash
uv run pytest tests/unittests/ -v --tb=short 2>&1 | tail -20
```

Save this output -- it will be compared against Phase 7 results.

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

**Hotfix-specific additions**:

- **Production reproducibility**: how to reproduce in production environment
- **Workaround availability**: whether a temporary workaround exists

### Phase 3: Clarifying Questions

Compile all ambiguities into a single list and ask the user:

- Confirm the root cause is the expected bug (not a deeper issue)
- For fixes requiring interface changes: confirm acceptable scope
- Environment-specific behavior: does it reproduce everywhere or only in production?
- Is there an existing test that should have caught this? Should a regression test be added?
- **Rollback impact**: what happens if the fix fails and needs to be rolled back?
- **Monitoring**: which metrics should be monitored post-deployment?

**Do not proceed to Phase 4 until all blocking questions are answered.** _(In `--auto` mode, do not ask: assume reasonable defaults and record them under `## Assumptions` in the PR body.)_

### Phase 4: Solution Design

Based on the investigation and clarifications:

**Primary fix**: the recommended minimal change (Option 1 from investigating-bugs).

**Fallback / workaround**: if a full fix is blocked (e.g., requires external service change), document Option 2.

**Rollback plan**:

| Scenario                    | Action                                  | Expected Result |
| --------------------------- | --------------------------------------- | --------------- |
| Fix introduces new error    | `git revert <commit-sha>`               | Restore previous state |
| Partial failure             | <specific rollback steps>               | Mitigate impact |
| Database migration involved | <rollback migration script or command>  | Restore schema |

**Monitoring plan**:

- **Key metrics**: <specific metrics to watch post-deployment>
- **Alert thresholds**: <when to trigger alerts>
- **Monitoring duration**: <how long to actively monitor>

**Test plan**:

| Test              | Command                                          | Expected Result |
| ----------------- | ------------------------------------------------ | --------------- |
| Targeted smoke    | `uv run pytest tests/unittests/<path>/ -v -k smoke` | No failures |
| Regression test   | `uv run pytest tests/unittests/<new-test>.py -v` | Passes          |
| Core user journey | <manual or automated test>                       | Verified        |
| Ruff clean        | `uv run ruff check src/trust/<file>.py`          | No issues       |

Present the solution, rollback plan, monitoring plan, and test plan. Wait for user confirmation before proceeding. _(In `--auto` mode, select the primary fix and note the choice under `## Assumptions`.)_

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
- **Database changes**: yes/no - if yes, include migration script
- **API changes**: yes/no - if yes, confirm backward compatibility
- **Configuration changes**: yes/no - if yes, list environment variables or config files

**Branching Strategy:**

Ask the user to confirm the source branch for hotfix:

```
## Branching Confirmation

Hotfix branches typically originate from the production branch.

Please confirm:
- **Source branch**: [staging/main/master/other]
- **Hotfix branch name**: hotfix/issue-<NUMBER>-<kebab-case-title>
```

Wait for confirmation, then create the branch: _(In `--auto` mode, do not ask: default the source branch to `staging` and note it under `## Assumptions`.)_

```bash
git checkout <source-branch>
git pull origin <source-branch>
git checkout -b hotfix/issue-<NUMBER>-<kebab-case-title>
```

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

**Step 3 -- Targeted Testing**

Run the **hotfix test pack** (simplified, high-confidence tests):

```bash
# Core user journey tests for affected modules
uv run pytest tests/unittests/<affected-module>/ -v -k "smoke or critical"

# Backward compatibility check if API/DB changed
uv run pytest tests/unittests/<integration-tests>/ -v
```

**Step 4 -- Refactor if needed**

Refactor the fix for clarity if the minimum change is hard to read. Run tests again to confirm GREEN is maintained.

**Step 5 -- Lint**

```bash
uv run ruff check src/trust/<changed-file>.py
```

Fix any issues before proceeding to Quality Review.

Do not rename, refactor, or clean up code outside the approved scope.

### Phase 7: Quality Review & PR Creation

Apply **quality-gate** for the affected module (targeted for speed). All three steps below are **mandatory** -- do not skip any.

**Step 7a -- Format & Lint**

```bash
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
```

**Step 7b -- Targeted test suite**

```bash
uv run pytest tests/unittests/<affected-module>/ -v
```

Compare against the Phase 1 baseline:

- The specific error must no longer appear
- No new failures introduced in affected modules
- Core functionality verified

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

---

**Commit and create a draft PR into `staging`**

The hotfix flow ends at a **draft PR against `staging`**. The actual release
(merging, tagging, deploying, and back-merging to `dev`) is handled separately
by the **`/release` skill** -- do NOT merge, tag, or push to `staging`/`dev`,
and do NOT delete branches here.

Commit the changes:

```bash
git add <changed files>
git commit -m "$(cat <<'EOF'
fix: <what was wrong and what was corrected>

- Root cause: <1-sentence>
- Fix: <1-sentence>
- Tested: <test coverage>

Resolves #<ISSUE_NUMBER>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
git push -u origin hotfix/issue-<NUMBER>-<kebab-case-title>
```

Create a draft PR into `staging` using the project's PR template:

```bash
# The template is auto-populated from .github/PULL_REQUEST_TEMPLATE/
gh pr create --draft --base staging \
  --title "hotfix: <issue title>"
```

**After PR creation**, fill out the template with hotfix-specific information:

- **Root Cause**: <2-3 sentence technical explanation>
- **Fix Implementation**: <what was changed and why>
- **Rollback Plan**: <specific rollback steps if fix fails>
- **Monitoring**: Key metrics, alert thresholds, monitoring duration
- **Deployment Checklist**:
  - [ ] Staging deployment verified
  - [ ] Monitoring dashboard prepared
  - [ ] Rollback procedure documented
  - [ ] Stakeholders notified

Report the PR URL to the user.

Remind the user:
> **Important**: This hotfix stops at a draft PR into `staging`. Run the **`/release` skill** to perform the actual release (merge, tag, deploy, and back-merge to `dev`).

## Important Considerations

- **Stops at a draft PR into `staging`**: Do not merge, tag, push to shared branches, or delete branches. The actual release is handled by the **`/release` skill**.
- **Rollback plan**: Pre-prepared response for fix failure (mandatory)
- **Simplified testing**: High-confidence validation focused on impact scope, not full regression
- **Monitoring plan**: Post-deployment impact monitoring is critical
- **Stakeholder notification**: Do not forget to notify affected teams and users
- **Feature redirect**: If the issue is a feature request, stop and recommend `/build`.
- **ADR gate**: Before creating the PR, always run `review-with-adrs`. If the fix reveals an unwritten architectural rule, record it with `record-architectural-decision`.

## Differences from `/fix`

| Aspect | `/fix` | `/hotfix` |
|--------|--------|-----------|
| Use case | Bug fix during development | Emergency production fix |
| Source branch | `dev` | `staging` |
| PR target | `dev` | `staging` |
| Release | Normal release flow | Via **`/release` skill** |
| Test scope | Full regression | Targeted validation |
| Rollback plan | Optional | **Mandatory** |
| Monitoring plan | None | **Mandatory** |
| Approval gate | Phase 5 only | Phase 5 |
