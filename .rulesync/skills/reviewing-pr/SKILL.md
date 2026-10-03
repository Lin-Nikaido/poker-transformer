---
name: reviewing-pr
description: >-
  Reviews PR diff against 7 categories (Architecture, Type Safety, Async, ADK,
  Security, Performance, Code Quality) and ADR compliance. Use this skill when
  analyzing code changes in a pull request to identify issues introduced by the
  current diff. Returns structured review report with confidence-scored issues
  (80+ threshold).
---
# Reviewing PR

Reviews PR diff and generates a structured report.

**What it does**: Analyzes PR diff for issues across 7 review categories plus ADR compliance, scoring each finding by confidence (80-94: Important, 95-100: Critical).

**When to use it**: When analyzing code changes in a pull request to identify issues introduced by the current diff.

**Input**: PR number, diff text, changed files list

**Output**: Structured review report (Markdown format)

---

## Instructions

Use this checklist to execute the review workflow:

- [ ] Step 0: Load coding standards
- [ ] Step 1: Load PR context
- [ ] Step 2: Apply 7-category review
- [ ] Step 3: ADR compliance check (archgate + manual)
- [ ] Step 4: Generate structured report

### Step 0: Load Coding Standards

Before starting the review, read the project's coding standards:

```bash
cat docs/CODING_RULES.md
```

This document contains critical coding conventions that supplement the automated checks:
- Comment minimalism (self-documenting code)
- Error handling patterns (fail fast, never swallow)
- Type system guidelines (Pydantic vs dict)
- Function signature conventions (keyword-only arguments)
- Code quality principles (no patches/workarounds)

Many of these rules are NOT fully enforceable by archgate static analysis and require human judgment during review.

### Step 1: Load PR Context

Check PR basic information:
- Changed layers (`apis/`, `application/`, `core/`, `infrastructure/`)
- Lines added/deleted
- New files vs existing file modifications

### Step 2: Apply reviewer subagent

Apply the 7-category review rules from [[CHECK-RULES.md]]:

1. Architecture Violations
2. Type Safety
3. Async Correctness
4. ADK Agent Pattern
5. Security
6. Performance
7. Code Quality & Maintainability

Score each finding by confidence (0-79: skip, 80-94: Important, 95-100: Critical).

**Important**: Only report issues introduced in this change. Do not report existing code issues.

### Step 3: Apply review-with-adrs skill

Run ADR compliance check:

```bash
archgate check
```

If exit code is `1`, report violations as **Critical Issue**.

For ADRs with `rules: false`, manual review:
- Read `## Compliance` section of each ADR in `docs/adrs/`
- For each **Don't** item: Search diff for prohibited patterns
- For each **Do** item: Check if diff follows required patterns

### Step 4: Generate Structured Review Report

Generate report following the format in [[REPORT-FORMAT.md]].

**Important**: In Critical/Important Issues sections, describe each issue in structured format:
- **File**: File path (used for GitHub API posting)
- **Line**: Line number (used for GitHub API posting)
- **Category**: Category (used for review comment title)
- **Description**: Detailed problem description
- **Evidence**: Code snippet (optional)
- **Fix**: Concrete fix instruction (used for suggestion generation)
- **Confidence**: Confidence score

---

## Output Format

Report is returned in Markdown format and used by calling `/review` command to:
1. Post summary to GitHub PR comment
2. Post Critical/Important issues as individual review comments (including suggestions)
3. Classify issues not addressable via suggestions by category and create refactor PRs

