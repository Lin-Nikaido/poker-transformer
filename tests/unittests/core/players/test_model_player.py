import pytest
import torch
from torch import nn

from poker.core.players.model_player import ModelPlayer
from poker.core.types.actions import ActionKind
from tests.mockups.models import StubEncoder
from tests.mockups.models import StubModel
from tests.mockups.models import make_request


@pytest.mark.asyncio
async def test_players_share_updated_weights_without_sharing_random_state(
    stub_encoder: StubEncoder,
) -> None:
    model = StubModel()
    first = ModelPlayer(
        player_id="learner", model=model, encoder=stub_encoder, seed=7
    )
    second = ModelPlayer(
        player_id="learner", model=model, encoder=stub_encoder, seed=7
    )
    request = make_request(
        legal_kinds=(ActionKind.FOLD, ActionKind.CALL, ActionKind.RAISE)
    )
    optimizer = torch.optim.SGD(model.parameters(), lr=1)
    model.logits[0].backward()
    optimizer.step()
    optimizer.zero_grad()

    assert first.model is second.model is model
    assert first.model.logits[0].item() == -1
    global_rng = torch.random.get_rng_state().clone()
    first_choices = [
        (await first.select_action(request=request)).policy_trace.action_index
        for _ in range(12)
    ]
    second_choices = [
        (await second.select_action(request=request)).policy_trace.action_index
        for _ in range(12)
    ]
    assert first_choices == second_choices
    assert torch.equal(global_rng, torch.random.get_rng_state())
    assert model.training is True
    assert model.logits.grad is None


@pytest.mark.asyncio
async def test_model_player_rejects_another_players_request(
    stub_encoder: StubEncoder,
) -> None:
    player = ModelPlayer(
        player_id="other", model=StubModel(), encoder=stub_encoder, seed=7
    )
    with pytest.raises(ValueError, match="another player"):
        await player.select_action(
            request=make_request(legal_kinds=(ActionKind.CALL,))
        )


@pytest.mark.asyncio
async def test_model_player_rejects_empty_legal_mask(
    stub_encoder: StubEncoder,
) -> None:
    player = ModelPlayer(
        player_id="learner", model=StubModel(), encoder=stub_encoder, seed=7
    )
    with pytest.raises(ValueError, match="at least one legal"):
        await player.select_action(request=make_request(legal_kinds=()))


class InvalidModel(nn.Module):
    def __init__(self, *, output: torch.Tensor) -> None:
        super().__init__()
        self.output = output

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.output + inputs.sum() * 0


@pytest.mark.parametrize(
    "output",
    (torch.zeros(5), torch.zeros(1, 15), torch.full((15,), float("nan"))),
)
@pytest.mark.asyncio
async def test_model_player_rejects_invalid_model_output(
    output: torch.Tensor, stub_encoder: StubEncoder
) -> None:
    player = ModelPlayer(
        player_id="learner",
        model=InvalidModel(output=output),
        encoder=stub_encoder,
        seed=7,
    )
    with pytest.raises(ValueError, match="logit"):
        await player.select_action(
            request=make_request(legal_kinds=(ActionKind.CALL,))
        )


@pytest.mark.asyncio
async def test_model_player_owns_supplied_module_and_masks_illegal_actions(
    stub_encoder: StubEncoder,
) -> None:
    model = StubModel()
    player = ModelPlayer(
        player_id="learner", model=model, encoder=stub_encoder, seed=7
    )

    decision = await player.select_action(
        request=make_request(legal_kinds=(ActionKind.CALL,))
    )

    assert player.model is model
    assert decision.action.kind is ActionKind.CALL
    assert decision.policy_trace.action_index == 2
    assert decision.policy_trace.log_probability == pytest.approx(0)
    assert model.logits.grad is None
