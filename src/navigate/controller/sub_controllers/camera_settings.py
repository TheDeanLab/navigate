# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Third Party Imports

# Local Imports
from navigate.controller.sub_controllers.gui import GUIController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


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

        #: str: Solvent type
        self.solvent = "BABB"

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

        #: int: Trigger type - 1: Internal, 2: External, 3: Synchronous
        self.trigger_source = None

        #: int: Trigger active - 1: Edge, 2: Level, 3: Synchronous
        self.trigger_active = None

        #: int: Readout speed
        self.readout_speed = None

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
        self.mode_widgets["Sensor"].widget["values"] = ["Normal", "Light-Sheet"]
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
        self.mode_widgets["Sensor"].set(self.camera_setting_dict["sensor_mode"])
        self.update_sensor_mode()

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

        # Camera Framerate Info - 'exposure_time', 'readout_time',
        # 'framerate', 'frames_to_average'
        # Exposure time is currently for just the first active channel
        channels = microscope_state_dict["channels"]
        exposure_time = channels[list(channels.keys())[0]]["camera_exposure_time"]
        self.framerate_widgets["exposure_time"].set(exposure_time)
        self.framerate_widgets["frames_to_average"].set(
            self.camera_setting_dict["frames_to_average"]
        )


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
        self.camera_setting_dict["frames_to_average"] = self.framerate_widgets[
            "frames_to_average"
        ].get()

        binning = [
            int(x) if x != "" else 1
            for x in self.camera_setting_dict["binning"].split("x")
        ]
        img_width = x_pixels // binning[0]
        img_height = y_pixels // binning[1]

        self.camera_setting_dict["x_pixels"] = x_pixels
        self.camera_setting_dict["y_pixels"] = y_pixels
        self.camera_setting_dict["img_x_pixels"] = img_width
        self.camera_setting_dict["img_y_pixels"] = img_height
        self.camera_setting_dict["center_x"] = center_x
        self.camera_setting_dict["center_y"] = center_y

        self.roi_widgets["Width"].set(x_pixels)
        self.roi_widgets["Height"].set(y_pixels)
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
                self.camera_setting_dict[
                    "readout_direction"
                ] = self.camera_readout_directions[0]
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
        self.framerate_widgets["frames_to_average"].widget["state"] = state
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

        TODO: Should make sure that this is updated before we run the tiling wizard.
        Also can probably be done more elegantly in a configuration file and
        dictionary structure.
        """

        # pixel_size = self.default_pixel_size
        try:
            x_pixel = float(self.roi_widgets["Width"].get())
            y_pixel = float(self.roi_widgets["Height"].get())
        except ValueError:
            return

        microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
        zoom = microscope_state_dict["zoom"]
        # TODO: calculate fov_x and fov_y for additional microscopes
        if self.microscope_name:
            return
        microscope_name = microscope_state_dict["microscope_name"]
        pixel_size = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][microscope_name]["zoom"]["pixel_size"][zoom]

        physical_dimensions_x = x_pixel * pixel_size
        physical_dimensions_y = y_pixel * pixel_size

        self.roi_widgets["FOV_X"].set(physical_dimensions_x)
        self.roi_widgets["FOV_Y"].set(physical_dimensions_y)

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
        (
            self.default_width,
            self.default_height,
        ) = self.parent_controller.configuration_controller.camera_pixels
        self.trigger_source = camera_config_dict["trigger_source"]
        self.trigger_active = camera_config_dict["trigger_active"]
        self.readout_speed = camera_config_dict["readout_speed"]
        # framerate_widgets
        # self.framerate_widgets["exposure_time"].widget.min = camera_config_dict[
        #     "exposure_time_range"
        # ]["min"]
        # self.framerate_widgets["exposure_time"].widget.max = camera_config_dict[
        #     "exposure_time_range"
        # ]["max"]

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

    def update_camera_parameters_silent(self, value):
        """Update GUI camera parameters

        Parameters
        ----------
        value : tuple
            (sensor_mode, readout_direction, number_of_pixels)
        """
        sensor_mode, readout_direction, number_of_pixels = value
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
