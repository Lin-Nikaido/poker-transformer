---
name: record-architectural-decision
description: >-
  Record a new or updated Architecture Decision Record (ADR) in docs/adrs/.
  Load when an implementation or bug fix introduces a design decision, confirms
  an existing pattern, or reveals an unwritten architectural rule.
  Trigger: "ADR", "architectural decision", "design decision", "record decision",
  "update ADR", "new pattern", "architecture choice".
user-invocable: false
---

# Record Architectural Decision

Create or update an ADR in `docs/adrs/`. Each ADR consists of up to two files:

| File                            | Required         | Purpose                                              |
| ------------------------------- | ---------------- | ---------------------------------------------------- |
| `ARCH-NNN-kebab-title.md`       | Always           | Decision document (context / rationale / compliance) |
| `ARCH-NNN-kebab-title.rules.ts` | When automatable | Automated compliance checks run by Archgate          |

The `review-with-adrs` skill scans `docs/adrs/` dynamically at review time --
**no changes to that skill are needed** when you add a new ADR here.

---

## Step 1: Check Existing ADRs

List all files in `docs/adrs/` and decide which case applies:

```bash
ls docs/adrs/
```

| Outcome                                            | Next step                         |
| -------------------------------------------------- | --------------------------------- |
| An existing ADR already covers this decision fully | No action required -- reference it |
| An existing ADR needs updating                     | -> Step 5 (Update)                 |
| No ADR covers this decision                        | -> Step 2 (Create)                 |

---

## Step 2: Create the ADR Markdown File

### Determine the next ID

Inspect existing filenames (`ARCH-001-...`, `ARCH-002-...`, ...) and use `ARCH-(N+1)`.

**Alternative -- use the Archgate CLI if installed:**

```bash
archgate adr create --title "Your Title" --domain backend
```

This auto-assigns the next ID and creates the file in `.archgate/adrs/` (symlinked to `docs/adrs/`).
Try `archgate` first. If not found in PATH, fall back to `/usr/local/bin/archgate`.

### File naming

```
ARCH-NNN-kebab-case-title.md
```

Example: `ARCH-002-registry-pattern-for-pluggable-backends.md`

### ADR template

```markdown
---
id: ARCH-NNN
title: <Decision in plain English>
domain: backend # or: architecture / infrastructure / testing / agent
status: active  # active | deprecated | superseded
date: YYYY-MM-DD
rules: false    # set true only when adding a companion .rules.ts
files:          # glob patterns Archgate uses for automated checks (rules: true only)
  - 'src/trust/**/*.py'
---

## Context

(What problem or situation required this decision?)

## Decision

(What was decided? Include concrete before/after code examples.)

## Rationale

(Why this choice? What alternatives were considered and why were they rejected?)

**Alternative: <rejected option>**
<reason for rejection>

## Consequences

- **Positive**: <benefit>
- **Negative**: <trade-off or constraint>

## Compliance

**Do:**

- <required pattern>

**Don't:**

- <forbidden pattern>

## References

- [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- <link to related skill or ADR>
```

### Writing tips

- **Context**: Describe the _problem_, not the solution. Include what went wrong or what risk existed.
- **Decision**: Always include a code example. A before/after diff is ideal.
- **Rationale**: Show that alternatives were genuinely considered. Never write "N/A" -- if you can't think of an alternative, the decision is obvious enough that it may not need an ADR.
- **Compliance**: Make Do/Don't items concrete and unambiguous.

---

## Step 3: Create the `.rules.ts` File (when automatable)

### Should this ADR have a rules file?

Ask: **"Can a regex or glob catch the violation reliably?"**

| Scenario                                                     | Create `.rules.ts`?                              |
| ------------------------------------------------------------ | ------------------------------------------------ |
| Forbidden import (`from trust.infrastructure import ...`)    | **Yes** -- regex on import lines                  |
| Forbidden pattern in layer (`asyncio.run()` in async path)   | **Yes** -- regex on source lines                  |
| Forbidden directory exists (`core/repositories/`)            | **Yes** -- glob check                             |
| Code review judgment ("keep functions small")                | **No** -- subjective, document in Compliance only |
| Architectural pattern requiring context understanding        | **No** -- manual review only                      |

When you create a `.rules.ts`, set `rules: true` in the ADR frontmatter.
When you do NOT, leave `rules: false`.

### File naming

```
ARCH-NNN-kebab-case-title.rules.ts   <- same prefix as the .md file
```

### `.rules.ts` template

```typescript
/// <reference path="rules.d.ts" />

export default {
  rules: {
    'rule-id-in-kebab-case': {
      description: 'One-sentence description of what is forbidden and why.',
      severity: 'error', // "error" | "warning" | "info"
      check: async (ctx) => {
        for (const file of ctx.scopedFiles) {
          const matches = await ctx.grep(file, /your-pattern-here/)
          for (const match of matches) {
            ctx.report.violation({
              message: `Human-readable violation message -- what was found and why it's wrong`,
              file: match.file,
              line: match.line,
              fix: `Concrete one-line fix instruction`,
            })
          }
        }
      },
    },
  },
} satisfies RuleSet
```

### `RuleContext` API reference

```typescript
ctx.projectRoot          // string -- absolute path to repo root
ctx.scopedFiles          // string[] -- files matched by ADR's 'files:' globs
ctx.changedFiles         // string[] -- files changed in the current diff

ctx.glob(pattern)        // Promise<string[]> -- find files by glob
ctx.grep(file, /regex/)  // Promise<GrepMatch[]> -- search one file
ctx.grepFiles(/regex/, "glob") // Promise<GrepMatch[]> -- search multiple files

ctx.readFile(path)       // Promise<string> -- full file content
ctx.readJSON(path)       // Promise<unknown> -- parsed JSON

ctx.report.violation({ message, file?, line?, fix? }) // severity: error
ctx.report.warning({ message, file?, line?, fix? })   // severity: warning
ctx.report.info({ message, file?, line?, fix? })      // severity: info
```

`GrepMatch` fields: `file: string`, `line: number`, `column: number`, `content: string`

### Severity guidelines

| Severity    | When to use                                                                 |
| ----------- | --------------------------------------------------------------------------- |
| `"error"`   | Active decision -- violation must be fixed before merge                      |
| `"warning"` | Preferred pattern but exceptions exist (legacy code, migration in progress) |
| `"info"`    | Informational nudge -- no action required                                    |

### Common rule patterns

#### 1. Forbidden cross-layer import

```typescript
// Bad: core/ importing from infrastructure/
// src/trust/core/agents/some_agent/agent.py: from trust.infrastructure.database import ...

const matches = await ctx.grep(file, /from\s+trust\.infrastructure\b/)
ctx.report.violation({
  message: `core/ must not import from infrastructure/ -- depend on core abstractions only`,
  file: match.file,
  line: match.line,
  fix: `Inject the dependency via a registry or constructor parameter instead`,
})
```

#### 2. Forbidden synchronous I/O in async path

```typescript
// Bad: asyncio.run() inside an async function (blocks event loop)

const matches = await ctx.grep(file, /asyncio\.run\(/)
ctx.report.violation({
  message: `asyncio.run() inside an async context blocks the event loop`,
  file: match.file,
  line: match.line,
  fix: `Use 'await' directly; asyncio.run() is only valid as a top-level entrypoint`,
})
```

#### 3. Forbidden directory (glob-based)

```typescript
// Bad: src/trust/core/repositories/ exists (repositories belong in infrastructure/)

const files = await ctx.glob('src/trust/core/repositories/**')
for (const file of files) {
  ctx.report.violation({
    message: `Concrete repository implementations belong in infrastructure/, not core/`,
    file,
    fix: `Move to src/trust/infrastructure/ and expose via a core abstract base class`,
  })
}
```

#### 4. Missing tool registration (auto-discovery pattern)

```typescript
// Rule: tools must follow *_tool.py naming convention for auto-discovery by tool_registry

const toolFiles = await ctx.glob('src/trust/core/tools/**/*.py')
for (const file of toolFiles) {
  const basename = file.split('/').pop()
  if (basename !== '__init__.py' && 
      !basename.endsWith('_tool.py') && 
      !file.includes('/problems_handler/')) {
    ctx.report.warning({
      message: `Tool file should follow *_tool.py naming convention for auto-discovery`,
      file,
      fix: `Rename to *_tool.py so tool_registry can auto-discover it`,
    })
  }
}
```

#### 5. Legacy exception (warning for existing code, error for new)

```typescript
const isLegacyPath = match.file.includes('/legacy_module/')
const report = isLegacyPath ? ctx.report.warning : ctx.report.violation
report({
  message: `Direct boto3 call outside infrastructure/ layer`,
  file: match.file,
  line: match.line,
  fix: `Move AWS client calls to src/trust/infrastructure/external_clients/`,
})
```

---

## Step 4: Update Reference Documentation

After creating the ADR, update the following if the decision affects **where developers put code**.
Skip files where the addition would add no value (narrow or implementation-specific decisions).

### `docs/ARCHITECTURE.md`

This file is written in **Japanese**. All additions must be in Japanese.

- Add a row to the ADR table in the **Architecture Decision Records** section:
  ```markdown
  | [ARCH-NNN](adrs/ARCH-NNN-kebab-title.md) | One-line description in Japanese |
  ```
- If the ADR introduces a new **where to put code** rule, add or update the relevant section in Japanese.

### `.rulesync/rules/architecture.md`

Both files must be updated together -- `.rulesync/rules/architecture.md` is loaded into every agent's context.

- Add a row to the ADR table in **both** files:
  ```markdown
  | [ARCH-NNN](docs/adrs/ARCH-NNN-kebab-title.md) | One-line summary in English |
  ```
- If the ADR changes **where code goes**, update the layer description or patterns section.

### `.rulesync/subagents/` (when applicable)

Update subagent checklists when the ADR imposes a new **always-do** or **never-do** rule:

- **`architect.md`**: constraints list or design output sections
- **`reviewer.md`**: review checklist under the relevant category

Example addition to the Architecture Violations checklist in `reviewer.md`:

```markdown
- `core/` file importing from `infrastructure/` -- violates ARCH-NNN
```

---

## Step 5: Update an Existing ADR

1. Read the existing ADR file
2. Identify what changed:
   - `status` -> change to `deprecated` or `superseded`
   - `Compliance` -> add new Do/Don't items
   - `Consequences` -> update trade-offs
3. Apply the edit
4. Update `date` to today
5. If the decision is reversed: create a new ADR, then update the old ADR:
   ```yaml
   status: superseded
   superseded-by: ARCH-NNN
   ```
6. If adding automation to an existing ADR: create the `.rules.ts` and change `rules: false` -> `rules: true`

---

## Step 6: Verify

### ADR markdown

- [ ] File saved in `docs/adrs/` with the correct `ARCH-NNN-kebab-title.md` name
- [ ] All frontmatter fields filled: `id`, `title`, `domain`, `status`, `date`, `rules`
- [ ] `rules: true` if and only if a `.rules.ts` companion file was created
- [ ] All four required sections present: `## Context`, `## Decision`, `## Rationale`, `## Compliance`
- [ ] At least one code example in `## Decision`
- [ ] At least one alternative in `## Rationale`
- [ ] Concrete Do/Don't bullets in `## Compliance`

### `.rules.ts` (when `rules: true`)

- [ ] File saved as `ARCH-NNN-kebab-title.rules.ts` (same prefix as the `.md`)
- [ ] First line is `/// <reference path="rules.d.ts" />`
- [ ] Each rule has a kebab-case ID, `description`, `severity`, and `check`
- [ ] `check` is `async (ctx) => { ... }` -- always `async`
- [ ] Regex tested against real code -- not just the happy path, but also edge cases
- [ ] `fix` message is a concrete, copy-pasteable correction
- [ ] File ends with `} satisfies RuleSet`

The `review-with-adrs` skill will automatically detect this ADR and its rules on the next review run.
No manual update to `review-with-adrs/SKILL.md` is needed.
