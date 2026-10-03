---
name: enforcing-layer-boundaries
description: >-
  Decide which layer owns each piece of new code and verify the result against
  ARCH-001 and ARCH-014. Load before writing any file under src/recnavi/ during
  a feature or fix, and again before the quality gate.
  Trigger: "which layer", "layer boundary", "use case", "router", "core vs
  application", "where does this go", "ARCH-014".
user-invocable: false
---

# Enforcing Layer Boundaries

Assign every new piece of code to exactly one layer, then prove the assignment
holds. The call chain is `apis -> application -> core`.

Authoritative sources: [ARCH-001](../../../docs/adrs/ARCH-001-clean-architecture.md)
(dependency direction) and [ARCH-014](../../../docs/adrs/ARCH-014-layer-responsibilities.md)
(layer responsibilities). This skill is the working procedure; the ADRs win on
any disagreement.

---

## Step 1: Assign each change to a layer

For every behaviour the task introduces, answer one question and stop at the
first "yes".

| Question                                                         | Layer          | File                                                     |
| ---------------------------------------------------------------- | -------------- | -------------------------------------------------------- |
| Is it a rule about the domain, true regardless of who calls it?   | `core/`        | `core/<domain>/<noun>.py`                                 |
| Is it a shape of domain data?                                     | `core/types/`  | `core/types/<noun>.py`                                    |
| Is it a thing a user wants to achieve, in steps?                  | `application/` | `application/<domain>/<verb>_<noun>_usecase.py`           |
| Is it how that flow is exposed over HTTP?                         | `apis/`        | `apis/<group>/<group>_router.py`                          |
| Is it how an external system is actually reached?                 | `infrastructure/` | `infrastructure/<service>/<name>.py`                   |

If a behaviour seems to belong to two layers, it is two behaviours. Split it.

## Step 2: Write each layer to its own contract

**`core/` -- capabilities only.** A core function answers "what can this system
do with this domain object". It takes `BaseDatabase` or plain values, never a
`Request`. It never knows why it was called.

```python
async def get_projects(
    projects_db: BaseDatabase,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Project], str | None]:
```

**`application/` -- use cases only.** A use case answers "what does the caller
want to achieve". It is the only place that composes several core calls, applies
authorization decisions, or sequences steps. It is named `<verb>_<noun>_usecase`
and is callable with no HTTP present.

```python
async def get_projects_usecase(
    projects_db: BaseDatabase,
    group_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[Project], str | None]:
    """List the projects visible to a group, newest first."""
    return await get_projects(...)
```

A use case that currently only forwards to one core function is still correct.
It is the seam the next requirement attaches to.

**`apis/` -- transport only.** An endpoint does exactly three things, in order:

1. Resolve dependencies (`request.app.state.database[...]`, `Depends(verify_user)`)
2. Call **one** use case
3. Map the result onto a response schema

Nothing else. No branching on domain state, no loops over domain rules, and no
comments that narrate the flow -- if the endpoint needs a comment to explain
what it is doing, the explanation belongs in a use case name.

```python
@cms_router.get("/getProjects")
async def get_projects_endpoint(
    request: Request,
    user: User = Depends(verify_user),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> GetProjectsResponse:
    """List projects for the authenticated user's group."""
    projects_db = request.app.state.database[PROJECTS_TABLE_NAME]
    projects, next_cursor = await get_projects_usecase(
        projects_db=projects_db,
        group_id=user.group_id,
        limit=limit,
        cursor=cursor,
    )
    return GetProjectsResponse(
        projects=projects,
        next_cursor=next_cursor,
    )
```

## Step 3: Check the import table

`apis/` may import `recnavi.core.types` for annotations. It may not import any
other `core/` module.

| From              | May import                                            | Must never import                        |
| ----------------- | ----------------------------------------------------- | ---------------------------------------- |
| `apis/`           | `application/`, `apis/`, `core/types/`, `config/`, `exceptions/` | any other `core/`, `infrastructure/` |
| `application/`    | `core/`, `config/`, `exceptions/`                     | `apis/`, `infrastructure/`, `fastapi`    |
| `core/`           | `core/`, `config/`, `exceptions/`                     | `apis/`, `application/`, `infrastructure/`, `fastapi` |
| `infrastructure/` | `core/`, `config/`, `exceptions/`                     | `apis/`, `application/`                  |

Verify with:

```bash
grep -rn "from recnavi\.core\." src/recnavi/apis/ | grep -v "recnavi.core.types"
grep -rnE "^(from|import) (fastapi|starlette)" src/recnavi/application/ src/recnavi/core/
grep -rn "from recnavi\.infrastructure" src/recnavi/application/
grep -rnE "from recnavi\.(apis|application)" src/recnavi/core/
```

Every command above must print nothing.

## Step 4: Mirror the layer structure in tests

A use case is tested without FastAPI, using `MockDatabase` from
`tests/mockups/`:

```
src/recnavi/application/project/get_projects_usecase.py
  -> tests/unittests/application/project/test_get_projects_usecase.py
```

If a test for an `application/` module needs a FastAPI `TestClient`, the logic
under test is in the wrong layer.

## Step 5: Run the automated check

```bash
archgate check
```

If `archgate` is not on PATH, install it the way `.claude/scripts/init.sh` does:

```bash
mkdir -p "$HOME/.local/npm"
npm install --global --prefix "$HOME/.local/npm" archgate
export PATH="$HOME/.local/npm/bin:$PATH"
```

If `.archgate/` has no ADR symlinks yet (rulesync.sh has not run locally):

```bash
mkdir -p .archgate
ln -sfn ../docs/adrs .archgate/adrs
ln -sfn ../docs/adrs/rules.d.ts .archgate/rules.d.ts
```

ARCH-014 rules that gate this skill:

| Rule                                      | Catches                                             |
| ----------------------------------------- | ---------------------------------------------------- |
| `apis-must-not-import-core-logic`         | endpoint reaching past `application/` into `core/`   |
| `application-must-not-import-web-framework` | use case coupled to FastAPI                        |
| `core-must-not-import-web-framework`      | domain logic coupled to FastAPI                      |
| `core-must-not-import-upper-layers`       | inverted dependency out of `core/`                   |
| `application-must-not-import-infrastructure` | use case bound to a concrete adapter              |
| `usecase-naming-convention`               | public `application/` function not ending `_usecase` |
| `no-usecase-comments-in-apis`             | endpoint narrating a flow in comments                |

A violation is blocking. Do not suppress it -- move the code to the layer the
message names.

## Report

```markdown
## Layer Assignment

| Behaviour | Layer | File | Rationale |
| --------- | ----- | ---- | --------- |
| <what>    | core / application / apis / infrastructure | <path> | <why this layer> |

### Import check
- apis -> core (non-types): none / <list>
- application -> fastapi: none / <list>
- application -> infrastructure: none / <list>
- core -> upper layers: none / <list>

### archgate check
- ARCH-001: <N> passed / <N> failed
- ARCH-014: <N> passed / <N> failed
```
