# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from navigate.model.devices.mirrors.base import MirrorBase
from navigate.tools.decorators import log_initialization

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


@log_initialization
class ImagineOpticsMirror(MirrorBase):
    """ImageineOpticsMirror mirror class."""

    def __init__(self, microscope_name, device_connection, configuration):
        """Initialize the ImagineOpticsMirror class.

        Parameters
        ----------
        microscope_name : str
            Name of the microscope.
        device_connection : dict
            Dictionary containing the device connection information.
        configuration : dict
            Dictionary containing the configuration information.
        """
        super().__init__(microscope_name, device_connection, configuration)

        flat_path = configuration["configuration"]["microscopes"][microscope_name][
            "mirror"
        ]["hardware"]["flat_path"]
        self.mirror_controller.set_flat(pos_path=flat_path)

        logger.info("ImagineOpticsMirror Initialized")

        # flatten the mirror
        self.flat()

    def __del__(self) -> None:
        """Delete the ImagineOpticsMirror class."""
        pass

    def flat(self):
        """Move the mirror to the flat position."""
        self.mirror_controller.flat()

    def zero_flatness(self):
        """Zero the mirror flatness."""
        self.mirror_controller.move_absolute_zero()

    def set_positions_flat(self, pos):
        """Set the mirror to the flat position.

        Parameters
        ----------
        pos : list
            List of positions to set the mirror to.
        """
        self.mirror_controller.set_flat(pos)

    def display_modes(self, coefs):
        """Display the mirror modes.

        Parameters
        ----------
        coefs : list
            List of coefficients to display the mirror modes.
        """
        self.mirror_controller.display_modes(coefs)

    def get_modal_coefs(self):
        """Get the modal coefficients.

        Returns
        -------
        list
            List of modal coefficients.
        """
        return self.mirror_controller.get_modal_coefs()

    def set_from_wcs_file(self, path=None, name=None):
        """Set the mirror from a WCS file.

        Parameters
        ----------
        path : str, optional
            Path to the WCS file, by default None
        name : str, optional
            Name of the WCS file, by default None

        Returns
        -------
        list
            List of coefficients.
        """
        if path:
            coefs = self.mirror_controller.load_wcs(path=path, mode_file=True)
        elif name:
            coefs = self.mirror_controller.load_wcs(name=name, mode_file=True)
        return coefs

    def save_wcs_file(self, path=None, name=None):
        """Save the WCS file.

        Parameters
        ----------
        path : str, optional
            Path to save the WCS file, by default None
        name : str, optional
            Name of the WCS file, by default None
        """

        if path:
            self.mirror_controller.save_wcs(path=path, mode_file=True)
        elif name:
            self.mirror_controller.save_wcs(name=name, mode_file=True)
