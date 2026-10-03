# Review Check Rules

Review from **7 perspectives** with confidence scoring:

## 1. Architecture Violations (threshold: 80)

- Import from `infrastructure/` in `core/`
- `apis/` directly calling `core/` bypassing `application/`
- Direct instantiation of concrete classes (DB client, external API client) in `core/` or `application/`
- Missing registry registration
- Agent tool executing sync I/O (should be `async def`)
- Calling `asyncio.run()` inside async function
- Unit test introduced that depends on LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets
- Real AWS integration test missing `pytest.mark.real_aws`; ECS dispatch test missing `pytest.mark.ecs`

## 2. Type Safety (threshold: 80)

- `Any` type without justification comment
- `# type: ignore` without explanation
- Missing return type annotation on public functions
- Pydantic field accepting `Any` when concrete type is known
- Passing external input to DB queries or shell commands without validation

## 3. Async Correctness (threshold: 80)

- Missing `await` on coroutine calls
- Blocking I/O in `async def` (`requests.get`, `open()`, `time.sleep()`)
- Calling `asyncio.run()` in async context
- Missing `async with` for async context manager

## 4. ADK Agent Pattern (threshold: 80)

- Tool function using `asyncio.run()` (should be `async def`)
- Agent factory (`get_<name>_agent`) not registered in `AGENT_REGISTRY`
- Building `Agent` outside `core/agents/<name>/agent.py`
- `return_instruction()` or `return_description()` defined inline instead of in `prompts.py`

## 5. Security (threshold: 80)

- Passing user input to `subprocess`, `eval`, `exec` without sanitization
- Secrets or credentials hardcoded in source code
- Building SQL with string formatting instead of parameterized queries
- Fetching external URL without timeout parameter
- Creating AWS resources with overly broad IAM permissions (`"*"` resource in policy)

## 6. Performance (threshold: 80)

- N+1 DB queries in loop (should batch or use JOIN)
- Loading large file entirely in memory when streaming is possible
- Repeated external API calls to same data without caching
- Missing `await asyncio.gather()` for independent concurrent tasks
- Slower unit tests caused by unnecessary LocalStack/real-service setup when an in-process fake or Stubber would prove the same behavior

## 7. Code Quality & Maintainability (threshold: 80)

- Poor naming requiring explanatory comments (variable names that need comments to understand)
- Comments explaining "what" instead of "why" (not caught by archgate pattern matching)
- Using `dict` when Pydantic model should be used for cross-module data
- Magic strings/numbers that should be typed constants or enums
- Patch/workaround code with TODO/FIXME comments indicating temporary solutions
- Error swallowing without logging (not just `pass`, but also silent `return {}` or `return None`)
- Long functions (>50 lines) that should be extracted into smaller functions
- Functions doing multiple unrelated things (violating Single Responsibility Principle)

**Note**: Many of these issues are NOT caught by archgate static analysis, as they require semantic understanding and design judgment.

## Confidence Scoring

- 0-79: Do not report
- 80-94: Report as **Important**
- 95-100: Report as **Critical**

## Scope

**Important**: Only report issues introduced in this change. Do not report existing code issues.
