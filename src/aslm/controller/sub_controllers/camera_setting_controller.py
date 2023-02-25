# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

from aslm.controller.sub_controllers.gui_controller import GUIController

import logging
from pathlib import Path

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class CameraSettingController(GUIController):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)

        # default values
        self.in_initialization = True
        self.resolution_value = "1x"
        self.number_of_pixels = 10
        self.mode = "stop"
        self.solvent = "BABB"

        # Getting Widgets/Buttons
        self.mode_widgets = view.camera_mode.get_widgets()
        self.framerate_widgets = view.framerate_info.get_widgets()
        self.roi_widgets = view.camera_roi.get_widgets()
        self.roi_btns = view.camera_roi.get_buttons()

        # initialize
        self.default_pixel_size = None
        self.default_width, self.default_height = None, None
        self.trigger_source = None
        self.trigger_active = None
        self.readout_speed = None
        self.initialize()

        # Event binding
        self.pixel_event_id = None
        self.mode_widgets["Sensor"].widget.bind(
            "<<ComboboxSelected>>", self.update_sensor_mode
        )
        self.mode_widgets["Pixels"].get_variable().trace_add(
            "write", self.update_number_of_pixels
        )
        self.roi_widgets["Width"].get_variable().trace_add("write", self.update_fov)
        self.roi_widgets["Height"].get_variable().trace_add("write", self.update_fov)

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

        self.default_pixel_size = camera_config_dict["pixel_size_in_microns"]
        (
            self.default_width,
            self.default_height,
        ) = self.parent_controller.configuration_controller.camera_pixels
        self.trigger_source = camera_config_dict["trigger_source"]
        self.trigger_active = camera_config_dict["trigger_active"]
        self.readout_speed = camera_config_dict["readout_speed"]

        # Camera Mode
        self.mode_widgets["Sensor"].widget["values"] = ["Normal", "Light-Sheet"]
        self.mode_widgets["Sensor"].widget["state"] = "readonly"
        self.mode_widgets["Sensor"].widget.set(camera_config_dict["sensor_mode"])
        self.mode_widgets["Sensor"].widget.selection_clear()

        # Readout Mode
        self.mode_widgets["Readout"].widget["values"] = [
            " ",
            "Top-to-Bottom",
            "Bottom-to-Top",
        ]
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

        # framerate_widgets
        self.framerate_widgets["exposure_time"].widget.min = camera_config_dict[
            "exposure_time_range"
        ]["min"]
        self.framerate_widgets["exposure_time"].widget.max = camera_config_dict[
            "exposure_time_range"
        ]["max"]
        self.framerate_widgets["exposure_time"].set(camera_config_dict["exposure_time"])
        self.framerate_widgets["exposure_time"].widget["state"] = "disabled"
        self.framerate_widgets["readout_time"].widget["state"] = "disabled"
        self.framerate_widgets["max_framerate"].widget["state"] = "disabled"

        # Set range value
        self.roi_widgets["Width"].widget.config(to=self.default_width)
        self.roi_widgets["Width"].widget.config(from_=2)
        self.roi_widgets["Width"].widget.config(increment=2)
        self.roi_widgets["Height"].widget.config(to=self.default_height)
        self.roi_widgets["Height"].widget.config(from_=2)
        self.roi_widgets["Height"].widget.config(increment=2)

        # set binning options
        self.roi_widgets["Binning"].widget["values"] = [
            "{}x{}".format(i, i) for i in range(1, 5)
        ]
        self.roi_widgets["Binning"].widget["state"] = "readonly"

        # Center position
        self.roi_widgets["Center_X"].set(self.default_width / 2)
        self.roi_widgets["Center_Y"].set(self.default_height / 2)

        # This should not be edited for now
        # Center position
        self.roi_widgets["Center_X"].widget["state"] = "disabled"
        self.roi_widgets["Center_Y"].widget["state"] = "disabled"

        # FOV
        self.roi_widgets["FOV_X"].widget["state"] = "disabled"
        self.roi_widgets["FOV_Y"].widget["state"] = "disabled"

    def populate_experiment_values(self):
        """Sets values in View according to the experiment yaml file.

        Experiment yaml filed passed by controller.
        """
        self.in_initialization = True

        # Retrieve settings.
        self.camera_setting_dict = self.parent_controller.configuration["experiment"][
            "CameraParameters"
        ]
        self.microscope_state_dict = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]

        # Readout Settings
        self.mode_widgets["Sensor"].set(self.camera_setting_dict["sensor_mode"])
        if self.camera_setting_dict["sensor_mode"] == "Normal":
            self.mode_widgets["Readout"].set("")
            self.mode_widgets["Pixels"].set("")
        else:
            self.mode_widgets["Readout"].set(
                self.camera_setting_dict["readout_direction"]
            )
            self.mode_widgets["Pixels"].set(
                self.camera_setting_dict["number_of_pixels"]
            )

        # ROI Settings
        self.roi_widgets["Width"].set(self.camera_setting_dict["x_pixels"])
        self.roi_widgets["Height"].set(self.camera_setting_dict["y_pixels"])

        # Binning settins
        self.roi_widgets["Binning"].set(self.camera_setting_dict["binning"])

        # Camera Framerate Info - 'exposure_time', 'readout_time', 'framerate', 'frames_to_average'
        # Exposure time is currently for just the first active channel
        channels = self.microscope_state_dict["channels"]
        exposure_time = channels[list(channels.keys())[0]]["camera_exposure_time"]
        self.framerate_widgets["exposure_time"].set(exposure_time)
        self.framerate_widgets["frames_to_average"].set(
            self.camera_setting_dict["frames_to_average"]
        )

        # Physical Dimensions
        self.calculate_physical_dimensions()
        # readout time
        self.calculate_readout_time()

        # after initialization
        self.in_initialization = False

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

        # Camera Binning
        self.camera_setting_dict["binning"] = self.roi_widgets["Binning"].get()

        # Camera FOV Size.
        self.camera_setting_dict["x_pixels"] = self.roi_widgets["Width"].get()
        self.camera_setting_dict["y_pixels"] = self.roi_widgets["Height"].get()

        self.camera_setting_dict["number_of_cameras"] = 1
        self.camera_setting_dict["pixel_size"] = self.default_pixel_size
        self.camera_setting_dict["frames_to_average"] = self.framerate_widgets[
            "frames_to_average"
        ].get()

        return True

    def update_sensor_mode(self, *args):
        """Updates the camera sensor mode.

        Updates text in readout widget based on what sensor mode is selected
        If we are in the Light Sheet mode, then we want the camera
        self.model['CameraParameters']['sensor_mode']) == 12

        If we are in the normal mode, then we want the camera
        self.model['CameraParameters']['sensor_mode']) == 1

        Should initialize from the configuration file to the default version

        Parameters
        ----------
        *args : Variable length argument list.
        """
        # Camera Mode
        sensor_value = self.mode_widgets["Sensor"].widget.get()
        if sensor_value == "Normal":
            self.mode_widgets["Readout"].set(" ")
            self.mode_widgets["Readout"].widget["state"] = "disabled"
            self.mode_widgets["Pixels"].widget["state"] = "disabled"
            self.mode_widgets["Pixels"].widget.set("")
            self.mode_widgets["Sensor"].widget.selection_clear()

            self.show_verbose_info("Normal Camera Readout Mode")

        elif sensor_value == "Light-Sheet":
            self.mode_widgets["Readout"].widget.set("Top-to-Bottom")
            self.mode_widgets["Readout"].widget["state"] = "readonly"
            self.mode_widgets["Pixels"].set(
                self.number_of_pixels
            )  # Default to 10 pixels
            self.mode_widgets["Pixels"].widget.trigger_focusout_validation()
            self.mode_widgets["Pixels"].widget["state"] = "normal"

            self.show_verbose_info("Light Sheet Camera Readout Mode")

        # calculate readout time
        self.calculate_readout_time()

    def update_exposure_time(self, exposure_time):
        """When camera exposure time is changed, recalculate readout time

        Parameters
        ----------
        exposure_time : float
            exposure time in seconds
        """
        self.framerate_widgets["exposure_time"].set(exposure_time)
        self.calculate_readout_time()

    def update_roi(self, width):
        """Update ROI width and height.

        Parameters
        ----------
        width : int
            width of roi in pixels
        """
        width = self.default_width if width == "All" else float(width)

        def handler(*args):
            self.roi_widgets["Width"].set(width)
            self.roi_widgets["Height"].set(width)
            self.show_verbose_info("ROI width and height are changed to", width, width)

        return handler

    def update_fov(self, *args):
        """Recalculate fov and update the widgets: FOV_X and FOV_Y

        Parameters
        ----------
        *args : Variable length argument list.
        """
        if self.in_initialization:
            return
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
        self.roi_widgets["Width"].widget["state"] = state
        self.roi_widgets["Height"].widget["state"] = state
        self.roi_widgets["Binning"].widget["state"] = state_readonly
        for btn_name in self.roi_btns:
            self.roi_btns[btn_name]["state"] = state

    def calculate_physical_dimensions(self):
        """Calculate size of the FOV in microns.

        Calculates the size of the field of view according to the magnification of the system,
        the physical size of the pixel, and the number of pixels.
        update FOV_X and FOV_Y

        TODO: Should make sure that this is updated before we run the tiling wizard.  Also can probably be done more
        elegantly in a configuration file and dictionary structure.
        """
        # magnification == 'N/A' is a proxy for resolution == 'high'
        if (
            self.parent_controller.configuration["experiment"]["MicroscopeState"][
                "zoom"
            ]
            == "N/A"
        ):
            # 54-12-8 - EFLobj = 12.19 mm / RI
            tube_lens_focal_length = 300
            extended_focal_length = 12.19
            if self.solvent == "BABB":
                refractive_index = 1.56
            elif self.solvent == "Water":
                refractive_index = 1.333
            elif self.solvent == "CUBIC":
                refractive_index = 1.48
            elif self.solvent == "CLARITY":
                refractive_index = 1.45
            elif self.solvent == "uDISCO":
                refractive_index = 1.56
            elif self.solvent == "eFLASH":
                refractive_index = 1.458
            else:
                # Default unknown value - Specified as mid-range.
                refractive_index = 1.45

            multi_immersion_focal_length = extended_focal_length / refractive_index
            magnification = tube_lens_focal_length / multi_immersion_focal_length
        else:
            magnification = self.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["zoom"]
            magnification = float(magnification[:-1])

        pixel_size = self.default_pixel_size
        try:
            x_pixel = float(self.roi_widgets["Width"].get())
            y_pixel = float(self.roi_widgets["Height"].get())
        except ValueError as e:
            logger.error(f"{e} similar to TclError")
            return

        physical_dimensions_x = x_pixel * pixel_size / magnification
        physical_dimensions_y = y_pixel * pixel_size / magnification

        self.roi_widgets["FOV_X"].set(physical_dimensions_x)
        self.roi_widgets["FOV_Y"].set(physical_dimensions_y)

    def calculate_readout_time(self):
        """Calculate camera readout time.


        TODO: Highly specific to Hamamatsu. Should find a way to pass this from the camera to here.
        This should be moved to the camera device/API, ideally by calling a command from the camera.
        """

        h = 9.74436e-6  # Readout timing constant
        sensor_mode = self.mode_widgets["Sensor"].get()
        if (self.readout_speed == 1) and (sensor_mode == "Normal"):
            h = 32.4812e-6
        # the ROI height 'subarray_vsize'
        vn = float(self.roi_widgets["Height"].get())
        exposure_time = float(self.framerate_widgets["exposure_time"].get())

        if sensor_mode == "Normal":
            #  Area sensor mode operation
            if self.trigger_source == 1:
                # Internal Trigger Source
                max_frame_rate = 1 / ((vn / 2) * h)
                readout_time = exposure_time - ((vn / 2) * h)

            if self.trigger_active in [1, 2]:
                #  External Trigger Source
                #  Edge == 1, Level == 2
                max_frame_rate = 1 / ((vn / 2) * h + exposure_time + 10 * h)
                readout_time = exposure_time - ((vn / 2) * h + 10 * h)

            elif self.trigger_active == 3:
                #  External Trigger Source
                #  Synchronous Readout == 3
                max_frame_rate = 1 / ((vn / 2) * h + 5 * h)
                readout_time = exposure_time - ((vn / 2) * h + 5 * h)

        elif sensor_mode == "Light-Sheet":
            #  Progressive sensor mode operation
            max_frame_rate = 1 / (exposure_time + (vn + 10) * h)
            readout_time = exposure_time - 1 / (exposure_time + (vn + 10) * h)

        # return readout_time, max_frame_rate
        self.framerate_widgets["readout_time"].set(readout_time)
        self.framerate_widgets["max_framerate"].set(max_frame_rate * 1000)

    def update_number_of_pixels(self, *args):
        """Update the number of pixels in the ROI.

        In live mode, we should let the device know the number of pixels changed.

        Parameters
        ----------
        *args : tuple
            Unused

        """
        pixels = self.mode_widgets["Pixels"].get()
        if pixels != "":
            self.number_of_pixels = int(pixels)

        if self.mode != "live":
            return

        self.camera_setting_dict["number_of_pixels"] = self.number_of_pixels

        # tell central controller to update model
        if self.pixel_event_id:
            self.view.after_cancel(self.pixel_event_id)
        self.pixel_event_id = self.view.after(
            500,
            lambda: self.parent_controller.execute(
                "update_setting", "number_of_pixels"
            ),
        )
