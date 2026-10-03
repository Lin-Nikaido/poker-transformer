# Poker Transformer AI

A PyTorch Transformer poker agent trained with reinforcement learning through
self-play. The MVP targets six-max no-limit Texas Hold'em and provides a
reproducible local workflow for training, inference, and match evaluation.

## Development

Requirements: Python 3.12 and `uv`.

```powershell
uv sync --extra dev
uv run poker --help
```

See [INSTRUCTION.md](INSTRUCTION.md) for the agreed MVP requirements and
implementation roadmap, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for layer
ownership, and [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for development
checks.
