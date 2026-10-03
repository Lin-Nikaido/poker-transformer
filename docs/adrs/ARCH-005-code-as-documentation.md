---
id: ARCH-005
title: Code as Documentation (Comment Minimalism)
domain: backend
status: active
date: 2026-05-08
rules: true
files:
  - 'src/poker/**/*.py'
  - 'tests/**/*.py'
---

## Context

Comments that explain **what** code does create maintenance burden and often become stale. When code changes, comments are frequently forgotten, leading to misleading documentation. Modern Python with expressive naming and type hints makes most explanatory comments unnecessary.

Research shows that the best practice (as of 2026) is to write code that is self-documenting, using comments only to explain **why** a non-obvious decision was made, not **what** the code does.

## Decision

**Beauty lives in the Code. Code must be written so that its intent and behavior are immediately understandable from the code itself.**

Comments are forbidden in the following cases:

1. **Redundant comments** — explaining what code obviously does
2. **Separator comments** — dividing code blocks within a function
3. **Incorrect comments** — comments that contradict the code

Code structure (functions, methods, classes) must convey meaning. If a comment explains what a block does, that block should become a function or method with a descriptive name.

Comments must use ASCII characters and English. Non-ASCII user-facing text is
allowed in string literals; this rule applies to comments only.

### Examples

**✅ Do this:**

```python
user_principal = "0000000@example.com"
user_info = get_user_info(user_principal=user_principal)
```

**❌ Don't do this:**

```python
info = get_info("0000000@example.com")  # get user information from user principal
```

**✅ Do this (extract blocks into functions):**

```python
def read_message(user_mail: str):
    user = verify_user(user_mail)
    messages = load_messages(user)
    return [message.content for message in messages]
```

**❌ Don't do this (separator comments):**

```python
def read_message(user_mail: str):
    # verify user
    user_record = users_db.get(query=f"user_mail eq {user_mail}")
    user = convert_user_object_from_record(user_record)
    
    # load messages from db
    messages_records = message_db.get(query=f"user_id eq {user.id}")
    messages = [
        Message.model_validate(messages_record)
        for messages_record in messages_records
    ]
    
    # return message content as list of string
    return [message.content for message in messages]
```

**❌ Never write incorrect comments:**

```python
i -= 1  # increment  ← WRONG!
```

## Rationale

**Alternative: Allow comments for clarity**

This approach leads to comment rot. When code changes, comments are often left unchanged, creating misleading documentation. The cost of maintaining comments exceeds the benefit.

**Alternative: Require docstrings for all functions**

Docstrings are acceptable for public APIs (Google-style docstrings). However, internal implementation details should be self-explanatory through code structure and naming.

## Consequences

- **Positive**: Code changes do not require comment updates
- **Positive**: Developers focus on writing expressive code rather than explaining poor code
- **Positive**: No risk of comment-code divergence
- **Negative**: Developers must invest time in choosing meaningful names
- **Negative**: Complex algorithms may require extracting helper functions with descriptive names

## Compliance

**Do:**

- Write self-documenting code with expressive variable and function names
- Extract blocks into functions with descriptive names instead of adding separator comments
- Use type hints to document expected types
- Write Google-style docstrings for public APIs only

**Don't:**

- Write comments like `i += 1  # increment` or `vector = vector / vector.norm()  # normalize`
- Use separator comments like `# verify user` or `# load messages from db`
- Add comments explaining what code does (use comments only for **why**, not **what**)
- Write comments that duplicate code logic

**When comments ARE acceptable:**

- Historical context: `# Workaround for boto3 bug #1234 — remove after upgrade to v1.28+`
- Non-obvious business logic: `# VAT rate changes on fiscal year boundary per tax code §123`
- Performance considerations: `# Using set() here reduces O(n²) to O(n)`

## References

- [docs/CODING_RULES.md](../CODING_RULES.md) — Section "Do NOT explain with comments or documents"
- [Best practices for writing code comments (Stack Overflow)](https://stackoverflow.blog/2021/12/23/best-practices-for-writing-code-comments/)
- [Code comment best practices (TechTarget)](https://www.techtarget.com/searchsoftwarequality/tip/Code-comment-best-practices-every-developer-should-know)
