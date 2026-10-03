---
name: fetching-github-issue
description: Fetches a GitHub Issue by number and produces a structured summary covering type, requirements, acceptance criteria, and open questions. Use before planning any feature or bug fix workflow.
---

# Fetching GitHub Issue

Retrieves a GitHub Issue and extracts the information needed for planning.

**Input**: Issue number (integer).

## Instructions

### Step 1: Fetch the Issue

```bash
gh issue view <NUMBER> --json number,title,body,labels,assignees,comments,state,url
```

For any linked issues found in the body (`#NNN`, `closes #NNN`):

```bash
gh issue view <LINKED_NUMBER> --json number,title,state
```

### Step 2: Classify Type

| Type | Signals |
|---|---|
| `feature` | Label `enhancement`/`feature`; body describes new capability |
| `bug` | Label `bug`; body describes unexpected behavior or error |
| `chore` | Label `chore`/`refactor`/`docs`; no new behavior |

If ambiguous, note it and defer to user confirmation.

### Step 3: Output Structured Summary

```
## Issue Summary

| Field | Value |
|---|---|
| Number | #<N> |
| Title | <title> |
| Type | feature / bug / chore |
| URL | <url> |

### Requirements
- <requirement from body or comments>

### Acceptance Criteria
- [ ] <criterion>

### Affected Areas
- <module path or feature area mentioned in the issue>

### Open Questions
- <ambiguity not resolved by the issue text>
```
