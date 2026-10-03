---
name: build
description: "Implements a new feature for the TRUST backend from a GitHub Issue through a 6-phase workflow: requirements, exploration, clarification, design, plan (with user approval gate), TDD implementation, and quality review with draft PR creation."
targets: ["*"]
claudecode:
  skills:
    - fetching-github-issue
    - exploring-codebase
    - designing-feature
    - quality-gate
    - record-architectural-decision
    - review-with-adrs
  allowed-tools: Read, Write, Edit, Bash(gh issue view *), Bash(gh issue list *), Bash(gh pr create *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git status *), Bash(git log *), Bash(git diff *), Bash(uv run pytest *), Bash(uv run ruff *), Bash(archgate *), Bash(grep *), Bash(find *), Bash(ls *), Bash(mkdir *)
  disable-model-invocation: true
---

# Build

Implements a new feature from a GitHub Issue through a structured workflow.

**Phases 1-4 are read-only. File changes begin only in Phase 5 after explicit user approval.**

## Usage

```
/build <issue-number>
/build <natural language description of what to build>
/build --auto <issue-number>
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
  materially different outcomes), or if requirements stay too ambiguous to
  produce a concrete Phase 5 implementation plan, do NOT write code or open a
  PR. Instead, post the blocking questions as a comment on the issue with
  `gh issue comment <number>` and end the command. Prefer asking over shipping a
  guess when the choice is consequential.

Without `--auto`, behave exactly as documented below, honoring every gate.

## Procedure

### Phase 1: Requirements

**If `$ARGUMENTS` is an issue number**: Apply **fetching-github-issue** and present the structured summary.

**If `$ARGUMENTS` is a natural language description**: Synthesize the request into the same structured format:

```
## Issue Summary

| Field | Value                       |
| ----- | --------------------------- |
| Type  | feature                     |
| Title | <inferred from description> |

### Requirements
- <extracted from description>

### Acceptance Criteria
- [ ] <inferred criterion>

### Open Questions
- <ambiguities not resolved by the description>
```

Present the summary. If the request is a **bug fix** (not a new feature), stop and recommend:
> This appears to be a bug fix. Use `/fix` instead.

Do not proceed until the user confirms the issue type and summary. _(Skipped in `--auto` mode.)_

### Phase 2: Exploration

Run **in parallel**:

1. Apply **exploring-codebase**, focusing on the modules and feature areas mentioned in the issue.
2. If the issue involves agents: Read `src/trust/core/agents/agent_registry.py` (dynamic agent management) and check existing agent metadata in DynamoDB.
3. If the issue involves tools: Read `src/trust/core/tools/tool_registry.py` (auto-discovery mechanism) and scan `core/tools/*_tool.py` files.

Present all reports. Identify conflicts or constraints the design must respect.

### Phase 3: Clarifying Questions

Compile all ambiguities from Phases 1-2 into a single list and ask the user at once:

- Unresolved acceptance criteria
- Layer ownership decisions (which layer handles new logic?)
- Registry key for new components (if applicable)
- Database or migration requirements
- Any performance or backward-compatibility constraints

**Do not proceed to Phase 4 until all blocking questions are answered.** _(In `--auto` mode, do not ask: assume reasonable defaults and record them under `## Assumptions` in the PR body.)_

### Phase 4: Design

Apply **designing-feature** using the combined outputs from Phases 1-3.

Present at least **2 options** with pros/cons. Include the test strategy for each option.

**Do not proceed to Phase 5 until the user selects an option.** _(In `--auto` mode, select the recommended option and note the choice under `## Assumptions`.)_

### Phase 5: Implementation Plan

Produce the full plan. Present it and require explicit user approval before writing any file.

**Changes Required:**

| File                          | Change Type     | Description |
| ----------------------------- | --------------- | ----------- |
| `src/trust/<layer>/<file>.py` | Create / Modify | <purpose>   |

**New Component Skeleton** (no real logic yet -- plan only):

```python
# src/trust/<layer>/<file>.py
class NewComponent:
    async def method(self, ...) -> ...:
        ...
```

**Test Plan:**

| Test file                               | What to assert      |
| --------------------------------------- | ------------------- |
| `tests/unittests/<path>/test_<name>.py` | <expected behavior> |

**Risk Assessment:**

- Breaking change to existing interfaces: yes/no
- Database migration required: yes/no
- Affected callers: <list or "none">

**Do not write any files until the user approves this plan.** _(Skipped in `--auto` mode: proceed directly to Phase 6.)_

### Phase 6: TDD Implementation

Register the implementation steps as a TODO list with the `TodoWrite` tool before writing any code. Each component from the Phase 5 plan becomes one TODO item.

Implement in dependency order (dependencies before dependents):

1. Core types / interfaces (`core/`)
2. Infrastructure client or repository (if needed)
3. Core domain logic -- agent, tool, or domain service (`core/`)
4. Application use case (`application/`)
5. API endpoint and Pydantic schemas (`apis/`, if needed)
6. Registry registration (if applicable)

**For each component, follow the strict TDD cycle:**

```
a. Write the test cases for this component (derive from acceptance criteria)
b. Write ONE failing test
   -> uv run pytest tests/unittests/<path>/test_<name>.py -v  ->  🔴 RED
   If GREEN immediately: the test exercises nothing -- rewrite it before continuing
c. Write the minimum implementation to pass the test
   -> uv run pytest tests/unittests/<path>/test_<name>.py -v  ->  🟢 GREEN
d. Refactor if needed -> confirm still GREEN
e. Repeat (b-d) for each remaining test case
f. Run ruff on the changed file: uv run ruff check src/trust/<changed-file>.py
g. Mark the TODO item complete, then move to the next component
```

**Do not move to the next component until the current one is GREEN and ruff is clean.**

When adding agents, use **Dynamic Agent Registry (preferred)**:

- Create agent metadata via CMS API endpoint `/cms/createAgent` with instruction, description, and tool names
- Agent is stored in DynamoDB and instantiated at runtime via `AgentRegistry`
- No code deployment required for agent CRUD operations

For complex agents requiring static initialization, use **Static Agent Directory**:

- `core/agents/<name>/agent.py` -- `get_<name>_agent() -> Agent`
- `core/agents/<name>/prompts.py` -- `return_instruction()`, `return_description()`
- `core/agents/<name>/tools.py` -- tool callables (`async def` for any I/O)

### Phase 7: Quality Review

Apply **quality-gate** for the full suite. All three steps below are **mandatory** -- do not skip any.

**Step 7a -- Format & Lint**

```bash
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
```

**Step 7b -- Targeted unit tests (affected module first)**

```bash
uv run pytest tests/unittests/<affected-module>/ -v
```

If cross-module impact is suspected, also run:

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

**Architectural decisions**: If the implementation introduced a new design pattern not covered by any existing ADR, apply **record-architectural-decision** to capture it before creating the PR.

Once all checks pass, create a branch and draft PR:

```bash
git checkout -b feat/issue-<NUMBER>-<kebab-case-title>
git add <changed files>
git commit -m "feat: <concise description>"
gh pr create --draft --base dev \
  --title "feat: <issue title>" \
  --body "$(cat <<'EOF'
## Summary

Resolves #<ISSUE_NUMBER>

- <bullet: what was added>
- <bullet: which layer owns it>
- <bullet: registry key if applicable>

## Changes

| File                  | Change           |
| --------------------- | ---------------- |
| `src/trust/<path>.py` | Added / Modified |

## Test Plan

- [ ] `uv run pytest tests/unittests/<path>/ -v` passes
- [ ] Verify <acceptance criterion 1>
- [ ] Verify <acceptance criterion 2>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Report the PR URL to the user.

## Important Considerations

- **Read-only phases**: Phases 1-4 make zero file changes. Only Phase 5+ writes files.
- **Plan gate**: Phase 5 requires explicit user approval before implementation begins.
- **Parallel exploration**: Run codebase exploration and registry checks simultaneously in Phase 2.
- **Ask once**: Collect all clarifying questions in a single Phase 3 prompt.
- **Minimal diff**: Only add what the issue requires. Do not refactor adjacent code.
- **Bug redirect**: If the issue turns out to be a bug, stop and recommend `/fix`.
- **ADR gate**: Before creating the PR, always run `review-with-adrs`. If the design introduces a new pattern, record it with `record-architectural-decision`.
