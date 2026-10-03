# Contributing

# Get started

1. Install `uv` using the [installation guide](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and enter its root directory:
   ```commandline
   git clone https://github.com/YourIndependence/poker-transformer.git
   cd poker-transformer
   ```
3. Install the project and development dependencies:
   ```commandline
   uv sync --frozen --extra dev
   ```
4. Install the Git hooks:
   ```commandline
   uv run lefthook install
   ```
5. Confirm the CLI is available:
   ```commandline
   uv run poker --help
   ```

## Development environment

Use Python 3.12 and `uv` from the repository root:

```powershell
uv sync --extra dev
uv run poker --help
```

`uv.lock` is committed to keep the development environment reproducible. Update
it with `uv lock` after changing dependencies. PyTorch resolves from its CPU
wheel index as configured in `pyproject.toml`; the MVP training target is CPU.

## Development checks

Run the required checks from the repository root:

```powershell
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run pytest tests/unittests/ -v
npx archgate check
```

Unit tests must not require LocalStack, cloud credentials, external APIs, or
repository secrets. Use deterministic fakes for external boundaries. Add
cross-boundary checks under `tests/integration/` when an implementation
introduces those boundaries.

## Project workflow

1. Read the agreed scope and dependencies in `INSTRUCTION.md`.
2. Follow `docs/ARCHITECTURE.md` for layer ownership and dependency direction.
3. Add or update tests under the path corresponding to the source module.
4. Run the affected unit tests and the required checks above.

Do not create GitHub issues or send external messages without explicit user
approval.

## Start contributing

1. Set up your development environment.
2. Select an issue you want to do from [project](https://github.com/orgs/tmc-ccoe/projects/713).
   And assign the issue yourself.
   **NOTICE**
   If there are no issues you want to do, create an issue only after explicit
   approval.
3. Change issue status: `In progress`
4. create workspace branch.
   See also [branch naming rule](CODING_RULES.md#branch-rules).
5. Implement or fix the issue you selected. and its test codes.
   See also [CODING_RULES](CODING_RULES.md).
   The place where unittests code implement: See also [ARCHITECTURE.md](ARCHITECTURE.md#project-structure)
6. Check the affected unit tests first. Unit tests must not require LocalStack, real AWS, Microsoft 365, Box, Azure, Google APIs, or repository secrets.
    ```commandline
    uv run pytest tests/unittests/<affected-path>/ -v
    ```
7. Check **whole** unit tests pass.
    ```commandline
    uv run pytest tests/unittests/
    ```
8. Format the code
    ```commandline
    uv run pre-commit run --all-files
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/
    npx archgate check
    ```
9. Push your branch.
10. Run integration tests when the change crosses service boundaries.
    ```commandline
    uv run pytest
    ```
11. Submit your PR.
    **Do not forget** write `close: #IssueNo` in PR description.
