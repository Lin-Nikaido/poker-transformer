---
name: exploring-codebase
description: Scans the TRUST project to understand the architecture, conventions, and existing patterns relevant to a planned change. Use before designing or implementing any feature or bug fix.
---

# Exploring Codebase

Builds a focused picture of the existing code relevant to a task.

**Input**: A topic, module path, or feature area (e.g., `"document loader"`, `"chat endpoint"`, `"agent tool"`).

## Instructions

### Step 1: Locate Relevant Files

```bash
grep -r "<topic>" src/trust --include="*.py" -l
find src/trust -type f -name "*.py" -path "*<topic>*"
```

Target the most affected layer:

| Change type | Start here |
|---|---|
| New endpoint | `src/trust/apis/` |
| Business logic | `src/trust/application/` or `src/trust/core/` |
| New agent or tool | `src/trust/core/agents/` |
| External client | `src/trust/infrastructure/` |

### Step 2: Read Key Files

For each found file, extract:

- **Public interface**: function signatures, class `__init__`, names exported in `__init__.py`
- **Layer dependencies**: what it imports from other layers
- **Registry participation**: is it registered by key? Where?

### Step 3: Identify Conventions

From the files above, derive:

- **Naming**: `snake_case` modules, `PascalCase` classes, `get_<name>_agent()` factory pattern
- **Async**: is the affected layer async?
- **Registry key**: what string is used for this component type?
- **Test location**: `tests/unittests/<same-path-as-src>/`

### Step 4: Output Context Report

```
## Codebase Context Report

### Relevant Files
| File | Purpose | Key Exports |
|---|---|---|
| <path> | <what it does> | <functions/classes> |

### Conventions to Follow
- Naming: <example>
- Async: <yes/no>
- Registry key: <if applicable>

### Constraints
- <anything that would break if changed naively>

### Test Coverage
- Existing test file: <path or "none found">
- Coverage of affected code: <present / absent / partial>
```
