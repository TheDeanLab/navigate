"""Optional stage telemetry, independent of commanded-position caches."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StagePositionReadback(ABC):
    """Opt-in contract for bounded, nonblocking-admission position queries.

    Implementations must share the hardware connection's transaction lock with
    ordinary commands, skip busy connections, and raise on failed or incomplete
    reads. They must not stop motion or modify acquisition/focus caches.
    """

    @property
    @abstractmethod
    def position_readback_identity(self) -> object:
        """Return the shared physical connection used to deduplicate queries."""

    @abstractmethod
    def read_position_for_monitor(
        self, peers: tuple[StagePositionReadback, ...] = ()
    ) -> dict[str, float] | None:
        """Read this stage and same-connection peers in one bounded transaction.

        Parameters
        ----------
        peers : tuple
            Other stage wrappers sharing this physical connection.

        Returns
        -------
        dict or None
            Confirmed positions for all wrappers, or None when unavailable/busy.
        """
