# Configurator Mini Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a flexible mini-wizard experience inside each configurator hardware tab, with full device-aware behavior for Camera, Data Acquisition Card, and Stages.

**Architecture:** Keep the current Tk configurator and YAML format. Add a pure metadata/filtering layer under `navigate.config`, then have `HardwareTab` render steps, Basic/Advanced visibility, help text, and warnings from that metadata. Preserve the existing visible-field serialization path and add a merge layer for loaded hidden values.

**Tech Stack:** Python, Tkinter/ttk, pytest, existing Navigate configuration dictionaries, existing `navigate` conda environment.

---

## File Structure

- Create: `src/navigate/config/configuration_wizard.py`
  - Pure helper module for wizard metadata defaults, step ordering, field visibility, validation warnings, and save/load merging.
- Modify: `src/navigate/config/configuration_database.py`
  - Add `hardware_wizard_metadata`, keyed by the current hardware tab labels.
  - Fully describe Camera, Data Acquisition Card, and Stages in the first pass.
  - Provide fallback shell metadata for non-pilot tabs.
- Modify: `src/navigate/view/configurator_application_window.py`
  - Add mini-wizard layout state to `HardwareTab`.
  - Render step navigation, Basic/Advanced toggle, field rows, inline hints, contextual help, and warning labels.
  - Keep field variables available to the existing controller serialization path.
- Modify: `src/navigate/controller/configurator.py`
  - Pass wizard metadata into hardware tabs.
  - Track loaded hardware blocks on tabs.
  - Merge visible edited values with preserved loaded values during save.
  - Warn on save when a device type change would drop stale loaded values.
- Modify: `test/config/test_configuration_database.py`
  - Cover pilot metadata shape and required field coverage.
- Create: `test/config/test_configuration_wizard.py`
  - Cover pure visibility, validation, and merge helpers.
- Modify: `test/view/test_configurator_application_window.py`
  - Cover the shared wizard shell, Basic/Advanced toggle wiring, and pilot field visibility.

Use the repo root `/Users/Dean/Documents/GitHub/navigate` as the working directory for all commands.

---

### Task 1: Add Pure Wizard Helper Module

**Files:**
- Create: `src/navigate/config/configuration_wizard.py`
- Create: `test/config/test_configuration_wizard.py`

- [ ] **Step 1: Write failing tests for metadata defaults and visibility**

Add this file:

```python
# test/config/test_configuration_wizard.py
from copy import deepcopy

import pytest

from navigate.config.configuration_wizard import (
    ADVANCED_IMPORTANCE,
    BASIC_IMPORTANCE,
    DEFAULT_STEP,
    collect_step_warnings,
    field_applies_to_device,
    field_is_visible,
    get_field_metadata,
    get_steps,
    merge_loaded_and_edited_values,
)


def test_get_steps_uses_metadata_order_and_fallback():
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {}, None],
        "serial": ["Serial", "Input", "string", None, None],
        "frame_config": {"ref": "hardware"},
    }
    metadata = {
        "steps": ["Device Type", "Connection"],
        "fields": {
            "hardware/type": {"step": "Device Type"},
            "serial": {"step": "Connection"},
        },
    }

    assert get_steps(widgets, metadata) == ["Device Type", "Connection"]
    assert get_steps(widgets, {}) == [DEFAULT_STEP]


def test_get_field_metadata_falls_back_to_default_step():
    metadata = {"fields": {"serial": {"step": "Connection", "importance": "required"}}}

    assert get_field_metadata(metadata, "serial") == {
        "step": "Connection",
        "importance": "required",
    }
    assert get_field_metadata(metadata, "missing") == {
        "step": DEFAULT_STEP,
        "importance": "recommended",
    }


def test_field_applies_to_device_without_rule_is_visible():
    assert field_applies_to_device({}, "Virtual Device")
    assert field_applies_to_device({"applies_to": ["Virtual Device"]}, "Virtual Device")
    assert not field_applies_to_device(
        {"applies_to": ["Photometrics Iris 15B"]}, "Virtual Device"
    )


@pytest.mark.parametrize("importance", sorted(BASIC_IMPORTANCE))
def test_basic_mode_shows_required_and_recommended_fields(importance):
    assert field_is_visible(
        field_key="delay",
        widget_spec=["Delay", "Spinbox", "float", {}, None],
        field_metadata={"step": "Timing", "importance": importance},
        selected_step="Timing",
        advanced_mode=False,
        selected_device="Virtual Device",
    )


@pytest.mark.parametrize("importance", sorted(ADVANCED_IMPORTANCE))
def test_basic_mode_hides_optional_and_advanced_fields(importance):
    assert not field_is_visible(
        field_key="camera_connection",
        widget_spec=["Camera Connection", "Input", "string", None, None],
        field_metadata={
            "step": "Connection",
            "importance": importance,
            "applies_to": ["Photometrics Iris 15B"],
        },
        selected_step="Connection",
        advanced_mode=False,
        selected_device="Virtual Device",
    )


def test_advanced_mode_shows_device_specific_fields_on_matching_step():
    assert field_is_visible(
        field_key="camera_connection",
        widget_spec=["Camera Connection", "Input", "string", None, None],
        field_metadata={
            "step": "Connection",
            "importance": "advanced",
            "applies_to": ["Photometrics Iris 15B"],
        },
        selected_step="Connection",
        advanced_mode=True,
        selected_device="Virtual Device",
    )


def test_field_visibility_honors_selected_step():
    assert not field_is_visible(
        field_key="delay",
        widget_spec=["Delay", "Spinbox", "float", {}, None],
        field_metadata={"step": "Timing", "importance": "recommended"},
        selected_step="Connection",
        advanced_mode=True,
        selected_device="Virtual Device",
    )


def test_collect_step_warnings_reports_missing_required_values():
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {}, None],
        "sample_rate": ["Sample Rate", "Input", "int", None, None],
    }
    metadata = {
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "sample_rate": {"step": "Timing", "importance": "required"},
        }
    }
    values = {"hardware/type": "National Instruments", "sample_rate": ""}

    assert collect_step_warnings(widgets, metadata, values) == {
        "Timing": ["Sample Rate is required."]
    }


def test_merge_loaded_and_edited_values_preserves_hidden_values_without_type_change():
    loaded = {
        "hardware": {
            "type": "Photometrics",
            "serial_number": "302352",
            "camera_connection": "USB",
        },
        "delay": 10,
    }
    edited = {"hardware": {"type": "Photometrics"}, "delay": 12}

    result = merge_loaded_and_edited_values(
        loaded_block=loaded,
        edited_block=edited,
        device_type_changed=False,
    )

    assert result == {
        "hardware": {
            "type": "Photometrics",
            "serial_number": "302352",
            "camera_connection": "USB",
        },
        "delay": 12,
    }


def test_merge_loaded_and_edited_values_drops_loaded_values_after_type_change():
    loaded = {"hardware": {"type": "Photometrics", "camera_connection": "USB"}}
    edited = {"hardware": {"type": "Synthetic"}}

    result = merge_loaded_and_edited_values(
        loaded_block=deepcopy(loaded),
        edited_block=deepcopy(edited),
        device_type_changed=True,
    )

    assert result == edited
```

- [ ] **Step 2: Run tests to verify they fail for the missing module**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_wizard.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'navigate.config.configuration_wizard'`.

- [ ] **Step 3: Add the helper implementation**

Create `src/navigate/config/configuration_wizard.py`:

```python
"""Helpers for the configuration assistant mini-wizard UI."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_STEP = "Details"
BASIC_IMPORTANCE = {"required", "recommended"}
ADVANCED_IMPORTANCE = {"optional", "advanced"}
NON_FIELD_WIDGET_TYPES = {"Button", "Label"}


def get_field_metadata(metadata: dict[str, Any], field_key: str) -> dict[str, Any]:
    """Return metadata for a field, with conservative defaults."""
    fields = metadata.get("fields", {})
    field_metadata = fields.get(field_key, {})
    return {
        "step": field_metadata.get("step", DEFAULT_STEP),
        "importance": field_metadata.get("importance", "recommended"),
        **field_metadata,
    }


def get_steps(widgets: dict[str, list[Any]], metadata: dict[str, Any]) -> list[str]:
    """Return ordered wizard steps for a hardware tab."""
    configured_steps = metadata.get("steps", [])
    if configured_steps:
        return list(configured_steps)

    steps = []
    for field_key, widget_spec in widgets.items():
        if field_key == "frame_config":
            continue
        if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
            continue
        step = get_field_metadata(metadata, field_key)["step"]
        if step not in steps:
            steps.append(step)
    return steps or [DEFAULT_STEP]


def field_applies_to_device(
    field_metadata: dict[str, Any],
    selected_device: str | None,
) -> bool:
    """Return whether a metadata rule applies to the selected device label."""
    applies_to = field_metadata.get("applies_to")
    if not applies_to or not selected_device:
        return True
    return selected_device in applies_to


def field_is_visible(
    *,
    field_key: str,
    widget_spec: list[Any],
    field_metadata: dict[str, Any],
    selected_step: str,
    advanced_mode: bool,
    selected_device: str | None,
) -> bool:
    """Return whether a field should be visible for the current wizard state."""
    if field_key == "frame_config":
        return False
    if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
        return True
    if field_metadata.get("step", DEFAULT_STEP) != selected_step:
        return False
    if advanced_mode:
        return True
    if field_metadata.get("importance", "recommended") not in BASIC_IMPORTANCE:
        return False
    return field_applies_to_device(field_metadata, selected_device)


def _display_name(widget_spec: list[Any], field_key: str) -> str:
    if widget_spec and widget_spec[0]:
        return str(widget_spec[0])
    return field_key.replace("/", " ").replace("_", " ").title()


def collect_step_warnings(
    widgets: dict[str, list[Any]],
    metadata: dict[str, Any],
    values: dict[str, Any],
) -> dict[str, list[str]]:
    """Return required-field warnings grouped by wizard step."""
    warnings: dict[str, list[str]] = {}
    for field_key, widget_spec in widgets.items():
        if field_key == "frame_config":
            continue
        if widget_spec[1] in NON_FIELD_WIDGET_TYPES:
            continue
        field_metadata = get_field_metadata(metadata, field_key)
        if field_metadata.get("importance") != "required":
            continue
        value = values.get(field_key)
        if value is None or str(value).strip() == "":
            step = field_metadata.get("step", DEFAULT_STEP)
            warnings.setdefault(step, []).append(
                f"{_display_name(widget_spec, field_key)} is required."
            )
    return warnings


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def merge_loaded_and_edited_values(
    *,
    loaded_block: dict[str, Any] | None,
    edited_block: dict[str, Any],
    device_type_changed: bool,
) -> dict[str, Any]:
    """Merge visible edits with loaded hidden values."""
    if device_type_changed or not loaded_block:
        return deepcopy(edited_block)
    return _deep_merge(loaded_block, edited_block)
```

- [ ] **Step 4: Run helper tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_wizard.py -q
```

Expected: PASS.

- [ ] **Step 5: Format and commit Task 1**

Run:

```bash
ruff format src/navigate/config/configuration_wizard.py test/config/test_configuration_wizard.py
ruff check src/navigate/config/configuration_wizard.py test/config/test_configuration_wizard.py
git add src/navigate/config/configuration_wizard.py test/config/test_configuration_wizard.py
git commit -m "Add configurator wizard helper functions"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 2: Add Pilot Wizard Metadata

**Files:**
- Modify: `src/navigate/config/configuration_database.py`
- Modify: `test/config/test_configuration_database.py`

- [ ] **Step 1: Add failing metadata tests**

Append these tests to `test/config/test_configuration_database.py`:

```python
from navigate.config.configuration_database import (
    camera_hardware_widgets,
    daq_hardware_widgets,
    hardware_wizard_metadata,
    stage_hardware_widgets,
)


def test_hardware_wizard_metadata_has_shell_for_every_hardware_tab():
    expected_tabs = {
        "Camera",
        "Data Acquisition Card",
        "Filter Wheel",
        "Galvo",
        "Lasers",
        "Remote Focus Devices",
        "Adaptive Optics",
        "Shutters",
        "Stages",
        "Zoom Device",
    }

    assert set(hardware_wizard_metadata) == expected_tabs


def test_camera_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Camera"]["fields"]
    expected_field_keys = {
        key
        for key, value in camera_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }

    assert set(fields) == expected_field_keys
    assert hardware_wizard_metadata["Camera"]["device_field"] == "hardware/type"
    assert fields["hardware/type"]["importance"] == "required"
    assert fields["hardware/camera_connection"]["applies_to"] == [
        "Photometrics Iris 15B"
    ]


def test_daq_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Data Acquisition Card"]["fields"]
    expected_field_keys = {
        key
        for key, value in daq_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }

    assert set(fields) == expected_field_keys
    assert fields["sample_rate"]["importance"] == "required"
    assert fields["trigger_reset_count"]["importance"] == "advanced"


def test_stage_wizard_metadata_covers_all_fields():
    fields = hardware_wizard_metadata["Stages"]["fields"]
    expected_field_keys = {
        key
        for key, value in stage_hardware_widgets.items()
        if key != "frame_config" and value[1] not in {"Button", "Label"}
    }

    assert set(fields) == expected_field_keys
    assert hardware_wizard_metadata["Stages"]["device_field"] == "type"
    assert fields["volts_per_micron"]["applies_to"] == ["NI Analog/Digital Device"]
    assert fields["controllername"]["applies_to"] == ["Physik Instrumente"]
```

- [ ] **Step 2: Run tests to verify metadata is missing**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_database.py -q
```

Expected: FAIL with `ImportError` or `AttributeError` for `hardware_wizard_metadata`.

- [ ] **Step 3: Add metadata to `configuration_database.py`**

Append this near the bottom of `src/navigate/config/configuration_database.py`, before `deceased_device_type_names`:

```python
hardware_wizard_metadata = {
    "Camera": {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Connection", "Timing", "Orientation", "Review"],
        "fields": {
            "hardware/type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Select the camera driver used by this microscope.",
                "help": "Virtual Device is suitable for synthetic hardware tests.",
            },
            "hardware/serial_number": {
                "step": "Connection",
                "importance": "recommended",
                "hint": 'Example: "302352"',
                "help": "Use the manufacturer serial number when the camera driver needs a specific device.",
            },
            "hardware/camera_connection": {
                "step": "Connection",
                "importance": "advanced",
                "applies_to": ["Photometrics Iris 15B"],
                "hint": "Photometrics Iris 15B only.",
                "help": "Leave hidden in Basic mode unless configuring a Photometrics Iris 15B camera.",
            },
            "defect_correct_mode": {
                "step": "Timing",
                "importance": "recommended",
                "hint": "Use Off unless the camera workflow requires correction.",
                "help": "This value maps to the camera defect-correction mode used by supported drivers.",
            },
            "delay": {
                "step": "Timing",
                "importance": "recommended",
                "hint": "Camera trigger delay in milliseconds.",
                "help": "This delay contributes to acquisition timing and waveform alignment.",
            },
            "settle_down": {
                "step": "Timing",
                "importance": "advanced",
                "hint": "Additional camera settle time in milliseconds.",
                "help": "Use this only when a camera needs extra time before exposure timing is stable.",
            },
            "flip_x": {
                "step": "Orientation",
                "importance": "recommended",
                "hint": "Flip camera images along X.",
                "help": "Use when the camera orientation is reversed relative to the microscope coordinate system.",
            },
            "flip_y": {
                "step": "Orientation",
                "importance": "recommended",
                "hint": "Flip camera images along Y.",
                "help": "Use when the camera orientation is reversed relative to the microscope coordinate system.",
            },
            "supported_channel_count": {
                "step": "Review",
                "importance": "recommended",
                "hint": "Number of channels to expose in the microscope UI.",
                "help": "This controls how many channel rows the microscope can present.",
            },
        },
    },
    "Data Acquisition Card": {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Timing", "Triggering", "Laser Switching", "Review"],
        "fields": {
            "hardware/type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Select the DAQ or virtual timing device.",
                "help": "National Instruments is the common physical DAQ path. Virtual Device is for synthetic hardware.",
            },
            "sample_rate": {
                "step": "Timing",
                "importance": "required",
                "hint": "Example: 100000",
                "help": "Sample rate controls generated analog and digital timing resolution.",
            },
            "trigger_reset_count": {
                "step": "Timing",
                "importance": "advanced",
                "hint": "Default: 0 disables trigger reset.",
                "help": "Use a positive value only for unstable systems that need periodic trigger reset.",
            },
            "master_trigger_out_line": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Example: PXI6259/port0/line1",
                "help": "Digital output line for the master trigger.",
            },
            "camera_trigger_out_line": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Example: /PXI6259/ctr0",
                "help": "Counter or digital output line used to trigger the camera.",
            },
            "trigger_source": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Example: /PXI6259/PFI0",
                "help": "Input line used as the external trigger source.",
            },
            "laser_port_switcher": {
                "step": "Laser Switching",
                "importance": "advanced",
                "applies_to": ["National Instruments"],
                "hint": "Example: PXI6733/port0/line0",
                "help": "Digital line used by systems with a laser port switcher.",
            },
            "laser_switch_state": {
                "step": "Laser Switching",
                "importance": "advanced",
                "applies_to": ["National Instruments"],
                "hint": "Logical state that turns the switch on.",
                "help": "Keep this hidden unless a laser port switcher is installed.",
            },
        },
    },
    "Stages": {
        "device_field": "type",
        "steps": [
            "Device Type",
            "Axes",
            "Motion Limits",
            "Controller Settings",
            "Advanced",
            "Review",
        ],
        "fields": {
            "type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Select the stage controller type.",
                "help": "The selected stage type determines which controller fields are relevant.",
            },
            "serial_number": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Controller serial number when required by the driver.",
                "help": "Some USB or vendor drivers need a serial number to select the correct controller.",
            },
            "axes": {
                "step": "Axes",
                "importance": "required",
                "hint": "Example: [x, y, z]",
                "help": "Axes define which microscope dimensions this stage controls.",
            },
            "axes_mapping": {
                "step": "Axes",
                "importance": "recommended",
                "hint": "Example: [X, M, Y]",
                "help": "Maps Navigate axes to controller-specific axis labels.",
            },
            "feedback_alignment": {
                "step": "Axes",
                "importance": "advanced",
                "applies_to": [
                    "Applied Scientific Instrumentation",
                    "ASI MFC2000",
                    "ASI MS2000",
                ],
                "hint": "ASI stage only. Example: [90, 90, 90]",
                "help": "Defines ASI feedback alignment for configured axes.",
            },
            "device_units_per_mm": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["ThorLabs KCube Inertial Device KST101"],
                "hint": "KST101 only. Example: 2000.0",
                "help": "Conversion between controller units and microscope distance.",
            },
            "volts_per_micron": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Analog stage only. Example: 0.1*x+0.05",
                "help": "Expression used to convert microns into analog control voltage.",
            },
            "min": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Minimum analog output voltage.",
                "help": "Only used by analog stage control.",
            },
            "max": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Maximum analog output voltage.",
                "help": "Only used by analog stage control.",
            },
            "distance_threshold": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Analog-controlled stage threshold.",
                "help": "Used for analog-controlled galvo or piezo stage behavior.",
            },
            "settle_duration_ms": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Analog stage settle duration in milliseconds.",
                "help": "Adds settling time after analog-controlled movement.",
            },
            "controllername": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "PI only. Example: C-884",
                "help": "Physik Instrumente controller model name.",
            },
            "stages": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "PI only. Example: L-509.20DG10 L-509.40DG10",
                "help": "Physik Instrumente stage model list.",
            },
            "refmode": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "PI only. Example: FRF FRF",
                "help": "Physik Instrumente reference modes.",
            },
            "port": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Example: COM1",
                "help": "Serial port for stage controllers that communicate over serial.",
            },
            "baudrate": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Example: 9600",
                "help": "Serial baudrate for compatible stage controllers.",
            },
            "timeout": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Example: 0.25",
                "help": "Serial timeout in seconds.",
            },
        },
    },
    "Filter Wheel": {"steps": ["Details"], "fields": {}},
    "Galvo": {"steps": ["Details"], "fields": {}},
    "Lasers": {"steps": ["Details"], "fields": {}},
    "Remote Focus Devices": {"steps": ["Details"], "fields": {}},
    "Adaptive Optics": {"steps": ["Details"], "fields": {}},
    "Shutters": {"steps": ["Details"], "fields": {}},
    "Zoom Device": {"steps": ["Details"], "fields": {}},
}
```

- [ ] **Step 4: Run metadata tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_database.py -q
```

Expected: PASS.

- [ ] **Step 5: Format and commit Task 2**

Run:

```bash
ruff format src/navigate/config/configuration_database.py test/config/test_configuration_database.py
ruff check src/navigate/config/configuration_database.py test/config/test_configuration_database.py
git add src/navigate/config/configuration_database.py test/config/test_configuration_database.py
git commit -m "Add configurator wizard metadata"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 3: Pass Metadata Into Hardware Tabs

**Files:**
- Modify: `src/navigate/controller/configurator.py`
- Modify: `src/navigate/view/configurator_application_window.py`
- Modify: `test/view/test_configurator_application_window.py`

- [ ] **Step 1: Add failing view test for metadata on hardware tabs**

Append this test to `test/view/test_configurator_application_window.py`:

```python
from navigate.view.configurator_application_window import HardwareTab


def test_hardware_tab_stores_wizard_metadata(tk_root):
    metadata = {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Timing"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "delay": {"step": "Timing", "importance": "recommended"},
        },
    }
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {"Virtual": "Synthetic"}, None],
        "delay": ["Delay", "Spinbox", "float", {"from": 0, "to": 10}, None],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert tab.wizard_metadata == metadata
    assert tab.wizard_steps == ["Device Type", "Timing"]
    assert tab.current_step.get() == "Device Type"

    tab.destroy()
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_stores_wizard_metadata -q
```

Expected: FAIL with `TypeError` for unexpected `wizard_metadata` or missing attributes.

- [ ] **Step 3: Update `HardwareTab.__init__` to accept metadata**

Modify the imports in `src/navigate/view/configurator_application_window.py`:

```python
from navigate.config.configuration_wizard import get_steps
```

Update the `HardwareTab.__init__` signature and initialization:

```python
class HardwareTab(ttk.Frame):
    def __init__(
        self,
        name,
        hardware_widgets,
        *args,
        widgets=None,
        top_widgets=None,
        hardware_widgets_value=[None],
        constants_widgets_value=[None],
        wizard_metadata=None,
        **kwargs,
    ):
        ...
        self.name = name
        self.wizard_metadata = wizard_metadata or {}
        self.wizard_steps = get_steps(hardware_widgets or {}, self.wizard_metadata)
        self.current_step = tk.StringVar(value=self.wizard_steps[0])
        self.advanced_mode = tk.BooleanVar(value=False)
```

Do not change field rendering in this step.

- [ ] **Step 4: Pass metadata from `MicroscopeTab.create_hardware_tab`**

Update the `MicroscopeTab.create_hardware_tab` signature:

```python
def create_hardware_tab(
    self,
    name,
    hardware_widgets,
    widgets=None,
    top_widgets=None,
    wizard_metadata=None,
    **kwargs,
):
    tab = HardwareTab(
        name,
        hardware_widgets,
        widgets=widgets,
        top_widgets=top_widgets,
        wizard_metadata=wizard_metadata,
        **kwargs,
    )
```

Update `src/navigate/controller/configurator.py` imports:

```python
from navigate.config.configuration_database import (
    hardwares_dict,
    hardwares_config_name_dict,
    hardware_wizard_metadata,
)
```

Update both places that call `microscope_tab.create_hardware_tab(...)` so they pass:

```python
wizard_metadata=hardware_wizard_metadata.get(hardware_type, {})
```

- [ ] **Step 5: Run the targeted view test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_stores_wizard_metadata -q
```

Expected: PASS.

- [ ] **Step 6: Run existing configurator view tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 7: Format and commit Task 3**

Run:

```bash
ruff format src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
ruff check src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git add src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git commit -m "Pass wizard metadata into configurator tabs"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 4: Render Shared Mini-Wizard Shell

**Files:**
- Modify: `src/navigate/view/configurator_application_window.py`
- Modify: `test/view/test_configurator_application_window.py`

- [ ] **Step 1: Add failing shell-rendering test**

Append this test:

```python
def test_hardware_tab_builds_wizard_shell(tk_root):
    metadata = {
        "steps": ["Device Type", "Timing"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "delay": {"step": "Timing", "importance": "recommended"},
        },
    }
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {"Virtual": "Synthetic"}, None],
        "delay": ["Delay", "Spinbox", "float", {"from": 0, "to": 10}, None],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert isinstance(tab.step_frame, ttk.Frame)
    assert isinstance(tab.field_frame, ttk.Frame)
    assert isinstance(tab.help_frame, ttk.Frame)
    assert len(tab.step_buttons) == 2
    assert "Device Type" in tab.step_buttons
    assert "Timing" in tab.step_buttons

    tab.destroy()
```

- [ ] **Step 2: Run the failing shell test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_builds_wizard_shell -q
```

Expected: FAIL with missing `step_frame`, `field_frame`, `help_frame`, or `step_buttons`.

- [ ] **Step 3: Build shell frames in `HardwareTab.__init__`**

In `HardwareTab.__init__`, replace the single-column `content_frame` children with a wizard body. Keep `top_frame`, `hardware_frame`, and `bottom_frame` as attributes so existing code paths still have containers:

```python
self.wizard_header = ttk.Frame(content_frame)
self.wizard_header.grid(
    row=0,
    column=0,
    sticky=tk.NSEW,
    padx=get_theme_space_px(10),
    pady=get_theme_space_px(3),
)

self.advanced_toggle = ttk.Checkbutton(
    self.wizard_header,
    text="Advanced",
    variable=self.advanced_mode,
    command=self.refresh_wizard_visibility,
)
self.advanced_toggle.grid(row=0, column=0, sticky=tk.W)

self.wizard_body = ttk.Frame(content_frame)
self.wizard_body.grid(row=1, column=0, sticky=tk.NSEW, padx=get_theme_space_px(10))

self.step_frame = ttk.Frame(self.wizard_body)
self.step_frame.grid(row=0, column=0, sticky=tk.NW, padx=get_theme_padding_px((0, 8)))

self.field_frame = ttk.Frame(self.wizard_body)
self.field_frame.grid(row=0, column=1, sticky=tk.NSEW)

self.help_frame = ttk.Frame(self.wizard_body)
self.help_frame.grid(row=0, column=2, sticky=tk.NW, padx=get_theme_padding_px((8, 0)))

self.top_frame = ttk.Frame(self.field_frame)
self.top_frame.grid(row=0, column=0, sticky=tk.NSEW)

self.hardware_frame = ttk.Frame(self.field_frame)
self.hardware_frame.grid(row=1, column=0, sticky=tk.NSEW)

self.bottom_frame = ttk.Frame(self.field_frame)
self.bottom_frame.grid(row=2, column=0, sticky=tk.NSEW)

self.step_buttons = {}
for index, step in enumerate(self.wizard_steps):
    button = ttk.Button(
        self.step_frame,
        text=step,
        command=lambda step=step: self.select_wizard_step(step),
    )
    button.grid(row=index, column=0, sticky=tk.EW, pady=get_theme_space_px(1))
    self.step_buttons[step] = button
```

Add these methods to `HardwareTab`:

```python
def select_wizard_step(self, step: str) -> None:
    """Select a wizard step and refresh visible fields."""
    self.current_step.set(step)
    self.refresh_wizard_visibility()

def refresh_wizard_visibility(self) -> None:
    """Refresh wizard field visibility."""
    return
```

- [ ] **Step 4: Run shell tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_builds_wizard_shell -q
```

Expected: PASS.

- [ ] **Step 5: Run all configurator view tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 6: Format and commit Task 4**

Run:

```bash
ruff format src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
ruff check src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git add src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git commit -m "Render configurator mini wizard shell"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 5: Add Step And Mode-Based Field Visibility

**Files:**
- Modify: `src/navigate/view/configurator_application_window.py`
- Modify: `test/view/test_configurator_application_window.py`

- [ ] **Step 1: Add failing test for step filtering**

Append this test:

```python
def test_hardware_tab_filters_fields_by_step_and_advanced_mode(tk_root):
    metadata = {
        "device_field": "hardware/type",
        "steps": ["Device Type", "Connection"],
        "fields": {
            "hardware/type": {"step": "Device Type", "importance": "required"},
            "hardware/camera_connection": {
                "step": "Connection",
                "importance": "advanced",
                "applies_to": ["Photometrics Iris 15B"],
            },
        },
    }
    widgets = {
        "hardware/type": [
            "Device Type",
            "Combobox",
            "string",
            {"Photometrics Iris 15B": "Photometrics", "Virtual Device": "Synthetic"},
            None,
        ],
        "hardware/camera_connection": [
            "Camera Connection",
            "Input",
            "string",
            None,
            "Photometrics Iris 15B only",
        ],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tk_root.update_idletasks()

    assert tab.field_rows["hardware/type"].winfo_ismapped()
    assert not tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.select_wizard_step("Connection")
    tk_root.update_idletasks()
    assert not tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.advanced_mode.set(True)
    tab.refresh_wizard_visibility()
    tk_root.update_idletasks()
    assert tab.field_rows["hardware/camera_connection"].winfo_ismapped()

    tab.destroy()
```

- [ ] **Step 2: Run the failing filtering test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_filters_fields_by_step_and_advanced_mode -q
```

Expected: FAIL with missing `field_rows` or visible-row assertion failure.

- [ ] **Step 3: Store field row frames and metadata during widget creation**

Update imports:

```python
from navigate.config.configuration_wizard import (
    field_is_visible,
    get_field_metadata,
    get_steps,
)
```

In `HardwareTab.__init__`, initialize:

```python
self.field_rows = {}
self.field_widgets = {}
self.field_info_labels = {}
self.field_specs = {}
self.field_variables = {}
```

In `create_hardware_widgets`, wrap each non-label row in a row frame and store it:

```python
row_frame = ttk.Frame(content_frame)
row_frame.grid(row=i, column=0, columnspan=3, sticky=tk.NSEW)
self.field_rows[k] = row_frame
self.field_specs[k] = v
row_parent = row_frame
```

Grid the label, widget, and info label into `row_parent` instead of `content_frame`. Store widgets:

```python
self.field_widgets[k] = widget
self.field_variables[k] = self.variables[k]
```

For button and label rows, keep current behavior unless the row can be safely wrapped without changing button callbacks.

- [ ] **Step 4: Implement selected device lookup and refresh**

Add methods to `HardwareTab`:

```python
def get_selected_device(self) -> str | None:
    """Return the current selected device label for this tab."""
    device_field = self.wizard_metadata.get("device_field")
    if not device_field:
        return None
    variable = self.field_variables.get(device_field)
    if variable is None:
        return None
    try:
        return variable.get()
    except tk._tkinter.TclError:
        return None

def refresh_wizard_visibility(self) -> None:
    """Refresh fields for the active step and mode."""
    selected_step = self.current_step.get()
    selected_device = self.get_selected_device()
    advanced_mode = bool(self.advanced_mode.get())
    for field_key, row in self.field_rows.items():
        widget_spec = self.field_specs.get(field_key)
        if widget_spec is None:
            row.grid_remove()
            continue
        metadata = get_field_metadata(self.wizard_metadata, field_key)
        if field_is_visible(
            field_key=field_key,
            widget_spec=widget_spec,
            field_metadata=metadata,
            selected_step=selected_step,
            advanced_mode=advanced_mode,
            selected_device=selected_device,
        ):
            row.grid()
        else:
            row.grid_remove()
```

When creating a Combobox for the metadata device field, bind:

```python
if k == self.wizard_metadata.get("device_field"):
    widget.bind("<<ComboboxSelected>>", lambda event: self.refresh_wizard_visibility())
```

Call `self.refresh_wizard_visibility()` at the end of `build_widgets`.

- [ ] **Step 5: Run the filtering test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_filters_fields_by_step_and_advanced_mode -q
```

Expected: PASS.

- [ ] **Step 6: Run view tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 7: Format and commit Task 5**

Run:

```bash
ruff format src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
ruff check src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git add src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git commit -m "Filter configurator fields by wizard state"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 6: Add Contextual Help And Inline Warnings

**Files:**
- Modify: `src/navigate/view/configurator_application_window.py`
- Modify: `test/view/test_configurator_application_window.py`

- [ ] **Step 1: Add failing test for help text and warnings**

Append this test:

```python
def test_hardware_tab_updates_help_and_warning_text(tk_root):
    metadata = {
        "steps": ["Device Type"],
        "fields": {
            "hardware/type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Select a camera.",
                "help": "Virtual Device is suitable for synthetic hardware.",
            },
        },
    }
    widgets = {
        "hardware/type": ["Device Type", "Combobox", "string", {"": "", "Virtual Device": "Synthetic"}, None],
    }

    tab = HardwareTab("Camera", widgets, root=tk_root, wizard_metadata=metadata)
    tab.variables["hardware/type"].set("")
    tab.refresh_wizard_visibility()
    tk_root.update_idletasks()

    assert "Virtual Device is suitable" in tab.help_text.get("1.0", "end")
    assert "Device Type is required." in tab.warning_text.get("1.0", "end")

    tab.destroy()
```

- [ ] **Step 2: Run the failing help test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_updates_help_and_warning_text -q
```

Expected: FAIL with missing `help_text` or `warning_text`.

- [ ] **Step 3: Add help and warning widgets**

In `HardwareTab.__init__`, after creating `self.help_frame`, add:

```python
self.help_title = ttk.Label(self.help_frame, text="Help")
self.help_title.grid(row=0, column=0, sticky=tk.W, pady=get_theme_padding_px((0, 3)))

self.help_text = tk.Text(self.help_frame, width=32, height=8, wrap="word")
self.help_text.grid(row=1, column=0, sticky=tk.NSEW)
self.help_text.configure(state="disabled")

self.warning_title = ttk.Label(self.help_frame, text="Warnings")
self.warning_title.grid(row=2, column=0, sticky=tk.W, pady=get_theme_padding_px((8, 3)))

self.warning_text = tk.Text(self.help_frame, width=32, height=6, wrap="word")
self.warning_text.grid(row=3, column=0, sticky=tk.NSEW)
self.warning_text.configure(state="disabled")
```

- [ ] **Step 4: Update help and warning content during refresh**

Add imports:

```python
from navigate.config.configuration_wizard import collect_step_warnings
```

Add methods to `HardwareTab`:

```python
def _current_values(self) -> dict[str, str]:
    values = {}
    for key, variable in self.field_variables.items():
        try:
            values[key] = variable.get()
        except tk._tkinter.TclError:
            values[key] = ""
    return values

def _set_text_widget(self, widget: tk.Text, text: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    widget.configure(state="disabled")

def update_wizard_help(self) -> None:
    selected_step = self.current_step.get()
    help_lines = []
    for field_key in self.field_rows:
        metadata = get_field_metadata(self.wizard_metadata, field_key)
        if metadata.get("step") != selected_step:
            continue
        help_text = metadata.get("help")
        if help_text:
            help_lines.append(help_text)
    self._set_text_widget(self.help_text, "\n\n".join(help_lines))

def update_wizard_warnings(self) -> None:
    warnings = collect_step_warnings(
        self.field_specs,
        self.wizard_metadata,
        self._current_values(),
    )
    current = warnings.get(self.current_step.get(), [])
    self._set_text_widget(self.warning_text, "\n".join(current))
```

At the end of `refresh_wizard_visibility`, call:

```python
self.update_wizard_help()
self.update_wizard_warnings()
```

- [ ] **Step 5: Run the help test**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py::test_hardware_tab_updates_help_and_warning_text -q
```

Expected: PASS.

- [ ] **Step 6: Run view tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 7: Format and commit Task 6**

Run:

```bash
ruff format src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
ruff check src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git add src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py
git commit -m "Add configurator wizard help and warnings"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 7: Preserve Loaded Hidden Values On Save

**Files:**
- Modify: `src/navigate/controller/configurator.py`
- Modify: `test/config/test_configuration_wizard.py`

- [ ] **Step 1: Add focused tests for stale-value warnings**

Append these tests to `test/config/test_configuration_wizard.py`:

```python
from navigate.config.configuration_wizard import device_type_changed


def test_device_type_changed_reads_nested_device_type():
    loaded = {"hardware": {"type": "Photometrics"}}
    edited = {"hardware": {"type": "Synthetic"}}

    assert device_type_changed(loaded, edited, "hardware/type")
    assert not device_type_changed(loaded, loaded, "hardware/type")


def test_device_type_changed_handles_missing_loaded_value():
    edited = {"hardware": {"type": "Synthetic"}}

    assert not device_type_changed(None, edited, "hardware/type")
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_wizard.py::test_device_type_changed_reads_nested_device_type test/config/test_configuration_wizard.py::test_device_type_changed_handles_missing_loaded_value -q
```

Expected: FAIL with missing `device_type_changed`.

- [ ] **Step 3: Add nested lookup and device-type comparison helper**

Add this to `src/navigate/config/configuration_wizard.py`:

```python
def nested_get(data: dict[str, Any] | None, path: str) -> Any:
    """Return a nested value using slash-separated configurator paths."""
    if not data:
        return None
    current: Any = data
    for part in path.split("/"):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def device_type_changed(
    loaded_block: dict[str, Any] | None,
    edited_block: dict[str, Any],
    device_field: str | None,
) -> bool:
    """Return whether a hardware block changed device type during editing."""
    if not loaded_block or not device_field:
        return False
    loaded_value = nested_get(loaded_block, device_field)
    edited_value = nested_get(edited_block, device_field)
    if loaded_value is None or edited_value is None:
        return False
    return loaded_value != edited_value
```

- [ ] **Step 4: Run helper tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_wizard.py -q
```

Expected: PASS.

- [ ] **Step 5: Track loaded hardware blocks on created hardware tabs**

In `src/navigate/view/configurator_application_window.py`, initialize on `HardwareTab`:

```python
self.loaded_hardware_block = None
```

In `src/navigate/controller/configurator.py`, inside `load_configuration`, after each `create_hardware_tab(...)`, get the newly created hardware tab and store the loaded block:

```python
hardware_tab = microscope_tab.tab_list[-1]
hardware_tab.loaded_hardware_block = config_dict["microscopes"][microscope_name].get(
    hardware_ref_name,
    None,
)
```

If `tab_list[-1]` is not the widget instance in this code path, use the tab id returned by `microscope_tab.tabs()[-1]` and resolve it with `microscope_tab.nametowidget(...)`.

- [ ] **Step 6: Merge loaded hidden values during save**

Import helpers in `src/navigate/controller/configurator.py`:

```python
from navigate.config.configuration_wizard import (
    device_type_changed,
    merge_loaded_and_edited_values,
)
```

After `hardware_dict` is populated for a hardware tab in `save`, merge it:

```python
metadata = hardware_wizard_metadata.get(hardware_name, {})
changed_type = device_type_changed(
    getattr(hardware_tab, "loaded_hardware_block", None),
    hardware_dict,
    metadata.get("device_field"),
)
if changed_type:
    warning_info[hardware_name] = True
hardware_dict = merge_loaded_and_edited_values(
    loaded_block=getattr(hardware_tab, "loaded_hardware_block", None),
    edited_block=hardware_dict,
    device_type_changed=changed_type,
)
microscope_dict[hardwares_config_name_dict.get(hardware_name, hardware_name)] = hardware_dict
```

Move the existing assignment to `microscope_dict[...]` so it happens after the merge, not before.

- [ ] **Step 7: Run helper tests and a syntax-focused controller import check**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_wizard.py test/view/test_configurator_application_window.py -q
python - <<'PY'
from navigate.controller.configurator import Configurator
print(Configurator.__name__)
PY
```

Expected: pytest PASS and the import check prints `Configurator`.

- [ ] **Step 8: Format and commit Task 7**

Run:

```bash
ruff format src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/config/test_configuration_wizard.py
ruff check src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/config/test_configuration_wizard.py
git add src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/config/test_configuration_wizard.py
git commit -m "Preserve hidden configurator values on save"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 8: Validate Pilot Behavior End-To-End

**Files:**
- Modify: `test/view/test_configurator_application_window.py`
- Modify: `test/config/test_configuration_database.py`

- [ ] **Step 1: Add metadata-driven pilot visibility tests**

Append this test to `test/view/test_configurator_application_window.py`:

```python
from navigate.config.configuration_database import (
    camera_hardware_widgets,
    daq_hardware_widgets,
    hardware_wizard_metadata,
    stage_hardware_widgets,
)


def test_pilot_tabs_can_render_with_wizard_metadata(tk_root):
    cases = [
        ("Camera", camera_hardware_widgets),
        ("Data Acquisition Card", daq_hardware_widgets),
        ("Stages", stage_hardware_widgets),
    ]
    for name, widgets in cases:
        tab = HardwareTab(
            name,
            widgets,
            root=tk_root,
            wizard_metadata=hardware_wizard_metadata[name],
        )
        tk_root.update_idletasks()

        assert tab.wizard_steps == hardware_wizard_metadata[name]["steps"]
        assert tab.step_buttons
        assert tab.field_rows

        tab.destroy()
```

- [ ] **Step 2: Add non-pilot shell metadata test**

Append this test to `test/config/test_configuration_database.py`:

```python
def test_non_pilot_wizard_metadata_uses_details_shell():
    for name in [
        "Filter Wheel",
        "Galvo",
        "Lasers",
        "Remote Focus Devices",
        "Adaptive Optics",
        "Shutters",
        "Zoom Device",
    ]:
        assert hardware_wizard_metadata[name]["steps"] == ["Details"]
        assert hardware_wizard_metadata[name]["fields"] == {}
```

- [ ] **Step 3: Run pilot and metadata tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_database.py test/config/test_configuration_wizard.py test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 4: Run full configurator view tests**

Run:

```bash
python -m pytest -o addopts='' test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 8**

Run:

```bash
ruff format src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py test/config/test_configuration_database.py
ruff check src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py test/config/test_configuration_database.py
git add src/navigate/view/configurator_application_window.py test/view/test_configurator_application_window.py test/config/test_configuration_database.py
git commit -m "Validate pilot configurator wizard tabs"
```

Expected: `ruff` exits 0 and the commit succeeds.

---

### Task 9: Run Full Verification

**Files:**
- No planned source edits unless verification reveals a concrete failure.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
python -m pytest -o addopts='' test/config/test_configuration_database.py test/config/test_configuration_wizard.py test/view/test_configurator_application_window.py -q
```

Expected: PASS.

- [ ] **Step 2: Run relevant controller tests**

Run:

```bash
python -m pytest -o addopts='' test/controller/test_configuration_controller.py -q
```

Expected: PASS.

- [ ] **Step 3: Run lint and formatting checks**

Run:

```bash
ruff check src/navigate/config/configuration_database.py src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/config/test_configuration_database.py test/config/test_configuration_wizard.py test/view/test_configurator_application_window.py
ruff format --check src/navigate/config/configuration_database.py src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py test/config/test_configuration_database.py test/config/test_configuration_wizard.py test/view/test_configurator_application_window.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 4: Run a synthetic configurator launch smoke test**

Use the existing Navigate conda environment:

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate navigate
python - <<'PY'
import tkinter as tk
from navigate.view.configurator_application_window import ConfigurationAssistantWindow

root = tk.Tk()
root.withdraw()
view = ConfigurationAssistantWindow(root)
root.update_idletasks()
view.destroy()
root.destroy()
print("configurator-window-ok")
PY
```

Expected: prints `configurator-window-ok` with no traceback.

- [ ] **Step 5: Confirm verification did not leave uncommitted changes**

Run:

```bash
git status --short
```

Expected: no output when Step 1 through Step 4 already pass.

---

### Task 10: Final Review Checklist

**Files:**
- Inspect: `src/navigate/config/configuration_database.py`
- Inspect: `src/navigate/config/configuration_wizard.py`
- Inspect: `src/navigate/controller/configurator.py`
- Inspect: `src/navigate/view/configurator_application_window.py`
- Inspect: `test/config/test_configuration_database.py`
- Inspect: `test/config/test_configuration_wizard.py`
- Inspect: `test/view/test_configurator_application_window.py`

- [ ] **Step 1: Confirm scope matches the approved spec**

Check these statements against the diff:

```text
Camera, DAQ, and Stages have full field metadata.
Every hardware tab has a wizard shell.
Basic mode is the default.
Step navigation is clickable and non-blocking.
Hidden loaded values are preserved unless device type changes.
Device type changes warn before stale values are dropped on save.
```

- [ ] **Step 2: Confirm no visual-companion or scratch files are staged**

Run:

```bash
git status --short
```

Expected: no `.superpowers/`, temp image, or scratch file appears in staged changes.

- [ ] **Step 3: Inspect final diff**

Run:

```bash
git diff --stat HEAD
git diff -- src/navigate/config/configuration_database.py src/navigate/config/configuration_wizard.py src/navigate/controller/configurator.py src/navigate/view/configurator_application_window.py
```

Expected: the diff only contains configurator wizard implementation and tests.

- [ ] **Step 4: Prepare handoff summary**

Include:

```text
Implemented mini-wizard shell for configurator hardware tabs.
Added metadata-driven Basic/Advanced filtering for Camera, DAQ, and Stages.
Added contextual help and inline warnings.
Preserved hidden loaded values on save unless device type changes.
Verified with targeted pytest, ruff, git diff --check, and a Tk smoke test.
```
