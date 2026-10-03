# CONTRIBUTING

Thank you your joining to TRUST project!
If you not have developer permission for this project. [Let us know](https://teams.microsoft.com/l/team/19%3A0y18oOqTlX8-UJnHBcdSMHWqPrv4U1dCbOprt_2Tu701%40thread.tacv2/conversations?groupId=7457ac2e-39ed-4471-b635-7a58c30ef8e7&tenantId=d1c1335e-f582-42a9-b6fe-5e1a16eb9bc8), We can invite you.

# Get started

1. At first install `uv`. See also [here](https://docs.astral.sh/uv/getting-started/installation/)
2. Set up AWS Configure. See [AWS SSO configuration](#aws-sso-configuration).
3. Clone this repo
    ```commandline
    git clone https://github.com/YourIndependence/poker-transformer.git
    ```
4. Make venv
    ```commandline
    cd trust-core
    uv venv --python "python3.12" ".venv"
    ```
5. Install dependency
    ```commandline
    uv sync --frozen --extra dev
    ```
6. Install dev tools.
   1. [archgate](https://github.com/archgate/cli) (ADR manager) is invoked via `npx` in git hooks - no explicit installation is required.
       **NOTICE**: archgate does not support `linux/arm64`. On that platform the hooks will automatically skip the check.

   2. And set up rulesync
       ```commandline
       .rulesync/rulesync.sh
       ```
   3. Install [gitleaks](https://github.com/gitleaks/gitleaks) (SAT for secrets).
    - Linux
        ```commandline
        apt install gitleaks
        ```
    - Mac
        ```commandline
        brew install gitleaks
        ```
    - Windows
        1. Download exe from [gitleaks](https://github.com/gitleaks/gitleaks/releases).
        2. Unpack and place exe into local. (e.g.: `C:\Users\{USER_NAME}\.gitleaks`)
        3. Set Path.

7. Run in local as trial.
    ```commandline
    uv run python -m cli local_server run
    ```

# Start contributing

1. Set your development environment.
2. Select an issue you want to do from [project](https://github.com/orgs/tmc-ccoe/projects/713).
   And assign the issue yourself.
   **NOTICE**
   If there are no issues you want to do. Create the issue first.
3. Change issue status: `In progress`
4. create workspace branch.
   See also [branch naming rule](CODING_RULES.md#branch-rules).
5. Implement or fix the issue you selected. and its test codes.
   See also [CODING_RULES](CODING_RULES.md).
   The place where unittests code implement: See also [ARCHITECTURE.md](ARCHITECTURE.md#directory-architecture)
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
