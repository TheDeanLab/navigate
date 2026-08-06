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

# Third Party Imports
import numpy as np
import matplotlib.ticker as tck
from tkinter import messagebox

# Local Imports
import navigate
from navigate.controller.sub_controllers.gui import GUIController
from navigate.view.popups.autofocus_setting_popup import AutofocusPopup

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopupController(GUIController):
    """Class creates the popup to configure autofocus parameters."""

    CALIBRATION_ACTIONS = {
        "Regular": None,
        "Auto Defocus": "auto_defocus",
        "Capture Reference": "capture_reference",
        "Populate Defocus": "populate_defocus",
    }

    def __init__(
        self,
        view: AutofocusPopup,
        parent_controller: "navigate.controller.controller.Controller",
    ) -> None:
        """
        Parameters
        ----------
        view : AutofocusPopup
            The view of the autofocus popup.
        parent_controller : navigate.controller.controller.Controller
            The parent controller of the autofocus popup.
        """
        super().__init__(view, parent_controller)

        #: dict: The autofocus setting dictionary.
        self.widgets = self.view.get_widgets()

        #: str: The microscope name.
        self.microscope_name = None

        #: dict: The autofocus setting dictionary.
        self.setting_dict = None

        #: object: The autofocus figure.
        self.autofocus_fig = self.view.fig

        #: object: The autofocus coarse plot.
        self.autofocus_coarse = self.view.coarse

        #: dict: Temporary reference focus for defocus calibration.
        self.defocus_calibration_reference = None

        self.populate_experiment_values()

        #: object: The autofocus coarse plot.
        self.coarse_plot = None

        # Dismiss popup.
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", self.close_popup)

        self.view.autofocus_btn.configure(command=self.start_autofocus)
        self.view.stop_acquisition_btn.configure(command=self.stop_acquisition)
        acquire_bar_controller = getattr(
            self.parent_controller, "acquire_bar_controller", None
        )
        self.acquisition_state = getattr(
            self.parent_controller,
            "autofocus_acquisition_state",
            "running"
            if acquire_bar_controller and acquire_bar_controller.is_acquiring
            else "idle",
        )
        self.autofocus_active = bool(
            getattr(self.parent_controller, "is_autofocusing", False)
        )
        self._update_button_states()
        self.view.inputs["device"].get_variable().trace_add(
            "write", self.update_device_ref
        )
        self.view.inputs["device_ref"].get_variable().trace_add(
            "write", self.show_autofocus_setting
        )
        for k in self.view.setting_vars:
            self.view.setting_vars[k].trace_add("write", self.update_setting_dict(k))

    @staticmethod
    def _channel_key_to_label(channel_key: str) -> str:
        """Convert an internal channel key to the GUI channel label."""
        if channel_key.startswith("channel_"):
            return f"CH{channel_key.removeprefix('channel_')}"
        return channel_key

    @staticmethod
    def _channel_label_to_key(channel_label: str) -> str:
        """Convert a GUI channel label to the internal channel key."""
        if channel_label.startswith("CH") and channel_label[2:].isdigit():
            return f"channel_{channel_label[2:]}"
        return channel_label

    def close_popup(self, *_: tuple[str]) -> None:
        """Close the popup window

        Parameters
        ----------
        _ : tuple[str]
            The event arguments.
        """
        # We should add saving function to the function closing the window

        self.view.popup.dismiss()
        delattr(self.parent_controller, "af_popup_controller")

    def populate_experiment_values(self) -> None:
        """Populate Experiment Values

        Populates the experiment values from the experiment settings dictionary
        """
        self.setting_dict = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ]
        self.microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]

        setting_dict = self.setting_dict[self.microscope_name]

        # Default to stages, if they exist.
        if "stage" in setting_dict:
            device = "stage"
        else:
            device = setting_dict.keys()[0]
        self.widgets["device"].widget["values"] = setting_dict.keys()
        self.widgets["device"].set(device)

        # Default to the f axis, if it exists.
        if "f" in setting_dict[device]:
            device_ref = "f"
        else:
            device_ref = setting_dict[device].keys()[0]
        self.widgets["device_ref"].widget["values"] = setting_dict[device].keys()
        self.widgets["device_ref"].set(device_ref)

        channels = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["channels"]
        channel_keys = list(channels.keys())
        selected_channel = next(
            (channel for channel in channel_keys if channels[channel]["is_selected"]),
            channel_keys[0] if channel_keys else "",
        )
        self.widgets["target_channel"].widget["values"] = tuple(
            self._channel_key_to_label(channel) for channel in channel_keys
        )
        self.widgets["target_channel"].set(self._channel_key_to_label(selected_channel))
        self.widgets["calibration_action"].widget["values"] = tuple(
            self.CALIBRATION_ACTIONS.keys()
        )
        self.widgets["calibration_action"].set("Regular")
        self._update_reference_status()

        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def showup(self) -> None:
        """Shows the popup window"""
        self.view.popup.deiconify()

    def _update_button_states(self) -> None:
        """Render valid autofocus actions for the current lifecycle state."""
        acquire_bar_controller = getattr(
            self.parent_controller, "acquire_bar_controller", None
        )
        acquisition_mode = getattr(acquire_bar_controller, "mode", "live")
        can_start = (
            not self.autofocus_active
            and self.acquisition_state in ("idle", "running")
            and (self.acquisition_state == "idle" or acquisition_mode == "live")
        )
        can_stop = self.acquisition_state == "running"
        self.view.autofocus_btn.configure(state="normal" if can_start else "disabled")
        self.view.stop_acquisition_btn.configure(
            state="normal" if can_stop else "disabled"
        )

    def set_acquisition_state(self, state: str) -> None:
        """Update the acquisition lifecycle state and popup actions."""
        self.acquisition_state = state
        self._update_button_states()

    def set_autofocus_state(self, is_active: bool) -> None:
        """Update autofocus activity and popup actions."""
        self.autofocus_active = is_active
        self._update_button_states()

    def stop_acquisition(self) -> None:
        """Stop the active acquisition through the main controller."""
        acquire_bar_controller = getattr(
            self.parent_controller, "acquire_bar_controller", None
        )
        if not acquire_bar_controller or not acquire_bar_controller.is_acquiring:
            self.set_acquisition_state("idle")
            self.set_autofocus_state(False)
            return

        self.set_acquisition_state("stopping")
        acquire_bar_controller.view.acquire_btn.configure(state="disabled")
        self.parent_controller.execute("stop_acquire")

    def start_autofocus(self) -> None:
        """Starts the autofocus process."""
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device"
        ] = device
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device_ref"
        ] = device_ref

        # verify autofocus parameters
        setting_dict = self.setting_dict[self.microscope_name][device][device_ref]
        warning_message = ""
        for k in ["coarse", "fine"]:
            if setting_dict[f"{k}_selected"]:
                try:
                    step = float(setting_dict[f"{k}_step_size"])
                    value = float(setting_dict[f"{k}_range"])
                    if step <= 0 or value < step:
                        warning_message += f"{k} settings are not correct!\n"
                except Exception as e:
                    logger.exception(e)
                    warning_message += f"{k} settings are not correct!\n"
        if warning_message:
            messagebox.showerror(
                title="Navigate",
                message=warning_message,
            )
            return
        target_channel = self._channel_label_to_key(
            self.widgets["target_channel"].widget.get()
        )
        # check if the target cahnnel is activated in channel settings
        channels = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["channels"]
        for channel_key, channel_settings in channels.items():
            if channel_key == target_channel and not channel_settings["is_selected"]:
                channel_name = f"CH{channel_key.removeprefix('channel_')}"
                messagebox.showerror(
                    title="Navigate",
                    message=(
                        f"Please activate {channel_name} in channel settings "
                        "before proceeding!"
                    ),
                )
                return

        action_label = self.widgets["calibration_action"].widget.get()
        calibration_action = self.CALIBRATION_ACTIONS.get(action_label)
        reference_channel = None
        set_defocus_for_all_flag = False
        if calibration_action == "auto_defocus":
            if self.parent_controller.acquire_bar_controller.is_acquiring:
                messagebox.showwarning(
                    title="Navigate",
                    message=(
                        "Please stop the acquisition before calculating defocus values."
                    ),
                )
                return
            reference_channel = target_channel
            calibration_action = "capture_reference"
            set_defocus_for_all_flag = True
            # set all the defocus value to 0
            channels = self.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["channels"]
            for channel_key in channels.keys():
                self._write_channel_defocus(channel_key, 0)
        elif calibration_action == "capture_reference":
            reference_channel = target_channel
        elif self.defocus_calibration_reference is not None:
            reference_channel = self.defocus_calibration_reference["channel"]

        self._write_channel_defocus(target_channel, 0)
        self.parent_controller.execute(
            "autofocus",
            device,
            device_ref,
            target_channel,
            calibration_action,
            reference_channel,
            set_defocus_for_all_flag,
        )

    def handle_autofocus_complete(self, payload: dict) -> None:
        """Handle autofocus completion metadata for defocus calibration."""
        action = payload.get("calibration_action")
        if action == "capture_reference":
            self.defocus_calibration_reference = {
                "channel": payload["channel"],
                "focus_position": float(payload["focus_position"]),
            }
            self._update_reference_status()
            self._notify_defocus_reference(self.defocus_calibration_reference)
            # update defocus value
            channels = self.parent_controller.configuration["experiment"][
                "MicroscopeState"
            ]["channels"]
            defocus = channels[payload["channel"]]["defocus"]
            for channel_key in channels.keys():
                self._write_channel_defocus(
                    channel_key, channels[channel_key]["defocus"] - defocus
                )
            return

        if action == "populate_defocus":
            if self.defocus_calibration_reference is None:
                self._show_missing_reference_warning()
                return
            target_channel = payload["channel"]
            target_focus = float(payload["focus_position"])
            reference_focus = self.defocus_calibration_reference["focus_position"]
            focus = target_focus - reference_focus
            if target_channel == self.defocus_calibration_reference["channel"]:
                focus = 0
            self._write_channel_defocus(target_channel, focus)

        if self.defocus_calibration_reference is not None:
            self._notify_defocus_reference(self.defocus_calibration_reference)

    def _write_channel_defocus(self, channel_key: str, defocus: float) -> None:
        channels = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["channels"]
        channels[channel_key]["defocus"] = defocus
        handler = getattr(self.parent_controller, "event_listeners", {}).get(
            "channel_defocus"
        )
        if handler is not None:
            handler((channel_key, defocus))

    def _notify_defocus_reference(self, reference: dict) -> None:
        handler = getattr(self.parent_controller, "event_listeners", {}).get(
            "defocus_reference"
        )
        if handler is not None:
            handler(reference)

    def _update_reference_status(self) -> None:
        if not hasattr(self.view, "reference_status_var"):
            return
        if self.defocus_calibration_reference is None:
            reference_channel = self.setting_dict.get("reference_channel", None)
            self.view.reference_status_var.set(
                f"Reference: {reference_channel or 'none'}"
            )
            return
        channel = self._channel_key_to_label(
            self.defocus_calibration_reference["channel"]
        )
        focus = self.defocus_calibration_reference["focus_position"]
        self.view.reference_status_var.set(f"Reference: {channel} @ {focus:.3f}")
        # update reference channel info in the experiment file
        self.setting_dict["reference_channel"] = channel
        self.setting_dict["reference_position"] = focus

    def _show_missing_reference_warning(self) -> None:
        messagebox.showwarning(
            title="Navigate",
            message="Capture a reference focus before populating defocus.",
        )

    def update_device_ref(self, *_: tuple[str]) -> None:
        """Update device reference name

        Parameters
        ----------
        _: tuple[str]
            The event arguments.
        """
        device = self.widgets["device"].widget.get()
        device_refs = self.setting_dict[self.microscope_name][device].keys()
        self.widgets["device_ref"].widget["values"] = device_refs
        self.widgets["device_ref"].widget.set(device_refs[0])

    def show_autofocus_setting(self, *_: tuple[str]) -> None:
        """Show Autofocus Parameters

        Parameters
        ----------
        _: tuple[str]
            The event arguments.
        """
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        setting_dict = self.setting_dict[self.microscope_name]
        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def update_setting_dict(self, parameter: str) -> callable:
        """Show Autofocus Parameters

        Parameters
        ----------
        parameter : str
            The parameter to be updated.

        Returns
        -------
        callable
            The function to update the parameter
        """

        def func(*_: tuple[str]) -> None:
            device = self.widgets["device"].widget.get()
            device_ref = self.widgets["device_ref"].widget.get()
            self.setting_dict[self.microscope_name][device][device_ref][
                parameter
            ] = self.view.setting_vars[parameter].get()

        return func

    def display_plot(self, data_and_flags: tuple[np.ndarray, bool, bool]) -> None:
        """
        Display autofocus data, handling segmentation, plot mode, and redraw.

        This method unpacks and normalizes incoming data, splits it into coarse
        and fine segments according to the current autofocus settings, renders
        scatter and/or line plots on the coarse axes, optionally clears previous
        data, marks the detected maximum(s), and schedules a non-blocking canvas
        redraw.

        Parameters
        ----------
        data_and_flags : tuple[np.ndarray, bool, bool]
            Tuple of ``(data, line_plot, clear_data)``. ``data`` contains sample
            rows with stage positions in column 0 and signal values in column 1.
            ``line_plot`` overlays a continuous red line when true, and
            ``clear_data`` clears the axes and draws peak indicators when true.

        Raises
        ------
        ValueError
            May be raised if ``data`` is empty or has fewer than two columns
            (propagated from internal processing or from ``_plot_maxima``).
        """
        # Unpack the data and flags
        data, line_plot, clear_data = data_and_flags
        data = np.asarray(data, dtype=float)

        # Pull current settings for the selected device/ref
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        settings = self.setting_dict[self.microscope_name][device][device_ref]

        # Calculate the coarse portion of the data
        coarse_range = float(settings.get("coarse_range", 500))
        coarse_step = float(settings.get("coarse_step_size", 50))
        coarse_steps = int(coarse_range) // int(coarse_step) + 1

        if clear_data:
            self.autofocus_coarse.clear()
            if data.shape[0] > 0:
                self.autofocus_coarse.plot(
                    data[:coarse_steps, 0], data[:coarse_steps, 1], "k."
                )

            # fine segment begins after coarse, not at fine_steps
            if data.shape[0] > coarse_steps:
                self.autofocus_coarse.plot(
                    data[coarse_steps:, 0], data[coarse_steps:, 1], "k."
                )

            if data.size:
                self._plot_maxima(data)

        if line_plot and data.size:
            self.autofocus_coarse.plot(data[:, 0], data[:, 1], "r-")

        self._redraw_plot()

    def _redraw_plot(self):
        """
        Redraw the autofocus coarse plot and refresh the figure canvas.

        This method updates the plot title and axis labels, applies scientific
        formatting to the y-axis, enables minor tick locators on both axes,
        tightens the figure layout, and schedules a non-blocking canvas redraw.

        """
        self.autofocus_coarse.set_title("Discrete Cosine Transform", fontsize=18)
        self.autofocus_coarse.set_xlabel("Focus Stage Position", fontsize=16)
        self.autofocus_coarse.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        self.autofocus_coarse.yaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_coarse.xaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_fig.tight_layout()
        self.autofocus_fig.canvas.draw_idle()

    def _plot_maxima(self, data: np.ndarray) -> None:
        """
        Plot vertical and horizontal indicators for the autofocus data maximum.

        This method finds the maximum signal value and its corresponding x location,
        reads the current axes limits, draws a vertical dashed line at the peak location
        and a horizontal dashed line at the peak value, and stores the plotted line
        references on `self.coarse_plot`.

        Parameters
        ----------
        data : numpy.ndarray
            2D array with shape (N, >=2). Column 0 contains x positions and column 1
            contains the corresponding signal values.

        Raises
        ------
        ValueError
            If `data` is empty or does not contain at least two columns.

        """
        y_max = np.max(data[:, 1])
        peak_loc = data[np.argmax(data[:, 1]), 0]

        y_axes_limit = self.autofocus_coarse.get_ylim()
        x_axes_limit = self.autofocus_coarse.get_xlim()

        # Vertical Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [peak_loc, peak_loc], [y_axes_limit[0], y_axes_limit[1]], "--", color="gray"
        )

        # Horizontal Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [x_axes_limit[0], x_axes_limit[1]], [y_max, y_max], "--", color="gray"
        )

    @property
    def custom_events(self) -> dict[str, callable]:
        """Custom events for this controller

        Returns
        -------
        dict[str, callable]
            The custom events for this controller.
        """
        return {
            "autofocus": self.display_plot,
            "autofocus_complete": self.handle_autofocus_complete,
        }
