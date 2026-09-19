# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Persistent autofocus defocus-calibration event processing."""

from tkinter import messagebox
from typing import Any


class AutofocusCalibrationController:
    """Process autofocus completion metadata independently of popup lifetime."""

    def __init__(self, parent_controller: Any) -> None:
        """Create a calibration event processor.

        Parameters
        ----------
        parent_controller : Any
            Main controller that owns configuration and event listeners.
        """
        self.parent_controller = parent_controller
        self.reference = None

    def handle_autofocus_complete(self, payload: dict) -> None:
        """Apply autofocus completion metadata to defocus calibration state.

        Parameters
        ----------
        payload : dict
            Completed autofocus channel, position, and calibration action.
        """
        action = payload.get("calibration_action")
        if action == "capture_reference":
            self.reference = {
                "channel": payload["channel"],
                "focus_position": float(payload["focus_position"]),
            }
            self._persist_reference(payload)
            self._notify_reference()

            channels = self._channels
            reference_defocus = channels[payload["channel"]]["defocus"]
            for channel_key in channels.keys():
                self.write_channel_defocus(
                    channel_key,
                    channels[channel_key]["defocus"] - reference_defocus,
                )
            self._refresh_open_popup()
            return

        if action == "populate_defocus":
            if self.reference is None:
                messagebox.showwarning(
                    title="Navigate",
                    message="Capture a reference focus before populating defocus.",
                )
                return
            target_channel = payload["channel"]
            target_focus = float(payload["focus_position"])
            focus = target_focus - self.reference["focus_position"]
            if target_channel == self.reference["channel"]:
                focus = 0
            self.write_channel_defocus(target_channel, focus)

        self._notify_reference()
        self._refresh_open_popup()

    @property
    def _channels(self) -> dict:
        """Return configured acquisition channels."""
        return self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["channels"]

    def _persist_reference(self, payload: dict) -> None:
        """Persist reference metadata when the originating settings are known."""
        device = payload.get("device")
        device_ref = payload.get("device_ref")
        if device is None or device_ref is None:
            return
        experiment = self.parent_controller.configuration["experiment"]
        microscope_name = experiment["MicroscopeState"]["microscope_name"]
        settings = experiment["AutoFocusParameters"][microscope_name][device][
            device_ref
        ]
        channel = self.reference["channel"]
        settings["reference_channel"] = (
            f"CH{channel.removeprefix('channel_')}"
            if channel.startswith("channel_")
            else channel
        )
        settings["reference_position"] = self.reference["focus_position"]

    def write_channel_defocus(self, channel_key: str, defocus: float) -> None:
        """Write one defocus value and notify the channels controller."""
        self._channels[channel_key]["defocus"] = defocus
        handler = getattr(self.parent_controller, "event_listeners", {}).get(
            "channel_defocus"
        )
        if handler is not None:
            handler((channel_key, defocus))

    def _notify_reference(self) -> None:
        """Notify the channels controller of the active reference, if any."""
        if self.reference is None:
            return
        handler = getattr(self.parent_controller, "event_listeners", {}).get(
            "defocus_reference"
        )
        if handler is not None:
            handler(self.reference)

    def _refresh_open_popup(self) -> None:
        """Refresh reference text only while a live popup exists."""
        popup_controller = getattr(
            self.parent_controller, "af_popup_controller", None
        )
        if popup_controller is not None:
            popup_controller._update_reference_status()
