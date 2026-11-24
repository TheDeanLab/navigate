"""Main-thread presentation of asynchronous laser settings transactions."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from navigate.controller.controller import Controller
    from navigate.view.popups.laser_setting_popup import AdvancedLaserSettingPopup


class AdvancedLaserSettingController:
    """Show confirmed laser settings without accessing hardware from Tk.

    Parameters
    ----------
    popup : AdvancedLaserSettingPopup
        View containing selectors and readback labels.
    parent_controller : Controller
        Application command dispatcher.
    """

    mode_labels = {
        "cw": "CW",
        "digital": "Digital",
        "analog": "Analog",
        "mixed": "Mixed",
    }

    def __init__(
        self, popup: "AdvancedLaserSettingPopup", parent_controller: "Controller"
    ) -> None:
        self.view = popup
        self.parent_controller = parent_controller
        self._closed = False
        self._pending = False
        self._request_id = 0
        self._identity = None
        self._modes: list[str] = []
        self._lasers: dict[str, str] = {}
        self._acquiring = parent_controller.acquire_bar_controller.is_acquiring
        self._microscopes = parent_controller.configuration["configuration"][
            "microscopes"
        ]
        self.view.inputs["microscope"].configure(values=list(self._microscopes))
        selected = parent_controller.configuration["experiment"]["MicroscopeState"][
            "microscope_name"
        ]
        self.view.variables["microscope"].set(selected)
        self.view.inputs["microscope"].bind(
            "<<ComboboxSelected>>", self.update_microscope
        )
        self.view.inputs["laser"].bind(
            "<<ComboboxSelected>>", lambda event: self.refresh()
        )
        self.view.buttons["refresh"].configure(command=self.refresh)
        self.view.buttons["apply"].configure(command=self.apply_mode)
        self.view.buttons["close"].configure(command=self.close_popup)
        self.view.popup.protocol("WM_DELETE_WINDOW", self.close_popup)
        self.view.popup.bind("<Escape>", lambda event: self.close_popup())
        self.update_microscope()

    def _busy(self) -> bool:
        """Read acquisition state only on the Tk thread."""
        return (
            self._acquiring
            or self.parent_controller.acquire_bar_controller.is_acquiring
        )

    def _update_controls(self) -> None:
        """Lock selectors during requests and hardware operations during capture."""
        idle = not self._pending and not self._busy()
        for name in ("microscope", "laser"):
            self.view.inputs[name].configure(
                state="disabled" if self._pending else "readonly"
            )
        writable = idle and self._identity is not None and bool(self._modes)
        self.view.inputs["mode"].configure(state="readonly" if writable else "disabled")
        self.view.buttons["apply"].configure(state="normal" if writable else "disabled")
        self.view.buttons["refresh"].configure(
            state="normal" if idle and self._lasers else "disabled"
        )

    def _clear_readbacks(self) -> None:
        """Remove stale readbacks when selecting or refreshing a device."""
        self._identity = None
        self._modes = []
        self.view.variables["mode"].set("")
        self.view.inputs["mode"].configure(values=())
        for name, variable in self.view.variables.items():
            if name not in ("microscope", "laser", "mode", "status"):
                variable.set("Unknown")

    def update_microscope(self, event: object = None) -> None:
        """Populate configured wavelengths without opening connections."""
        if self._pending or self._closed:
            return
        name = self.view.variables["microscope"].get()
        lasers = self._microscopes.get(name, {}).get("laser", [])
        self._lasers = {
            f"{entry['wavelength']} nm": str(entry["wavelength"]) for entry in lasers
        }
        self.view.inputs["laser"].configure(values=list(self._lasers))
        self.view.variables["laser"].set(next(iter(self._lasers), ""))
        self.refresh()

    def refresh(self) -> None:
        """Request one live snapshot while idle; never poll during capture."""
        if self._closed or self._pending:
            return
        self._clear_readbacks()
        if self._busy() or not self._lasers:
            self.view.variables["status"].set(
                "Stop acquisition to read or change laser settings."
                if self._busy()
                else "No lasers configured for this microscope."
            )
            self._update_controls()
            return
        self._request()

    def apply_mode(self) -> None:
        """Submit a supported selection with the last confirmed connection token."""
        if self._closed or self._pending or self._busy() or self._identity is None:
            return
        label = self.view.variables["mode"].get()
        mode = next((m for m in self._modes if self.mode_labels[m] == label), None)
        if mode is not None:
            self._request(mode)

    def _request(self, mode: Optional[str] = None) -> None:
        """Capture Tk state before dispatching the immutable request to a worker."""
        self._request_id += 1
        request = {
            "microscope": self.view.variables["microscope"].get(),
            "laser": self._lasers[self.view.variables["laser"].get()],
            "request_id": self._request_id,
        }
        if mode is not None:
            request.update(mode=mode, identity=self._identity)
        self._pending = True
        self._update_controls()
        self.view.variables["status"].set(
            "Applying modulation mode…" if mode else "Reading laser settings…"
        )
        self.parent_controller.execute(
            "laser_advanced_settings", request, self._receive
        )

    def _receive(self, result: dict) -> None:
        """Present only the latest response for this open popup on the Tk thread."""
        if self._closed or result.get("request_id") != self._request_id:
            return
        if result.get("microscope") != self.view.variables[
            "microscope"
        ].get() or result.get("laser") != self._lasers.get(
            self.view.variables["laser"].get()
        ):
            return
        self._pending = False
        self._clear_readbacks()
        if self._busy():
            self.view.variables["status"].set(
                "Stop acquisition to read or change laser settings."
            )
            self._update_controls()
            return
        values = self.view.variables
        connection = result.get("connection", "unavailable")
        values["connection"].set(
            {
                "not_configured": "Software control not configured",
                "simulated": "Simulated",
                "connected": "Connected",
                "busy": "Busy — read deferred",
                "unavailable": "Unavailable",
            }.get(connection, "Unknown")
        )
        if connection in ("connected", "simulated"):
            self._identity = result["identity"]
            self._modes = result["available_modes"]
            self.view.inputs["mode"].configure(
                values=[self.mode_labels[m] for m in self._modes]
            )
            current = self.mode_labels.get(
                result["mode"], "Unavailable for acquisition"
            )
            values["mode"].set(current if result["mode"] in self._modes else "")
            values["current_mode"].set(current)
            values["device_identity"].set(result["device_identity"])
            serial = result["power_source"] == "serial"
            values["power_source"].set("Serial" if serial else "External hardware")
            values["limits"].set(
                f"{result['minimum_mw']:g}–{result['maximum_mw']:g} mW"
            )
            values["reference"].set(
                f"{result['percent_reference_mw']:g} mW"
                if serial
                else "External hardware scale"
            )
            acquisition_mode = result["acquisition_mode"]
            values["acquisition_mode"].set(
                self.mode_labels.get(acquisition_mode, "Preserve device mode")
            )
            kind = "peak pulse" if result["power_kind"] == "peak_pulse" else "CW"
            values["setpoint"].set(
                f"{result['setpoint_mw']:g} mW ({kind})"
                if result["setpoint_mw"] is not None
                else (
                    "Unknown" if result["mode"] is None else "External analog control"
                )
            )
            measured = result["measured_power_mw"]
            values["measured"].set(
                "Unknown" if measured is None else f"{measured:g} mW"
            )
            emission = result["emission_enabled"]
            values["emission"].set(
                "Unknown" if emission is None else "Yes" if emission else "No"
            )
            values["read_at"].set(result["read_at"])
        status = (
            result.get("error")
            or result.get("mode_error")
            or result.get("mode_warning")
        )
        if not status:
            status = (
                "Configure software_control to enable these settings."
                if connection == "not_configured"
                else "Readbacks refreshed. Mode changes leave illumination gates closed."
            )
            if result.get("power_source") == "serial":
                status += " Serial power requires CW or digital mode."
        values["status"].set(status)
        self._update_controls()

    def set_acquisition_state(self, acquiring: bool) -> None:
        """Disable hardware requests during capture and refresh when it ends."""
        if self._closed:
            return
        self._acquiring = acquiring
        if acquiring:
            self._clear_readbacks()
            self.view.variables["status"].set(
                "Stop acquisition to read or change laser settings."
            )
            self._update_controls()
        else:
            self.refresh()

    def showup(self) -> None:
        """Raise the existing popup and request fresh idle readbacks."""
        self.view.popup.deiconify()
        self.view.popup.lift()
        self.refresh()

    def close_popup(self) -> None:
        """Destroy the view; in-flight callbacks safely ignore closed widgets."""
        if self._closed:
            return
        self._closed = True
        self.view.popup.destroy()
        if (
            getattr(self.parent_controller, "advanced_laser_setting_controller", None)
            is self
        ):
            del self.parent_controller.advanced_laser_setting_controller
