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

from aslm.controller.sub_controllers.widget_functions import validate_wrapper
from aslm.controller.sub_controllers.gui_controller import GUIController
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

"""
TODO Create a dictionary for widgets that holds a list of widgets for each column.Will attempt after formatting.
"""


class ChannelSettingController(GUIController):
    def __init__(self, view, parent_controller=None, configuration_controller=None):
        super().__init__(view, parent_controller)

        self.configuration_controller = configuration_controller
        # num: numbers of channels
        self.num = self.configuration_controller.number_of_channels
        # 'live': acquire mode is set to 'continuous'
        self.mode = "stop"
        self.in_initialization = True
        self.event_id = None
        self.channel_setting_dict = None

        # add validation functions to spinbox
        for i in range(self.num):
            validate_wrapper(self.view.exptime_pulldowns[i])
            validate_wrapper(self.view.interval_spins[i])
            validate_wrapper(self.view.laserpower_pulldowns[i])

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
        for i in range(5):
            self.view.channel_checks[i].config(state=state)
            self.view.interval_spins[i].config(state=state)
            self.view.laser_pulldowns[i]["state"] = state_readonly
            if self.mode != "live" or (
                self.mode == "live" and not self.view.channel_variables[i].get()
            ):
                self.view.exptime_pulldowns[i].config(state=state)
            if not self.view.channel_variables[i].get():
                self.view.laserpower_pulldowns[i].config(state=state)
                self.view.filterwheel_pulldowns[i]["state"] = state
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
            self.view.filterwheel_pulldowns[i]["values"] = setting_dict["filter"]
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
            self.view.exptime_pulldowns[channel_id].validate()
            self.view.interval_spins[channel_id].validate()
            self.view.laserpower_pulldowns[channel_id].validate()

        self.show_verbose_info("channel has been set new value")

    def set_spinbox_range_limits(self, settings):
        """Set the range limits for the spinboxes in the View.

        Parameters
        ----------
        settings : dict
            Dictionary containing the range limits for the spinboxes.

            This function will set the spinbox widget's values of from_, to, step

            Examples
            --------
            >>> settings = {
            >>>     "exposure_time": [0.001, 10],
            >>>     "interval_time": [0.001, 10],
            >>>     "laser_power": [0.001, 10],
            >>>     "defocus": [-10, 10]
            >>> }
            >>> self.set_spinbox_range_limits(settings)
        """

        temp_dict = {
            "laser_power": self.view.laserpower_pulldowns,
            "exposure_time": self.view.exptime_pulldowns,
            "interval_time": self.view.interval_spins,
        }
        for k in temp_dict:
            widgets = temp_dict[k]
            for i in range(self.num):
                widgets[i].configure(from_=settings[k]["min"])
                widgets[i].configure(to=settings[k]["max"])
                widgets[i].configure(increment=settings[k]["step"])

    def channel_callback(self, channel_id, widget_name):
        """Callback function for the channel widgets.

        In 'live' mode (when acquire mode is set to 'continuous') and a channel is selected,
        any change of the channel setting will influence devices instantly
        this function will call the central controller to response user's request

        Parameters
        ----------
        channel_id : int
            The channel id.
        widget_name : str
            The name of the widget.

        Examples
        --------
        >>> self.channel_callback(0, "laser")
        """

        channel_vals = self.get_vals_by_channel(channel_id)
        prefix = "channel_"

        def update_setting_dict(setting_dict, widget_name):
            if channel_vals[widget_name].get() is None:
                return False

            if widget_name == "laser":
                setting_dict["laser"] = channel_vals["laser"].get()
                setting_dict["laser_index"] = self.get_index(
                    "laser", channel_vals["laser"].get()
                )
            elif widget_name == "filter":
                setting_dict["filter"] = channel_vals["filter"].get()
                setting_dict["filter_position"] = self.get_index(
                    "filter", channel_vals["filter"].get()
                )
            elif widget_name in [
                "laser_power",
                "camera_exposure_time",
                "interval_time",
            ]:
                try:
                    setting_dict[widget_name] = float(channel_vals[widget_name].get())
                except:
                    setting_dict[widget_name] = 0
                    return False
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
            """

            if self.in_initialization:
                return

            if channel_vals[widget_name].get() is None:
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

            update_setting_dict(setting_dict, widget_name)

            if self.mode == "live":
                # call central controller
                if self.event_id:
                    self.view.after_cancel(self.event_id)
                self.event_id = self.view.after(
                    500,
                    lambda: self.parent_controller.execute("update_setting", "channel"),
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
            "filter": self.view.filterwheel_variables[index],
            "camera_exposure_time": self.view.exptime_variables[index],
            "laser_power": self.view.laserpower_variables[index],
            "interval_time": self.view.interval_variables[index],
            "defocus": self.view.defocus_variables[index],
        }
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
        elif dropdown_name == "filter":
            return self.view.filterwheel_pulldowns[0]["values"].index(value)
        return -1
