"""DCAM timing-output discovery and transactions, independent of the native DLL."""

import math
from typing import Any, Optional

from navigate.tools.common_functions import copy_proxy_object

COUNT = 0x001C0010
STRIDE = 0x100
FIELDS = {
    "kind": (
        0x001C0160,
        {
            1: "low",
            2: "global_exposure",
            3: "programmable",
            4: "trigger_ready",
            5: "high",
            6: "any_row_exposure",
        },
    ),
    "source": (
        0x001C0110,
        {1: "exposure", 2: "readout_end", 3: "vsync", 4: "hsync", 6: "input_trigger"},
    ),
    "polarity": (0x001C0120, {1: "negative", 2: "positive"}),
    "active": (0x001C0130, {1: "edge", 2: "level"}),
    "delay_s": (0x001C0140, None),
    "pulse_width_s": (0x001C0150, None),
    "base_sensor": (
        0x001C0170,
        {1: "view1", 2: "view2", 15: "any_view", 16: "all_views"},
    ),
    "pre_hsync_count": (0x001C0190, None),
}
SHARED = {
    "channel_sync": (0x001C0030, {1: "1channel", 2: "2channels", 3: "3channels"}),
    "programmable_start": (0x001C0050, {1: "first_exposure", 2: "first_readout"}),
}
LABELS = {
    "exposure": "Exposure",
    "positive": "Positive",
    "negative": "Negative",
    "edge": "Edge",
    "level": "Level",
    "view1": "View 1",
    "view2": "View 2",
    "any_view": "Any view",
    "all_views": "All views",
    "1channel": "1 channel",
    "2channels": "2 channels",
    "3channels": "3 channels",
    "first_exposure": "First exposure",
    "first_readout": "First readout",
    "low": "Low (constant)",
    "high": "High (constant)",
    "global_exposure": "Global exposure",
    "programmable": "Programmable pulse",
    "trigger_ready": "Trigger ready",
    "any_row_exposure": "Any-row exposure",
    "vsync": "Readout start (Vsync)",
    "readout_end": "Readout end",
    "input_trigger": "Input trigger",
    "hsync": "Line timing (Hsync)",
}


def finite(value: Any) -> bool:
    """Reject booleans, including DCAM's False failure sentinel."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def applicable(field: str, settings: dict) -> bool:
    """Return whether a stored field participates in the selected output function."""
    if field == "kind":
        return True
    if settings.get("kind") in ("low", "high"):
        return False
    if field in ("polarity", "base_sensor"):
        return True
    return settings.get("kind") == "programmable" and (
        field != "pre_hsync_count" or settings.get("source") == "hsync"
    )


def normalize_outputs(settings: dict) -> dict:
    """Validate the portable schema without consulting or changing hardware.

    Parameters
    ----------
    settings : dict
        Versioned output selection, optionally backed by Manager proxies.

    Returns
    -------
    dict
        Independent values with string connector keys and numeric timing fields.

    Raises
    ------
    ValueError
        The schema, enum value or numeric timing is invalid.
    """
    settings = copy_proxy_object(settings)
    if (
        not isinstance(settings, dict)
        or type(settings.get("version")) is not int
        or settings["version"] != 1
    ):
        raise ValueError("Output triggers require schema version 1.")
    if set(settings) - {"version", "connectors", "shared"}:
        raise ValueError("Unknown output-trigger setting.")
    connectors = settings.get("connectors")
    if not isinstance(connectors, dict):
        raise ValueError("Output connectors must be a mapping.")
    normalized = {}
    for number, fields in connectors.items():
        if isinstance(number, bool) or str(number) not in tuple(
            str(i) for i in range(1, 17)
        ):
            raise ValueError("Output connector numbers must be between 1 and 16.")
        if str(number) in normalized:
            raise ValueError("Duplicate output connector.")
        if (
            not isinstance(fields, dict)
            or "kind" not in fields
            or set(fields) - FIELDS.keys()
        ):
            raise ValueError(f"Invalid settings for TIMING {number}.")
        for name, value in fields.items():
            enum = FIELDS[name][1]
            # The existing experiment writer emits JSON exponent numbers (1e-06).
            # YAML 1.1 readers may load these as strings; preserve that lifecycle.
            if enum is None and isinstance(value, str):
                try:
                    value = fields[name] = float(value)
                except ValueError:
                    raise ValueError(f"Invalid {name}: {value}.") from None
            if enum is not None:
                if not isinstance(value, str) or value not in enum.values():
                    raise ValueError(f"Unknown {name}: {value}.")
            elif (
                not finite(value)
                or value < 0
                or (name == "pulse_width_s" and value == 0)
            ):
                raise ValueError(f"Invalid {name}: {value}.")
            elif name == "pre_hsync_count" and value != int(value):
                raise ValueError("Pre-Hsync count must be an integer.")
        normalized[str(number)] = fields
    settings["connectors"] = normalized
    shared = settings.get("shared", {})
    if not isinstance(shared, dict) or set(shared) - SHARED.keys():
        raise ValueError("Invalid shared output settings.")
    for key, value in shared.items():
        if value not in SHARED[key][1].values():
            raise ValueError(f"Invalid {key}: {value}.")
    return settings


class HamamatsuOutputTriggers:
    """Operate one physical camera's outputs using public DCAM property methods."""

    def __init__(self, sdk: Any, lightsheet: bool = False) -> None:
        self.sdk = sdk
        self.lightsheet = lightsheet

    def count(self) -> int:
        """Return a validated connector count; absent properties mean unsupported."""
        try:
            value = self.sdk.get_property_value(COUNT)
        except (KeyError, AttributeError, TypeError):
            return 0
        return (
            int(value)
            if finite(value) and value == int(value) and 0 <= value <= 16
            else 0
        )

    def field(self, name: str, number: Optional[int] = None) -> dict:
        """Read a single field's capabilities without writes."""
        prop, enum = (SHARED if number is None else FIELDS)[name]
        prop += (number - 1) * STRIDE if number is not None else 0
        low, high, step = self.sdk.get_property_range(prop)
        if not all(finite(v) for v in (low, high, step)) or low > high or step < 0:
            return {"available": False, "reason": "Not reported by this camera."}
        current = self.sdk.get_property_value(prop)
        result = dict(
            available=True,
            writable=self.sdk.is_property_writable(prop),
            current=None,
            minimum=low,
            maximum=high,
            step=step,
            reason="",
            choices={},
        )
        if enum is not None:
            values = self.sdk.get_property_values(prop)
            if not values or any(not finite(v) or v != int(v) for v in values):
                result.update(
                    writable=False, reason="The camera did not report reliable choices."
                )
                values = ()
            result["choices"] = {
                enum[int(v)]: LABELS.get(
                    enum[int(v)],
                    self.sdk.get_property_value_text(prop, v) or enum[int(v)],
                )
                for v in values
                if int(v) in enum
            }
            result["current"] = enum.get(current) if finite(current) else None
            if self.lightsheet and name == "kind":
                result["choices"].pop("global_exposure", None)
        else:
            result["current"] = current if finite(current) else None
        if result["current"] is None:
            result.update(writable=False, reason="Camera readback is unavailable.")
        elif not result["writable"]:
            result["reason"] = "Read-only in the current camera mode."
        return result

    def capabilities(self) -> dict:
        """Return serializable connector and shared-property descriptions."""
        count = self.count()
        return dict(
            supported=bool(count),
            connectors={
                str(n): {key: self.field(key, n) for key in FIELDS}
                for n in range(1, count + 1)
            },
            shared={key: self.field(key) for key in SHARED} if count else {},
        )

    def snapshot(self) -> dict[int, float]:
        """Read every available output property for exact rollback or device reset."""
        values = {}
        props = [prop for prop, _ in SHARED.values()] if self.count() else []
        props += [
            prop + (n - 1) * STRIDE
            for n in range(1, self.count() + 1)
            for prop, _ in FIELDS.values()
        ]
        for prop in props:
            if self.sdk.get_property_range(prop)[0] is None:
                continue
            value = self.sdk.get_property_value(prop)
            if not finite(value):
                raise RuntimeError(f"Cannot snapshot output property {prop:#x}.")
            values[prop] = value
        return values

    def restore(self, snapshot: dict[int, float]) -> None:
        """Restore exact values and verify them, including unchanged read-only fields."""
        try:

            def restore_value(prop, value):
                if self.sdk.get_property_value(prop) == value:
                    return
                if not self.sdk.is_property_writable(
                    prop
                ) or not self.sdk.prop_setvalue(prop, value):
                    raise RuntimeError(f"Cannot restore output property {prop:#x}.")

            for prop, _ in SHARED.values():
                if prop in snapshot:
                    restore_value(prop, snapshot[prop])
            for number in range(1, self.count() + 1):
                kind = FIELDS["kind"][0] + (number - 1) * STRIDE
                dependent = [
                    base + (number - 1) * STRIDE
                    for name, (base, _) in FIELDS.items()
                    if name != "kind"
                ]
                if (
                    kind in snapshot
                    and snapshot[kind] not in (1, 5)
                    and self.sdk.get_property_value(kind) != 3
                ):
                    restore_value(kind, snapshot[kind])
                # Timing may become read-only in LOW/READY. Restore it before
                # restoring that final function, enabling PROGRAMABLE if needed.
                if any(
                    prop in snapshot
                    and self.sdk.get_property_value(prop) != snapshot[prop]
                    and not self.sdk.is_property_writable(prop)
                    for prop in dependent
                ):
                    self._write("kind", "programmable", number)
                for prop in dependent:
                    if prop in snapshot:
                        restore_value(prop, snapshot[prop])
                if kind in snapshot:
                    restore_value(kind, snapshot[kind])
            for prop, value in snapshot.items():
                actual = self.sdk.get_property_value(prop)
                if not finite(actual) or not math.isclose(
                    actual, value, rel_tol=0, abs_tol=1e-12
                ):
                    raise RuntimeError(
                        f"Output restoration readback failed for {prop:#x}."
                    )
        except Exception as exc:
            self.sdk._advanced_settings_error = (
                "Camera output restoration failed; reconnect before acquiring."
            )
            raise RuntimeError(self.sdk._advanced_settings_error) from exc

    def _write(self, name: str, value: Any, number: Optional[int] = None) -> None:
        cap = self.field(name, number)
        if not cap["available"]:
            raise ValueError(f"Output {number or 'shared'}: {name} is unavailable.")
        prop, enum = (SHARED if number is None else FIELDS)[name]
        prop += (number - 1) * STRIDE if number is not None else 0
        if enum is not None:
            if value not in cap["choices"]:
                raise ValueError(
                    f"Output {number or 'shared'}: unsupported {name}={value}."
                )
            raw = next(k for k, v in enum.items() if v == value)
        else:
            raw = value
            if not cap["minimum"] <= raw <= cap["maximum"]:
                raise ValueError(
                    f"{name} must be between {cap['minimum']} and {cap['maximum']}."
                )
            step = cap["step"]
            if step and not math.isclose(
                (raw - cap["minimum"]) / step,
                round((raw - cap["minimum"]) / step),
                abs_tol=1e-6,
                rel_tol=0,
            ):
                raise ValueError(f"{name} must use steps of {step}.")
        if cap["current"] != value:
            if not cap["writable"] or not self.sdk.prop_setvalue(prop, raw):
                raise RuntimeError(
                    f"Camera rejected output {number or 'shared'} {name}."
                )
        actual = self.sdk.get_property_value(prop)
        if not finite(actual) or not math.isclose(
            actual, raw, rel_tol=0, abs_tol=1e-12
        ):
            raise RuntimeError(
                f"Output {number or 'shared'} {name} readback did not match."
            )

    def apply(self, settings: dict) -> dict:
        """Apply a selection or restore every affected connector on failure.

        Parameters
        ----------
        settings : dict
            Versioned connector and optional shared selections. The caller must
            serialize access and ensure capture is stopped.

        Returns
        -------
        dict
            Confirmed selections, retaining inactive timing preferences.

        Raises
        ------
        ValueError
            A selection is unsupported or outside the reported range or step.
        RuntimeError
            A write, readback or restoration failed.
        """
        if self.sdk.__dict__.get("_advanced_settings_error"):
            raise RuntimeError(self.sdk._advanced_settings_error)
        settings = normalize_outputs(settings)
        count = self.count()
        if not count or any(int(n) > count for n in settings["connectors"]):
            raise ValueError("Saved output connector is unavailable on this camera.")
        snapshot = self.snapshot()
        try:
            for name, value in settings.get("shared", {}).items():
                self._write(name, value)
            for number, fields in settings["connectors"].items():
                # Some drivers expose source/timing only after selecting PROGRAMABLE.
                # Capture is stopped, but DCAM does not promise glitch-free switching.
                for name in FIELDS:
                    if name in fields and applicable(name, fields):
                        self._write(name, fields[name], int(number))
                for name in FIELDS:
                    if applicable(name, fields):
                        current = self.field(name, int(number)).get("current")
                        if name not in fields and current is not None:
                            fields[name] = current
                if (
                    fields["kind"] == "programmable"
                    and not {"source", "delay_s", "pulse_width_s"} <= fields.keys()
                ):
                    raise RuntimeError(
                        "Camera did not confirm programmable output timing."
                    )
            # Shared options and later writes may couple connectors: verify all again.
            for number, fields in settings["connectors"].items():
                for name, value in fields.items():
                    if applicable(name, fields):
                        current = self.field(name, int(number)).get("current")
                        matches = (
                            math.isclose(current, value, rel_tol=0, abs_tol=1e-12)
                            if finite(current) and finite(value)
                            else current == value
                        )
                        if not matches:
                            raise RuntimeError(
                                "Output settings changed while configuring another connector."
                            )
                        fields[name] = current
            for name, value in settings.get("shared", {}).items():
                if self.field(name).get("current") != value:
                    raise RuntimeError(
                        "Shared output settings changed during configuration."
                    )
        except Exception:
            self.restore(snapshot)
            raise
        return settings
