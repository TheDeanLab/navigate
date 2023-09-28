# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard library imports

# Third party imports

# Local application imports
from aslm.model.features.autofocus import Autofocus


class CalculateFocusRange:
    """CalculateFocusRange class for determining the focus range using autofocus.

    This class provides functionality to calculate the focus range of a microscope
    using autofocus measurements.

    Parameters:
    ----------
    model : MicroscopeModel
        The microscope model object used for focus range calculation.

    Attributes:
    ----------
    model : MicroscopeModel
        The microscope model associated with the focus range calculation.

    autofocus : Autofocus
        An Autofocus instance used for autofocus operations.

    config_table : dict
        A dictionary defining the configuration for various stages of focus range
        calculation. It contains the following keys:
        - "signal": Configuration for the signal acquisition stage.
        - "data": Configuration for the data acquisition stage.
        - "node": Configuration related to node type and device.

    Methods:
    --------
    pre_func_signal():
        Prepare for the signal acquisition stage, setting up initial values and
        configurations.

    in_func_signal():
        Perform actions during the signal acquisition stage, such as autofocus
        measurements.

    end_func_signal():
        Finalize the signal acquisition stage and check if additional steps are needed.

    pre_func_data():
        Prepare for the data acquisition stage, if applicable.

    in_func_data(frame_ids=[]):
        Perform actions during the data acquisition stage, possibly for specific
        frame IDs.

    end_func_data():
        Finalize the data acquisition stage, if applicable.

    Notes:
    ------
    - This class is used to calculate the focus range of a microscope by utilizing
    autofocus measurements. It provides methods for different stages of the
    calculation process.

    - The `config_table` attribute is a dictionary that defines the configuration for
    each stage of the calculation process, including initialization, main execution,
    and finalization steps.

    - The autofocus measurements are performed using an instance of the `Autofocus`
    class, which is initialized with the same `model` object used for focus range
    calculation.

    - The focus range calculation involves signal acquisition and data acquisition
    stages, which are controlled using the provided methods.

    - The `CalculateFocusRange` class can be used to automate the process of
    determining the optimal focus range for microscopy experiments.
    """

    def __init__(self, model):
        self.model = model
        self.autofocus = Autofocus(model)
        self.config_table = {
            "signal": {
                "init": self.pre_func_signal,
                "main": self.in_func_signal,
                "end": self.end_func_signal,
            },
            "data": {
                "init": self.pre_func_data,
                "main": self.in_func_data,
                "end": self.end_func_data,
            },
            "node": {"node_type": "multi-step", "device_related": True},
        }

    def pre_func_signal(self):
        """Prepare for the signal acquisition stage.

        This method sets up initial values and configurations before the signal
        acquisition stage.

        Parameters:
        ----------
        None

        Returns:
        -------
        None
        """
        self.model.active_microscope.current_channel = 0
        self.model.active_microscope.prepare_next_channel()
        self.autofocus.pre_func_signal()
        self.autofocus_count = 0
        self.focus_start_pos = None
        self.focus_end_pos = None

        # get current z pos, calculate last z pos in a stack
        stage_pos = self.model.get_stage_position()
        self.current_z_pos = stage_pos["z_pos"]
        self.last_z_pos = self.current_z_pos + float(
            self.model.configuration["experiment"]["MicroscopeState"]["end_position"]
        )

    def in_func_signal(self):
        """Perform actions during the signal acquisition stage.

        This method is responsible for carrying out actions during the signal
        acquisition stage, such as performing autofocus measurements and calculating
        focus-related parameters.

        Parameters:
        ----------
        None

        Returns:
        -------
        None
        """
        if self.autofocus_count == 0:
            self.focus_start_pos = self.autofocus.in_func_signal()
        else:
            self.focus_end_pos = self.autofocus.in_func_signal()

            # calculate the slope and save it
            if self.focus_end_pos:
                microscope_state = self.model.configuration["experiment"][
                    "MicroscopeState"
                ]
                microscope_state["end_focus"] = (
                    float(microscope_state["start_focus"])
                    + self.focus_end_pos
                    - self.focus_start_pos
                )

    def end_func_signal(self):
        """
        Finalize the signal acquisition stage.

        This method finalizes the signal acquisition stage and checks if additional
        steps are needed based on the results of autofocus measurements.

        Parameters:
        ----------
        None

        Returns:
        -------
        bool
            A boolean value indicating whether additional steps are required.
        """
        r = self.autofocus.end_func_signal()
        if r:
            self.autofocus_count += 1
            if self.autofocus_count == 1:
                # move one z step
                # TODO: should the focus move at the same time?
                self.model.move_stage({"z_abs": self.last_z_pos}, wait_until_done=True)
                self.autofocus.pre_func_signal()
        return self.autofocus_count >= 2

    def pre_func_data(self):
        """
        Prepare for the data acquisition stage, if applicable.

        This method prepares for the data acquisition stage, which may involve
        setting up configurations or performing actions before data acquisition begins.

        Parameters:
        ----------
        None

        Returns:
        -------
        None
        """
        self.autofocus.pre_func_data()

    def in_func_data(self, frame_ids=[]):
        """
        Perform actions during the data acquisition stage, possibly for specific
        frame IDs.

        This method performs actions during the data acquisition stage, which may
        include data
        acquisition for specific frame IDs if provided.

        Parameters:
        ----------
        frame_ids : list, optional
            A list of frame IDs for which data acquisition should be performed.
            Default is an empty list.

        Returns:
        -------
        None
        """
        self.autofocus.in_func_data(frame_ids)

    def end_func_data(self):
        """
        Finalize the data acquisition stage, if applicable.

        This method finalizes the data acquisition stage, and it may involve
        additional actions or
        checks.

        Parameters:
        ----------
        None

        Returns:
        -------
        bool
            A boolean value indicating whether additional steps are required.
        """
        r = self.autofocus.end_func_data()
        if r:
            self.autofocus.pre_func_data()

        return r and self.autofocus_count >= 2
