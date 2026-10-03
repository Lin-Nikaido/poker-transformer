---
name: jira-ticket
description: >-
  Fetch and display a specific Jira ticket with full details (description, AC, status,
  assignee, dependencies). Optionally transition its status.
  Trigger: "check XXX", "update status", "Jira ticket", "details XXX".
---

# Jira Ticket - Read & Update

Fetch and display the specified project ticket, then optionally update its status.

## Usage

```
/jira-ticket check XXX
/jira-ticket update status
```

---

## Step 1: Fetch Ticket

Use `mcp__jira__jira_get_issue` with the ticket key provided as `$ARGUMENTS`.

Fields to extract:
- `key`, `issuetype`, `summary`, `status`, `priority`, `assignee`
- `parent` (Epic or parent story)
- `description` (convert Atlassian Document Format to plain text for display)
- `issuelinks` (used to extract blocking relationships)

From `issuelinks`, extract:

| Kind | Condition | Label |
|------|-----------|-------|
| Blocks | `type.name == "Blocks"` and `outwardIssue` exists | Tickets blocked by this one |
| Blocked by | `type.name == "Blocks"` and `inwardIssue` exists | Tickets blocking this one |

---

## Step 2: Display

Output the ticket in this format:

```
---
**XXX: <summary>**

| Field    | Value |
|----------|-------|
| Status   | <status> |
| Priority | <priority> |
| Assignee | <assignee or "Unassigned"> |
| Type     | <issuetype> |
| Parent / Epic | <parent key>: <parent summary> or "None" |

**Description**
<First 600 characters of description. Truncate with "... (truncated)" if longer.>

**Acceptance Criteria**
<Extract the AC / Acceptance Criteria section from the description.
If not found, display: "⚠️ AC not documented">

**Dependencies**
- Blocks: <XXX (<status>)> or "None"
- Blocked by: <YYY (<status>)> or "None"
---
```

---

## Step 3: Offer Status Update (optional)

After displaying the ticket, ask the user:

> Would you like to update the status? (Current: **<status>**)

If the user confirms:

1. Use `mcp__jira__jira_get_transitions` to fetch available transitions
2. Present the options as a numbered list
3. Apply the chosen transition with `mcp__jira__jira_transition_issue`
4. Confirm the updated status after the transition completes

If the user declines or does not respond, exit without further action.

---

## Error Handling

| Case | Response |
|------|----------|
| Ticket key not found | "Ticket `XXX` was not found. Please verify the key." |
| No argument provided | "Please specify a ticket key. Example: `/jira-ticket 274`" |

---

## Related Skills

| Skill | When to use |
|-------|-------------|
| `/draft-pr` | Drafting a PR after implementation is complete |
| `/quality-gate` | Running quality checks before merge |
