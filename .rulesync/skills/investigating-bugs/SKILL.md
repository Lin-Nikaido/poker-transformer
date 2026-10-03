---
name: investigating-bugs
description: Locates the root cause of a bug in the TRUST backend, identifies the exact file and line, assesses downstream impact, and proposes a minimal fix. Use after exploring the codebase for a bug issue.
---

# Investigating Bugs

Produces a root cause analysis for a bug.

**Input**: Issue summary (from `fetching-github-issue`) + error message or stack trace + context report (from `exploring-codebase`).

## Instructions

### Step 1: Characterize the Failure

From the issue, identify:

- **Entry point**: which endpoint, CLI command, or background job triggered it
- **Symptom**: exact error message, exception class, or incorrect behavior
- **Reproducibility**: consistent or intermittent?

```bash
grep -r "<ErrorClass or key phrase>" src/trust --include="*.py" -n
```

### Step 2: Trace to Root Cause

Read the call path from entry point to failure site:

- The exact file + line where the incorrect behavior originates
- Why it is wrong (incorrect logic, wrong assumption, missing guard, type mismatch)
- Symptom vs. root cause -- don't fix a symptom

### Step 3: Assess Impact

```bash
grep -r "<broken function or class>" src/trust --include="*.py" -l
```

- Which other modules import or call the broken code?
- Does a fix require an interface change that breaks callers?
- Is there a test that should have caught this? (test gap)

### Step 4: Output Report

```
## Bug Report

### Root Cause
- **File**: `src/trust/<path>.py:<line>`
- **What's wrong**: <explanation>
- **Why it wasn't caught**: <test gap or environment difference>

### Call Path
<entry point> -> <module A> -> <module B> -> <broken line>

### Downstream Impact
- <module or caller that will be affected by a fix>

### Fix Options

#### Option 1 (Recommended): <name>
<minimal fix description>

#### Option 2 (Workaround): <name>
<defensive guard at caller, if full fix is blocked>
```
