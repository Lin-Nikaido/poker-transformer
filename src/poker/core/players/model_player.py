"""A seated player that directly owns a reference to a PyTorch module."""

from uuid import UUID

import torch
from torch import Tensor
from torch import nn

from poker.core.actions.action_options import get_action_mask
from poker.core.actions.action_options import get_action_options
from poker.core.players.base_player import BasePlayer
from poker.core.ports.observation_encoder import BaseObservationEncoder
from poker.core.types.decisions import DecisionRequest
from poker.core.types.decisions import PlayerDecision
from poker.core.types.decisions import PolicyTrace


class ModelPlayer(BasePlayer):
    """Encode observations and sample legal actions from the supplied model."""

    def __init__(
        self,
        *,
        player_id: UUID | None = None,
        model: nn.Module,
        encoder: BaseObservationEncoder,
        seed: int,
        policy_version: str = "initial",
    ) -> None:
        super().__init__(player_id=player_id)
        self.model: nn.Module = model
        self.encoder = encoder
        self.policy_version = policy_version
        self.generator = torch.Generator(device="cpu").manual_seed(seed)

    async def _select_action_impl(
        self, *, request: DecisionRequest
    ) -> PlayerDecision:
        """Sample a legal action without modifying weights or model mode."""
        action_mask = get_action_mask(legal_actions=request.legal_actions)
        if not any(action_mask):
            raise ValueError(
                "A model decision requires at least one legal action"
            )
        with torch.no_grad():
            output: object = self.model(
                self.encoder.encode(observation=request.observation),
            )
            if not isinstance(output, Tensor) or output.shape != (
                len(action_mask),
            ):
                raise ValueError(
                    "The model must return one logit per action index"
                )
            logits = output.to(device="cpu", dtype=torch.float32)
            if not torch.isfinite(logits).all():
                raise ValueError("Model logits must be finite")
            mask = torch.tensor(action_mask, dtype=torch.bool)
            log_probabilities = logits.masked_fill(
                ~mask, -torch.inf
            ).log_softmax(dim=0)
            action_index = int(
                torch.multinomial(
                    log_probabilities.exp(),
                    num_samples=1,
                    generator=self.generator,
                ).item()
            )
        return PlayerDecision(
            action=get_action_options()[action_index],
            policy_trace=PolicyTrace(
                action_index=action_index,
                log_probability=float(log_probabilities[action_index].item()),
                policy_version=self.policy_version,
            ),
        )
