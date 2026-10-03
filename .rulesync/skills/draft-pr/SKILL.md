---
name: draft-pr
description: >-
  Generate a pull request title and body in fenced Markdown so the user can copy-paste directly.
  Load when wrapping up an implementation or bug fix and the user needs a PR draft.
  Trigger: "PR", "pull request", "draft PR", "PR title", "PR body".
user-invocable: false
argument-hint: '[scope -- e.g. "main", "abc123..HEAD", "staged only", "2 weeks ago", "2026-04-01"]'
---

**Request**: $ARGUMENTS

# Draft PR Skill

After completing implementation or a bug fix, produce a PR title and body that the user can
copy-paste directly into GitHub. Output both inside a single fenced Markdown block.

**Core principle: reviewers need context before code.**
Lead with _Why_ (the problem), surface _Why not_ (alternatives rejected), enumerate _What_ changed,
and only then explain _How_ if the implementation is non-obvious.

> **IMPORTANT -- Draft only.**
> This skill produces text output only.
> Never run `git commit`, `git push`, or any `gh` command automatically.
> Always wait for explicit user instruction before executing any of these commands.

---

## Step 0 -- Determine the Scope of Changes

**Goal**: Resolve which commits and/or staged changes to include in the PR draft.

### 0-A: Parse `$ARGUMENTS`

| Argument example             | Resolved scope                                      |
| ---------------------------- | --------------------------------------------------- |
| _(empty)_                    | Default: `git log dev..HEAD` + staged changes       |
| `"main"`                     | `git log main..HEAD` (all commits not yet on main)  |
| `"dev"`                      | `git log dev..HEAD`                                 |
| `"abc1234"`                  | `git log abc1234..HEAD` (from that commit to HEAD)  |
| `"abc1234..HEAD"`            | Same -- explicit range syntax                        |
| `"abc1234..def5678"`         | `git log abc1234..def5678`                          |
| `"staged only"`              | Only `git diff --cached` (ignore committed changes) |
| `"2 weeks ago"`              | `git log --since="2 weeks ago"` on current branch   |
| `"2026-04-01"`               | `git log --since="2026-04-01"` on current branch    |
| `"2026-04-01 to 2026-04-30"` | `git log --since="2026-04-01" --until="2026-04-30"` |
| `"since yesterday"`          | `git log --since="yesterday"` on current branch     |

If the argument is empty or ambiguous, use the default scope (`dev..HEAD`) and inform the user.

### 0-B: Collect the Diff

Run the commands that match the resolved scope:

```bash
# Always check staged changes
git diff --cached --stat

# Commit-range scope (e.g. main..HEAD, abc123..HEAD)
git log <RANGE> --oneline
git diff <RANGE> --stat

# Date-based scope (e.g. --since="2 weeks ago" --until="2026-04-30")
git log --since="<START>" --until="<END>" --oneline
git diff $(git log --since="<START>" --until="<END>" --format="%H" | tail -1)..HEAD --stat
```

### 0-C: Confirm with the user

Report the resolved scope and summary of changes **in Japanese**, then ask for confirmation
before drafting.

> **⏸️ STOP -- Phase 0 complete.**
> Confirm the resolved scope with the user **in Japanese**.
> **Do NOT begin drafting until the user explicitly approves.**

---

## Output Format

Wrap **everything** (title line included) in one fenced code block so the user can copy it as-is:

````
```
feat: <25-char summary in English>

## Background

- <1-3 lines on the problem, risk, or requirement this PR addresses>
- <reference the incident, tech debt, or security concern that motivated the work>

## Alternatives Considered and Rejected <!-- omit for trivial changes -->

- **<rejected alternative>**: <why it was not adopted>
- **<another rejected alternative>**: <why it was not adopted>

## Changes

### <layer or package name>

- <filename>: <what changed>
- ...

### <layer or package name> (repeat as needed)
- ...

## Implementation Notes <!-- omit if obvious from the diff -->

- <implementation intent or algorithm choice that cannot be inferred from reading the code>

## Verification <!-- omit if obvious from the diff -->

- [ ] <verification item 1>
- [ ] <verification item 2>
```
````

---

## Rules

### Title line

- **English only**, imperative mood (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`)
- **50 characters or fewer** -- no trailing period
- Prefix guide:

  | Prefix      | When to use                              |
  | ----------- | ---------------------------------------- |
  | `feat:`     | New functionality visible to users       |
  | `fix:`      | Bug fix                                  |
  | `refactor:` | Code restructure with no behavior change |
  | `chore:`    | Tooling, deps, CI, config                |
  | `docs:`     | Documentation only                       |

### Why section

- Written in **English**
- 1-3 bullet points: the **problem, risk, or requirement** that triggered this change -- not the solution
- Ask: "What would have gone wrong if this PR were never made?" -- that answer belongs here
- Reference incidents, requirements, security risks, or technical debt that motivated the work
- ❌ Do not lead with the conclusion ("Due to X, we did Y")
- ❌ Do not describe the solution -- that belongs in What / How

### Why not section

- Written in **English**
- **Required** when the PR involves a design decision, architectural choice, or non-trivial trade-off
- **Omit entirely** for trivial changes (dependency bumps, typo fixes, config-only changes)
- List alternatives that were seriously considered and explain briefly why each was rejected
- Format: `**<alternative>**: <rejection reason>` -- one line per alternative
- Do not write "None" -- if you cannot think of a meaningful alternative, the section should be omitted
- Filling this section prevents the most common review comment: "why didn't you just...?" and
  preserves design context that would otherwise disappear once the PR is merged

### What section

- Written in **English**
- Group by layer or package -- use section headers (`###`):
  - `packages/<name>`
  - `apps/tenant -- infrastructure`
  - `apps/tenant -- presentation`
  - `Documentation`
- Each item: `- <filename>: <what changed>` -- one line per file or logical group

### How section -- optional

- Written in **English**
- **Include only** when the implementation is non-obvious from reading the diff:
  - Reason for choosing a specific algorithm or data structure
  - Design intent behind a type or abstraction
  - An unavoidable workaround and why it was necessary
- Omit entirely if the code speaks for itself -- do not pad with obvious statements
- ❌ Do not duplicate content already in What

### Verification section

- Written in **English**
- Checklist items tailored to the actual change (not boilerplate)
- Always include mock / real-API toggle check when HTTP behavior was touched

### What NOT to include

- Implementation details already obvious from the diff
- Filler phrases ("In this PR, we...", "As a result of this change...")
- Future work or TODOs unrelated to this PR

### Output format -- mandatory

- The PR title + body **must** be wrapped in a single fenced code block (` ``` ` ... ` ``` `).
- After the fenced block, add a **Sample Commands** section (see below) so the user can act immediately.
- Never output the PR draft as plain prose outside a fenced block.

---

## Sample Commands (always append after the draft block)

After the fenced PR draft block, always output the following section verbatim (fill in `<branch>`
and `<title>` with the actual values):

````
---

### Sample Commands

To use as a commit message (when the last commit is not yet pushed):

```bash
git commit -m "<title>"
```

To create a PR using GitHub CLI:

```bash
gh pr create \
  --base dev \
  --head <branch> \
  --title "<title>" \
  --body "$(cat <<'EOF'
<body -- paste the PR body here>
EOF
)"
```

> **Note**: The above commands are for reference only. Please verify before executing.
> This skill does not automatically execute `git` / `gh` commands.
````

---

## Rationale: Why this structure

| Section | Value to the reviewer                                                                  |
| ------- | -------------------------------------------------------------------------------------- |
| Why     | Establishes urgency and scope before a single line of code is reviewed                 |
| Why not | Shows alternatives were evaluated; prevents "why didn't you just..." review comments     |
| What    | Provides a guided tour of the diff without having to trace the entire change tree      |
| How     | Clarifies intent for non-obvious decisions only; omitted when the diff is self-evident |

The _Why not_ section carries outsized value: it preserves design context that would otherwise
disappear the moment the PR is merged, letting future contributors understand the reasoning behind
the code without re-opening the same debate. This mirrors the "alternatives considered" section
used in Amazon Design Docs, Chromium CLs, and major OSS projects like React.

---

## Example (security migration)

````
```
fix: migrate Cognito auth to USER_SRP_AUTH

## Background

- The `USER_PASSWORD_AUTH` flow was found vulnerable to MITM attacks as it sends passwords in plaintext to the server
- AWS best practices recommend the SRP flow, and our security audit flagged this for improvement

## Alternatives Considered and Rejected

- **`CUSTOM_AUTH` flow**: Requires additional Lambda trigger implementation, increasing infrastructure cost and low-priority work
- **Keep `USER_PASSWORD_AUTH` while adding other mitigations**: Rejected because the root cause remains. We need full migration

## Changes

### src/trust/auth -- infrastructure

- `auth.ts`: Changed auth flow to a 2-step process: `initiateAuth` / `respondToAuthChallenge`

## Verification

- [ ] Able to log in with correct credentials
- [ ] Appropriate error is displayed for incorrect password
```
````
