# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""Serializable camera capabilities and normalized monochrome image formats.

SDK transport formats (including packing and row padding) belong to the adapter.
These descriptors describe the arrays delivered to Navigate, not transport bytes.
"""

from dataclasses import dataclass
import math
from numbers import Integral
from typing import Any, Optional

import numpy as np


@dataclass(frozen=True)
class CameraExposureTiming:
    """Confirmed row exposure and illumination sweep durations, in seconds.

    ``line_interval`` is None for Area acquisition. In Light-Sheet acquisition,
    the full sweep includes row scanning and must not be replaced by row exposure.
    """

    exposure_time: float
    sweep_time: float
    line_interval: Optional[float] = None

    def __post_init__(self) -> None:
        for value in (self.exposure_time, self.sweep_time, self.line_interval):
            if value is not None and (
                isinstance(value, bool) or not math.isfinite(value) or value <= 0
            ):
                raise ValueError("Confirmed camera timing must be finite and positive.")
        if self.sweep_time < self.exposure_time:
            raise ValueError("Camera sweep cannot be shorter than row exposure.")


@dataclass(frozen=True)
class CameraSettingCapability:
    """Describe a setting in the current camera operating mode.

    Parameters
    ----------
    current_value : object, optional
        Confirmed value, or None when it cannot be determined.
    choices : tuple
        Values the adapter can apply in the current operating mode.
    writable : bool
        Whether the adapter supports changing this setting.
    requires_idle : bool
        Whether acquisition must be stopped before applying a value.
    reason : str
        Explanation to display when the setting is unavailable or read-only.
    value_labels : tuple
        Optional (value, label) pairs supplied by the camera.
    """

    current_value: Any = None
    choices: tuple = ()
    writable: bool = False
    requires_idle: bool = True
    reason: str = "This camera driver does not support this setting."
    value_labels: tuple = ()


@dataclass(frozen=True)
class CameraImageFormat:
    """Describe unpacked, right-aligned monochrome arrays delivered by a driver.

    Parameters
    ----------
    dtype : str
        Unsigned array type: uint8 or uint16. Legacy drivers use uint16.
    bit_depth : int, optional
        Number of meaningful output bits. None means unknown, even when the
        storage width is known. It is not inferred from an image's maximum value.
    """

    dtype: str = "uint16"
    bit_depth: Optional[int] = None

    def __post_init__(self) -> None:
        if self.dtype not in ("uint8", "uint16"):
            raise ValueError("Camera arrays must use uint8 or uint16.")
        if self.bit_depth is not None:
            bits = self._validate_bit_depth(self.bit_depth)
            if bits > self.bytes_per_pixel * 8:
                raise ValueError("Camera bit depth exceeds the array storage width.")
            object.__setattr__(self, "bit_depth", bits)

    @staticmethod
    def _validate_bit_depth(bit_depth: int) -> int:
        if isinstance(bit_depth, (bool, np.bool_)) or not isinstance(
            bit_depth, Integral
        ):
            raise TypeError("Camera bit depth must be a whole number.")
        if not 1 <= bit_depth <= 16:
            raise ValueError("Camera bit depth must be between 1 and 16.")
        return int(bit_depth)

    @classmethod
    def for_bit_depth(cls, bit_depth: int) -> "CameraImageFormat":
        """Choose the smallest supported array type preserving all output bits.

        Parameters
        ----------
        bit_depth : int
            Confirmed camera output precision, from 1 to 16 bits.

        Returns
        -------
        CameraImageFormat
            An unsigned byte or unsigned 16-bit word format.
        """
        bits = cls._validate_bit_depth(bit_depth)
        return cls("uint8" if bits <= 8 else "uint16", bits)

    @property
    def bytes_per_pixel(self) -> int:
        """Return storage bytes per pixel, independently of meaningful bits."""
        return np.dtype(self.dtype).itemsize
