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
import tkinter as tk

# Third party imports

# Local application imports
from navigate.controller.sub_controllers.gui_controller import GUIController

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class ChannelSettingController(GUIController):
    """Controller for the channel setting widgets."""

    def __init__(self, view, parent_controller=None, configuration_controller=None):
        """Initialize the ChannelSettingController.

        Parameters
        ----------
        view : navigate.view.channel_setting_view.ChannelSettingView
            The view for the channel setting widgets.
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller.
        configuration_controller : ConfigurationController
            The configuration controller.
        """
        super().__init__(view, parent_controller)

        #: ConfigurationController: The configuration controller.
        self.configuration_controller = configuration_controller

        # num: numbers of channels
        self.num = self.configuration_controller.number_of_channels
        self.number_of_filter_wheels = (
            self.configuration_controller.number_of_filter_wheels
        )
        self.view.populate_frame(
            channels=self.num, filter_wheels=self.number_of_filter_wheels
        )

        #: str: The mode of the channel setting controller. Either 'live' or 'stop'.
        self.mode = "stop"

        #: bool: Whether the channel setting controller is in initialization.
        self.in_initialization = True

        #: int: The event id.
        self.event_id = None

        #: dict: The channel setting dictionary.
        self.channel_setting_dict = None

        # widget command binds
        for i in range(self.num):
            channel_vals = self.get_vals_by_channel(i)
            for name in channel_vals:
                channel_vals[name].trace_add("write", self.channel_callback(i, name))

    def set_mode(self, mode="stop"):
        """Set the mode of the channel setting controller.

        Parameters
        ----------
        mode : str
            "stop" or "live"

        Examples
        --------
        >>> self.set_mode("live")
        """

        self.mode = mode
        state = "normal" if mode == "stop" else "disabled"
        state_readonly = "readonly" if mode == "stop" else "disabled"
        for i in range(self.num):
            # State set regardless of operating mode.
            self.view.channel_checks[i].config(state=state)
            self.view.interval_spins[i].config(state="disabled")
            self.view.laser_pulldowns[i]["state"] = state_readonly

            if self.mode != "live" or (
                self.mode == "live" and not self.view.channel_variables[i].get()
            ):
                self.view.exptime_pulldowns[i].config(state=state)

            if not self.view.channel_variables[i].get():
                self.view.laserpower_pulldowns[i].config(state=state)
                for j in range(self.number_of_filter_wheels):
                    self.view.filterwheel_pulldowns[
                        i * self.number_of_filter_wheels + j
                    ]["state"] = state_readonly
                self.view.defocus_spins[i].config(state=state)

    def initialize(self):
        """Populates the laser and filter wheel options in the View.

        Examples
        --------
        >>> self.initialize()
        """
        setting_dict = self.configuration_controller.channels_info
        for i in range(self.num):
            self.view.laser_pulldowns[i]["values"] = setting_dict["laser"]
            for j in range(self.number_of_filter_wheels):
                ref_name = f"filter_wheel_{j}"
                self.view.filterwheel_pulldowns[i * self.number_of_filter_wheels + j][
                    "values"
                ] = setting_dict[ref_name]
        self.show_verbose_info("channel has been initialized")

    def populate_experiment_values(self, setting_dict):
        """Populates the View with the values from the setting dictionary.

        Set channel values according to channel id
        the value should be a dict {
        'channel_id': {
            'is_selected': True(False),
            'laser': ,
            'filter': ,
            'camera_exposure_time': ,
            'laser_power': ,
            'interval_time':}
        }

        Parameters
        ----------
        setting_dict : dict
            Dictionary containing the values for the experiment.
        """
        self.populate_empty_values()
        self.channel_setting_dict = setting_dict
        prefix = "channel_"
        for channel in setting_dict.keys():
            channel_id = int(channel[len(prefix) :]) - 1
            channel_vals = self.get_vals_by_channel(channel_id)
            if not channel_vals:
                return
            channel_value = setting_dict[channel]
            for name in channel_vals:
                channel_vals[name].set(channel_value[name])

            # validate exposure_time, interval, laser_power
            self.view.exptime_pulldowns[channel_id].trigger_focusout_validation()
            self.view.interval_spins[channel_id].trigger_focusout_validation()
            self.view.laserpower_pulldowns[channel_id].trigger_focusout_validation()

        self.show_verbose_info("channel has been set new value")

    def populate_empty_values(self):
        """Populates the View with empty values.

        If the user changes the number of channels, the new channels need
        to be populated with a default value.
        """
        for i in range(self.num):
            if self.view.laser_pulldowns[i].get() == "":
                self.view.laser_pulldowns[i].set(
                    self.view.laser_pulldowns[i]["values"][0]
                )

            if self.view.filterwheel_pulldowns[i].get() == "":
                self.view.filterwheel_pulldowns[i].set(
                    self.view.filterwheel_pulldowns[i]["values"][0]
                )

            if self.view.exptime_pulldowns[i].get() == "":
                self.view.exptime_pulldowns[i].set(100.0)

            if self.view.laserpower_pulldowns[i].get() == "":
                self.view.laserpower_pulldowns[i].set(10.0)

            if self.view.interval_spins[i].get() == "":
                self.view.interval_spins[i].set(1.0)

    def set_spinbox_range_limits(self, settings):
        """Set the range limits for the spinboxes in the View.

        This function will set the spinbox widget's values of from_, to, step
        according to the settings

        Parameters
        ----------
        settings : dict
            Dictionary containing the range limits for the spinboxes.
        """

        for i in range(self.num):
            self.view.laserpower_pulldowns[i].configure(
                from_=settings["channel_settings"]["laser_power"].get("min", 0),
                to=settings["channel_settings"]["laser_power"].get("max", 100),
                increment=settings["channel_settings"]["laser_power"].get("step", 1),
            )

            self.view.exptime_pulldowns[i].configure(
                from_=settings["channel_settings"]["exposure_time"].get("min", 0),
                to=settings["channel_settings"]["exposure_time"].get("max", 100),
                increment=settings["channel_settings"]["exposure_time"].get("step", 1),
            )

            self.view.interval_spins[i].configure(
                from_=settings["channel_settings"]["interval"].get("min", 0),
                to=settings["channel_settings"]["interval"].get("max", 100),
                increment=settings["channel_settings"]["interval"].get("step", 1),
            )

            self.view.defocus_spins[i].configure(
                from_=settings["channel_settings"]["defocus"].get("min", 0),
                to=settings["channel_settings"]["defocus"].get("max", 100),
                increment=settings["channel_settings"]["defocus"].get("step", 0.01),
            )

    def channel_callback(self, channel_id, widget_name):
        """Callback function for the channel widgets.

        In 'live' mode (when acquire mode is set to 'continuous') and a channel is
        selected, any change of the channel setting will influence devices
        instantly this function will call the central controller to response user's
        request

        Parameters
        ----------
        channel_id : int
            The channel id.
        widget_name : str
            The name of the widget.

        Returns
        -------
        success : bool
            Whether the callback function is executed successfully.

        Examples
        --------
        >>> self.channel_callback(0, "laser")
        """

        channel_vals = self.get_vals_by_channel(channel_id)
        prefix = "channel_"

        def update_setting_dict(setting_dict, widget_name):
            """Update the setting dictionary.

            Parameters
            ----------
            setting_dict : dict
                The setting dictionary.
            widget_name : str
                The name of the widget.

            Returns
            -------
            success : bool
                Whether the setting dictionary is updated successfully.
            """
            if channel_vals[widget_name].get() is None:
                return False

            if widget_name == "laser":
                setting_dict["laser"] = channel_vals["laser"].get()
                setting_dict["laser_index"] = self.get_index(
                    "laser", channel_vals["laser"].get()
                )
            elif widget_name.startswith("filter"):
                for i in range(self.number_of_filter_wheels):
                    ref_name = f"filter_wheel_{i}"
                    setting_dict[ref_name] = channel_vals[ref_name].get()
                    setting_dict[f"filter_position_{i}"] = self.get_index(
                        ref_name, channel_vals[ref_name].get()
                    )
            elif widget_name in [
                "laser_power",
                "camera_exposure_time",
                "interval_time",
            ]:
                try:
                    setting_dict[widget_name] = float(channel_vals[widget_name].get())
                except Exception:
                    setting_dict[widget_name] = 0
                    return False
                # ref_name = (
                #     "exposure_time"
                #     if widget_name == "camera_exposure_time"
                #     else widget_name
                # )
                # setting_range = self.parent_controller.parent_controller.
                # configuration["configuration"]["gui"]["channels"][ref_name]
                # if (
                #     setting_dict[widget_name] < setting_range["min"]
                #     or setting_dict[widget_name] > setting_range["max"]
                # ):
                #     return False
            else:
                setting_dict[widget_name] = channel_vals[widget_name].get()

            if widget_name == "camera_exposure_time" or widget_name == "is_selected":
                self.parent_controller.execute("recalculate_timepoint")
            return True

        def func(*args):
            """The function to be called when the channel widget is changed.

            Parameters
            ----------
            *args : tuple
                The arguments passed to the callback function.

            Returns
            -------
            success : bool
            """

            if self.in_initialization:
                return

            try:
                if channel_vals[widget_name].get() is None:
                    return
            except tk._tkinter.TclError:
                channel_vals[widget_name].set(0)
                return

            channel_key = prefix + str(channel_id + 1)
            if channel_key not in self.channel_setting_dict.keys():
                # update self.channel_setting_dict
                setting_dict = self.parent_controller.parent_controller.manager.dict()
                # check whether all the settings are validate
                for name in channel_vals:
                    if not update_setting_dict(setting_dict, name):
                        return
                self.channel_setting_dict[channel_key] = setting_dict
                return

            setting_dict = self.channel_setting_dict[channel_key]

            r = update_setting_dict(setting_dict, widget_name)

            if self.mode == "live":
                # call central controller
                if self.event_id:
                    self.view.after_cancel(self.event_id)
                if r:
                    self.event_id = self.view.after(
                        500,
                        lambda: self.parent_controller.execute(
                            "update_setting", "channel"
                        ),
                    )

            self.show_verbose_info("channel setting has been changed")

        return func

    def get_vals_by_channel(self, index):
        """Get the values of the channel widgets by channel id.

        This function return all the variables according channel_id

        Parameters
        ----------
        index : int
            The channel id.

        Returns
        -------
        dict
            The values of the channel widgets.

        Examples
        --------
        >>> self.get_vals_by_channel(0)
        """
        if index < 0 or index >= self.num:
            return {}
        result = {
            "is_selected": self.view.channel_variables[index],
            "laser": self.view.laser_variables[index],
            "camera_exposure_time": self.view.exptime_variables[index],
            "laser_power": self.view.laserpower_variables[index],
            "interval_time": self.view.interval_variables[index],
            "defocus": self.view.defocus_variables[index],
        }
        for i in range(self.number_of_filter_wheels):
            ref_name = f"filter_wheel_{i}"
            result[ref_name] = self.view.filterwheel_variables[
                index * self.number_of_filter_wheels + i
            ]
        return result

    def get_index(self, dropdown_name, value):
        """Get the index of the value in the dropdown list.

        Parameters
        ----------
        dropdown_name : str
            The name of the dropdown list.
        value : str
            The value of the dropdown list.

        Returns
        -------
        int
            The index of the value in the dropdown list.

        Examples
        --------
        >>> self.get_index("laser", "488")
        """
        if not value:
            return -1
        if dropdown_name == "laser":
            return self.view.laser_pulldowns[0]["values"].index(value)
        elif dropdown_name.startswith("filter"):
            idx = int(dropdown_name[dropdown_name.rfind("_") + 1 :])
            return self.view.filterwheel_pulldowns[idx]["values"].index(value)
        return -1

    def verify_experiment_values(self):
        """Verify channel settings and return warning info

        Returns
        -------
        string
            Warning info
        """
        selected_channel_num = 0
        for channel_key in self.channel_setting_dict.keys():
            setting_dict = self.channel_setting_dict[channel_key]
            idx = int(channel_key[len("channel_") :]) - 1
            if setting_dict["is_selected"]:
                selected_channel_num += 1

                # TODO: setting_range unspecified.
                # laser power
                if (
                    setting_dict["laser_power"]
                    < self.view.laserpower_pulldowns[idx]["from"]
                ):
                    return (
                        "Laser power below configured threshold. "
                        # f"Please adjust to meet or exceed the specified minimum "
                        # f"in the configuration.yaml("
                        # f"{setting_range['laser_power']['min']})."
                    )
                elif (
                    setting_dict["laser_power"]
                    > self.view.laserpower_pulldowns[idx]["to"]
                ):
                    return (
                        "Laser power exceeds configured maximum. "
                        # f"Please adjust to meet or be below the specified maximum "
                        # f"in the configuration.yaml("
                        # f"{setting_range['laser_power']['max']})."
                    )
                # exposure time
                if (
                    setting_dict["camera_exposure_time"]
                    < self.view.exptime_pulldowns[idx]["from"]
                ):
                    return (
                        "Exposure time below configured threshold. "
                        # f"Please adjust to meet or exceed the specified minimum "
                        # f"in the configuration.yaml("
                        # f"{setting_range['exposure_time']['min']})."
                    )
                elif (
                    setting_dict["camera_exposure_time"]
                    > self.view.exptime_pulldowns[idx]["to"]
                ):
                    return (
                        "Exposure time exceeds configured maximum. "
                        # f"Please adjust to meet or be below the specified maximum "
                        # f"in the configuration.yaml("
                        # f"{setting_range['exposure_time']['max']})"
                    )

        if selected_channel_num == 0:
            return "No selected channel!"
        return None
