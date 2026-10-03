# Architecture

## Project structure

The installable Python package is `poker`, located under `src/poker/`. The
repository is being built as a poker AI, so the structure below describes both
the modules that exist now and the ownership rules for modules added by the MVP.

```text
src/poker/
  cli/             Typer command-line boundary
  application/     Training, inference, and evaluation use cases
  core/            Poker domain types, rules, policy interfaces, and algorithms
  infrastructure/ External engines, checkpoint files, and other adapters
  config/          Configuration loading and validation
tests/
  unittests/       Fast isolated tests mirroring src/poker/
  integration/     Tests across adapters and system boundaries
```

## Layer responsibilities

| Layer | Owns | May depend on |
| --- | --- | --- |
| `cli/` | Parse command-line input, call an application use case, render output | `application/`, `config/` |
| `application/` | Coordinate training, inference, and evaluation workflows | `core/` and injected ports |
| `core/` | Poker rules and observations, legal actions, rewards, model-independent algorithms, and port definitions | Standard library and domain-level dependencies only |
| `infrastructure/` | Concrete game engine, storage, external service, and file adapters | `core/` |
| `config/` | Parse and validate settings at the process boundary | Configuration libraries |

Dependencies point inward: command-line and infrastructure adapters connect to
application/core contracts; domain logic does not import CLI, application, or
infrastructure modules. PyTorch model computation belongs to the policy/model
implementation in `core/` because it implements the policy contract. Training
loop coordination belongs to `application/`.

## I/O and async boundary

All external I/O is owned by `infrastructure/` and exposed through injected
interfaces. Database, network, and asynchronous file operations use `async def`
and are awaited by application use cases. Do not call `asyncio.run()` from an
async request path. CPU-bound PyTorch inference and training are synchronous
computation; keep them out of async I/O adapters and use an explicit worker
boundary if a future async service must invoke long-running model work.

The current MVP is a local CLI and does not need an HTTP API, database, cloud
service, or distributed worker. Add adapters only when a use case needs them.

## Tests

Unit tests mirror source paths under `tests/unittests/` and use fakes for ports.
They do not depend on LocalStack, real cloud services, or repository secrets.
Cross-boundary tests belong under `tests/integration/`. See
`docs/CONTRIBUTING.md` for local commands.
