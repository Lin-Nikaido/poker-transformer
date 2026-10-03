---
name: release
description: "Routes to appropriate release workflow: normal release (dev to staging) or hotfix release (specific PR). Prompts user when no arguments provided."
targets: ["*"]
claudecode:
  skills:
    - release-update
    - release-hotfix
  allowed-tools: Bash(echo *), AskUserQuestion, Skill
  disable-model-invocation: false
---

# Release

Entry point for release operations. Routes to the appropriate release workflow based on arguments.

## Usage

```
# Interactive mode (user chooses release type)
/release

# Normal release from dev to staging
/release dev major
/release dev minor
/release dev patch

# Hotfix release (specific PR)
/release #808
/release 808
```

## Routing Logic

The command analyzes `$ARGUMENTS` and routes to the appropriate skill:

1. **No arguments** to Ask user to choose
2. **Starts with "dev"** to Invoke `release-update` skill
3. **Is a number** (with or without `#`) to Invoke `release-hotfix` skill
4. **Other** to Show error message

## Procedure

### Step 1: Parse Arguments

**Step 1.1**: Check if arguments are empty

If `$ARGUMENTS` is empty or only whitespace, proceed to Step 2 (user prompt).

**Step 1.2**: Check if arguments start with "dev"

```bash
if [[ "$ARGUMENTS" =~ ^dev ]]; then
  echo "Route: Normal release (dev to staging)"
  # Extract version bump type (major/minor/patch)
  BUMP_TYPE=$(echo "$ARGUMENTS" | sed 's/^dev *//')
fi
```

If matched, proceed to Step 3 (invoke release-update).

**Step 1.3**: Check if arguments are a PR number

```bash
# Remove optional '#' prefix and check if it's a number
CLEANED=$(echo "$ARGUMENTS" | sed 's/^#//' | xargs)
if [[ "$CLEANED" =~ ^[0-9]+$ ]]; then
  echo "Route: Hotfix release (PR #$CLEANED)"
fi
```

If matched, proceed to Step 4 (invoke release-hotfix).

**Step 1.4**: If no pattern matches, show error

```
[ERROR] Invalid arguments: "$ARGUMENTS"

Usage:
  /release                  # Interactive mode
  /release dev [major|minor|patch]  # Normal release
  /release #<PR-NUMBER>     # Hotfix release

Examples:
  /release dev minor
  /release #808
```

Exit with error.

### Step 2: User Prompt (No Arguments)

When no arguments are provided, ask the user to choose the release type.

Use `AskUserQuestion` to present options:

**Question**: "What type of release do you want to perform?"

**Options**:

1. **Normal release from dev branch**
   - Description: "Create a release PR from dev to staging with version bump (major/minor/patch)"
   - If selected: Ask follow-up question for version bump type

2. **Hotfix release for a specific PR**
   - Description: "Release a specific hotfix PR that's already merged or ready to merge to staging"
   - If selected: Ask follow-up question for PR number

**Follow-up questions**:

If "Normal release" is selected:
- Question: "What version bump type?"
- Options: major, minor, patch
- After selection, set `ROUTE="dev"` and `BUMP_TYPE=<selected>`

If "Hotfix release" is selected:
- Question: "What is the PR number?"
- Input: Text field for PR number
- After input, set `ROUTE="hotfix"` and `PR_NUMBER=<input>`

After user responses, proceed to Step 3 or Step 4 accordingly.

### Step 3: Invoke release-update

For normal releases (dev to staging).

**Step 3.1**: Validate bump type

Ensure `BUMP_TYPE` is one of: `major`, `minor`, `patch`.

If invalid:
```
[ERROR] Invalid version bump type: "$BUMP_TYPE"

Must be one of: major, minor, patch
```

Exit with error.

**Step 3.2**: Invoke the skill

```
Skill: release-update
Arguments: $BUMP_TYPE
```

The `release-update` skill will handle the complete workflow.

### Step 4: Invoke release-hotfix

For hotfix releases (specific PR).

**Step 4.1**: Validate PR number

```bash
# Remove '#' prefix if present
PR_NUMBER=$(echo "$PR_NUMBER" | sed 's/^#//')

# Check if it's a valid number
if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] Invalid PR number: $PR_NUMBER"
  exit 1
fi
```

**Step 4.2**: Invoke the skill

```
Skill: release-hotfix
Arguments: $PR_NUMBER
```

The `release-hotfix` skill will handle the complete workflow.

## Implementation Notes

### Argument Parsing Examples

| Input | Route | Extracted Value |
|-------|-------|-----------------|
| (empty) | prompt | (user chooses) |
| `dev major` | release-update | `major` |
| `dev minor` | release-update | `minor` |
| `dev patch` | release-update | `patch` |
| `#808` | release-hotfix | `808` |
| `808` | release-hotfix | `808` |
| `foo` | error | N/A |

### Error Messages

**Invalid input**:
```
[ERROR] Invalid arguments: "{INPUT}"

The /release command accepts:
1. No arguments (interactive mode)
2. "dev [major|minor|patch]" for normal releases
3. A PR number (e.g., "#808" or "808") for hotfix releases

Examples:
  /release
  /release dev minor
  /release #808
```

**Skill invocation failed**:
```
[ERROR] Failed to invoke {SKILL_NAME} skill

Error: {ERROR_MESSAGE}

Please check:
- The skill exists and is properly configured
- Required tools are available
- Repositories are in a clean state
```

## User Experience Flow

### Interactive Mode

```
User: /release

Assistant: [Presents question with two options]
  1. Normal release from dev branch
  2. Hotfix release for a specific PR

User: [Selects "Normal release"]

Assistant: [Presents follow-up question]
  What version bump type? major / minor / patch

User: [Selects "minor"]

Assistant: [Invokes release-update skill with "minor" argument]
```

### Direct Mode (with arguments)

**Normal release**:
```
User: /release dev minor
Assistant: [Parses arguments, invokes release-update skill directly]
```

**Hotfix release**:
```
User: /release #808
Assistant: [Parses arguments, invokes release-hotfix skill directly]
```

## Notes

- This is a routing command that delegates actual work to specialized skills
- The skills `release-update` and `release-hotfix` must exist in `.rulesync/commands/`
- User prompts use the `AskUserQuestion` tool for better UX
- All validation happens before skill invocation
- Skill invocation failures are caught and reported to the user
