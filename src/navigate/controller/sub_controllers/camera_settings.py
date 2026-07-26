# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging
import os
from typing import Optional

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.config.config import update_config_dict, get_navigate_path
from navigate.tools.file_functions import write_to_yaml
from navigate.controller.configuration_controller import ConfigurationController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AdvancedCameraSettingController:
    """Controller for the Advanced Camera Settings popup."""

    def __init__(
        self,
        popup: "AdvancedCameraSettingPopup",
        parent_controller: "Controller",
        *args,
        **kwargs,
    ) -> None:
        """Initialize the AdvancedCameraSettingController class.

        Parameters
        ----------
        popup : AdvancedCameraSettingPopup
            The popup window for advanced camera settings
        parent_controller : Controller
            The parent controller that manages this popup
        *args
            Variable length argument list
        **kwargs
            Arbitrary keyword arguments
        """

        # Initialize the parent controller
        self.parent_controller = parent_controller

        #: PopUp: Popup window for the camera settings.
        self.view = popup

        #: ConfigurationController: Controller for the local configuration.
        self.local_config_controller = ConfigurationController(
            self.parent_controller.configuration
        )

        # Populate the list of microscopes in the dropdown.
        self.view.microscope.set_values(self.local_config_controller.microscope_list)

        #: str: The current microscope name.
        self.current_microscope = self.local_config_controller.microscope_name

        # Set the current microscope in the dropdown.
        self.view.microscope.set(self.current_microscope)

        #: dict: Camera configuration dictionary for the current microscope.
        self.camera_dict = self.local_config_controller.microscope_config["camera"]

        #: event: Event for refreshing temperature button.
        self.refresh_temperature_event = None

        self.update_microscope(in_initialization=True)

        # Add a trace to the microscope dropdown to detect microscope changes.
        self.view.microscope.variable.trace_add("write", self.update_microscope)

        # Configure traces for closing the window or pressing escape.
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", lambda event: self.close_popup())

        # register event listeners
        self.parent_controller.register_event_listener(
            "camera_temperature", self.update_temperature
        )

        logger.debug("Advanced camera settings popup initialized.")

    def showup(self):
        """This function will let the popup window show in front."""
        self.view.popup.deiconify()

    def save_camera_settings(self) -> None:
        """Save the current camera settings to the configuration file."""

        # Update the camera dictionary in the main configuration.
        update_config_dict(
            manager=self.parent_controller.manager,
            parent_dict=self.parent_controller.configuration["configuration"][
                "microscopes"
            ][self.current_microscope],
            config_name="camera",
            new_config=self.camera_dict,
        )

        # Save the updated configuration to a YAML file.
        write_to_yaml(
            content_dict=self.parent_controller.configuration["configuration"],
            filename=os.path.join(get_navigate_path(), "config", "configuration.yaml"),
        )

        # Update the configuration controller with the new configuration.
        self.parent_controller.configuration_controller.update_configuration()

        # Update the camera view controller to apply the new flip flags immediately
        if hasattr(self.parent_controller, "camera_view_controller"):
            camera_config = self.parent_controller.configuration["configuration"][
                "microscopes"
            ][self.current_microscope]["camera"]
            self.parent_controller.camera_view_controller.flip_flags = {
                "x": camera_config.get("flip_x", False),
                "y": camera_config.get("flip_y", False),
            }
            logger.debug(
                f"Updated camera flip flags for {self.current_microscope}: "
                f"{self.parent_controller.camera_view_controller.flip_flags}"
            )

        # save to experiment
        self.parent_controller.configuration["experiment"]["CameraParameters"][
            self.current_microscope
        ]["trigger_source"] = self.view.inputs["trigger_source"].get()

        self.parent_controller.configuration["experiment"]["CameraParameters"][
            self.current_microscope
        ]["cooling"] = self.view.inputs["cooling"].get()

    def flip_axis(self, axis: str) -> None:
        """Flip the camera axis in the configuration.

        Parameters
        ----------
        axis : str
            The axis to flip, e.g., 'x' or 'y'.
        """
        # Update the loaded configuration.
        self.parent_controller.configuration["configuration"]["microscopes"][
            self.current_microscope
        ]["camera"][f"flip_{axis}"] = self.view.flip_flags[axis].get()

        # Update our local camera dictionary with the new flip flag.
        self.camera_dict[f"flip_{axis}"] = self.view.flip_flags[axis].get()
        logger.debug(
            f"Updating camera {axis} flip flag to {self.camera_dict[f'flip_{axis}']}..."
        )

    def set_cooling_state(self, *args) -> None:
        """Set the cooling state based on the dropdown selection."""
        cooling_state = self.view.inputs["cooling"].get()
        if self.local_config_controller.camera_config_dict.get("cooling", False):
            # set cooling parameter to the camera
            self.parent_controller.execute(
                "set_camera_cooling_state", self.current_microscope, cooling_state
            )
            # stop previous temperature refresh event
            if self.refresh_temperature_event is not None:
                self.view.popup.after_cancel(self.refresh_temperature_event)

            if cooling_state == "On":
                self.view.buttons["refresh_temperature"]["state"] = "disabled"
                # enable it after 10 seconds
                self.refresh_temperature_event = self.view.popup.after(
                    10000,
                    lambda: self.view.buttons["refresh_temperature"].config(
                        state="normal"
                    ),
                )
            else:
                self.view.buttons["refresh_temperature"]["state"] = "normal"
        else:
            cooling_state = "Off"
            self.view.inputs["cooling"].set("Off")
            self.view.buttons["refresh_temperature"]["state"] = "disabled"

        # set the cooling state in the experiment configuration for the same camera
        self.camera_setting_dict["cooling"] = cooling_state
        for microscope_name in self.parent_controller.configuration["configuration"][
            "microscopes"
        ].keys():
            if microscope_name == self.current_microscope:
                continue
            if self.local_config_controller.is_same_camera(microscope_name):
                self.parent_controller.configuration["experiment"]["CameraParameters"][
                    microscope_name
                ]["cooling"] = cooling_state

    def refresh_temperature(self) -> None:
        """Refresh the camera cooling temperature display."""
        self.parent_controller.execute(
            "get_camera_temperature", self.current_microscope
        )

    def update_temperature(self, temperature: float) -> None:
        """Update the temperature display in the popup.

        Parameters
        ----------
        temperature : float
            The current camera temperature.
        """
        if temperature is not None:
            self.view.variables["cooling_temperature"].set(f"{temperature:.1f}")
        else:
            self.view.variables["cooling_temperature"].set("N/A")

    def close_popup(self) -> None:
        """Close the popup window."""
        self.save_camera_settings()
        self.view.popup.destroy()

        if hasattr(self.parent_controller, "advanced_camera_setting_controller"):
            del self.parent_controller.advanced_camera_setting_controller

        logger.debug(
            "Advanced camera settings popup closed and sub-controller deleted."
        )

    def update_microscope(
        self, *args, in_initialization: Optional[bool] = False
    ) -> None:
        """Update the microscope configuration when the microscope is changed.

        Parameters
        ----------
        in_initialization : bool, optional
            If True, this method is called during initialization and does not
            save the previous camera settings.
        """
        # Save the configuration for the previous microscope before switching.
        if not in_initialization:
            self.save_camera_settings()

        self.parent_controller.execute(
            "stop_refresh_camera_temperature", self.current_microscope
        )

        # Get the current microscope from the dropdown.
        self.current_microscope = self.view.microscope.get()
        self.view.clear_view()

        # Update the local configuration controller with the new microscope.
        self.local_config_controller.change_microscope(
            microscope_name=self.current_microscope
        )

        # Update camera config dictionary
        self.camera_dict = self.local_config_controller.microscope_config["camera"]

        # Get the current flip flags for x and y axes
        current_flip_flags = {
            "x": self.camera_dict.get("flip_x", False),
            "y": self.camera_dict.get("flip_y", False),
        }

        # Initialize the view with the flip flags
        self.view.populate_view(current_flip_flags)

        # Reconfigure traces for the new widgets
        self._configure_widget_traces()

        # populate other camera settings if needed
        # Camera Trigger Source
        self.camera_setting_dict = self.parent_controller.configuration["experiment"][
            "CameraParameters"
        ][self.current_microscope]
        trigger_source = self.camera_setting_dict.get("trigger_source", "External")
        self.view.inputs["trigger_source"]["values"] = self.camera_dict.get(
            "supported_trigger_sources", ["External"]
        )
        if trigger_source not in self.view.inputs["trigger_source"]["values"]:
            trigger_source = self.view.inputs["trigger_source"]["values"][0]
        self.view.inputs["trigger_source"].set(trigger_source)

        # cooling settings
        self.view.inputs["cooling"]["values"] = ["On", "Off"]
        if self.camera_dict.get("cooling", False):
            cooling = self.camera_setting_dict.get("cooling", "Off")
            self.view.inputs["cooling"].set(cooling)
            self.view.inputs["cooling"]["state"] = "readonly"
        else:
            self.view.inputs["cooling"].set("Off")
            self.view.inputs["cooling"]["state"] = "disabled"

    def _configure_widget_traces(self) -> None:
        """Configure traces and commands for widgets after they're created."""
        # Configure the flip flags for each camera axis.
        for key, value in self.view.flip_flags.items():
            value.trace_add("write", lambda *args, k=key: self.flip_axis(k))

        # Save button trace.
        self.view.save_button.configure(command=self.save_camera_settings)

        self.view.inputs["cooling"].bind("<<ComboboxSelected>>", self.set_cooling_state)
        self.view.buttons["refresh_temperature"].configure(
            command=self.refresh_temperature
        )


class CameraSettingController(GUIController):
    """Controller for the camera settings."""

    def __init__(self, view, parent_controller=None, microscope_name=None):
        """Initialize the camera setting controller.

        Parameters
        ----------
        view : tkinter.Frame
            The view for the camera settings.
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller.
        """
        super().__init__(view, parent_controller)

        #: str: Camera name
        self.microscope_name = microscope_name

        #: bool: True if in initialization
        self.in_initialization = True

        #: str: Resolution value
        self.resolution_value = "1x"

        #: str: Mode value
        self.mode = "stop"

        # Getting Widgets/Buttons

        #: dict: Mode widgets
        self.mode_widgets = view.camera_mode.get_widgets()

        #: dict: Framerate widgets
        self.framerate_widgets = view.framerate_info.get_widgets()

        #: dict: ROI widgets
        self.roi_widgets = view.camera_roi.get_widgets()

        #: dict: ROI buttons
        self.roi_btns = view.camera_roi.get_buttons()

        # initialize

        #: int: Default pixel size
        self.default_pixel_size = None

        #: int: Default width
        #: int: Default height
        self.default_width, self.default_height = None, None

        #: int: Camera width step interval
        self.step_width = 4

        #: int: Camera height step interval
        self.step_height = 4

        #: int: Camera width minimum
        self.min_width = 4

        #: int: Camera height minimum
        self.min_height = 4
        self.initialize()

        # Event binding
        #: bool: True if pixel event id
        self.pixel_event_id = None
        self.mode_widgets["Sensor"].widget.bind(
            "<<ComboboxSelected>>", self.update_sensor_mode
        )
        self.mode_widgets["Pixels"].get_variable().trace_add(
            "write", self.update_number_of_pixels
        )
        self.roi_widgets["Width"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["Height"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["is_centered"].get_variable().trace_add(
            "write", self.update_fov
        )
        self.roi_widgets["Top_X"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["Top_Y"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["Bottom_X"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["Bottom_Y"].get_variable().trace_add("write", self.update_fov)

        for btn_name in self.roi_btns:
            self.roi_btns[btn_name].config(command=self.update_roi(btn_name))

    def initialize(self):
        """Sets widgets based on data given from main controller/config."""

        # Get Default Configuration Values
        camera_config_dict = (
            self.parent_controller.configuration_controller.camera_config_dict
        )
        if camera_config_dict is None:
            return

        self.update_camera_device_related_setting()

        # Camera Mode
        self.mode_widgets["Sensor"].widget["state"] = "readonly"
        self.mode_widgets["Sensor"].widget.selection_clear()

        # Readout Mode
        self.camera_readout_directions = camera_config_dict[
            "supported_readout_directions"
        ]
        self.mode_widgets["Readout"].widget["values"] = self.camera_readout_directions

        self.mode_widgets["Readout"].widget["state"] = "disabled"
        self.mode_widgets["Readout"].selection_clear()

        # Pixels
        self.mode_widgets["Pixels"].widget["state"] = "disabled"
        self.mode_widgets["Pixels"].set("")
        self.mode_widgets["Pixels"].widget.config(from_=1)  # min value
        self.mode_widgets["Pixels"].widget.config(
            to=self.default_height / 2
        )  # max value
        self.mode_widgets["Pixels"].widget.config(increment=1)  # step value

        self.framerate_widgets["exposure_time"].widget["state"] = "disabled"
        self.framerate_widgets["readout_time"].widget["state"] = "disabled"
        self.framerate_widgets["max_framerate"].widget["state"] = "disabled"

        # Set range value
        self.roi_widgets["Width"].widget.config(from_=2)
        self.roi_widgets["Width"].widget.config(increment=2)
        self.roi_widgets["Height"].widget.config(from_=2)
        self.roi_widgets["Height"].widget.config(increment=2)

        # set binning options
        self.roi_widgets["Binning"].widget["values"] = [
            "{}x{}".format(i, i) for i in [1, 2, 4]
        ]
        self.roi_widgets["Binning"].widget["state"] = "readonly"

        # FOV
        self.roi_widgets["FOV_X"].widget["state"] = "disabled"
        self.roi_widgets["FOV_Y"].widget["state"] = "disabled"

    def populate_experiment_values(self):
        """Sets values in View according to the experiment yaml file.

        Experiment yaml filed passed by controller.
        """
        self.in_initialization = True

        # Retrieve settings.

        # Microscope state dictionary
        microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        microscope_name = (
            self.microscope_name
            if self.microscope_name
            else microscope_state_dict["microscope_name"]
        )
        #: dict: Camera setting dictionary
        self.camera_setting_dict = self.parent_controller.configuration["experiment"][
            "CameraParameters"
        ][microscope_name]

        # Readout Settings
        self.update_sensor_mode(self.camera_setting_dict["sensor_mode"])

        # ROI Settings
        if self.camera_setting_dict.get("is_centered", True):
            self.camera_setting_dict["is_centered"] = True
            self.roi_widgets["is_centered"].set(True)
        else:
            self.roi_widgets["is_centered"].set(False)
        self.roi_widgets["Top_X"].set(self.camera_setting_dict.get("top_x", 0))
        self.roi_widgets["Top_Y"].set(self.camera_setting_dict.get("top_y", 0))
        self.roi_widgets["Bottom_X"].set(
            self.camera_setting_dict.get("bottom_x", self.default_width)
        )
        self.roi_widgets["Bottom_Y"].set(
            self.camera_setting_dict.get("bottom_y", self.default_height)
        )
        if self.camera_setting_dict["x_pixels"] > self.default_width:
            self.camera_setting_dict["x_pixels"] = self.default_width
        if self.camera_setting_dict["y_pixels"] > self.default_height:
            self.camera_setting_dict["y_pixels"] = self.default_height
        self.roi_widgets["Width"].set(self.camera_setting_dict["x_pixels"])
        self.roi_widgets["Height"].set(self.camera_setting_dict["y_pixels"])

        # Binning settings
        self.roi_widgets["Binning"].set(self.camera_setting_dict["binning"])

        # Camera Framerate Info - 'exposure_time', 'readout_time', 'framerate'
        # Exposure time is currently for just the first active channel
        channels = microscope_state_dict["channels"]
        exposure_time = channels[list(channels.keys())[0]]["camera_exposure_time"]
        self.framerate_widgets["exposure_time"].set(exposure_time)

        # after initialization
        self.in_initialization = False

        self.update_fov()

    def update_experiment_values(self, *args):
        """Updates experiment yaml file according to the values in View.

        Update the dictionary so that it can be combined with all the other
        sub-controllers, and then sent to the model.

        Args:
            *args: Variable length argument list.
        """
        # Camera Operation Mode
        self.camera_setting_dict["sensor_mode"] = self.mode_widgets["Sensor"].get()
        if self.camera_setting_dict["sensor_mode"] == "Light-Sheet":
            self.camera_setting_dict["readout_direction"] = self.mode_widgets[
                "Readout"
            ].get()
            self.camera_setting_dict["number_of_pixels"] = self.mode_widgets[
                "Pixels"
            ].get()
            # light-sheet doesn't support binning
            self.roi_widgets["Binning"].set("1x1")

        # Camera Binning
        self.camera_setting_dict["binning"] = self.roi_widgets["Binning"].get()

        # Camera FOV Size.
        if not self.roi_widgets["is_centered"].get():
            top_x = self.roi_widgets["Top_X"].get()
            top_y = self.roi_widgets["Top_Y"].get()
            bottom_x = self.roi_widgets["Bottom_X"].get()
            bottom_y = self.roi_widgets["Bottom_Y"].get()
            if (
                top_x % self.step_width
                or top_y % self.step_height
                or bottom_x % self.step_width
                or bottom_y % self.step_height
                or top_x >= bottom_x
                or top_y >= bottom_y
                or bottom_x > self.default_width
                or bottom_y > self.default_height
            ):
                warning_message = (
                    "The camera ROI Boundary isn't correct, please set a valid value!"
                    + f"The values of X must be divisible by {self.step_width}!"
                    + f"The values of Y must be divisible by {self.step_height}!"
                )
                return warning_message

            center_x = (bottom_x + top_x) // 2
            center_y = (bottom_y + top_y) // 2
        else:
            center_x = self.default_width // 2
            center_y = self.default_height // 2

        x_pixel = self.roi_widgets["Width"].get()
        y_pixel = self.roi_widgets["Height"].get()

        # Round to nearest step
        x_pixels = int(x_pixel // self.step_width) * self.step_width
        y_pixels = int(y_pixel // self.step_height) * self.step_height

        if x_pixels < self.min_width:
            x_pixels = self.min_width
        if y_pixels < self.min_height:
            y_pixels = self.min_height

        self.camera_setting_dict["pixel_size"] = self.default_pixel_size

        binning = [
            int(x) if x != "" else 1
            for x in self.camera_setting_dict["binning"].split("x")
        ]
        img_width = x_pixels // binning[0]
        img_height = y_pixels // binning[1]
        img_width = img_width - img_width % self.step_width
        img_height = img_height - img_height % self.step_height

        x_pixels = img_width * binning[0]
        y_pixels = img_height * binning[1]

        self.camera_setting_dict["x_pixels"] = x_pixels
        self.camera_setting_dict["y_pixels"] = y_pixels
        self.camera_setting_dict["img_x_pixels"] = img_width
        self.camera_setting_dict["img_y_pixels"] = img_height
        self.camera_setting_dict["center_x"] = center_x
        self.camera_setting_dict["center_y"] = center_y

        self.roi_widgets["Width"].set(x_pixels)
        self.roi_widgets["Height"].set(y_pixels)
        if self.calculate_physical_dimensions() is False:
            return (
                "Image physical dimensions could not be calculated from the "
                "current microscope configuration.\n\n"
                "Please verify that the zoom value and pixel size are "
                "configured correctly in the configuration YAML."
            )
        self.camera_setting_dict["fov_x"] = self.roi_widgets["FOV_X"].get()
        self.camera_setting_dict["fov_y"] = self.roi_widgets["FOV_Y"].get()

        return ""

    def update_sensor_mode(self, *args):
        """Updates the camera sensor mode.

        Updates text in readout widget based on what sensor mode is selected
        If we are in the Light Sheet mode, then we want the camera
        self.model['CameraParameters']['sensor_mode']) == 12

        If we are in thef normal mode, then we want the camera
        self.model['CameraParameters']['sensor_mode']) == 1

        Should initialize from the configuration file to the default version

        Parameters
        ----------
        *args : Variable length argument list.
             usually args[0] is tkinter.Event or a str
        """
        # Camera Mode
        if len(args) > 0 and type(args[0]) is str:
            sensor_value = args[0]
            if sensor_value not in self.mode_widgets["Sensor"].widget["values"]:
                sensor_value = self.mode_widgets["Sensor"].widget["values"][0]
            self.mode_widgets["Sensor"].widget.set(sensor_value)
        else:
            sensor_value = self.mode_widgets["Sensor"].widget.get()
        if sensor_value == "Normal":
            self.mode_widgets["Readout"].set(" ")
            self.mode_widgets["Readout"].widget["state"] = "disabled"
            self.mode_widgets["Pixels"].widget["state"] = "disabled"
            self.mode_widgets["Pixels"].widget.set("")
            self.mode_widgets["Sensor"].widget.selection_clear()

            self.show_verbose_info("Normal Camera Readout Mode")

        elif sensor_value == "Light-Sheet":
            # readout-direction from experiment
            if (
                self.camera_setting_dict["readout_direction"]
                not in self.camera_readout_directions
            ):
                self.camera_setting_dict["readout_direction"] = (
                    self.camera_readout_directions[0]
                )
            self.mode_widgets["Readout"].widget.set(
                self.camera_setting_dict["readout_direction"]
            )
            self.mode_widgets["Readout"].widget["state"] = "readonly"
            self.mode_widgets["Pixels"].set(
                self.camera_setting_dict["number_of_pixels"]
            )
            self.mode_widgets["Pixels"].widget.trigger_focusout_validation()
            self.mode_widgets["Pixels"].widget["state"] = "normal"

            self.show_verbose_info("Light Sheet Camera Readout Mode")

        # calculate readout time
        self.update_readout_time()

    def update_exposure_time(self, exposure_time):
        """When camera exposure time is changed, recalculate readout time

        Parameters
        ----------
        exposure_time : float
            exposure time in seconds
        """
        self.framerate_widgets["exposure_time"].set(exposure_time)

    def update_roi(self, btn_name):
        """Update ROI width and height.

        Parameters
        ----------
        btn_name : roi button name
            width of roi in pixels: "All", 1600, 1024, 512
        """

        def handler(*args):
            if btn_name == "All":
                width = self.default_width
                height = self.default_height
            else:
                width = float(btn_name)
                height = width
                if width > self.default_width:
                    width = self.default_width
                if height > self.default_height:
                    height = self.default_height
            self.roi_widgets["is_centered"].set(True)
            self.roi_widgets["Width"].set(width)
            self.roi_widgets["Height"].set(height)
            self.show_verbose_info("ROI width and height are changed to", width, height)

        return handler

    def update_fov(self, *args):
        """Recalculate fov and update the widgets: FOV_X and FOV_Y

        Parameters
        ----------
        *args : Variable length argument list.
        """
        if self.in_initialization:
            return

        self.set_roi_widgets_state()
        self.camera_setting_dict["is_centered"] = self.roi_widgets["is_centered"].get()
        if not self.roi_widgets["is_centered"].get():
            error_flag = False
            for widget_name in ["Top_X", "Top_Y", "Bottom_X", "Bottom_Y"]:
                step_value = (
                    self.step_width if widget_name.endswith("X") else self.step_height
                )
                max_value = (
                    self.default_width
                    if widget_name.endswith("X")
                    else self.default_height
                )
                try:
                    value = int(self.roi_widgets[widget_name].get())
                except (TypeError, ValueError):
                    return
                if value < 0 or value > max_value or value % step_value:
                    self.roi_widgets[widget_name].widget._focusout_invalid()
                    error_flag = True
            if error_flag:
                return
            width = self.roi_widgets["Bottom_X"].get() - self.roi_widgets["Top_X"].get()
            height = (
                self.roi_widgets["Bottom_Y"].get() - self.roi_widgets["Top_Y"].get()
            )
            if width <= 0:
                self.roi_widgets["Top_X"].widget._focusout_invalid()
                self.roi_widgets["Bottom_X"].widget._focusout_invalid()
                error_flag = True
            if height <= 0:
                self.roi_widgets["Top_Y"].widget._focusout_invalid()
                self.roi_widgets["Bottom_Y"].widget._focusout_invalid()
                error_flag = True
            if error_flag:
                return
            # reset widgets
            for widget_name in ["Top_X", "Top_Y", "Bottom_X", "Bottom_Y"]:
                self.roi_widgets[widget_name].widget._toggle_error(False)

            self.camera_setting_dict["top_x"] = self.roi_widgets["Top_X"].get()
            self.camera_setting_dict["bottom_x"] = self.roi_widgets["Bottom_X"].get()
            self.camera_setting_dict["top_y"] = self.roi_widgets["Top_Y"].get()
            self.camera_setting_dict["bottom_y"] = self.roi_widgets["Bottom_Y"].get()
            self.camera_setting_dict["x_pixels"] = width
            self.camera_setting_dict["y_pixels"] = height
            self.roi_widgets["Width"].widget.set(width)
            self.roi_widgets["Height"].widget.set(height)
        self.calculate_physical_dimensions()

    def set_mode(self, mode):
        """Set widget configuration based upon imaging mode.

        This function will change state of widgets according to different mode
        'stop' mode will let the editable widget be 'normal'
        in 'live' and 'stack' mode, some widgets are disabled

        Parameters
        ----------
        mode : str
            One of 'live', 'z-stack', 'stop', 'single'
        """
        self.mode = mode
        state = "disabled" if mode != "stop" else "normal"
        state_readonly = "disabled" if mode != "stop" else "readonly"
        self.mode_widgets["Sensor"].widget["state"] = state_readonly
        if self.mode_widgets["Sensor"].get() == "Light-Sheet":
            self.mode_widgets["Readout"].widget["state"] = state_readonly
            self.mode_widgets["Pixels"].widget["state"] = (
                "normal" if mode == "live" else state
            )
        else:
            self.mode_widgets["Readout"].widget["state"] = "disabled"
            self.mode_widgets["Pixels"].widget["state"] = "disabled"
        if mode != "stop":
            self.roi_widgets["Width"].widget["state"] = "disabled"
            self.roi_widgets["Height"].widget["state"] = "disabled"
            for widget_name in ["Top_X", "Top_Y", "Bottom_X", "Bottom_Y"]:
                self.roi_widgets[widget_name].widget["state"] = "disabled"
        else:
            self.set_roi_widgets_state()
        self.roi_widgets["Binning"].widget["state"] = state_readonly
        for btn_name in self.roi_btns:
            self.roi_btns[btn_name]["state"] = state

    def set_roi_widgets_state(self):
        """Set the status of ROI widgets"""

        roi_boundary_state = (
            "disabled" if self.roi_widgets["is_centered"].get() else "normal"
        )
        size_state = "normal" if roi_boundary_state == "disabled" else "disabled"
        for widget_name in ["Top_X", "Top_Y", "Bottom_X", "Bottom_Y"]:
            self.roi_widgets[widget_name].widget["state"] = roi_boundary_state
        self.roi_widgets["Width"].widget["state"] = size_state
        self.roi_widgets["Height"].widget["state"] = size_state

    def calculate_physical_dimensions(self):
        """Calculate size of the FOV in microns.

        Calculates the size of the field of view according to the magnification of the
        system, the physical size of the pixel, and the number of pixels.
        update FOV_X and FOV_Y

        Returns
        -------
        bool
            True if the calculation is successful.
        """
        try:
            x_pixel = float(self.roi_widgets["Width"].get())
            y_pixel = float(self.roi_widgets["Height"].get())
        except ValueError:
            return False

        microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        zoom = microscope_state_dict["zoom"]
        if self.microscope_name:
            # Set the zoom value and save the pixel size to the camera settings when enabling the additional microscope for acquisition.
            try:
                pixel_size = float(self.camera_setting_dict["pixel_size"])
            except (KeyError, TypeError, ValueError):
                logger.warning(
                    f"Invalid pixel size configured for microscope "
                    f"'{self.microscope_name}' at zoom '{zoom}' in the "
                    "configuration YAML."
                )
                return False

        else:
            microscope_name = microscope_state_dict["microscope_name"]
            try:
                pixel_size = float(
                    self.parent_controller.configuration["configuration"][
                        "microscopes"
                    ][microscope_name]["zoom"]["pixel_size"][zoom]
                )
            except KeyError:
                logger.warning(
                    f"No pixel size is configured for microscope "
                    f"'{microscope_name}' at zoom '{zoom}' in the configuration YAML."
                )
                return False
            except (TypeError, ValueError):
                logger.warning(
                    f"Invalid pixel size configured for microscope "
                    f"'{microscope_name}' at zoom '{zoom}' in the "
                    "configuration YAML."
                )
                return False

        physical_dimensions_x = x_pixel * pixel_size
        physical_dimensions_y = y_pixel * pixel_size

        # Updating these widget values automatically syncs them with the Tiling Wizard.
        self.roi_widgets["FOV_X"].set(physical_dimensions_x)
        self.roi_widgets["FOV_Y"].set(physical_dimensions_y)

        return True

    def update_readout_time(self):
        """Update camera readout time.


        TODO: Highly specific to Hamamatsu Orca Flash 4.0.
        Should find a way to pass this from the camera to here.
        This should be moved to the camera device/API,
        ideally by calling a command from the camera.
        """
        sensor_mode = self.mode_widgets["Sensor"].get()

        if sensor_mode == "Normal":
            readout_time = self.camera_setting_dict["readout_time"]

        elif sensor_mode == "Light-Sheet":
            #  Progressive sensor mode operation
            readout_time = 0

        # return readout_time
        self.framerate_widgets["readout_time"].set(readout_time)

    def update_number_of_pixels(self, *args):
        """Update the number of pixels in the ROI.

        In live mode, we should let the device know the number of pixels changed.

        Parameters
        ----------
        *args : tuple
            Unused

        """
        if self.mode != "live":
            return

        if self.pixel_event_id:
            self.view.after_cancel(self.pixel_event_id)

        pixels = self.mode_widgets["Pixels"].get()
        if pixels == "":
            return

        self.camera_setting_dict["number_of_pixels"] = int(pixels)
        # tell central controller to update model
        self.pixel_event_id = self.view.after(
            500,
            lambda: self.parent_controller.execute(
                "update_setting", "number_of_pixels"
            ),
        )

    def update_camera_device_related_setting(self):
        """Update caramera device related parameters.

        This function will update default width and height according to microscope name.

        """
        if self.microscope_name is None:
            camera_config_dict = (
                self.parent_controller.configuration_controller.camera_config_dict
            )
        else:
            camera_config_dict = self.parent_controller.configuration["configuration"][
                "microscopes"
            ][self.microscope_name]["camera"]

        if camera_config_dict is None:
            return

        self.step_width = camera_config_dict.get("x_pixels_step", 4)
        self.step_height = camera_config_dict.get("y_pixels_step", 4)
        self.min_width = camera_config_dict.get("x_pixels_min", 4)
        self.min_height = camera_config_dict.get("y_pixels_min", 4)

        self.default_pixel_size = camera_config_dict["pixel_size_in_microns"]
        self.default_height = camera_config_dict["y_pixels"]
        self.default_width = camera_config_dict["x_pixels"]

        # roi max width and height
        self.roi_widgets["Width"].widget.config(to=self.default_width)
        self.roi_widgets["Height"].widget.config(to=self.default_height)
        if self.roi_widgets["Width"].get() > self.default_width:
            self.roi_widgets["Width"].set(self.default_width)
        if self.roi_widgets["Height"].get() > self.default_height:
            self.roi_widgets["Height"].set(self.default_height)

        self.roi_widgets["Bottom_X"].widget.config(to=self.default_width)
        self.roi_widgets["Bottom_Y"].widget.config(to=self.default_height)

        # update camera setting_dict
        microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        microscope_name = (
            self.microscope_name
            if self.microscope_name
            else microscope_state_dict["microscope_name"]
        )
        self.camera_setting_dict = self.parent_controller.configuration["experiment"][
            "CameraParameters"
        ][microscope_name]

        self.mode_widgets["Sensor"].widget["values"] = camera_config_dict.get(
            "supported_sensor_modes", ["Normal"]
        )
        if (
            self.mode_widgets["Sensor"].get()
            not in self.mode_widgets["Sensor"].widget["values"]
        ):
            self.update_sensor_mode(self.mode_widgets["Sensor"].widget["values"][0])

    def update_camera_parameters_silent(self, value):
        """Update GUI camera parameters

        Parameters
        ----------
        value : tuple
            (sensor_mode, readout_direction, number_of_pixels)
        """
        microscope_name, sensor_mode, readout_direction, number_of_pixels = value
        if (
            self.microscope_name is None
            and microscope_name
            != self.parent_controller.configuration_controller.microscope_name
        ):
            return
        if self.microscope_name is not None and microscope_name != self.microscope_name:
            return
        if sensor_mode:
            self.update_sensor_mode(sensor_mode)
        if readout_direction:
            self.mode_widgets["Readout"].set(readout_direction)
        if number_of_pixels:
            self.mode_widgets["Pixels"].set(number_of_pixels)

    @property
    def custom_events(self):
        """dict: Custom events for this controller"""
        return {"display_camera_parameters": self.update_camera_parameters_silent}
