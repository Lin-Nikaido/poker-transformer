"""The model-input boundary shared by inference and future training."""

from abc import ABC
from abc import abstractmethod

from torch import Tensor

from poker.core.types.table import PlayerObservation


class BaseObservationEncoder(ABC):
    """Convert a player-safe observation into model inputs."""

    @abstractmethod
    def encode(
        self,
        *,
        observation: PlayerObservation,
    ) -> Tensor:
        """Encode observable information without external I/O."""
        ...
