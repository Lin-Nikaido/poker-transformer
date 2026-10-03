---
name: release-update
description: "Creates a release PR from dev to staging through a 5-phase workflow: version bump calculation, PR collection since last release, release note generation, PR creation, and verification."
targets: ["*"]
claudecode:
  skills: []
  allowed-tools: Read, Write, Edit, Bash(gh pr list *), Bash(gh pr view *), Bash(gh repo view *), Bash(git *), Bash(grep *), Bash(find *), Bash(ls *)
  disable-model-invocation: false
---

# Release Update

Creates a release PR from `dev` branch to `staging` branch with semantic versioning.

**Phases 1-3 are read-only. PR creation happens in Phase 4 after user approval.**

## Usage

```
/release dev major
/release dev minor
/release dev patch
```

This skill is typically invoked from the main `/release` command with `dev` argument.

## Prerequisites

- Current branch must be `dev`
- Working tree must be clean (no uncommitted changes)
- All changes must be already merged to `dev`
- `$ARGUMENTS` must contain one of: `major`, `minor`, `patch`

## Procedure

### Phase 1: Version Calculation

**Step 1.1**: Verify current branch

```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "dev" ]; then
  echo "ERROR: Must be on dev branch. Current branch: $CURRENT_BRANCH"
  exit 1
fi
```

If not on `dev`, stop and instruct the user:

> You must be on the `dev` branch. Run `git checkout dev` and try again.

**Step 1.2**: Check working tree status

```bash
git status --porcelain
```

If there are uncommitted changes, stop and instruct the user:

> Working tree has uncommitted changes. Commit or stash them before creating a release.

**Step 1.3**: Get the latest version from past release PR titles

```bash
LATEST_VERSION=$(gh pr list --base staging --state merged --limit 20 --json title \
  --jq '[.[] | .title | select(test("Release.*[0-9]+\\.[0-9]+\\.[0-9]+"))] | first |
        match("[0-9]+\\.[0-9]+\\.[0-9]+") | .string')
```

If no release PRs exist, set `LATEST_VERSION="0.0.0"`.

Expected PR title formats:

- `Release Ver.1.2.0`
- `Release Ver 1.2.0`
- `Release 1.2.0`

**Step 1.4**: Calculate new version based on `$ARGUMENTS`

Parse `$ARGUMENTS` to determine bump type:

- If `$ARGUMENTS` contains `major`: increment major version (e.g., 1.2.0 -> 2.0.0)
- If `$ARGUMENTS` contains `minor`: increment minor version (e.g., 1.2.0 -> 1.3.0)
- If `$ARGUMENTS` contains `patch`: increment patch version (e.g., 1.2.0 -> 1.2.1)

If `$ARGUMENTS` is empty or invalid, stop and ask:

> Specify the version bump type: `major`, `minor`, or `patch`.

Example calculation:

```bash
# For LATEST_VERSION="1.2.0" and bump type "minor"
# Parse: MAJOR=1, MINOR=2, PATCH=0
# Increment MINOR: NEW_VERSION="1.3.0"
```

Present the version bump:

```
## Version Bump

Current version: {LATEST_VERSION} (from last release PR)
New version: {NEW_VERSION}
Bump type: {major|minor|patch}
```

**Do not proceed until the user confirms the version.**

### Phase 2: Collect Merged PRs Since Last Release

**Step 2.1**: Get the merge date of the last release PR to `staging`

```bash
LAST_RELEASE_DATE=$(gh pr list --base staging --state merged --limit 1 --json mergedAt --jq '.[0].mergedAt')
```

If no previous release exists, use a safe default date (e.g., `2025-01-01T00:00:00Z`).

**Step 2.2**: List all PRs merged to `dev` after that date

```bash
gh pr list --base dev --state merged --limit 100 --json number,title,mergedAt,labels \
  --jq "map(select(.mergedAt > \"$LAST_RELEASE_DATE\")) | .[] | \"#\(.number) \(.title) [\(.labels | map(.name) | join(\", \"))]\"" \
  | sort -t'#' -k2 -n
```

**Step 2.3**: Categorize PRs

Group PRs by their labels or title prefixes:

- **Feature** (new features): PRs with `feat:` or `feat/` prefix or `enhancement` label
- **Fix** (bug fixes): PRs with `fix:` or `fix/` or `hotfix/` prefix or `bug` label
- **Others** (other changes): All remaining PRs

Present the categorized list:

```
## Merged PRs Since Last Release ({LAST_RELEASE_DATE})

### Feature
- #XXX <title>
- #YYY <title>

### Fix
- #AAA <title>
- #BBB <title>

### Others
- #CCC <title>
- #DDD <title>
```

Ask the user to review and confirm the PR list. Allow them to add/remove PRs manually.

### Phase 3: Generate Release Notes

**Step 3.1**: Read the release PR template

```bash
cat .github/PULL_REQUEST_TEMPLATE/release.md
```

**Step 3.2**: Generate the PR body

Replace placeholders in the template:

- `{lastMergedDate}`: Use `LAST_RELEASE_DATE` (format: YYYY-MM-DD)
- Fill in the **Feature**, **Fix**, and **Others** sections with the categorized PRs from Phase 2

**Step 3.3**: Present the generated PR body

```markdown
# Release Ver.{NEW_VERSION}

## Attention

Do NOT push any commit to `main` branch directory.
Please issue a pull request.

- [ ] Check ALL PR by [`is:pr is:merged base:dev merged:>{lastMergedDate}`](../pulls?q=is%3Apr+is%3Amerged+base%3Adev+merged%3A%3E{lastMergedDate})  
       See also: [LastMergedDate](../pulls?q=is%3Apr+is%3Amerged+base%3Astaging+base%3Amain)
- [ ] Write [Release note](https://github.com/tmc-ccoe/trust-app/blob/dev/src/assets/releaseNote.md)

## Feature

- #{PR_NUMBER} {PR_TITLE}

## Fix

- #{PR_NUMBER} {PR_TITLE}

## Others

- #{PR_NUMBER} {PR_TITLE}

## Notes

---

@toro
please code review!
```

**Do not proceed to Phase 4 until the user approves the PR body.**

### Phase 4: Create Release PR

**Step 4.1**: Create the PR from `dev` to `staging`

```bash
gh pr create \
  --base staging \
  --head dev \
  --title "Release Ver.{NEW_VERSION}" \
  --body "$(cat <<'EOF'
{GENERATED_PR_BODY}
EOF
)"
```

**Step 4.2**: Output the PR URL

```
✅ Release PR created: {PR_URL}
```

### Phase 5: Post-Creation Verification

**Step 5.1**: Verify the PR was created successfully

```bash
gh pr view {PR_NUMBER} --json number,title,baseRefName,headRefName
```

**Step 5.2**: Remind the user of next steps

```
## Next Steps

1. Review the PR: {PR_URL}
2. Update the release note: https://github.com/tmc-ccoe/trust-app/blob/dev/src/assets/releaseNote.md
3. Request review from @toro
4. Merge the PR after approval
5. Tag the release: `git tag {NEW_VERSION} && git push origin {NEW_VERSION}`
```

## Error Handling

- **Git errors**: If any git command fails, stop and report the error to the user.
- **GitHub API errors**: If `gh` command fails, check authentication (`gh auth status`) and report the error.
- **No PRs found**: If no PRs are found since the last release, warn the user but allow them to proceed.

## Notes

- This command does NOT create git tags. Tags must be created manually after the PR is merged.
- This command does NOT update version numbers in source files (e.g., `pyproject.toml`). Version bumps in source files are handled separately.
- The release PR template is stored at `.github/PULL_REQUEST_TEMPLATE/release.md`.
- Version numbers are extracted from past release PR titles (e.g., `Release Ver.1.2.0`), NOT from git tags.
