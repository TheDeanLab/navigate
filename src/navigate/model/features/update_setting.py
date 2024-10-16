# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
import logging
from functools import reduce

# Third party imports

# Local application imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class ChangeResolution:
    """
    ChangeResolution class for modifying the resolution mode of a microscope.

    This class provides functionality to change the resolution mode of a microscope by
    reconfiguring the microscope settings and updating the active microscope.

    Notes:
    ------
    - This class is used to change the resolution mode of a microscope by updating the
    microscope settings and configuring the active microscope accordingly.

    - The `resolution_mode` parameter specifies the desired resolution mode, and the
    `zoom_value` parameter specifies the zoom value to be set. These parameters can
    be adjusted to modify the microscope's configuration.

    - The `ChangeResolution` class is typically used to adapt the microscope's settings
    for different imaging requirements during microscopy experiments.

    - The resolution change process involves reconfiguring the microscope, updating the
    active microscope instance, and resuming data acquisition.

    - The `config_table` attribute is used to define the configuration for the
    resolution change process, including signal acquisition and cleanup steps.
    """

    def __init__(self, model, resolution_mode="high", zoom_value="N/A"):
        """Initialize the ChangeResolution class.


        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for resolution mode changes.
        resolution_mode : str, optional
            The desired resolution mode to set for the microscope. Default is "high".
        zoom_value : str, optional
            The zoom value to set for the microscope. Default is "N/A".
        """
        #: MicroscopeModel: The microscope model associated with the resolution change.
        self.model = model

        #: dict: A dictionary defining the configuration for the resolution change
        self.config_table = {
            "signal": {"main": self.signal_func, "cleanup": self.cleanup},
            "node": {"device_related": True},
        }

        #: str: The desired resolution mode to set for the microscope.
        self.resolution_mode = resolution_mode

        #: str: The zoom value to set for the microscope.
        self.zoom_value = zoom_value

    def signal_func(self):
        """Perform actions to change the resolution mode and update the active
         microscope.

        This method carries out actions to change the resolution mode of the microscope
         by reconfiguring the microscope settings, updating the active microscope, and
         resuming data acquisition.

        Returns:
        -------
        bool
            A boolean value indicating the success of the resolution change process.
        """
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()
        # prepare new microscope
        self.model.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ] = self.resolution_mode
        self.model.configuration["experiment"]["MicroscopeState"][
            "zoom"
        ] = self.zoom_value
        self.model.change_resolution(self.resolution_mode)
        logger.debug(f"current resolution is {self.resolution_mode}")
        logger.debug(
            f"current active microscope is {self.model.active_microscope_name}"
        )
        # prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        # prepare channel
        self.model.active_microscope.prepare_next_channel()
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        """Perform cleanup actions if needed.

        This method is responsible for performing cleanup actions if required after the
        resolution change process.
        """
        self.model.resume_data_thread()


class SetCameraParameters:
    """
    SetCameraParameters class for modifying the parameters of a camera.

    This class provides functionality to update the parameters of a camera.

    Notes:
    ------
    - This class can set sensor_mode, readout_direction and rolling_shutter_with.

    - If the value of a parameter is None it doesn't update the parameter value.
    """

    def __init__(
        self,
        model,
        microscope_name=None,
        sensor_mode="Normal",
        readout_direction=None,
        rolling_shutter_width=None,
    ):
        """Initialize the ChangeResolution class.


        Parameters:
        ----------
        model : MicroscopeModel
            The microscope model object used for resolution mode changes.
        sensor_mode : str, optional
            The desired sensor mode to set for the camera. "Normal" or "Light-Sheet"
        readout_direction : str, optional
            The readout direction to set for the camera.
            "Top-to-Bottom", "Bottom-to-Top", "Bidirectional" or "Rev. Bidirectional"
        rolling_shutter_width : int, optional
            The number of pixels for the rolling shutter.
        """
        #: MicroscopeModel: The microscope model associated with the resolution change.
        self.model = model

        #: dict: A dictionary defining the configuration for the resolution change
        self.config_table = {
            "signal": {"main": self.signal_func, "cleanup": self.cleanup},
            "node": {"device_related": True},
        }
        #: str: Microscope name
        self.microscope_name = microscope_name

        #: str: The desired sensor mode to set for the camera.
        self.sensor_mode = sensor_mode

        #: str: The reading direction to set for the microscope.
        self.readout_direction = readout_direction

        #: int: The number of pixels for the rolling shutter.
        try:
            self.rolling_shutter_width = int(rolling_shutter_width)
        except (ValueError, TypeError):
            self.rolling_shutter_width = None

    def signal_func(self):
        """Perform actions to change the resolution mode and update the active
         microscope.

        This method carries out actions to change the resolution mode of the microscope
         by reconfiguring the microscope settings, updating the active microscope, and
         resuming data acquisition.

        Returns:
        -------
        bool
            A boolean value indicating the success of the resolution change process.
        """
        if (
            self.microscope_name is None
            or self.microscope_name
            not in self.model.configuration["configuration"]["microscopes"].keys()
        ):
            self.microscope_name = self.model.active_microscope_name
        update_flag = False
        update_sensor_mode = False
        camera_parameters = self.model.configuration["experiment"]["CameraParameters"][
            self.microscope_name
        ]
        camera_config = self.model.configuration["configuration"]["microscopes"][
            self.microscope_name
        ]["camera"]
        updated_value = [None] * 3
        if (
            self.sensor_mode in ["Normal", "Light-Sheet"]
            and self.sensor_mode != camera_parameters["sensor_mode"]
        ):
            update_flag = True
            update_sensor_mode = True
            camera_parameters["sensor_mode"] = self.sensor_mode
            updated_value[0] = self.sensor_mode
        if camera_parameters["sensor_mode"] == "Light-Sheet":
            if self.readout_direction in camera_config[
                "supported_readout_directions"
            ] and (
                update_sensor_mode
                or camera_parameters["readout_direction"] != self.readout_direction
            ):
                update_flag = True
                camera_parameters["readout_direction"] = self.readout_direction
                updated_value[1] = self.readout_direction
            if self.rolling_shutter_width and (
                update_sensor_mode
                or self.rolling_shutter_width != camera_parameters["number_of_pixels"]
            ):
                update_flag = True
                camera_parameters["number_of_pixels"] = self.rolling_shutter_width
                updated_value[2] = self.rolling_shutter_width

        if not update_flag:
            return True
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()
        # set parameters and prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        self.model.event_queue.put(("display_camera_parameters", updated_value))
        # prepare channel
        self.model.active_microscope.prepare_next_channel()
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        self.model.resume_data_thread()


class UpdateExperimentSetting:

    def __init__(self, model, experiment_parameters={}):
        self.model = model

        #: dict: A dictionary defining the configuration for the resolution change
        self.config_table = {
            "signal": {"main": self.signal_func, "cleanup": self.cleanup},
            "node": {"device_related": True},
        }

        self.experiment_parameters = experiment_parameters

    def signal_func(self):
        """Perform actions to change the resolution mode and update the active
         microscope.

        This method carries out actions to change the resolution mode of the microscope
         by reconfiguring the microscope settings, updating the active microscope, and
         resuming data acquisition.

        Returns:
        -------
        bool
            A boolean value indicating the success of the resolution change process.
        """
        if type(self.experiment_parameters) != dict:
            return False
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()

        # update experiment values
        for k, v in self.experiment_parameters.items():
            try:
                parameters = k.split(".")
                config_ref = reduce(lambda pre, n: f"{pre}['{n}']", parameters, "")
                exec(f"self.model.configuration['experiment']{config_ref} = {v}")
            except Exception as e:
                logger.error(f"*** parameter {k} failed to update to value {v}")
                logger.error(e)
        # set parameters and prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        # prepare channel
        self.model.active_microscope.prepare_next_channel()
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        self.model.resume_data_thread()
