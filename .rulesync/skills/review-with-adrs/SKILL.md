---
name: review-with-adrs
description: >-
  Check code changes against Architecture Decision Records using Archgate.
  Load during code review to run `archgate check` for automated rule enforcement,
  then supplement with manual review of human-only ADR Compliance sections.
  Reports violations as Critical Issues in the review report.
  Trigger: "review ADR", "ADR compliance", "architecture review", "check ADR".
user-invocable: false
---

# Review with ADRs

Enforce Architecture Decision Records against the current codebase using Archgate.

The primary mechanism is **`archgate check`**, which runs every ADR that has a companion
`.rules.ts` enforcement file. For ADRs without automated rules, supplement with a manual
Compliance section review.

---

## Step 1: Run Automated Checks

> **In CI (`GITHUB_ACTIONS=true`), skip this step.**
> Archgate runs in a dedicated `archgate` CI job. Proceed directly to Step 2.

```bash
archgate check
```

Try `archgate check` first. If not found in PATH, fall back to the absolute path below.

```bash
archgate check
```

**If neither works (not installed):**

```bash
npm install -g archgate
archgate check
```

**If `.archgate/` symlinks are not set up locally (rulesync.sh not yet run):**

```bash
mkdir -p .archgate
ln -sfn ../docs/adrs .archgate/adrs
ln -sfn ../docs/rules.d.ts .archgate/rules.d.ts
archgate check
```

Try `archgate` first. If not found in PATH, fall back to `/usr/local/bin/archgate`.
If neither works, read `docs/adrs/*.md` directly with the Read tool.

**Interpret the output:**

- Exit code `0` -> no automated violations found
- Exit code `1` -> violations reported with file path, line number, and which ADR was broken

Report each violation as a **Critical Issue** in the review report:

```markdown
## Critical Issues -- must fix

- [ADR ARCH-NNN] `src/trust/path/to/file.py:42`: <violation message from archgate check>
  ADR: [ARCH-NNN: Title](docs/adrs/ARCH-NNN-xxx.md)
  Fix: <concrete fix instruction>
```

---

## Step 2: Supplement with Manual ADR Review

`archgate check` only runs ADRs with `rules: true` and a companion `.rules.ts` file.
For ADRs where `rules: false`, perform a targeted manual review:

1. List all ADRs in `docs/adrs/`
2. For each ADR, read its `## Compliance` section
3. For each **Don't** bullet: search the diff for the forbidden pattern
4. For each **Do** bullet: check whether the diff follows the required pattern

Report findings in the review report:

- Explicit `Don't` pattern matched -> **Critical Issue**
- `Do` pattern not followed -> **Important Issue**
- Spirit violated but ambiguous -> **Suggestion**

---

## Step 3: Report ADR Coverage Gaps

If the diff introduces a pattern not covered by any existing ADR:

> Pattern `<description>` is not covered by any current ADR.
> If this is a significant design decision, load `record-architectural-decision`
> to capture it as a new ADR.

---

## Step 4: Fill the ADR Section of the Review Report

Use the appropriate template depending on context:

**Local review** (Step 1 was executed):

```markdown
## ADR Compliance

### Automated checks (`archgate check`)

- Exit code: 0 (pass) / 1 (violations -- see Critical Issues above)

### Manual review (rules: false ADRs)

- Checked N ADRs from docs/adrs/

### Violations

- (list, or "None found")

### Coverage gaps

- (list, or "None")
```

**CI review** (Step 1 was skipped):

```markdown
## ADR Compliance

### Automated checks (`archgate check`)

- Handled by the dedicated `archgate` CI job -- see CI results for violations.

### Manual review (rules: false ADRs)

- Checked N ADRs from docs/adrs/

### Violations

- (list, or "None found")

### Coverage gaps

- (list, or "None")
```
