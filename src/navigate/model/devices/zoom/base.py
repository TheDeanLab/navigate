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


# Standard Library Imports
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

# Third Party Imports

# Local Imports
from navigate.tools.decorators import log_initialization
from navigate.config.configuration_schema import CollectionSpec, SettingSpec

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ZoomBase(ABC):
    """ZoomBase parent class."""

    configuration_schema = {
        "zoom_values": CollectionSpec(
            label="Zoom Values",
            storage="parallel_mappings",
            key_field="zoom",
            value_field="position",
            storage_fields=("position", "pixel_size"),
            minimum_items=0,
            item_schema={
                "zoom": SettingSpec(
                    str,
                    label="Zoom",
                    help_text="Zoom label used by the application.",
                    required=True,
                ),
                "position": SettingSpec(
                    float,
                    label="Position",
                    help_text="Device position for this zoom label.",
                    required=True,
                ),
                "pixel_size": SettingSpec(
                    float,
                    label="Pixel Size (um)",
                    help_text=(
                        "Positive object-space pixel size at this zoom, in "
                        "micrometres."
                    ),
                    minimum=0.000001,
                    step=0.001,
                    required=True,
                ),
            },
        ),
        "stage_positions": CollectionSpec(
            label="Stage Position Calibration",
            storage="nested_mapping",
            key_field="solvent",
            value_field="position",
            minimum_items=0,
            item_schema={
                "solvent": SettingSpec(
                    str,
                    label="Solvent",
                    help_text="Immersion solvent for this calibration.",
                    required=True,
                ),
                "axis": SettingSpec(
                    str,
                    label="Stage Axis",
                    help_text="Stage axis adjusted for this calibration.",
                    required=True,
                ),
                "zoom": SettingSpec(
                    str,
                    label="Zoom",
                    help_text="Zoom label for this calibration point.",
                    required=True,
                ),
                "position": SettingSpec(
                    float,
                    label="Position",
                    help_text="Stage position offset for this calibration point.",
                    required=True,
                ),
            },
        ),
    }

    def __init__(
        self,
        microscope_name: str,
        device_controller: Any,
        configuration: dict,
        *args: Optional[Any],
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize the parent zoom class.

        Parameters
        ----------
        microscope_name : str
            Name of microscope in configuration
        device_controller : object
            Hardware device to connect to
        configuration : multiprocesing.managers.DictProxy
            Global configuration of the microscope
        """

        #: dict: Configuration dictionary for the device.
        self.configuration = configuration["configuration"]["microscopes"][
            microscope_name
        ]["zoom"]

        #: dict: Zoom dictionary
        self.zoomdict = self.configuration["position"]
        self.build_stage_dict()

        #: float: the desired zoom setting
        self.zoomvalue = None

    def __del__(self) -> None:
        """Delete the ZoomBase object."""
        pass

    def __str__(self) -> str:
        """Return the string representation of the ZoomBase object."""
        return "ZoomBase"

    def build_stage_dict(self) -> None:
        """
        Construct a dictionary of stage offsets in between different zoom values.

        This assumes self.configuration["stage_positions"] is a dictionary of ideal
        focus positions for the same object taken in the same solvent at
        each magnification. e.g.,

        stage_positions:
            BABB:
                f:
                    0.63x: 0
                    1x: 70775
                    2x: 72455
                    3x: 72710
                    4x: 72795
                    5x: 72850
                    6x: 72880

        The resulting dictionary is keyed first on solvent (refractive index),
        followed by the stage axis to offset, followed by the current magnification
        and then the target magnification.
        """
        try:
            stage_positions = self.configuration["stage_positions"]
        except KeyError:
            self.stage_offsets = None
            return

        #: dict: Dictionary of stage offsets in between different zoom values.
        self.stage_offsets = {}
        for solvent, axes in stage_positions.items():
            self.stage_offsets[solvent] = {}
            for axis, mags in axes.items():
                self.stage_offsets[solvent][axis] = {}
                for mag_curr, focus_curr in mags.items():
                    self.stage_offsets[solvent][axis][mag_curr] = {}
                    for mag_target, focus_target in mags.items():
                        self.stage_offsets[solvent][axis][mag_curr][mag_target] = (
                            focus_target - focus_curr
                        )

    @abstractmethod
    def set_zoom(self, zoom: dict, wait_until_done=False) -> None:
        """Change the microscope zoom.

        Confirms tha the zoom position is available in the zoomdict

        Parameters
        ----------
        zoom : dict
            Zoom dictionary
        wait_until_done : bool
            Delay parameter.

        Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.zoomvalue = zoom
        else:
            logger.error(f"Zoom designation, {zoom}, not in the configuration")
            raise ValueError("Zoom designation not in the configuration")

    def move(self, position: int, wait_until_done: bool = False) -> None:
        """Move the Zoom Servo

        Parameters
        ----------
        position : int
            Location to move to.
        wait_until_done : bool
            Delay parameter
        """
        pass

    def read_position(self) -> int:
        """Read the position of the Zoom Servo

        Returns
        -------
        cur_position : int
            Current position of Zoom
        """
        cur_position = None
        return cur_position
