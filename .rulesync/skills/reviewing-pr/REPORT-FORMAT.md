# Review Report Format

Output Markdown report in the following format:

```markdown
## Verdict

**[Approved / Approved with suggestions / Needs revision]**

---

## Critical Issues (confidence >= 95) -- must fix

### Issue #1: <Short description>

- **File**: `src/trust/path/to/file.py`
- **Line**: 42
- **Category**: Architecture
- **Description**: <issue description>
- **Evidence**: `<code snippet>`
- **Fix**: <concrete fix instruction>
- **Confidence**: 98%

### Issue #2: <Short description>

- **File**: `src/trust/path/to/file.py`
- **Line**: 88
- **Category**: Type Safety
- **Description**: <issue description>
- **Fix**: <concrete fix instruction>
- **Confidence**: 95%

## Important Issues (confidence 80-94) -- should fix

### Issue #3: <Short description>

- **File**: `src/trust/path/to/file.py`
- **Line**: 120
- **Category**: Async
- **Description**: <issue description>
- **Fix**: <concrete fix instruction>
- **Confidence**: 85%

## Architecture Violations

<specific findings, or "None found">

## Type Safety Issues

<specific findings, or "None found">

## Async / Performance Issues

<specific findings, or "None found">

## Security Findings

<specific findings, or "None found">

## Code Quality & Maintainability

<specific findings, or "None found">

## ADR Compliance

### Automated checks (`archgate check`)
- Exit code: 0 (pass) / 1 (violations)

### Manual review (rules: false ADRs)
- Checked N ADRs from docs/adrs/

### Violations
- <list, or "None found">

## Suggestions (confidence < 80, optional)

<optional before/after code blocks for simpler alternatives>

---

## Summary

<1-2 sentence overall assessment>
```

## Field Descriptions

In Critical/Important Issues sections, describe each issue in structured format:

- **File**: File path (used for GitHub API posting)
- **Line**: Line number (used for GitHub API posting)
- **Category**: Category (used for review comment title)
- **Description**: Detailed problem description
- **Evidence**: Code snippet (optional)
- **Fix**: Concrete fix instruction (used for suggestion generation)
- **Confidence**: Confidence score

## Usage

Report is returned in Markdown format and used by calling `/review` command to:

1. Post summary to GitHub PR comment
2. Post Critical/Important issues as individual review comments (including suggestions)
3. Classify issues not addressable via suggestions by category and create refactor PRs
