# Channel-Aware Defocus and Autofocus Calibration Implementation Plan

> **For the implementing agent:** REQUIRED SUB-SKILL: Use test-driven development to implement this plan.

**Goal:** Make per-channel defocus absolute to a channel-independent zero-defocus focus position instead of relative to whichever channel happens to be selected first, and add an autofocus calibration workflow that can measure and populate per-channel defocus values.

**Architecture:** Defocus remains stored only in each channel entry under `configuration["experiment"]["MicroscopeState"]["channels"][channel_key]["defocus"]`. Acquisition code derives a transient `zero_defocus_focus` at runtime by subtracting the active channel defocus from the current focus position. Every channel then moves to `zero_defocus_focus + channel_defocus`. Autofocus can optionally target a specific channel and report its best focus position back to the controller; the controller stores only a temporary calibration reference in memory and writes measured defocus values into the existing per-channel field.

**Tech Stack:** Python 3.9.7 in conda env `navigate`, Tkinter GUI, ProxyDict/YAML configuration, pytest, ruff.

---

## File Structure

Modify these files:

- `/Users/Dean/Documents/GitHub/navigate/src/navigate/config/gui_configuration.yml` - allow signed defocus values in the GUI spinbox.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/config/config.py` - validate `defocus` as a float without rejecting negative values.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/microscope.py` - derive and use a channel-independent runtime zero-defocus focus position for single, live, continuous, and customized acquisitions.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/common_features.py` - apply the same zero-defocus reference model to software z-stack and ASI z-stack acquisitions.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/autofocus.py` - support selecting the autofocus channel and reporting best focus metadata for defocus calibration.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/autofocus.py` - add the reference-capture and populate-defocus autofocus workflow.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/view/popups/autofocus_setting_popup.py` - add channel and calibration controls.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_tab.py` - add a custom event for programmatically updating a channel defocus widget.
- `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_settings.py` - confirm widget updates continue to write into the existing channel dictionary.

Add or extend tests in:

- `/Users/Dean/Documents/GitHub/navigate/test/config/test_config.py`
- `/Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py`
- `/Users/Dean/Documents/GitHub/navigate/test/model/features/test_common_features.py`
- `/Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py`
- `/Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_autofocus.py`
- `/Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_channels_settings.py`

---

## Current Behavior To Preserve And Correct

Current behavior:

- Channel defocus is already persisted in the experiment config under each channel.
- `PrepareNextChannel` currently stores `central_focus` from the stage position when the first selected channel is prepared, then moves every channel to `central_focus + channel["defocus"]`.
- Z-stack logic stores a selected-channel `defocus` list, then adds the selected channel offset to stack focus positions.
- Autofocus currently calls `prepare_acquisition()` and `prepare_next_channel()`, so it always autofocuses using the first selected acquisition channel.

Problem:

- The runtime reference is effectively the current focus position of the first selected channel.
- If channel 2 is focused with defocus `+3.0`, and channel 1 is later deselected, channel 2 becomes the first selected channel but still receives `+3.0` from its own already-focused plane.
- This makes the focus plane depend on selection order rather than channel calibration.

Required behavior:

- Defocus values are offsets from a zero-defocus focus position.
- The zero-defocus focus position is not a persistent configuration value.
- At acquisition start, infer it from the currently focused channel:

```python
zero_defocus_focus = current_focus_position - active_channel_defocus
target_focus = zero_defocus_focus + target_channel_defocus
```

- For a channel whose defocus is already physically applied at the microscope, preparing that same channel should not move focus.
- Changing the first selected channel should not change the physical meaning of the stored defocus values.
- Autofocus calibration writes only the measured per-channel `defocus` into the existing channel field.

---

## Implementation Tasks

### 1. Allow Signed Per-Channel Defocus

Signed defocus is required because chromatic focus shifts can be above or below the zero-defocus focus position.

- [ ] Write a failing config validation test in `/Users/Dean/Documents/GitHub/navigate/test/config/test_config.py`.

```python
def test_verify_experiment_config_preserves_negative_channel_defocus(self):
    experiment = build_minimal_experiment_config()
    experiment["MicroscopeState"]["channels"]["channel_2"]["defocus"] = -2.5

    verify_experiment_config(experiment)

    assert experiment["MicroscopeState"]["channels"]["channel_2"]["defocus"] == -2.5
```

Use the local helper style that already exists in `test_config.py`; do not introduce a second config fixture pattern unless the existing tests cannot express this.

- [ ] Run the focused test and confirm it fails for the current implementation:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/config/test_config.py -q
```

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/config/gui_configuration.yml` so `channel_settings.defocus.min` allows negative values. Use a conservative symmetric range, for example `-100.0` to `100.0`, unless nearby hardware constraints imply a larger existing range.

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/config/config.py` so `defocus` remains float-validated but is not reset only because it is negative.

Expected shape:

```python
if k == "defocus":
    channel_value[k] = float(channel_value[k])
elif channel_value[k] < 0:
    channel_value[k] = temp[k]
```

- [ ] Run:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/config/test_config.py -q
```

---

### 2. Refactor Channel Preparation Around A Runtime Zero-Defocus Focus

This is the core acquisition behavior for single, live, continuous, and customized acquisition paths that use `PrepareNextChannel`.

- [ ] Write focused tests in `/Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py`.

Test case A: when the first selected channel already has a nonzero defocus and the stage is currently focused for that channel, preparing that channel does not add its defocus a second time.

```python
def test_prepare_next_channel_infers_zero_defocus_focus_from_current_channel(model):
    microscope = model.active_microscope
    microscope.prepare_acquisition()

    channels = microscope.configuration["experiment"]["MicroscopeState"]["channels"]
    channels["channel_1"]["is_selected"] = False
    channels["channel_2"]["is_selected"] = True
    channels["channel_2"]["defocus"] = 3.0

    microscope.current_channel = 1
    microscope.get_stage_position = lambda: {"f_pos": 103.0}

    microscope.prepare_next_channel()

    assert microscope.zero_defocus_focus == pytest.approx(100.0)
    assert microscope.move_stage.call_args.kwargs["f_abs"] == pytest.approx(103.0)
```

Test case B: when switching from channel 2 to channel 3, the target focus is computed from the same zero-defocus focus position.

```python
def test_prepare_next_channel_moves_between_channel_offsets_from_zero_defocus(model):
    microscope = model.active_microscope
    microscope.prepare_acquisition()

    channels = microscope.configuration["experiment"]["MicroscopeState"]["channels"]
    channels["channel_1"]["is_selected"] = False
    channels["channel_2"]["is_selected"] = True
    channels["channel_3"]["is_selected"] = True
    channels["channel_2"]["defocus"] = 3.0
    channels["channel_3"]["defocus"] = -1.5

    microscope.current_channel = 1
    microscope.get_stage_position = lambda: {"f_pos": 103.0}

    microscope.prepare_next_channel()
    microscope.prepare_next_channel()

    assert microscope.zero_defocus_focus == pytest.approx(100.0)
    assert microscope.move_stage.call_args.kwargs["f_abs"] == pytest.approx(98.5)
```

Adapt the mock object names to match the existing test fixtures. The important assertions are the inferred reference and absolute focus target.

- [ ] Run the focused tests and confirm they fail:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py::test_prepare_next_channel_infers_zero_defocus_focus_from_current_channel /Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py::test_prepare_next_channel_moves_between_channel_offsets_from_zero_defocus -q
```

- [ ] In `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/microscope.py`, replace the old `central_focus` semantics with explicit transient state.

Add or rename runtime fields:

```python
self.zero_defocus_focus = None
self.acquisition_focus_restore_position = None
```

Keep `central_focus` only as a compatibility alias if other code still references it. If retained, set it equal to `zero_defocus_focus` and add a short comment that it is deprecated runtime state.

- [ ] Add a helper that derives the focus reference once.

```python
def _ensure_zero_defocus_focus(self, channel: dict) -> None:
    if self.zero_defocus_focus is not None:
        return

    stage_position = self.get_stage_position()
    current_focus = stage_position.get("f_pos")
    if current_focus is None:
        return

    channel_defocus = float(channel.get("defocus", 0.0))
    self.acquisition_focus_restore_position = current_focus
    self.zero_defocus_focus = current_focus - channel_defocus
```

- [ ] Add a single helper for channel setup so autofocus can target a specific channel without depending on selected-channel order.

```python
def prepare_channel(self, channel_key: str, update_daq_task_flag: bool = True) -> None:
    channel = self.channels[channel_key]
    self._ensure_zero_defocus_focus(channel)
    if self.zero_defocus_focus is not None:
        target_focus = self.zero_defocus_focus + float(channel.get("defocus", 0.0))
        self.move_stage({"f_abs": target_focus}, update_focus=False)
    self._apply_channel_laser_camera_filter_state(channel_key, update_daq_task_flag)
```

Use existing code from `prepare_next_channel` for camera, laser, filter wheel, zoom, and DAQ setup rather than changing hardware behavior.

- [ ] Rework `prepare_next_channel` so it only finds the next selected `channel_key`, updates `current_channel`, and calls `prepare_channel(channel_key, update_daq_task_flag)`.

- [ ] Update `prepare_acquisition` so it clears:

```python
self.current_channel = 0
self.zero_defocus_focus = None
self.acquisition_focus_restore_position = None
self.central_focus = None
```

- [ ] Update `end_acquisition` to restore the physical focus where the user began acquisition, not the derived zero-defocus focus.

```python
if self.acquisition_focus_restore_position is not None:
    self.move_stage({"f_abs": self.acquisition_focus_restore_position}, wait_until_done=True)
```

If compatibility requires `central_focus`, do not restore to it when it differs from `acquisition_focus_restore_position`.

- [ ] Run:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py -q
```

---

### 3. Apply The Same Reference Model To Z-Stack Acquisition

Z-stack must use the same per-channel interpretation as continuous acquisition. The stack start focus should be interpreted as the current physical focus for the current channel, then converted to a zero-defocus stack reference internally.

- [ ] Add tests in `/Users/Dean/Documents/GitHub/navigate/test/model/features/test_common_features.py`.

Test software z-stack focus targets:

```python
def test_z_stack_channel_defocus_is_relative_to_zero_defocus_reference(model):
    feature = ZStackAcquisition(model, saving_flag=False)
    feature.defocus = [3.0, -1.5]
    feature.first_channel_defocus = 3.0
    feature.start_focus = 103.0
    feature.current_position = {"f": 0.0}

    assert feature._focus_target_for_channel(0) == pytest.approx(103.0)
    assert feature._focus_target_for_channel(1) == pytest.approx(98.5)
```

Test ASI z-stack applies the computed focus target to `f_abs`:

```python
def test_asi_z_stack_uses_channel_defocus_in_stage_move(model):
    feature = ASIZStackAcquisition(model, saving_flag=False)
    feature.defocus = [3.0, -1.5]
    feature.first_channel_defocus = 3.0
    feature.start_focus = 103.0
    feature.current_position = {"f": 0.0}

    assert feature._focus_target_for_channel(1) == pytest.approx(98.5)
```

Adapt method names if the helper is private and placed differently. The required test coverage is that ASI no longer computes a defocused position and then ignores it when writing `f_abs`.

- [ ] Run the focused z-stack tests and confirm they fail:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/features/test_common_features.py -q
```

- [ ] In `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/common_features.py`, add a shared helper to `ZStackAcquisition`.

```python
def _focus_target_for_channel(self, channel_index: int) -> float:
    zero_defocus_start_focus = self.start_focus - self.first_channel_defocus
    return (
        zero_defocus_start_focus
        + self.current_position[self.primary_f_axis]
        + self.defocus[channel_index]
    )
```

If `primary_f_axis` is not already explicit, initialize it from the focus device key currently used in the stack implementation.

- [ ] In `pre_signal_func`, after building `self.defocus`, record:

```python
self.first_channel_defocus = self.defocus[0] if self.defocus else 0.0
```

This preserves the physical start plane as the first prepared selected channel while converting it into a zero-defocus stack reference internally.

- [ ] Replace direct formulas like:

```python
self.start_focus + self.current_position[self.focus_axis] + self.defocus[self.current_channel_in_list]
```

with:

```python
self._focus_target_for_channel(self.current_channel_in_list)
```

- [ ] Simplify channel-change focus logic in `signal_end` by recomputing from the helper after channel index or z step changes instead of incrementally subtracting one defocus and adding another. Incremental arithmetic is fragile and recreates order dependence.

- [ ] In `ASIZStackAcquisition.signal_func`, ensure the actual stage move uses the defocus-aware computed focus:

```python
current_focus_position = self._focus_target_for_channel(self.current_channel_in_list)
pos_dict[f"{self.focus_axis}_abs"] = current_focus_position
```

Do not leave the current behavior where `current_focus_position` is calculated and then ignored.

- [ ] Run:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/features/test_common_features.py -q
```

---

### 4. Add Channel-Aware Autofocus Execution

Autofocus must be able to focus a selected calibration channel even if that channel is not first in the acquisition channel list.

- [ ] Add tests in `/Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py`.

Test target channel preparation:

```python
def test_autofocus_prepares_requested_channel(model):
    autofocus = Autofocus(model, device="stage", device_ref="f", target_channel="channel_2")

    autofocus.run()

    model.active_microscope.prepare_channel.assert_called_once_with("channel_2")
```

Test completion payload:

```python
def test_autofocus_reports_best_focus_for_channel(model):
    autofocus = Autofocus(
        model,
        device="stage",
        device_ref="f",
        target_channel="channel_2",
        calibration_action="populate_defocus",
    )
    autofocus.focus_pos = 123.4

    autofocus.end_func_data()

    assert (
        "autofocus_complete",
        {
            "channel": "channel_2",
            "focus_position": 123.4,
            "device": "stage",
            "device_ref": "f",
            "calibration_action": "populate_defocus",
        },
    ) in model.event_queue.put.call_args_list
```

Use the existing event queue fixture style; if the current tests assert direct queue calls differently, preserve that style.

- [ ] Run focused tests and confirm they fail:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py -q
```

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/autofocus.py`.

Extend initialization:

```python
def __init__(
    self,
    model,
    device,
    device_ref,
    target_channel=None,
    calibration_action=None,
    reference_channel=None,
):
    ...
    self.target_channel = target_channel
    self.calibration_action = calibration_action
    self.reference_channel = reference_channel
```

- [ ] In `run`, after `model.prepare_acquisition()`, prepare the target channel when provided.

```python
if self.target_channel:
    active_microscope.prepare_channel(self.target_channel)
else:
    active_microscope.prepare_next_channel()
```

- [ ] At autofocus completion, keep existing behavior that updates `StageParameters`, then also emit an event payload for controller-level calibration workflows.

```python
if self.target_channel:
    self.model.event_queue.put(
        (
            "autofocus_complete",
            {
                "channel": self.target_channel,
                "focus_position": self.focus_pos,
                "device": self.device,
                "device_ref": self.device_ref,
                "calibration_action": self.calibration_action,
                "reference_channel": self.reference_channel,
            },
        )
    )
```

- [ ] Update the model command wiring that creates `Autofocus` so optional target channel and calibration metadata can flow from controller to feature. Search for the existing `"autofocus"` command handler before editing.

- [ ] Run:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py -q
```

---

### 5. Add Autofocus Calibration UI And Controller Workflow

The GUI should make the tedious manual workflow explicit:

1. Select a reference channel.
2. Run autofocus and capture that best focus as the temporary reference.
3. Select a target channel.
4. Run autofocus and populate target defocus as `target_best_focus - reference_best_focus`.

The temporary reference focus is sample-position-specific and must not be persisted to YAML.

- [ ] Add controller tests in `/Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_autofocus.py`.

Test reference capture:

```python
def test_autofocus_controller_captures_temporary_reference_focus(controller):
    payload = {
        "channel": "channel_1",
        "focus_position": 100.0,
        "calibration_action": "capture_reference",
    }

    controller.handle_autofocus_complete(payload)

    assert controller.defocus_calibration_reference == {
        "channel": "channel_1",
        "focus_position": 100.0,
    }
```

Test populate defocus:

```python
def test_autofocus_controller_populates_target_defocus_from_reference(controller):
    controller.defocus_calibration_reference = {
        "channel": "channel_1",
        "focus_position": 100.0,
    }
    payload = {
        "channel": "channel_2",
        "focus_position": 102.25,
        "calibration_action": "populate_defocus",
    }

    controller.handle_autofocus_complete(payload)

    channels = controller.parent_controller.configuration["experiment"]["MicroscopeState"]["channels"]
    assert channels["channel_2"]["defocus"] == pytest.approx(2.25)
    controller.parent_controller.execute.assert_called_with(
        "channel_defocus",
        "channel_2",
        2.25,
    )
```

Test missing reference:

```python
def test_autofocus_controller_does_not_populate_without_reference(controller):
    payload = {
        "channel": "channel_2",
        "focus_position": 102.25,
        "calibration_action": "populate_defocus",
    }

    controller.handle_autofocus_complete(payload)

    channels = controller.parent_controller.configuration["experiment"]["MicroscopeState"]["channels"]
    assert channels["channel_2"]["defocus"] != 2.25
```

- [ ] Add a channel GUI update test in `/Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_channels_settings.py` or the existing channels-tab controller test file.

```python
def test_channels_tab_controller_sets_channel_defocus_widget(controller):
    controller.set_channel_defocus("channel_2", 2.25)

    assert controller.view.channel_variables["channel_2"]["defocus"].get() == pytest.approx(2.25)
```

- [ ] Run the new controller tests and confirm they fail:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_autofocus.py /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_channels_settings.py -q
```

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/view/popups/autofocus_setting_popup.py`.

Add compact controls near the autofocus settings:

- Target channel selector.
- Calibration action selector with at least:
  - regular autofocus
  - capture reference
  - populate defocus
- A small status label that shows the captured reference channel and focus when present.

Keep copy short. Do not add a long explanatory help panel to the GUI.

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/autofocus.py`.

Store temporary calibration state:

```python
self.defocus_calibration_reference = None
```

When starting autofocus, read the target channel and calibration action from the popup and forward them:

```python
self.parent_controller.execute(
    "autofocus",
    device,
    device_ref,
    target_channel,
    calibration_action,
    reference_channel,
)
```

Add completion handling:

```python
def handle_autofocus_complete(self, payload: dict) -> None:
    action = payload.get("calibration_action")
    if action == "capture_reference":
        self.defocus_calibration_reference = {
            "channel": payload["channel"],
            "focus_position": float(payload["focus_position"]),
        }
        self._update_reference_status()
        return

    if action == "populate_defocus":
        if self.defocus_calibration_reference is None:
            self._show_missing_reference_warning()
            return

        target_channel = payload["channel"]
        target_focus = float(payload["focus_position"])
        reference_focus = self.defocus_calibration_reference["focus_position"]
        defocus = target_focus - reference_focus
        self._write_channel_defocus(target_channel, defocus)
```

Write helper:

```python
def _write_channel_defocus(self, channel_key: str, defocus: float) -> None:
    channels = self.parent_controller.configuration["experiment"]["MicroscopeState"]["channels"]
    channels[channel_key]["defocus"] = defocus
    self.parent_controller.execute("channel_defocus", channel_key, defocus)
```

Do not persist `defocus_calibration_reference`.

- [ ] Wire the event queue so `"autofocus_complete"` payloads reach `AutofocusPopupController.handle_autofocus_complete`. Use the existing controller event-dispatch pattern rather than adding a parallel event loop.

- [ ] Update `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_tab.py`.

Add:

```python
def set_channel_defocus(self, channel_key: str, defocus: float) -> None:
    channel_vars = self.view.channel_variables[channel_key]
    channel_vars["defocus"].set(defocus)
```

Register the custom event:

```python
def custom_events(self):
    return {
        "exposure_time": self.set_exposure_time,
        "channel_defocus": self.set_channel_defocus,
    }
```

If the actual channel variable storage is under a different attribute, use the existing `set_exposure_time` method as the exact pattern.

- [ ] Confirm `/Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_settings.py` still writes the updated widget value to:

```python
configuration["experiment"]["MicroscopeState"]["channels"][channel_key]["defocus"]
```

No new persistent configuration key should be added.

- [ ] Run:

```bash
conda run -n navigate python -m pytest /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_autofocus.py /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_channels_settings.py -q
```

---

### 6. Update User-Facing Documentation

The user-facing docs should define defocus in terms of the zero-defocus focus position and should avoid language implying that the first selected channel is the reference.

- [ ] Search existing docs for defocus and autofocus text:

```bash
rg -n "defocus|autofocus|focus" /Users/Dean/Documents/GitHub/navigate/docs /Users/Dean/Documents/GitHub/navigate/src/navigate/view
```

- [ ] Update the relevant docs page, likely under `/Users/Dean/Documents/GitHub/navigate/docs/source`, to state:

```text
Channel defocus is a per-channel focus offset from the zero-defocus focus position. During acquisition, Navigate infers the zero-defocus focus position from the current focus and the current channel defocus, then moves each channel to zero-defocus focus plus that channel's defocus.
```

- [ ] Add one sentence for autofocus calibration:

```text
Autofocus calibration can capture a temporary reference-channel best focus, then populate another channel's defocus from the measured focus difference.
```

- [ ] Do not document a persistent shared reference plane field, because no such field exists.

---

### 7. Integration Validation

- [ ] Run focused tests for all touched areas:

```bash
conda run -n navigate python -m pytest \
  /Users/Dean/Documents/GitHub/navigate/test/config/test_config.py \
  /Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py \
  /Users/Dean/Documents/GitHub/navigate/test/model/features/test_common_features.py \
  /Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py \
  /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_autofocus.py \
  /Users/Dean/Documents/GitHub/navigate/test/controller/sub_controllers/test_channels_settings.py \
  -q
```

- [ ] Run lint/format checks on modified Python files:

```bash
conda run -n navigate python -m ruff check \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/config/config.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/model/microscope.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/common_features.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/model/features/autofocus.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/autofocus.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_tab.py \
  /Users/Dean/Documents/GitHub/navigate/src/navigate/controller/sub_controllers/channels_settings.py
```

- [ ] Run the existing known-green smoke tests:

```bash
conda run -n navigate python -m pytest \
  /Users/Dean/Documents/GitHub/navigate/test/model/test_microscope.py::test_prepare_next_channel \
  /Users/Dean/Documents/GitHub/navigate/test/model/features/test_autofocus.py \
  -q
```

- [ ] If GUI changes are substantial, manually launch the app in the `navigate` conda env and verify:

```bash
conda run -n navigate python -m navigate
```

Manual checks:

- Set channel 1 defocus to `0.0`, channel 2 defocus to `+2.0`, channel 3 defocus to `-1.0`.
- Focus physically at channel 2's best focus.
- Select only channel 2 and acquire: channel 2 should not receive an extra `+2.0`.
- Select channels 1 and 2 and acquire: channel 1 should move to the zero-defocus focus, channel 2 should move back to channel 2's best focus.
- Deselect channel 1 and acquire channel 2 again: channel 2 should remain at the same best focus.
- Run autofocus in regular mode and confirm legacy behavior still works.
- Run autofocus calibration capture for channel 1, then populate channel 2 and confirm channel 2 defocus is updated in the Channels tab and existing configuration dictionary.

---

## Risk Notes

- The biggest behavior risk is accidentally restoring focus to the derived zero-defocus focus instead of the physical focus where acquisition began. Keep separate runtime fields for those concepts.
- Z-stack has multiple code paths; software z-stack and ASI z-stack both need explicit test coverage because ASI currently appears to compute a defocus-aware focus position and then not use it in `pos_dict`.
- Autofocus completion currently updates stage parameters. The new calibration event should be additive and should not remove existing stage update behavior.
- Do not add a persistent `shared_chromatic_reference_plane`, `zero_defocus_focus`, or calibration reference field to the YAML configuration. The only persisted calibration output is each channel's existing `defocus` value.

---

## Expected Final Behavior

After implementation:

- Per-channel defocus has the same meaning no matter which channels are selected.
- Deselecting the original first channel no longer makes the next channel receive its defocus twice.
- Continuous, live, single, customized, software z-stack, and ASI z-stack acquisitions all compute channel focus from the same runtime zero-defocus reference.
- Autofocus can target a selected channel for calibration.
- The autofocus popup can capture a temporary reference-channel best focus and populate a target channel defocus from the measured focus difference.
- The existing ProxyDict/YAML channel `defocus` field remains the source of truth for persisted chromatic offsets.
