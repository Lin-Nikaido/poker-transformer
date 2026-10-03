---
description: >-
  Reviews a GitHub PR through a 6-phase workflow: PR fetch, diff and test
  coverage analysis, open discussion analysis, review execution (7 categories +
  ADR), individual comment posting with suggestions, and refactor PR creation.
skills:
  - reviewing-pr
  - exploring-codebase
  - quality-gate
  - record-architectural-decision
  - review-with-adrs
allowed-tools: >-
  Read, Bash(gh pr *), Bash(git *), Bash(uv run ruff *), Bash(uv run pytest *),
  Bash(archgate *), Bash(grep *), Bash(find *), Bash(ls *)
disable-model-invocation: true
---
# Review

Reviews a GitHub PR and automatically posts the review as PR comments.
Creates individual discussion threads for each issue with inline suggestions.
If improvement suggestions are found, creates independent refactor PRs per review category.

**All phases run automatically without user approval gates.**

## Usage

```
/review <PR-NUMBER>
/review <PR-URL>

/review <PR-NUMBER> onlocal
/review <PR-URL> onlocal
```

### Modes

| Mode      | Behavior                                                                                              |
| --------- | ----------------------------------------------------------------------------------------------------- |
| Default   | Execute the full workflow including GitHub comment posting and refactor PR creation                   |
| `onlocal` | Execute the full analysis workflow but perform no GitHub write operations and no git write operations |

## Procedure

### Execution Mode

Parse command arguments.

If the final argument is `onlocal`:

```text
LOCAL_MODE=true
```

Otherwise:
```text
LOCAL_MODE=false
```

When LOCAL_MODE=true:

- Do NOT post PR comments 
- Do NOT post review comments 
- Do NOT reply to discussions
- Do NOT create branches
- Do NOT commit
- Do NOT push
- Do NOT create PRs

Generate all reports locally and save them under /tmp.


### Phase 1: PR Information Retrieval

**Step 1 -- Fetch PR metadata**

```bash
gh pr view <NUMBER> --json number,title,author,url,headRefName,baseRefName,additions,deletions,files
```

**Step 2 -- Fetch PR diff**

```bash
gh pr diff <NUMBER> > /tmp/pr-<NUMBER>.diff
```

**Step 3 -- Display changed files list**

Display PR basic information:

```
## PR #<NUMBER>: <Title>

- Author: <author>
- Base branch: <baseRefName>
- Head branch: <headRefName>
- Additions: +<N> / Deletions: -<N>
- Files changed: <N>

### Changed Files
- src/trust/<layer>/<file>.py (+N, -N)
...
```

---

### Phase 2: Diff Analysis & Impact Assessment

**Use a subagent for file analysis to preserve main context:**

Delegate file-heavy operations to a subagent to prevent context pollution. 
Use the Agent tool with a description like "Analyze PR diff and assess impact" to offload Steps 1-3.  

**Step 0 -- Exploration**
Apply **exploring-codebase**, focusing on the modules and feature areas mentioned in the PR.

**Step 1 -- Layer analysis**

Identify changed layers:

```bash
grep -E '^diff --git' /tmp/pr-<NUMBER>.diff | grep -o 'src/trust/[^/]*' | sort -u
```

Output example:
```
## Affected Layers
- apis/ -- <N> files
- application/ -- <N> files
- core/ -- <N> files
- infrastructure/ -- <N> files
```

**Step 2 -- Change classification**

```bash
grep -E '^diff --git' /tmp/pr-<NUMBER>.diff | wc -l  # Total files
grep -E '^\+\+\+ b/' /tmp/pr-<NUMBER>.diff | grep '/dev/null' | wc -l  # Deleted files
```

Report classification:
```
## Change Classification
- New files: <N>
- Modified files: <N>
- Deleted files: <N>
```

**Step 3 -- Change-to-test coverage check**

Do not use line coverage percentages as the primary signal. Instead, identify the
behaviors introduced or changed by the PR and verify that each behavior has
corresponding test evidence.

**3.1 -- List implemented or changed behaviors**

Read `/tmp/pr-<NUMBER>.diff` and create a behavior-level inventory. Group related
diff hunks into one item when they implement the same user-visible or domain
behavior.

Split inventory items by behavior, not by file. Even if multiple changes appear
in the same file, create separate rows when they affect different behaviors,
verification targets, or failure modes.

Include, when present:
- New or changed API endpoints, request/response schemas, validators, and status codes
- New or changed application use cases, orchestration paths, or background tasks
- New or changed core/domain logic, stores, agents, tools, preprocessors, and registries
- New or changed error handling, authorization, permission, retry, timeout, or fallback behavior
- New or changed data loading, parsing, persistence, or external-client behavior

Exclude pure documentation, formatting-only changes, and test-only refactors unless
they affect runtime behavior.


Output:

```markdown
| ID | Source diff | Changed behavior |
|---|---|---|
| <Number> | `src/trust/...:<symbol>` | <behavior summary> |
```


**3.2 -- Find matching test evidence**
For each behavior, determine the tests required to prove the behavior.

Include, when applicable:

- Success path
- Failure path
- Boundary conditions
- Error handling
- Permission / authorization outcomes
- Retry, timeout, and fallback behavior
- Regression scenarios affected by the change

Do not inspect existing tests yet.


Output:

```markdown
| ID | Source diff | Changed behavior | Required test scenarios |
|---|---|---|---|
| <Number> | `src/trust/...:<symbol>` | <behavior summary> | - <scenario1><\br>- <scenario2> |
```


**3.3 -- Verify test coverage**

For each behavior item, inspect both existing tests and tests changed in this PR.
Prefer unit tests for pure logic and application behavior; require integration or
API-level tests when the changed behavior is only meaningful across layers.
Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure,
Google APIs, or repository secrets. Real AWS coverage must be under
`tests/integration/` with `pytest.mark.real_aws`; ECS dispatch coverage must also
use `pytest.mark.ecs`.

Useful checks:
```bash
find tests/unittests -name "test_*.py" | grep -F "<affected-module>"
find tests/integration -name "test_*.py" | grep -F "<affected-feature>"
grep -n "test_" /tmp/pr-<NUMBER>.diff | grep "tests/"
```

Test evidence must assert the changed behavior or bug prevention directly. Do not
count tests that only import the module, exercise a smoke path, or assert the old
behavior without touching the changed branch.


**3.4 -- Report behavior coverage**


Output:

```markdown
## Test Coverage
| ID | Source diff | Changed behavior | Required test scenarios | Matching test | Status |
|---|---|---|---|---|---|
| <Number> | `src/trust/...:<symbol>` | <behavior summary> | - <scenario1><\br>- <scenario2> | `tests/...::<test_name>` or None | Covered / Missing |

```

Save the matrix also to:

```text
/tmp/test-coverage-<NUMBER>.md
```

Status definitions:
- **Covered**: A targeted test exists and asserts the new or changed behavior.
- **Partial**: Tests exist for nearby behavior, but a changed branch, edge case, or
  cross-layer contract is not asserted.
- **Missing**: No meaningful test evidence exists for the changed behavior.

Treat **Missing** and unjustified **Partial** statuses as review issues. Report them
as **Important** unless the gap creates a high-risk regression path, in which case
report as **Critical**. Accept no-test cases only when the PR clearly justifies why
the change is documentation-only, generated code, dead code removal, or otherwise
not practically testable.

**Diff size warning**:

If changes exceed 1000 lines:
> **WARNING**: Large PR detected (1000+ lines changed)
> Review may take longer. Consider splitting into smaller PRs.

---

### Phase 3: Open Discussion Analysis & Fix Verification

When LOCAL_MODE=true:

Skip all GitHub comment creation.

Instead, append verification results to:

```text
/tmp/review-discussion-results-<NUMBER>.md
```

**Use case**: Re-review after fixes have been applied following initial review

**CRITICAL**: This phase MUST process ALL unresolved review comments (top-level discussions), regardless of whether the author has already replied. Every `/review` execution must post fresh verification results.

**Step 1 -- Fetch unresolved discussions**

Fetch ALL top-level unresolved review comments (threads):

```bash
gh api repos/:owner/:repo/pulls/<NUMBER>/comments \
  --jq '.[] | select(.in_reply_to_id == null or .in_reply_to_id == 0) | select(.resolved != true) | {id, path, line, body, commit_id, user: .user.login}'
```

**IMPORTANT**: 
- Only target UNRESOLVED discussions (resolved discussions are excluded)
- Do NOT filter out discussions that already have author replies
- The presence of author replies does not exempt a discussion from verification
- `commit_id` field captures the commit SHA at which the comment was posted

If no unresolved review comments exist:
```
[INFO] No unresolved review comments found. Skipping Phase 3.
```

Skip to Phase 4.

---

**Step 2 -- Classify each unresolved discussion**

Analyze each unresolved comment body:

- **Discussion**: Questions about design choices, implementation approaches, trade-offs
- **Review Issue**: Code problems, improvement suggestions, fix requests

Classification criteria:
- "should", "must", "need", "problem", "bug", "fix" -> Review Issue
- "what about", "discuss", "option", "consider" -> Discussion

Report classification:
```
## Unresolved Discussion Classification
- Review Issues: <N>
- Discussions: <N>
```

---

**Step 3 -- Verify fix status for Review Issues**

**MANDATORY REQUIREMENT**: For EVERY discussion classified as Review Issue, you MUST post a NEW reply comment with verification results on EVERY `/review` execution. 

- Do NOT skip this step even if the author has already replied
- Do NOT skip this step even if you posted a verification before
- Each `/review` run should post fresh verification based on current code state

For each discussion classified as Review Issue:

**3.1 -- Fetch discussion metadata including commit_id**

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID> \
  --jq '{id, path, line, body, commit_id, user: .user.login}'
```

This returns the commit SHA at which the comment was made.

**3.2 -- Get the latest commit on the PR**

```bash
LATEST_COMMIT=$(gh pr view <NUMBER> --json headRefOid --jq .headRefOid)
```

**3.3 -- Check if the file was modified since the comment**

```bash
git fetch origin
git diff <comment_commit_id> ${LATEST_COMMIT} -- <file_path>
```

**Case 1: No diff (file unchanged)**
- The issue has NOT been addressed
- Proceed to post [NEEDS FIX] reply

**Case 2: Diff exists (file changed)**
- Read the diff output
- Check if the specific line mentioned in the comment was modified
- Analyze whether the change addresses the original issue
- Determine fix status (VERIFIED or NEEDS FIX)

**3.4 -- Read current code at the relevant line**

```bash
git show ${LATEST_COMMIT}:<file_path> | sed -n '<line>p'
```

Use this to understand current code state and validate fix appropriateness.

**3.5 -- Post verification reply (MANDATORY)**

You MUST post a reply to the discussion thread with one of the following statuses:

**If fixed:**

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[VERIFIED] **Fix confirmed**

Original issue: <summary of original issue>

Fix details:
- <explanation of what was changed between commit <comment_commit_id> and <LATEST_COMMIT>>
- \`<file>:<line>\`

Current code properly addresses this issue.

Generated with [Claude Code](https://claude.com/claude-code)"
```

**If not fixed (no changes):**

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[NEEDS FIX] **Not yet addressed**

Original issue: <summary of original issue>

Status:
- No changes detected in \`<file>\` since comment was posted (commit <comment_commit_id>)
- The issue remains unaddressed

\`\`\`suggestion
<fixed code>
\`\`\`

Recommended fix shown above.

Generated with [Claude Code](https://claude.com/claude-code)"
```

**If insufficient fix:**

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[NEEDS FIX] **Fix is insufficient**

Original issue: <summary of original issue>

Changes detected between commits:
- Comment posted at: <comment_commit_id>
- Latest commit: <LATEST_COMMIT>

Remaining problems:
- <explanation of what still needs fixing>

\`\`\`suggestion
<fixed code>
\`\`\`

Recommended fix shown above.

Generated with [Claude Code](https://claude.com/claude-code)"
```

If too complex for suggestion format:

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[NEEDS FIX] **Fix is insufficient**

Original issue: <summary of original issue>

Changes detected between commits:
- Comment posted at: <comment_commit_id>
- Latest commit: <LATEST_COMMIT>

Remaining problems:
- <explanation of what still needs fixing>

This issue requires structural changes. A Refactor PR will be created in Phase 6.

Generated with [Claude Code](https://claude.com/claude-code)"
```

**3.6 -- Track for Phase 6**

If the issue is not fixed or requires complex changes:
- Add to Phase 6 Refactor PR creation targets
- Include the discussion comment ID for later reference
- Record the commit range for context (<comment_commit_id> to <LATEST_COMMIT>)

---

**Step 4 -- Report results**

Report verification results:

```
## Review Issue Verification Results

Verified <N> Review Issues from open discussions:
- [VERIFIED] Comment #<ID>: <issue summary> - Fix confirmed
- [NEEDS FIX] Comment #<ID>: <issue summary> - Insufficient fix, reply posted
- [NEEDS FIX] Comment #<ID>: <issue summary> - Tracked for Phase 6 refactor PR

Discussions (no action):
- Comment #<ID>: <discussion summary>
```

For discussions classified as Discussion:
- Add to "Open Discussions" section in Phase 5 summary comment
- No automatic action (requires human judgment)

---

**After Phase 3 completes:**

Run compaction to clear Phase 3 API responses from context before starting the review:

```
/compact Focus on unresolved issues list and file paths only
```

This is a large workflow, so explicit compaction helps preserve main context for Phase 4-6.

---

### Phase 4: Review Execution

**Step 1 -- Load Coding Standards**

Before executing the review, load the project's coding standards:

```bash
cat docs/CODING_RULES.md
```

This document contains critical conventions that guide the review:
- Comment minimalism and self-documenting code
- Error handling patterns (fail fast, never swallow errors)
- Type system guidelines (Pydantic-first, no bare `dict`)
- Function signature conventions (keyword-only arguments)
- ASCII-only encoding policy
- Code quality principles (no patches/workarounds)

**Important**: Many of these rules require human judgment and are NOT fully covered by archgate static analysis. The reviewer must apply these standards when evaluating the PR.

---

**Step 2 -- Execute review**

Apply **reviewing-pr** skill with the following context:

- PR number: `<NUMBER>`
- PR diff: `/tmp/pr-<NUMBER>.diff`
- Changed files: `<list from Phase 1>`
- Affected layers: `<list from Phase 2>`
- Change-to-test coverage matrix: `<matrix from Phase 2 Step 3>`
- Coding standards: `docs/CODING_RULES.md` (loaded in Step 1)

**reviewing-pr** skill executes:
1. Load coding standards (Step 0)
2. 7-category review by reviewer subagent (Step 2)
   - **Review scope**: Review ALL changed files in the PR diff. Do not limit the review to "high-impact" or "critical" files. Large PRs (1000+ lines) should still receive comprehensive review across all changed files.
   - The reviewer subagent should read the entire PR diff and analyze every changed file (additions, modifications, deletions).
3. ADR compliance check via review-with-adrs (Step 3)
4. Include **Missing** and unjustified **Partial** test coverage rows as review
   findings under category `Testing`
5. Generate structured Markdown report (Step 4)


**quality gate check**: Apply **quality-gate** for the full suite.

**ADR compliance**: Apply **review-with-adrs** to check the implementation against active ADRs.

Save review report to `/tmp/review-report-<NUMBER>.md`.

---

### Phase 5: Comment Posting
If LOCAL_MODE=true:

- Do not execute any GitHub API write operation
- Do not create review comments
- Do not create summary comments


**Step 1 -- Create summary comment**

Extract summary from review report and format:

```markdown
# Code Review Report

**Reviewed by**: Claude Code (`/review` command)
**Timestamp**: <ISO 8601 datetime>
**PR**: #<NUMBER> (<title>)

---

## Verdict

**[Approved / Approved with suggestions / Needs revision]**

---

## Summary

- Critical Issues: <N>
- Important Issues: <N>
- Total Issues by Category:
  - Architecture: <N>
  - Type Safety: <N>
  - Async: <N>
  - ADK: <N>
  - Security: <N>
  - Performance: <N>
  - Code Quality: <N>
  - Testing: <N>

## Test Coverage

- Changed behaviors checked: <N>
- Covered: <N>
- Partial: <N>
- Missing: <N>

<Include the behavior-to-test matrix from Phase 2 Step 3, or a condensed version if the PR is large>

## ADR Compliance

- Automated checks: Pass / Fail
- Manual review: <N> ADRs checked
- Violations: <N> found

## Open Discussions (from Phase 3)

<List of discussions classified as "Discussion" in Phase 3>

- [Discussion #<ID>](<URL>): <summary>
- [Discussion #<ID>](<URL>): <summary>

[INFO] These require human judgment. No automatic action taken.

---

Generated with [Claude Code](https://claude.com/claude-code)
```

Save summary comment to `/tmp/review-summary-<NUMBER>.md`.

---

**Step 2 -- Post summary comment**

If LOCAL_MODE=true:
**SKIP** this step.

```bash
gh pr comment <NUMBER> --body "$(cat /tmp/review-summary-<NUMBER>.md)"
```

After successful posting, save comment URL:

```bash
SUMMARY_URL=$(gh pr view <NUMBER> --json comments --jq '.comments[-1].url')
```

```
[SUCCESS] Summary comment posted
   URL: <SUMMARY_URL>
```

---

**Step 3 -- Post individual issues as review comments**

For each Critical/Important issue:

**3.1 -- Extract file and line information**

From review report extract:
- File path: `src/trust/path/to/file.py`
- Line number: `42`
- Category: `Architecture`
- Issue description: `<issue description>`
- Fix suggestion: `<fix instruction>`

**3.2 -- Determine if suggestion format is applicable**

Use suggestion format if:
- Fix is limited to consecutive lines in one file
- Fix can be expressed as concrete code
- No major surrounding context changes needed

**3.3 -- Post with suggestion format**

If LOCAL_MODE=true:
Do **NOT** post comment. Add comment to `/tmp/review-summary-<NUMBER>.md`.


```bash
# Get current code at line
CURRENT_CODE=$(sed -n '<LINE>p' <FILE_PATH>)

# Post review comment
gh api repos/:owner/:repo/pulls/<NUMBER>/comments \
  --method POST \
  --field body="**[<Category>]** <Issue description>

\`\`\`suggestion
<fixed code>
\`\`\`

**Fix**: <Fix instruction>

**Confidence**: <XX>%

---
Generated with [Claude Code](https://claude.com/claude-code)" \
  --field path="<FILE_PATH>" \
  --field line=<LINE> \
  --field side="RIGHT"
```

**3.4 -- Post without suggestion format**

If suggestion format not applicable, post issue summary only:

If LOCAL_MODE=true:
Do **NOT** post comment. Add comment to `/tmp/review-summary-<NUMBER>.md`.


```bash
gh api repos/:owner/:repo/pulls/<NUMBER>/comments \
  --method POST \
  --field body="**[<Category>]** <Issue description>

**Problem**: <current problem explanation>

**Action**: This issue is complex and will be addressed in a separate Refactor PR in Phase 6.

**Confidence**: <XX>%

---
Generated with [Claude Code](https://claude.com/claude-code)" \
  --field path="<FILE_PATH>" \
  --field line=<LINE> \
  --field side="RIGHT"
```

Record issue ID and add to Phase 6 Refactor PR creation targets.

---

**Step 4 -- Report posting results**

```
[SUCCESS] Individual review comments posted

- Total comments: <N>
- With suggestions: <N>
- Requiring refactor PR: <N>
```

---

### Phase 6: Refactor PR Creation
If LOCAL_MODE=true:

Skip the entire Phase 6.

No branch creation.
No commit.
No push.
No PR creation.

**Prerequisites**: Execute only if there are issues that could not be posted with suggestion format in Phase 5, or Review Issues from Phase 3 that were determined to need fixes.

If no issues:
```
[SUCCESS] All issues addressed via inline suggestions. Skipping refactor PR creation.
```

---

**Step 1 -- Classify issues requiring refactor**

Extract and group by category (Category):
- Issues from Phase 4 review that could not be posted with suggestion format in Phase 5
- Review Issues from Phase 3 determined to need fixes

```
Refactor Suggestions by Category:
- Architecture: 2 issues (1 from new review, 1 from open discussion)
- Type Safety: 1 issue (from new review)
- Async: 3 issues (2 from new review, 1 from open discussion)
```

**Step 2 -- Create Refactor PR per category**

For each category, execute the following sequentially:

**2.1 -- Get current branch information**

```bash
ORIGINAL_BRANCH=$(gh pr view <NUMBER> --json headRefName --jq .headRefName)
BASE_BRANCH=$(gh pr view <NUMBER> --json baseRefName --jq .baseRefName)
```

**2.2 -- Create new branch from original branch**

```bash
CATEGORY_SLUG=$(echo "<Category>" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
REFACTOR_BRANCH="refactor/pr-<NUMBER>-${CATEGORY_SLUG}"

git fetch origin "${ORIGINAL_BRANCH}"
git checkout -b "${REFACTOR_BRANCH}" "origin/${ORIGINAL_BRANCH}"
```

**2.3 -- Apply fixes**

For each issue in this category:
- Apply fix described in review report **Fix** section
- Use `Edit` tool to modify files

**2.4 -- Commit changes**

```bash
git add <modified-files>
git commit -m "refactor(${CATEGORY_SLUG}): fix <category> issues from PR #<NUMBER>

Addresses the following issues:
- <file>:<line>: <issue summary>
- <file>:<line>: <issue summary>

Suggested in code review: <comment-url>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**2.5 -- Push & Create PR**

```bash
git push -u origin "${REFACTOR_BRANCH}"

gh pr create \
  --base "${ORIGINAL_BRANCH}" \
  --head "${REFACTOR_BRANCH}" \
  --title "refactor: Fix ${CATEGORY_SLUG} issues in PR #<NUMBER>" \
  --body "$(cat <<'EOF'
## Summary

This PR addresses **<Category>** issues identified in PR #<NUMBER> code review.

### Issues Fixed

- [ ] \`<file>:<line>\` - <issue description>
- [ ] \`<file>:<line>\` - <issue description>

### Review Context

Original review comment: <comment-url>

### Testing

- [ ] \`uv run ruff check <files>\` passes
- [ ] \`uv run pytest tests/unittests/<path>/ -v\` passes

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**2.6 -- Get new PR number**

```bash
NEW_PR_NUMBER=$(gh pr view "${REFACTOR_BRANCH}" --json number --jq .number)
```

**2.7 -- Update Phase 5 discussion with PR number**

For comments posted in Phase 5 Step 3.4 noting "Refactor PR will be created", add created PR number:

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[DONE] Refactor PR created: #${NEW_PR_NUMBER}

Fix proposal for this issue created in separate PR.

Generated with [Claude Code](https://claude.com/claude-code)"
```

**2.8 -- Update Phase 3 Open Discussion with PR number**

For discussions from Phase 3 determined to need fixes, also add created PR number:

```bash
gh api repos/:owner/:repo/pulls/comments/<COMMENT_ID>/replies \
  --method POST \
  --field body="[INFO] Created Refactor PR addressing this issue: #${NEW_PR_NUMBER}

Generated with [Claude Code](https://claude.com/claude-code)"
```

**2.9 -- Return to original branch**

```bash
git checkout "${BASE_BRANCH}"
```

**Step 3 -- Report created Refactor PRs**

```
[SUCCESS] Refactor PRs created:

- #<NEW_PR_1> - Architecture issues
  Branch: refactor/pr-<NUMBER>-architecture

- #<NEW_PR_2> - Type Safety issues
  Branch: refactor/pr-<NUMBER>-type-safety

- #<NEW_PR_3> - Async issues
  Branch: refactor/pr-<NUMBER>-async
```

---

## Important Considerations

- **Automatic execution**: All phases run automatically without approval gates
- **Confidence threshold**: Only report issues with confidence >= 80
- **Existing code excluded**: Only review issues introduced in this change
- **Large PR warning**: Show warning for changes exceeding 1000 lines
- **Individual issue posting**: Post Critical/Important issues as individual review comments
- **Suggestion priority**: Provide fix proposals in suggestion format whenever possible
- **Open Discussion analysis**: Analyze ALL UNRESOLVED review comments and verify fix status on EVERY execution
- **Re-review support**: Support re-review workflow after fixes following initial review
- **Always post verification**: Phase 3 MUST post verification replies to unresolved discussions even if author has already responded
- **Resolved discussions excluded**: Only unresolved discussions are verified; resolved discussions are skipped
- **Independent per category**: Each refactor PR managed on independent branch
- **Based on original branch**: Refactor PRs created from original PR branch (not `dev`)
- **Sequential creation**: Refactor PRs created sequentially not in parallel (avoid conflicts)
- **ADR compliance**: All fixes must comply with ADR
- **Output files**: All generated output must be written under `/tmp`.
- **onlocal Mode**: `onlocal` mode performs a dry-run review.
- **onlocal Mode**: `onlocal` mode must never modify GitHub state.
- **onlocal Mode**: `onlocal` mode must never modify git state.

---

## Error Handling

### PR does not exist

```
[ERROR] Error: PR #<NUMBER> not found
   Command: gh pr view <NUMBER>
```

### GitHub API rate limit

```
[ERROR] Error: GitHub API rate limit exceeded
   Retry after: <timestamp>
```

### Refactor PR creation failure

```
[WARNING] Warning: Failed to create refactor PR for <Category>
   Error: <error message>
   Continuing with remaining categories...
```

Individual failures shown as warnings, continue creating refactor PRs for other categories.
