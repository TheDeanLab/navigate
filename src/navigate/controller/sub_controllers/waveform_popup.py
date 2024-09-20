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

# Standard library imports
import logging

# Third-party imports

# Local application imports
from navigate.controller.sub_controllers.gui import GUIController
from navigate.tools.file_functions import save_yaml_file
from navigate.tools.common_functions import combine_funcs
from navigate.view.popups.waveform_parameter_popup_window import (
    AdvancedWaveformParameterPopupWindow,
)

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformPopupController(GUIController):
    """Controller for the waveform popup window.

    This controller is responsible for the waveform popup window. It is responsible for
    updating the waveform constants in the configuration file and saving the waveform
    constants to a file.
    """

    def __init__(self, view, parent_controller, waveform_constants_path):
        """Initialize the WaveformPopupController.

        Parameters
        ----------
        view : WaveformPopup
            The view for the controller.
        parent_controller : Controller
            The parent controller.
        waveform_constants_path : str
            The path to the waveform constants file.
        """
        super().__init__(view, parent_controller)

        # Microscope information
        #: dict: Waveform constants for the microscope.
        self.resolution_info = self.parent_controller.configuration[
            "waveform_constants"
        ]
        #: dict: Galvo constants for the microscope.
        self.galvo_setting = self.resolution_info["galvo_constants"]

        #: ConfigurationController: The configuration controller.
        self.configuration_controller = self.parent_controller.configuration_controller

        #: str: The path to the waveform constants file.
        self.waveform_constants_path = waveform_constants_path

        # Get mode and mag widgets
        #: dict: The widgets for the mode and magnification.
        self.widgets = self.view.get_widgets()

        #: dict: The variables for the mode and magnification.
        self.variables = self.view.get_variables()

        # Get configuration
        #: list: The lasers.
        self.lasers = self.configuration_controller.lasers_info

        #: str: The current resolution.
        self.resolution = None

        #: str: The current magnification.
        self.mag = None

        #: str: The current microscope operation mode.
        self.mode = "stop"

        #: dict: Remote focus experiment dictionary.
        self.remote_focus_experiment_dict = None

        #: bool: Flag to update galvo device.
        self.update_galvo_device_flag = None

        #: bool: Flag to update waveform parameters.
        self.update_waveform_parameters_flag = False

        #: bool: Flag to enable/disable waveforms.
        self.waveforms_enabled = True

        #: dict: Dictionary of amplitude values.
        self.amplitude_dict = None

        #: float: the minimum value of remote focus device
        self.laser_min = 0

        #: float: the maximum value of remote focus device
        self.laser_max = 1.0

        #: dict: Dictionary of galvo minimum values
        self.galvo_min = {}

        #: dict: Dictionary of galvo maximum values
        self.galvo_max = {}

        # event id list
        #: int: The event id.
        self.event_id = None

        # Event Binding
        # Switching microscopes modes (e.g., meso, nano, etc.)
        self.widgets["Mode"].widget.bind(
            "<<ComboboxSelected>>", self.show_magnification
        )

        # Switching magnifications (e.g., 10x, 20x, etc.)
        self.widgets["Mag"].widget.bind("<<ComboboxSelected>>", self.show_laser_info)

        # Changes to the waveform constants (amplitude, offset, etc.)
        for laser in self.lasers:
            self.variables[laser + " Amp"].trace_add(
                "write",
                self.update_remote_focus_settings(laser + " Amp", laser, "amplitude"),
            )
            self.variables[laser + " Off"].trace_add(
                "write",
                self.update_remote_focus_settings(laser + " Off", laser, "offset"),
            )

        # Changes to the galvo constants (amplitude, offset, etc.)
        for i in range(self.configuration_controller.galvo_num):
            galvo = f"Galvo {i}"
            self.variables[galvo + " Amp"].trace_add(
                "write", self.update_galvo_setting(galvo, " Amp", "amplitude")
            )
            self.variables[galvo + " Off"].trace_add(
                "write", self.update_galvo_setting(galvo, " Off", "offset")
            )
            self.variables[galvo + " Freq"].trace_add(
                "write", self.update_galvo_setting(galvo, " Freq", "frequency")
            )
            self.view.get_buttons()[galvo + " Freq"].configure(
                command=lambda: self.estimate_galvo_setting(galvo + " Freq")
            )

        # Changes in the delay, duty cycle, and smoothing waveform parameters
        # Delay, Duty, and Smoothing
        self.variables["Delay"].trace_add("write", self.update_waveform_parameters)
        self.variables["Duty"].trace_add("write", self.update_waveform_parameters)
        self.variables["Smoothing"].trace_add("write", self.update_waveform_parameters)
        self.variables["Ramp_falling"].trace_add(
            "write", self.update_waveform_parameters
        )
        self.variables["camera_delay"].trace_add(
            "write", self.update_waveform_parameters
        )
        self.variables["camera_settle_duration"].trace_add(
            "write", self.update_waveform_parameters
        )

        # Save waveform constants
        self.view.get_buttons()["Save"].configure(command=self.save_waveform_constants)

        # Temporarily disable waveforms
        self.view.get_buttons()["toggle_waveform_button"].configure(
            command=self.toggle_waveform_state
        )

        self.view.get_buttons()["advanced_galvo_setting"].configure(
            command=self.display_advanced_setting_window
        )

        # Save waveform constants upon closing the popup window
        self.view.popup.protocol(
            "WM_DELETE_WINDOW",
            combine_funcs(
                self.restore_amplitude,
                self.save_waveform_constants,
                self.view.popup.dismiss,
                lambda: delattr(self.parent_controller, "waveform_popup_controller"),
            ),
        )

        # All channels use the same galvo parameters
        self.widgets["all_channels"].widget.configure(
            command=self.set_galvo_to_all_channels
        )

        # Populate widgets
        self.widgets["Mode"].widget["values"] = list(
            self.resolution_info["remote_focus_constants"].keys()
        )
        self.widgets["Mode"].widget["state"] = "readonly"
        self.widgets["Mag"].widget["state"] = "readonly"

    def configure_widget_range(self):
        """Update widget ranges and precisions based on the current resolution mode.

        TODO: Other parameters we wish to enable/disable based on configuration?

        TODO: Should we instead change galvo amp/offset behavior based on a waveform
        type passed in the configuration? That is, should we pass galvo_l_waveform:
        sawtooth and galvo_r_waveform: dc_value? And then adjust the
        ETL_Popup_Controller accordingly? We could do the same for ETL vs. voice coil.

        This function updates the widget ranges and precisions based on the current
        resolution mode. The precision is set to -3 for high and nanoscale modes and -2
        for low mode. The increment is set to 0.001 for high and nanoscale modes and
        0.01 for low mode.

        """
        self.laser_min = self.configuration_controller.remote_focus_dict["hardware"][
            "min"
        ]
        self.laser_max = self.configuration_controller.remote_focus_dict["hardware"][
            "max"
        ]

        precision = int(
            self.configuration_controller.remote_focus_dict["hardware"].get(
                "precision", 0
            )
        )
        self.increment = int(
            self.configuration_controller.remote_focus_dict["hardware"].get("step", 0)
        )
        if precision == 0:
            precision = -4 if self.laser_max < 1 else -3
        elif precision > 0:
            precision = -precision
        if self.increment == 0:
            self.increment = 0.0001 if self.laser_max < 1 else 0.001
        elif self.increment < 0:
            self.increment = -self.increment

        # set ranges of value for those lasers
        for laser in self.lasers:
            self.widgets[laser + " Amp"].widget.configure(from_=self.laser_min)
            self.widgets[laser + " Amp"].widget.configure(to=self.laser_max)
            self.widgets[laser + " Amp"].widget.configure(increment=self.increment)
            self.widgets[laser + " Amp"].widget.set_precision(precision)
            self.widgets[laser + " Amp"].widget.trigger_focusout_validation()
            # TODO: The offset bounds should adjust based on the amplitude bounds,
            #       so that amp + offset does not exceed the bounds. Can be done
            #       in update_remote_focus_settings()
            self.widgets[laser + " Off"].widget.configure(from_=self.laser_min)
            self.widgets[laser + " Off"].widget.configure(to=self.laser_max)
            self.widgets[laser + " Off"].widget.configure(increment=self.increment)
            self.widgets[laser + " Off"].widget.set_precision(precision)
            self.widgets[laser + " Off"].widget.trigger_focusout_validation()

        for galvo, d in zip(self.galvos, self.galvo_dict):
            galvo_min = d["hardware"]["min"]
            galvo_max = d["hardware"]["max"]
            self.widgets[galvo + " Amp"].widget.configure(from_=galvo_min)
            self.widgets[galvo + " Amp"].widget.configure(to=galvo_max)
            self.widgets[galvo + " Amp"].widget.configure(increment=self.increment)
            self.widgets[galvo + " Amp"].widget.set_precision(precision)
            self.widgets[galvo + " Amp"].widget["state"] = "normal"
            self.widgets[galvo + " Amp"].widget.trigger_focusout_validation()
            # TODO: The offset bounds should adjust based on the amplitude bounds,
            #       so that amp + offset does not exceed the bounds. Can be done
            #       in update_remote_focus_settings()
            self.widgets[galvo + " Off"].widget.configure(from_=galvo_min)
            self.widgets[galvo + " Off"].widget.configure(to=galvo_max)
            self.widgets[galvo + " Off"].widget.configure(increment=self.increment)
            self.widgets[galvo + " Off"].widget.set_precision(precision)
            self.widgets[galvo + " Off"].widget["state"] = "normal"
            self.widgets[galvo + " Off"].widget.trigger_focusout_validation()

            self.widgets[galvo + " Freq"].widget.configure(from_=0)
            self.widgets[galvo + " Freq"].widget.configure(increment=self.increment)
            self.widgets[galvo + " Freq"].widget.set_precision(precision)
            self.widgets[galvo + " Freq"].widget["state"] = "normal"
            self.widgets[galvo + " Freq"].widget.trigger_focusout_validation()

            self.galvo_min[galvo] = galvo_min
            self.galvo_max[galvo] = galvo_max

        for i in range(len(self.galvos), self.configuration_controller.galvo_num):
            galvo_name = f"Galvo {i}"
            self.widgets[galvo_name + " Amp"].widget["state"] = "disabled"
            self.widgets[galvo_name + " Off"].widget["state"] = "disabled"
            self.widgets[galvo_name + " Freq"].widget["state"] = "disabled"

        # The galvo by default uses a sawtooth waveform.
        # However, sometimes we have a resonant galvo.
        # In the case of the resonant galvo, amplitude is zero and only the offset
        # can be controlled. We only define the offset in the configuration.yml file.
        # If only the offset is defined for galvo_{focus_prefix}, we disable the
        # amplitude.
        #

    def populate_experiment_values(self, force_update=False):
        """Set experiment values."""
        self.remote_focus_experiment_dict = self.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]
        resolution_value = self.remote_focus_experiment_dict["microscope_name"]
        zoom_value = self.remote_focus_experiment_dict["zoom"]
        mag = zoom_value
        if (
            not force_update
            and self.widgets["Mode"].get() == resolution_value
            and self.widgets["Mag"].get() == mag
        ):
            return

        # Microscope information
        self.resolution_info = self.parent_controller.configuration[
            "waveform_constants"
        ]
        self.galvo_setting = self.resolution_info["galvo_constants"]
        self.widgets["Mode"].set(resolution_value)
        self.show_magnification(mag)

        galvo_factor = self.resolution_info["other_constants"].get(
            "galvo_factor", "none"
        )
        self.set_galvo_factor(galvo_factor)

    def showup(self):
        """This function will let the popup window show in front."""
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def show_magnification(self, *args):
        """Show magnification options when the user changes the focus mode.

        Parameters
        ----------
        *args : tuple
            The first element is the new focus mode.
        """
        # restore amplitude before change resolution if needed
        self.restore_amplitude()
        # get resolution setting
        self.resolution = self.widgets["Mode"].widget.get()
        temp = list(
            self.resolution_info["remote_focus_constants"][self.resolution].keys()
        )
        self.widgets["Mag"].widget["values"] = temp

        if args[0] in temp:
            self.widgets["Mag"].widget.set(args[0])
        else:
            self.widgets["Mag"].widget.set(temp[0])

        # update laser info
        self.show_laser_info()

    def show_laser_info(self, *args):
        """Show laser info when the user changes magnification setting.

        Parameters
        ----------
        *args : tuple
            The first element is the new magnification setting.
        """
        # get galvo dict for the specified microscope/magnification
        self.galvo_dict = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][self.resolution]["galvo"]
        self.galvos = [f"Galvo {i}" for i in range(len(self.galvo_dict))]
        # restore amplitude before change mag if needed
        self.restore_amplitude()
        # get magnification setting
        self.mag = self.widgets["Mag"].widget.get()
        for laser in self.lasers:
            self.variables[laser + " Amp"].set(
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser]["amplitude"]
            )
            self.variables[laser + " Off"].set(
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser]["offset"]
            )

        # do not tell the model to update galvo
        self.update_galvo_device_flag = False
        for galvo in self.galvos:
            self.variables[galvo + " Amp"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("amplitude", 0)
            )
            self.variables[galvo + " Off"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("offset", 0)
            )
            self.variables[galvo + " Freq"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("frequency", 0)
            )
        self.update_galvo_device_flag = True

        # Load waveform parameters from configuration - Smooth, Delay, Duty Cycle.
        # Provide defaults should loading fail.
        # Currently pulls from the original microscope configuration YAML file, not the
        # current microscope configuration according to the model
        self.update_waveform_parameters_flag = False
        self.widgets["Smoothing"].set(
            self.resolution_info["other_constants"].get("percent_smoothing", 0)
        )
        self.widgets["Smoothing"].widget.trigger_focusout_validation()
        self.widgets["Delay"].set(
            self.resolution_info["other_constants"].get("remote_focus_delay", 7.5)
        )
        self.widgets["Delay"].widget.trigger_focusout_validation()
        self.widgets["Duty"].set(
            self.resolution_info["other_constants"]["remote_focus_settle_duration"]
        )
        self.widgets["Duty"].widget.trigger_focusout_validation()
        self.widgets["Ramp_falling"].set(
            self.resolution_info["other_constants"]["remote_focus_ramp_falling"]
        )
        self.widgets["Ramp_falling"].widget.trigger_focusout_validation()
        self.widgets["camera_delay"].set(
            self.resolution_info["other_constants"].get("camera_delay", 2)
        )
        self.widgets["camera_delay"].widget.trigger_focusout_validation()
        self.widgets["camera_settle_duration"].set(
            self.resolution_info["other_constants"]["camera_settle_duration"]
        )
        self.widgets["camera_settle_duration"].widget.trigger_focusout_validation()

        self.update_waveform_parameters_flag = True

        # update resolution value in central controller (menu)
        value = f"{self.resolution} {self.mag}"
        if self.parent_controller.menu_controller.resolution_value.get() != value:
            self.parent_controller.menu_controller.resolution_value.set(value)

        # reconfigure widgets
        self.configure_widget_range()
        # update advanced setting
        if hasattr(self, "advanced_setting_popup"):
            self.display_galvo_advanced_setting()

    def update_remote_focus_settings(self, name, laser, remote_focus_name):
        """Update remote focus settings in memory.

        Parameters
        ----------
        name : str
            The name of the variable.
        laser : str
            The name of the laser.
        remote_focus_name : str
            The name of the remote focus setting.
        """
        variable = self.variables[name]

        # TODO: Is this still a bug?
        # BUG Upon startup this will always run 0.63x,
        # and when changing magnification it will run 0.63x
        # before whatever mag is selected
        def func_laser(*args):
            value = self.resolution_info["remote_focus_constants"][self.resolution][
                self.mag
            ][laser][remote_focus_name]

            # Will only run code if value in constants does not match whats in GUI
            # for Amp or Off AND in Live mode
            # TODO: Make also work in the 'single' acquisition mode.
            variable_value = variable.get()
            logger.debug(
                f"Remote Focus Amplitude/Offset Changed pre if statement: "
                f"{variable_value}"
            )
            if value != variable_value and variable_value != "":
                # tell parent controller (the device)
                if self.event_id:
                    self.view.popup.after_cancel(self.event_id)

                try:
                    value = float(variable_value)
                except ValueError:
                    return
                if value < self.laser_min or value > self.laser_max:
                    return
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser][remote_focus_name] = variable_value
                logger.debug(
                    f"Remote Focus Amplitude/Offset Changed:, {variable_value}"
                )

                # Delay feature.
                self.event_id = self.view.popup.after(
                    500,
                    lambda: self.parent_controller.execute(
                        "update_setting", "resolution"
                    ),
                )

        return func_laser

    def update_waveform_parameters(self, *args, **wargs):
        """Update the waveform parameters for delay, duty cycle, and smoothing.

        Communicate changes to the parent controller.

        Parameters
        ----------
        *args : tuple
            The first element is the new waveform.
        **wargs : dict
            The key is the name of the waveform and the value is the waveform
        """
        if not self.update_waveform_parameters_flag:
            return

        if self.event_id:
            self.view.popup.after_cancel(self.event_id)
        # Get the values from the widgets.
        try:
            delay = float(self.widgets["Delay"].widget.get())
            duty_cycle = float(self.widgets["Duty"].widget.get())
            smoothing = float(self.widgets["Smoothing"].widget.get())
            ramp_falling = float(self.widgets["Ramp_falling"].widget.get())
            camera_delay = float(self.widgets["camera_delay"].widget.get())
            camera_settle_duration = float(
                self.widgets["camera_settle_duration"].widget.get()
            )
        except ValueError:
            return

        # Update the waveform parameters
        # all the lasers use the same delay, smoothing value
        self.resolution_info["other_constants"][
            "remote_focus_settle_duration"
        ] = duty_cycle
        self.resolution_info["other_constants"][
            "remote_focus_ramp_falling"
        ] = ramp_falling
        self.resolution_info["other_constants"]["remote_focus_delay"] = delay
        self.resolution_info["other_constants"]["percent_smoothing"] = smoothing
        self.resolution_info["other_constants"]["camera_delay"] = camera_delay
        self.resolution_info["other_constants"][
            "camera_settle_duration"
        ] = camera_settle_duration

        # Pass the values to the parent controller.
        self.event_id = self.view.popup.after(
            500,
            lambda: self.parent_controller.execute(
                "update_setting", "waveform_parameters"
            ),
        )

    def estimate_galvo_setting(self, *args, **kwargs):
        """Digitally scanned light-sheet frequency estimation.

        When imaging in a digitally scanned light-sheet mode, the galvo must
        operate at a specific frequency, otherwise periodic lines will appear in
        the image. This function estimates the frequency of the galvo based on the
        line interval and the number of pixels in the light-sheet mode.

        Note
        ----
            Will only work if all channels have the same exposure duration.
            The framerate widget doesn't update unless you change the
            exposure time in the channel settings. Default is 100ms.

        Parameters
        ----------
        *args : tuple
            The first element is the name of the galvo.
        **kwargs : dict
            The key is the name of the galvo and the value is the galvo setting.
        """

        # Get the name of the galvo.
        galvo_name = args[0]

        # Get the number of pixels in the light-sheet mode.
        number_of_pixels = (
            self.parent_controller.camera_setting_controller.mode_widgets[
                "Pixels"
            ].get()
        )

        # If not in the light-sheet mode, widget returns an empty string.
        if number_of_pixels == "":
            return

        # Get the exposure time. Convert to seconds.
        exposure_time = (
            self.parent_controller.camera_setting_controller.framerate_widgets[
                "exposure_time"
            ].get()
        )
        exposure_time = exposure_time / 1000

        # Get the light sheet exposure time.
        (
            light_sheet_exposure_time,
            _,
            _,
        ) = self.parent_controller.model.get_camera_line_interval_and_exposure_time(
            exposure_time, int(number_of_pixels) + 1
        )

        # Calculate the frequency of the galvo.
        frequency = 2 / light_sheet_exposure_time * exposure_time

        # Update the GUI
        self.view.inputs[galvo_name].widget.set(round(frequency, 3))

    def update_galvo_setting(self, galvo_name, widget_name, parameter):
        """Update galvo settings in memory.

        Parameters
        ----------
        galvo_name : str
            The name of the galvo.
        widget_name : str
            The name of the widget.
        parameter : str
            The name of the parameter.

        Returns
        -------
        func_galvo : function
            The function to update the galvo setting.
        """
        name = galvo_name + widget_name
        variable = self.variables[name]

        def func_galvo(*args):
            if not self.update_galvo_device_flag:
                return
            try:
                value = self.galvo_setting[galvo_name][self.resolution][self.mag][
                    parameter
                ]
            except KeyError:
                # Special case for galvo amplitude not being defined
                value = 0
            variable_value = variable.get()
            logger.debug(
                f"Galvo parameter {parameter} changed: "
                f"{variable_value} pre if statement"
            )
            if value != variable_value and variable_value != "":
                # change any galvo parameters as one event
                if self.event_id:
                    self.view.popup.after_cancel(self.event_id)

                try:
                    value = float(variable_value)
                except ValueError:
                    return
                if "Freq" not in widget_name and (
                    value < self.galvo_min[galvo_name]
                    or value > self.galvo_max[galvo_name]
                ):
                    return
                self.galvo_setting[galvo_name][self.resolution][self.mag][
                    parameter
                ] = variable_value
                logger.debug(f"Galvo parameter {parameter} changed: {variable_value}")

                self.event_id = self.view.popup.after(
                    500,
                    lambda: self.parent_controller.execute("update_setting", "galvo"),
                )

        return func_galvo

    def save_waveform_constants(self):
        """Save updated waveform parameters to yaml file."""
        # errors = self.get_errors()
        # if errors:
        #     return  # Dont save if any errors TODO needs testing
        save_yaml_file("", self.resolution_info, self.waveform_constants_path)

    """
    Example for preventing submission of a field/controller. So if there is an error in
    any field that is supposed to have validation then the config cannot be saved.
    """
    # TODO needs testing may also need to be moved to the remote_focus_popup class.
    #  Opinions welcome
    # def get_errors(self):
    #     """
    #     Get a list of field errors in popup
    #     """

    #     errors = {}
    #     for key, labelInput in self.widgets.items():
    #         if hasattr(labelInput.widget, 'trigger_focusout_validation'):
    #             labelInput.widget.trigger_focusout_validation()
    #         if labelInput.error.get():
    #             errors[key] = labelInput.error.get()
    #     return errors
    def toggle_waveform_state(self):
        """Temporarily disable waveform amplitude for quick alignment on stationary
        beam.
        """
        if self.waveforms_enabled is True:
            self.view.buttons["toggle_waveform_button"].config(state="disabled")
            self.view.buttons["toggle_waveform_button"].config(text="Enable Waveforms")
            self.amplitude_dict = {"resolution": self.resolution, "mag": self.mag}

            for laser in self.lasers:
                self.amplitude_dict[laser] = self.resolution_info[
                    "remote_focus_constants"
                ][self.resolution][self.mag][laser]["amplitude"]
                self.variables[laser + " Amp"].set(0)
                self.widgets[laser + " Amp"].widget.config(state="disabled")

            for galvo in self.galvos:
                self.amplitude_dict[galvo] = self.resolution_info["galvo_constants"][
                    galvo
                ][self.resolution][self.mag]["amplitude"]
                self.variables[galvo + " Amp"].set(0)
                self.widgets[galvo + " Amp"].widget.config(state="disabled")

            # Need to update main controller.
            self.waveforms_enabled = False
            self.view.popup.after(
                500,
                lambda: self.view.buttons["toggle_waveform_button"].config(
                    state="normal"
                ),
            )
        else:
            self.view.buttons["toggle_waveform_button"].config(state="disabled")
            self.show_laser_info()
            # call the parent controller the amplitude values are updated
            try:
                if self.event_id:
                    self.view.popup.after_cancel(self.event_id)
            except KeyError:
                pass

            self.event_id = self.view.popup.after(
                500,
                lambda: self.parent_controller.execute("update_setting", "galvo"),
            )
            self.view.popup.after(
                500,
                lambda: self.view.buttons["toggle_waveform_button"].config(
                    state="normal"
                ),
            )

    def restore_amplitude(self):
        """Restore amplitude values to previous values."""
        self.view.buttons["toggle_waveform_button"].config(text="Disable Waveforms")
        self.waveforms_enabled = True
        if self.amplitude_dict is None:
            return
        resolution = self.amplitude_dict["resolution"]
        mag = self.amplitude_dict["mag"]
        for laser in self.lasers:
            self.resolution_info["remote_focus_constants"][resolution][mag][laser][
                "amplitude"
            ] = self.amplitude_dict[laser]
            self.widgets[laser + " Amp"].widget.config(state="normal")
        for galvo in self.galvos:
            self.resolution_info["galvo_constants"][galvo][resolution][mag][
                "amplitude"
            ] = self.amplitude_dict[galvo]
            self.widgets[galvo + " Amp"].widget.config(state="normal")
        self.amplitude_dict = None

    def display_advanced_setting_window(self):
        """Display advanced galvo setting window"""
        if hasattr(self, "advanced_setting_popup"):
            galvo_factor = self.resolution_info["other_constants"].get(
                "galvo_factor", "none"
            )
            self.advanced_setting_popup.variables["galvo_factor"].set(galvo_factor)
            self.advanced_setting_popup.popup.deiconify()
            self.advanced_setting_popup.popup.attributes("-topmost", 1)
        else:
            self.advanced_setting_popup = AdvancedWaveformParameterPopupWindow(
                self.view
            )
            # close the window
            self.advanced_setting_popup.popup.protocol(
                "WM_DELETE_WINDOW",
                combine_funcs(
                    # save parameters
                    self.advanced_setting_popup.popup.dismiss,
                    lambda: delattr(self, "advanced_setting_popup"),
                ),
            )
            # register functioons
            self.advanced_setting_popup.variables["galvo_factor"].trace_add(
                "write", self.display_galvo_advanced_setting
            )
            galvo_factor = self.resolution_info["other_constants"].get(
                "galvo_factor", "none"
            )
            self.advanced_setting_popup.variables["galvo_factor"].set(galvo_factor)

    def display_galvo_advanced_setting(self, *args, **kwargs):
        """Generate dynamic galvo advanced setting widgets"""
        galvo_factor = self.advanced_setting_popup.variables["galvo_factor"].get()
        if galvo_factor == "none":
            factors = ["All"]
            galvos = []
            for i in range(self.configuration_controller.galvo_num):
                galvo_name = f"Galvo {i}"
                if self.resolution not in self.galvo_setting[galvo_name].keys():
                    continue
                galvos.append(
                    [
                        (
                            self.galvo_setting[galvo_name][self.resolution][self.mag][
                                "amplitude"
                            ],
                            self.galvo_setting[galvo_name][self.resolution][self.mag][
                                "offset"
                            ],
                        )
                    ]
                )
        else:
            if galvo_factor == "channel":
                channel_num = self.configuration_controller.number_of_channels
                factors = [f"Channel {i+1}" for i in range(channel_num)]
            else:  # laser
                factors = list(
                    self.resolution_info["remote_focus_constants"][self.resolution][
                        self.mag
                    ].keys()
                )
            galvos = []
            for i in range(self.configuration_controller.galvo_num):
                galvo_name = f"Galvo {i}"
                temp = []
                if self.resolution not in self.galvo_setting[galvo_name].keys():
                    continue
                galvo_setting = self.galvo_setting[galvo_name][self.resolution][
                    self.mag
                ]
                for fid in factors:
                    if fid not in galvo_setting.keys():
                        galvo_setting[fid] = {
                            "amplitude": galvo_setting["amplitude"],
                            "offset": galvo_setting["offset"],
                        }
                    temp.append(
                        (galvo_setting[fid]["amplitude"], galvo_setting[fid]["offset"])
                    )
                galvos.append(temp)

        self.advanced_setting_popup.generate_parameter_frame(factors, galvos)
        # set values
        for i in range(len(factors)):
            for j in range(len(galvos)):
                self.advanced_setting_popup.parameters[f"galvo_{i}_{j}_amp"].set(
                    galvos[j][i][0]
                )
                self.advanced_setting_popup.parameters[f"galvo_{i}_{j}_off"].set(
                    galvos[j][i][1]
                )
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_amp"
                ].widget.configure(from_=self.galvo_dict[j]["hardware"]["min"])
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_amp"
                ].widget.configure(to=self.galvo_dict[j]["hardware"]["max"])
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_amp"
                ].widget.configure(increment=self.increment)
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_off"
                ].widget.configure(from_=self.galvo_dict[j]["hardware"]["min"])
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_off"
                ].widget.configure(to=self.galvo_dict[j]["hardware"]["max"])
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_off"
                ].widget.configure(increment=self.increment)
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_amp"
                ].get_variable().trace_add(
                    "write", self.update_galvo_advanced_setting(i, j, factors[i], "amp")
                )
                self.advanced_setting_popup.parameters[
                    f"galvo_{i}_{j}_off"
                ].get_variable().trace_add(
                    "write", self.update_galvo_advanced_setting(i, j, factors[i], "off")
                )

        # update galvo factor
        if galvo_factor != self.resolution_info["other_constants"].get(
            "galvo_factor", "none"
        ):
            self.set_galvo_factor(galvo_factor)

    def update_galvo_advanced_setting(
        self, factor_id, galvo_id, factor_name, amp_or_off
    ):
        """Update galvo setting parameters

        Parameters
        ----------
        factor_id : int
            The index of the galvo factor
        galvo_id : int
            The index of the galvo device
        factor_name : str
            The name of galvo associated factor
        amp_or_off : str
            Amplitude or Offset: the value should be "amp" or "off

        Returns
        -------
        func : Function
            A widget function
        """

        def func(*args, **kwargs):
            try:
                value = float(
                    self.advanced_setting_popup.parameters[
                        f"galvo_{factor_id}_{galvo_id}_{amp_or_off}"
                    ].get()
                )
            except ValueError:
                return

            if self.event_id:
                self.view.popup.after_cancel(self.event_id)

            parameter_name = "amplitude" if amp_or_off == "amp" else "offset"
            galvo_name = f"Galvo {galvo_id}"
            if factor_name == "All":
                self.galvo_setting[galvo_name][self.resolution][self.mag][
                    parameter_name
                ] = value
            else:
                self.galvo_setting[galvo_name][self.resolution][self.mag][factor_name][
                    parameter_name
                ] = value

            self.event_id = self.view.popup.after(
                500,
                lambda: self.parent_controller.execute("update_setting", "galvo"),
            )

        return func

    def set_galvo_to_all_channels(self):
        """Set galvo factor to 'none' and use galvo parameters in all channels"""
        self.set_galvo_factor("none")
        self.resolution_info["other_constants"]["galvo_factor"] = "none"
        if hasattr(self, "advanced_setting_popup"):
            self.advanced_setting_popup.variables["galvo_factor"].set("none")

    def set_galvo_factor(self, galvo_factor="none"):
        """Set galvo factor and display information

        Parameters
        ----------
        galvo_factor : str
            The name of galvo factor: 'laser', 'channel', or 'none'
        """
        if galvo_factor != "none":
            self.view.inputs["galvo_info"].widget.configure(
                text=f"Associate with {galvo_factor}"
            )
            self.view.inputs["all_channels"].widget.configure(state="normal")
            self.view.inputs["all_channels"].set(False)
        else:
            self.view.inputs["galvo_info"].widget.configure(text="")
            self.view.inputs["all_channels"].widget.configure(state="disabled")
            self.view.inputs["all_channels"].set(True)

        self.resolution_info["other_constants"]["galvo_factor"] = galvo_factor
        if self.event_id:
            self.view.popup.after_cancel(self.event_id)
        self.event_id = self.view.popup.after(
            500,
            lambda: self.parent_controller.execute("update_setting", "galvo"),
        )
