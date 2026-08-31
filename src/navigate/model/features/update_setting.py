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

# Standard library imports
import logging
from functools import reduce
import time

# Third party imports

# Local application imports
from navigate.model.devices.configuration_schema import CollectionSpec, SettingSpec
from navigate.model.features.base import FeatureBase

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChangeResolution(FeatureBase):
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

    parameter_schema = {
        "resolution_mode": SettingSpec(
            str,
            default="high",
            label="Resolution",
            help_text="Microscope/resolution name to switch to.",
            required=True,
            dynamic_source="microscopes",
        ),
        "zoom_value": SettingSpec(
            str,
            default="N/A",
            label="Zoom",
            help_text="Zoom value to use after changing resolution.",
            required=True,
            dynamic_source="zoom_values",
            depends_on="resolution_mode",
        ),
    }

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
        # verify microscope name and zoom value
        if (
            self.resolution_mode
            not in self.model.configuration["configuration"]["microscopes"].keys()
        ):
            error_message = f"Can't change resolution: Microscope name {self.resolution_mode} isn't exist!"
            # logger.exception(error_message) doesn't work
            print(error_message)
            raise Exception(error_message)
        if (
            self.zoom_value
            not in self.model.configuration["configuration"]["microscopes"][
                self.resolution_mode
            ]["zoom"]["position"].keys()
        ):
            error_message = (
                f"Can't change resolution: Zoom value {self.zoom_value} isn't exist!"
            )
            # logger.exception(error_message) doesn't work
            print(error_message)
            raise Exception(error_message)
        # check the image size
        camera_config = self.model.configuration["experiment"]["CameraParameters"]
        if (
            camera_config[self.resolution_mode]["img_x_pixels"]
            != camera_config[self.model.active_microscope_name]["img_x_pixels"]
            or camera_config[self.resolution_mode]["img_y_pixels"]
            != camera_config[self.model.active_microscope_name]["img_y_pixels"]
        ):
            error_message = "Can't change resolution: Image sizes are different!"
            # logger.exception(error_message) doesn't work
            print(error_message)
            raise Exception(error_message)
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
        self.model.frame_id = 0
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


class SetCameraParameters(FeatureBase):
    """
    SetCameraParameters class for modifying the parameters of a camera.

    This class provides functionality to update the parameters of a camera.

    Notes:
    ------
    - This class can set sensor_mode, readout_direction and rolling_shutter_with.

    - If the value of a parameter is None it doesn't update the parameter value.
    """

    parameter_schema = {
        "microscope_name": SettingSpec(
            str,
            default=None,
            label="Microscope",
            help_text="Microscope name to update. Leave empty for the active microscope.",
            dynamic_source="microscopes",
        ),
        "sensor_mode": SettingSpec(
            str,
            default="Normal",
            label="Sensor Mode",
            help_text="Camera sensor mode.",
            choices=("Normal", "Light-Sheet"),
            required=True,
        ),
        "readout_direction": SettingSpec(
            str,
            default=None,
            label="Readout Direction",
            help_text="Readout direction for light-sheet sensor mode.",
            choices=(
                "Top-to-Bottom",
                "Bottom-to-Top",
                "Bidirectional",
                "Rev. Bidirectional",
            ),
        ),
        "rolling_shutter_width": SettingSpec(
            int,
            default=None,
            label="Rolling Shutter Width",
            help_text="Number of pixels used for rolling-shutter acquisition.",
            minimum=1,
            step=1,
        ),
    }

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
        updated_value = [None] * 4
        updated_value[0] = self.microscope_name
        if (
            self.sensor_mode in ["Normal", "Light-Sheet"]
            and self.sensor_mode != camera_parameters["sensor_mode"]
        ):
            update_flag = True
            update_sensor_mode = True
            camera_parameters["sensor_mode"] = self.sensor_mode
            updated_value[1] = self.sensor_mode
        if camera_parameters["sensor_mode"] == "Light-Sheet":
            if self.readout_direction in camera_config[
                "supported_readout_directions"
            ] and (
                update_sensor_mode
                or camera_parameters["readout_direction"] != self.readout_direction
            ):
                update_flag = True
                camera_parameters["readout_direction"] = self.readout_direction
                updated_value[2] = self.readout_direction
            if self.rolling_shutter_width and (
                update_sensor_mode
                or self.rolling_shutter_width != camera_parameters["number_of_pixels"]
            ):
                update_flag = True
                camera_parameters["number_of_pixels"] = self.rolling_shutter_width
                updated_value[3] = self.rolling_shutter_width

        if not update_flag or self.microscope_name != self.model.active_microscope_name:
            return True
        # pause data thread
        self.model.pause_data_thread()
        # end active microscope
        self.model.active_microscope.end_acquisition()
        # set parameters and prepare active microscope
        waveform_dict = self.model.active_microscope.prepare_acquisition()
        self.model.event_queue.put(("waveform", waveform_dict))
        self.model.event_queue.put(("display_camera_parameters", updated_value))
        self.model.frame_id = 0
        # prepare channel
        self.model.active_microscope.prepare_next_channel()
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        self.model.resume_data_thread()


class UpdateExperimentSetting(FeatureBase):

    description = "Update experiment values on the fly"
    parameter_schema = {
        "experiment_parameters": CollectionSpec(
            item_schema={
                "MicroscopeState.stack_cycling_mode": SettingSpec(
                    str,
                    default="per_stack",
                    label="Stack Cycling Mode",
                    help_text="How channels cycle through a z-stack.",
                    choices=("per_stack", "per_z"),
                    required=True,
                ),
                "MicroscopeState.start_position": SettingSpec(
                    float,
                    default=0,
                    label="Start Position",
                    help_text="Relative z-stack start position.",
                    step=0.1,
                ),
                "MicroscopeState.end_position": SettingSpec(
                    float,
                    default=0,
                    label="End Position",
                    help_text="Relative z-stack end position.",
                    step=0.1,
                ),
                "MicroscopeState.step_size": SettingSpec(
                    float,
                    default=0,
                    label="Step Size",
                    help_text="Distance between z planes.",
                    exclusive_minimum=0,
                    step=0.1,
                ),
                "MicroscopeState.number_z_steps": SettingSpec(
                    float,
                    default=1,
                    label="Number Z Steps",
                    help_text="Number of z planes in the stack.",
                    minimum=0,
                    step=1,
                ),
                "MicroscopeState.timepoints": SettingSpec(
                    int,
                    default=1,
                    label="Timepoints",
                    help_text="Number of timepoints to acquire.",
                    minimum=1,
                    step=1,
                ),
                "MicroscopeState.stack_pause": SettingSpec(
                    float,
                    default=0,
                    label="Stack Pause",
                    help_text="Pause between z-stack acquisitions.",
                    minimum=0,
                    step=0.1,
                ),
                "MicroscopeState.start_focus": SettingSpec(
                    float,
                    default=0,
                    label="Start Focus",
                    help_text="Relative remote-focus start position.",
                    step=0.1,
                ),
                "MicroscopeState.end_focus": SettingSpec(
                    float,
                    default=0,
                    label="End Focus",
                    help_text="Relative remote-focus end position.",
                    step=0.1,
                ),
                "MicroscopeState.channels": SettingSpec(
                    dict,
                    default={},
                    label="Channels",
                    help_text="Complete channel mapping for MicroscopeState.",
                ),
            },
            storage="single_mapping",
            label="Experiment Parameters",
            help_text="MicroscopeState values to update when this feature runs.",
            dynamic_source="microscope_state",
        ),
    }

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

        state = self.model.configuration["experiment"]["MicroscopeState"]
        pre_z_steps = state["number_z_steps"]
        pre_channels = sum(
            [v["is_selected"] is True for k, v in state["channels"].items()]
        )
        pre_timepoints = state["timepoints"]

        # update experiment values
        # check if any parameter about x, y, c, z, t changed
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
        self.model.frame_id = 0
        # prepare channel
        self.model.active_microscope.prepare_next_channel()
        # update image writer
        if self.model.image_writer:
            z_steps = state["number_z_steps"]
            channels = sum(
                [v["is_selected"] is True for k, v in state["channels"].items()]
            )
            timepoints = state["timepoints"]
            if (
                pre_z_steps != z_steps
                or pre_channels != channels
                or pre_timepoints != timepoints
            ):
                self.model.image_writer.initialize_saving(
                    sub_dir=time.strftime("%H%M%S")
                )
            try:
                self.model.image_writer.data_source.set_metadata_from_configuration_experiment(
                    self.model.configuration
                )
            except Exception as e:
                logger.exception(f"Update image writer metadata failed: {e}")
        # resume data thread
        self.model.resume_data_thread()
        return True

    def cleanup(self):
        self.model.resume_data_thread()
