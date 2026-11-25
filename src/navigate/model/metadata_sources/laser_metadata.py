"""Acquisition-local laser setting records, independent of image file format."""

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


class LaserMetadata:
    """Keep confirmed settings separate from GUI intent and share them with writers.

    Records describe channel preparation, not measured power during exposure.
    Identical channel settings are recorded once, avoiding work on every frame.
    """

    def __init__(self) -> None:
        #: Lock: Protect records shared by signal and image-writer threads.
        self._lock = Lock()
        #: str: Distinguishes records from successive acquisition preparations.
        self.acquisition_id = uuid4().hex
        #: list[dict]: Immutable copies of channel preparation events.
        self._records: list[dict] = []
        self._latest: dict[str, dict] = {}

    def record(self, channel: str, settings: dict) -> bool:
        """Append changed channel settings and return whether a record was added.

        Parameters
        ----------
        channel : str
            Experiment channel key.
        settings : dict
            Requested settings or a confirmed device snapshot.

        Returns
        -------
        bool
            Whether the channel's settings changed.
        """
        comparison = {k: v for k, v in settings.items() if k != "confirmed_at"}
        with self._lock:
            if self._latest.get(channel) == comparison:
                return False
            self._latest[channel] = deepcopy(comparison)
            self._records.append(
                {
                    "schema_version": 1,
                    "acquisition_id": self.acquisition_id,
                    "sequence": len(self._records),
                    "channel": channel,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    **deepcopy(settings),
                }
            )
        return True

    def read_since(self, cursor: int = 0) -> tuple[int, list[dict]]:
        """Copy records after a writer's cursor without hardware access.

        Parameters
        ----------
        cursor : int, optional
            Number of records already consumed by this writer.

        Returns
        -------
        tuple[int, list[dict]]
            Updated cursor and newly available metadata records.
        """
        with self._lock:
            return len(self._records), deepcopy(self._records[cursor:])
