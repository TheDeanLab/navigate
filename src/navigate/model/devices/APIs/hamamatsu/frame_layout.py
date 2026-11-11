"""Validated unpacked DCAM layouts for attaching native frame buffers."""

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class DCAMFrameLayout:
    """Describe byte offsets for an unpacked monochrome DCAM frame.

    Packed MONO12/MONO12P and color formats deliberately require a separate,
    verified decoder before they can be attached to Navigate buffers.
    """

    width: int
    height: int
    pixel_type: int
    row_bytes: int
    frame_bytes: int
    top_offset: int = 0

    def __post_init__(self) -> None:
        for name in (
            "width",
            "height",
            "pixel_type",
            "row_bytes",
            "frame_bytes",
            "top_offset",
        ):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(
                value, (int, float, np.integer)
            ):
                raise ValueError(f"Invalid DCAM {name}: {value!r}")
            if (
                not math.isfinite(value)
                or int(value) != value
                or value < (0 if name == "top_offset" else 1)
            ):
                raise ValueError(f"Invalid DCAM {name}: {value!r}")
            object.__setattr__(self, name, int(value))
        if self.pixel_type not in (1, 2):
            raise ValueError(
                "Only unpacked DCAM MONO8 and MONO16 layouts are supported."
            )
        row_size = self.width * np.dtype(self.dtype).itemsize
        if (
            self.row_bytes < row_size
            or self.frame_bytes
            < self.top_offset + (self.height - 1) * self.row_bytes + row_size
        ):
            raise ValueError(
                "DCAM byte counts do not contain the reported image geometry."
            )

    @property
    def dtype(self) -> str:
        """Return the native unpacked pixel container type."""
        return "uint8" if self.pixel_type == 1 else "uint16"

    def view(self, buffer: np.ndarray) -> np.ndarray:
        """Return pixels while excluding row padding and leading metadata bytes.

        Parameters
        ----------
        buffer : np.ndarray
            Contiguous native allocation containing at least ``frame_bytes`` bytes.
        """
        if buffer.nbytes < self.frame_bytes or not buffer.flags.c_contiguous:
            raise ValueError("Native allocation is smaller than the DCAM frame layout.")
        return np.ndarray(
            (self.height, self.width),
            dtype=self.dtype,
            buffer=buffer,
            offset=self.top_offset,
            strides=(self.row_bytes, np.dtype(self.dtype).itemsize),
        )
