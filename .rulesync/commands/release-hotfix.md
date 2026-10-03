---
name: release-hotfix
description: "Releases a hotfix through a 7-phase workflow: PR validation, staging merge confirmation, backend CI wait for main PR, frontend release note update, frontend CI wait, backmerge to dev, and final confirmation."
targets: ["*"]
claudecode:
  skills: []
  allowed-tools: Read, Write, Edit, Bash(gh pr *), Bash(gh repo *), Bash(gh workflow *), Bash(git *), Bash(grep *), Bash(find *), Bash(ls *), Bash(sleep *), Bash(cd *), AskUserQuestion
  disable-model-invocation: false
---

# Release Hotfix

Automates the hotfix release workflow across backend (trust-core) and frontend (trust-app) repositories.

**This is a multi-repository, multi-phase operation that requires user confirmation at key steps.**

## Usage

```
/release #808
/release 808
```

This skill is typically invoked from the main `/release` command when a PR number is provided.

## Prerequisites

- PR must exist and target `staging` branch
- Backend repository: `/workspaces/trust-core`
- Frontend repository: `/workspaces/trust-app`
- Both repositories must have clean working trees
- User must have write access to both repositories

## Procedure

### Phase 1: PR Validation

**Step 1.1**: Extract PR number from `$ARGUMENTS`

```bash
# Remove '#' prefix if present
PR_NUMBER=$(echo "$ARGUMENTS" | sed 's/^#//')
```

**Step 1.2**: Fetch PR information

```bash
cd /workspaces/trust-core
gh pr view "$PR_NUMBER" --json number,title,state,baseRefName,headRefName,merged,body
```

**Step 1.3**: Validate PR

Check the following:
- PR exists (command succeeds)
- `baseRefName` is `staging`
- Extract bug description from PR body if available

If validation fails, stop and show error:

> [ERROR] Error: PR #{PR_NUMBER} validation failed
> 
> - PR must exist
> - PR must target `staging` branch
> 
> Current PR base: {baseRefName}

**Step 1.4**: Present PR summary to user

```
## Hotfix Release Summary

**PR**: #{PR_NUMBER} - {TITLE}
**Branch**: {headRefName} to {baseRefName}
**Status**: {state} (merged: {merged})

{EXTRACTED_BUG_SUMMARY}

---

This will execute the following steps:
1. Confirm staging merge
2. Wait for backend CI to create staging to main PR
3. Update frontend release note
4. Wait for frontend CI to create staging to main PR
5. Create backmerge PRs (staging to dev) for both repos
6. Present all PRs for final review

Do you want to proceed with this hotfix release?
```

Wait for user confirmation before proceeding.

### Phase 2: Staging Merge Confirmation

**Step 2.1**: Check if PR is merged to staging

```bash
cd /workspaces/trust-core
MERGED=$(gh pr view "$PR_NUMBER" --json merged --jq '.merged')
```

**Step 2.2a**: If merged (`MERGED == true`)

Proceed to next phase.

**Step 2.2b**: If not merged (`MERGED == false`)

Stop and instruct user:

> [WARN] PR #{PR_NUMBER} is not merged to staging yet.
> 
> Please merge the PR first:
> ```
> gh pr merge {PR_NUMBER} --merge
> ```
> 
> After merging, re-run this command:
> ```
> /release #{PR_NUMBER}
> ```

Exit the workflow. User must merge and re-invoke.

### Phase 3: Backend CI Wait (staging to main PR)

**Step 3.1**: Wait for CI to create backend staging to main PR

The CI workflow `.github/workflows/pr_into_main.yaml` automatically creates a PR when something is merged to `staging`.

Poll for the PR with a timeout:

```bash
cd /workspaces/trust-core

echo "[WAIT] Waiting for backend CI to create staging to main PR..."

for i in {1..10}; do
  BACKEND_MAIN_PR=$(gh pr list --base main --head staging --json number --jq '.[0].number')
  
  if [ -n "$BACKEND_MAIN_PR" ]; then
    echo "[OK] Backend staging to main PR created: #$BACKEND_MAIN_PR"
    break
  fi
  
  echo "   Attempt $i/10 - waiting 30 seconds..."
  sleep 30
done

if [ -z "$BACKEND_MAIN_PR" ]; then
  echo "[ERROR] Timeout: Backend staging to main PR not created after 5 minutes"
  exit 1
fi
```

**Step 3.2**: On success, save the PR number and show to user

```
[OK] Backend: staging to main PR created
PR URL: https://github.com/tmc-ccoe/trust-core/pull/{BACKEND_MAIN_PR}

This PR will be merged later. First, we'll update the frontend release note.
```

**Step 3.3**: On timeout, stop and instruct user

> [ERROR] Backend CI did not create the staging to main PR within 5 minutes.
> 
> Please check:
> 1. GitHub Actions status: https://github.com/tmc-ccoe/trust-core/actions
> 2. Whether a staging to main PR already exists (manual creation)
> 3. CI workflow logs for errors
> 
> If the PR exists, note its number and continue manually.

### Phase 4: Frontend Release Note Update

**Step 4.1**: Calculate new version number

```bash
cd /workspaces/trust-app

# Get latest version from merged release PRs
LATEST_VERSION=$(gh pr list --base staging --state merged --limit 20 --json title \
  --jq '[.[] | .title | select(test("Release.*[0-9]+\\.[0-9]+\\.[0-9]+"))] | first |
        match("[0-9]+\\.[0-9]+\\.[0-9]+") | .string')

# Increment patch version
IFS='.' read -r MAJOR MINOR PATCH <<< "$LATEST_VERSION"
NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"

echo "Version: $LATEST_VERSION to $NEW_VERSION (patch increment)"
```

**Step 4.2**: Create release note branch

```bash
cd /workspaces/trust-app

git fetch origin
git checkout staging
git pull origin staging

BRANCH_NAME="doc/release-ver.$NEW_VERSION"
git checkout -b "$BRANCH_NAME"
```

**Step 4.3**: Extract bug information from backend PR

```bash
cd /workspaces/trust-core

# Get PR title and body
PR_TITLE=$(gh pr view "$PR_NUMBER" --json title --jq '.title')
PR_BODY=$(gh pr view "$PR_NUMBER" --json body --jq '.body')

# Try to extract structured information from PR body
# Look for sections like "Bug Description", "Root Cause", "Fix Implementation"
```

**Step 4.4**: Update release note file

Read the current release note and prepend new entry:

```bash
cd /workspaces/trust-app

RELEASE_NOTE_PATH="src/assets/releaseNote.md"
CURRENT_DATE=$(date +"%Y.%m.%d")

# Create new entry (template)
NEW_ENTRY="- $CURRENT_DATE Hotfix Ver.$NEW_VERSION - {Bug Title}
  - Bug fixes:
    - {Bug description from PR #$PR_NUMBER}
      - **Issue**: {Symptom}
      - **Fix**: {Fix description}
      - **Impact**: {Impact scope}
  - Technical details:
    - Backend PR: [tmc-ccoe/trust-core#$PR_NUMBER](https://github.com/tmc-ccoe/trust-core/pull/$PR_NUMBER)

"
```

Present the generated entry to the user for review and editing:

```
## Frontend Release Note Entry

The following entry will be added to `src/assets/releaseNote.md`:

---
{NEW_ENTRY}
---

Please review and edit if needed. The entry will be prepended to the existing release notes.
```

Wait for user confirmation or edit instruction.

**Step 4.5**: Apply the update

Use the Edit tool to prepend the new entry to the release note file, or Write if easier.

**Step 4.6**: Commit and push

```bash
cd /workspaces/trust-app

git add src/assets/releaseNote.md
git commit -m "docs: update release note for hotfix Ver.$NEW_VERSION

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin "$BRANCH_NAME"
```

**Step 4.7**: Create frontend release PR

```bash
cd /workspaces/trust-app

# Read the PR template
TEMPLATE_PATH=".github/PULL_REQUEST_TEMPLATE/release.md"

# Create PR body by filling in the template with hotfix info
# Feature: (empty)
# Fix: #{PR_NUMBER} {PR_TITLE}
# Others: (empty)

gh pr create \
  --base staging \
  --head "$BRANCH_NAME" \
  --title "Release Ver.$NEW_VERSION" \
  --body "$(cat <<EOF
# Release Ver.$NEW_VERSION

## Attention
Do NOT push any commit to \`main\` branch directory.
Please issue a pull request.

- [ ] Check ALL PR by [\`is:pr is:merged base:dev merged:>{lastMergedDate}\`](../pulls?q=is%3Apr+is%3Amerged+base%3Adev+merged%3A%3E{lastMergedDate})  
       See also: [LastMergedDate](../pulls?q=is%3Apr+is%3Amerged+base%3Astaging+base%3Amain)
- [ ] Write [Release note](/src/assets/releaseNote.md)

## Feature

## Fix
- [tmc-ccoe/trust-core#$PR_NUMBER]($BACKEND_PR_URL) $PR_TITLE

## Others

## Notes
Hotfix release for backend PR #$PR_NUMBER.

---
@toro
please code review!
EOF
)"

FRONTEND_STAGING_PR=$(gh pr view --json number --jq '.number')
```

**Step 4.8**: Request user to merge the frontend PR

```
[OK] Frontend: Release note update PR created
PR URL: https://github.com/tmc-ccoe/trust-app/pull/{FRONTEND_STAGING_PR}

Please review and merge this PR to staging.

Press Enter when the PR is merged to continue...
```

Wait for user input (cannot use AskUserQuestion for simple "press Enter", so instruct user to respond).

### Phase 5: Frontend CI Wait (staging to main PR)

**Step 5.1**: Wait for frontend CI to create staging to main PR

```bash
cd /workspaces/trust-app

echo "[WAIT] Waiting for frontend CI to create staging to main PR..."

for i in {1..10}; do
  FRONTEND_MAIN_PR=$(gh pr list --base main --head staging --json number --jq '.[0].number')
  
  if [ -n "$FRONTEND_MAIN_PR" ]; then
    echo "[OK] Frontend staging to main PR created: #$FRONTEND_MAIN_PR"
    break
  fi
  
  echo "   Attempt $i/10 - waiting 30 seconds..."
  sleep 30
done

if [ -z "$FRONTEND_MAIN_PR" ]; then
  echo "[ERROR] Timeout: Frontend staging to main PR not created after 5 minutes"
  exit 1
fi
```

**Step 5.2**: On success, save the PR number

```
[OK] Frontend: staging to main PR created
PR URL: https://github.com/tmc-ccoe/trust-app/pull/{FRONTEND_MAIN_PR}
```

### Phase 6: Backmerge PRs (staging to dev)

**Step 6.1**: Create backend backmerge PR (staging -> dev)

Directly create a PR from staging to dev without creating a new branch. Merge conflicts will be resolved on GitHub during the merge process.

```bash
cd /workspaces/trust-core

git checkout staging

gh pr create \
  --base dev \
  --head staging \
  --title "Backmerge: Hotfix #$PR_NUMBER staging to dev" \
  --body "$(cat <<EOF
# Backmerge

## Attention
Do NOT push any commit to \`main\` branch directory.
Please issue a pull request.

- [ ] Check ALL PR by [\`is:pr is:merged base:dev merged:>{lastMergedDate}\`](../pulls?q=is%3Apr+is%3Amerged+base%3Adev+merged%3A%3E2026-06-11)  
       See also: [LastMergedDate](../pulls?q=is%3Apr+is%3Amerged+base%3Astaging+base%3Amain)
- [ ] Write [Release note](https://github.com/tmc-ccoe/trust-app/blob/dev/src/assets/releaseNote.md)

## Feature

## Fix
- #$PR_NUMBER (hotfix backmerge from staging)

## Others

## Notes
Backmerge hotfix changes from staging to dev.

---
@toro
please code review!
EOF
)"
```

Save the PR number:
```bash
BACKEND_DEV_PR=$(gh pr view --json number --jq '.number')
```

**Step 6.2**: Create frontend backmerge PR (staging -> dev)

```bash
cd /workspaces/trust-app

git checkout staging

gh pr create \
  --base dev \
  --head staging \
  --title "Backmerge: Hotfix Ver.$NEW_VERSION staging to dev" \
  --body "$(cat <<EOF
# Backmerge

## Attention
Do NOT push any commit to \`main\` branch directory.
Please issue a pull request.

- [ ] Check ALL PR by [\`is:pr is:merged base:dev merged:>{lastMergedDate}\`](../pulls?q=is%3Apr+is%3Amerged+base%3Adev+merged%3A%3E2026-06-11)  
       See also: [LastMergedDate](../pulls?q=is%3Apr+is%3Amerged+base%3Astaging+base%3Amain)
- [ ] Write [Release note](/src/assets/releaseNote.md)

## Feature

## Fix
- Release note updated for Hotfix Ver.$NEW_VERSION

## Others

## Notes
Backmerge hotfix release note from staging to dev.

---
@toro
please code review!
EOF
)"
```

Save the PR number:
```bash
FRONTEND_DEV_PR=$(gh pr view --json number --jq '.number')
```

### Phase 7: Final Confirmation and Report

**Step 7.1**: Summarize all created PRs

Present the complete list to the user:

```
[SUCCESS] Hotfix release preparation completed successfully!

## Summary

**Hotfix**: PR #${PR_NUMBER} - ${PR_TITLE}
**Version**: ${NEW_VERSION}

## Pull Requests Created

### [DEPLOY] Main Branch (Production Release)

1. **Backend**: staging to main
   - PR: https://github.com/tmc-ccoe/trust-core/pull/${BACKEND_MAIN_PR}
   - Status: Ready for review

2. **Frontend**: staging to main
   - PR: https://github.com/tmc-ccoe/trust-app/pull/${FRONTEND_MAIN_PR}
   - Status: Ready for review

### [BACKMERGE] Dev Branch (Backmerge for Next Release)

3. **Backend**: staging to dev
   - PR: https://github.com/tmc-ccoe/trust-core/pull/${BACKEND_DEV_PR}
   - Status: Ready for review

4. **Frontend**: staging to dev
   - PR: https://github.com/tmc-ccoe/trust-app/pull/${FRONTEND_DEV_PR}
   - Status: Ready for review

## Next Steps

1. **Review and merge main PRs (#1, #2)** to deploy to production
2. **Verify production deployment** and monitor for issues
3. **Review and merge backmerge PRs (#3, #4)** to sync dev branch
4. Monitor production metrics and logs

[WARN] **Important**: Merge the main branch PRs first, then merge the dev backmerge PRs after production verification.
```

**Step 7.2**: Final notes

Remind the user of important considerations:

```
## Important Notes

- All PRs use the release template for consistency
- Backmerge ensures the hotfix is included in the next regular release
- If any PR merge is blocked by CI checks, resolve those issues before merging
- Production deployment should be monitored closely after merging main PRs
```

## Error Handling

### PR Not Found
```
[ERROR] Error: PR #{PR_NUMBER} not found

Please verify:
- PR number is correct
- You're in the correct repository (trust-core)
- You have access to view the PR
```

### PR Not Targeting Staging
```
[ERROR] Error: PR #{PR_NUMBER} does not target staging branch

Current base: {BASE_BRANCH}
Expected base: staging

Hotfix PRs must target the staging branch.
```

### CI Timeout
```
[ERROR] Error: CI workflow timed out

The automatic PR creation did not complete within 5 minutes.

Please check:
1. GitHub Actions: https://github.com/tmc-ccoe/{REPO}/actions
2. Workflow logs for errors
3. Whether the PR was already created manually

If needed, create the PR manually:
\`\`\`
gh pr create --base main --head staging --title "Auto: {ORIGINAL_TITLE} staging to main"
\`\`\`
```

### Merge Conflicts
```
[ERROR] Error: Merge conflicts detected during backmerge

Conflicted files:
{LIST}

Resolution steps:
1. Checkout the backmerge branch: \`git checkout {BRANCH}\`
2. Resolve conflicts in the listed files
3. Stage resolved files: \`git add <files>\`
4. Commit: \`git commit --no-edit\`
5. Push: \`git push origin {BRANCH}\`
6. Create PR: \`gh pr create --base dev --head {BRANCH} --title "..."\`
```

### Repository Not Found
```
[ERROR] Error: Frontend repository not found at /workspaces/trust-app

Please ensure both repositories are cloned:
- /workspaces/trust-core (backend)
- /workspaces/trust-app (frontend)
```

## Notes

- This workflow spans two repositories (trust-core, trust-app)
- CI automation is expected to create staging to main PRs automatically
- Backmerge prevents hotfix regression in future releases
- All git operations assume clean working trees
- User confirmation is required at key decision points
- Version increment is always PATCH for hotfixes
