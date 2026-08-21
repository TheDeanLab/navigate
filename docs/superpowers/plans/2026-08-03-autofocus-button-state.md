# Autofocus Button State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Disable Start Autofocus while autofocus is active without removing Navigate's ability to inject autofocus into Continuous Scan.

**Architecture:** Track acquisition state and autofocus activity separately. Existing controller lifecycle callbacks remain authoritative for acquisition startup, completion, and errors; a new model event marks completion of an injected autofocus sequence so Start can be re-enabled while Continuous Scan remains active.

**Tech Stack:** Python 3.9, tkinter/ttk, pytest, Navigate controller architecture.

## Global Constraints

- Keep separate Start Autofocus and Stop Acquisition buttons.
- Idle enables Start and disables Stop.
- Starting and Stopping disable both controls.
- Continuous Scan enables Start and Stop when autofocus is inactive.
- Active autofocus disables Start while leaving Stop enabled after acquisition starts.
- Non-live acquisition disables Start and enables Stop.
- Reuse `execute("stop_acquire")`; do not add another model stop path.
- Leave implementation changes uncommitted for the user's local smoke test.

---

### Task 1: Complementary Autofocus Button States

**Files:**
- Modify: `test/controller/sub_controllers/test_autofocus.py`
- Modify: `test/controller/test_controller.py`
- Modify: `src/navigate/controller/sub_controllers/autofocus.py`
- Modify: `src/navigate/controller/controller.py`
- Modify: `src/navigate/model/model.py`
- Modify: `test/model/test_model.py`

**Interfaces:**
- Consumes: `Controller.execute(command, *args)` and existing capture lifecycle callbacks.
- Produces: separate popup acquisition/autofocus state setters and the `autofocus_sequence_complete` model event.

- [x] **Step 1: Write failing popup state tests**

Update the popup controller tests to exercise the real ttk buttons:

```python
@pytest.mark.parametrize(
    ("state", "autofocus_active", "mode", "start_state", "stop_state"),
    [
        ("idle", False, "live", "normal", "disabled"),
        ("starting", True, "live", "disabled", "disabled"),
        ("running", False, "live", "normal", "normal"),
        ("running", True, "live", "disabled", "normal"),
        ("running", False, "z-stack", "disabled", "normal"),
        ("stopping", True, "live", "disabled", "disabled"),
    ],
)
def test_acquisition_state_controls_buttons(
    self, state, autofocus_active, mode, start_state, stop_state
):
    self.autofocus_controller.parent_controller.acquire_bar_controller.mode = mode
    self.autofocus_controller.set_acquisition_state(state)
    self.autofocus_controller.set_autofocus_state(autofocus_active)
    assert str(self.autofocus_controller.view.autofocus_btn["state"]) == start_state
    assert (
        str(self.autofocus_controller.view.stop_acquisition_btn["state"])
        == stop_state
    )
```

Update the stop-route test to assert that both popup controls are disabled
immediately after Stop Acquisition is invoked.

Add a controller test that begins with an active Continuous Scan, dispatches
autofocus, and verifies Start disables while Stop remains enabled. Feed an
`autofocus_sequence_complete` event through `Controller.update_event` and
verify both buttons become enabled.

Add a model test for `reset_feature_list` using a real in-memory event queue.
Verify the restored live feature list emits exactly
`("autofocus_sequence_complete", None)`.

- [x] **Step 2: Write failing controller lifecycle test**

Make the lifecycle test dispatch standalone autofocus while the popup is open
and assert:

```python
controller.execute("autofocus")
assert str(start_button["state"]) == "disabled"
assert str(stop_button["state"]) == "disabled"

controller._on_capture_started(microscope_name)
assert str(start_button["state"]) == "disabled"
assert str(stop_button["state"]) == "normal"

controller._finish_capture_ui("live", 0)
assert str(start_button["state"]) == "normal"
assert str(stop_button["state"]) == "disabled"

controller._set_autofocus_acquisition_state("starting")
with patch("navigate.controller.controller.messagebox.showerror"):
    controller._handle_capture_start_error(RuntimeError("startup failed"))
assert str(start_button["state"]) == "normal"
assert str(stop_button["state"]) == "disabled"
```

- [x] **Step 3: Run the tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest \
  -o addopts='' -q \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py::test_capture_lifecycle_updates_autofocus_stop_button
```

Expected: FAIL because acquisition and autofocus state are not separate and the
model does not emit a sequence-completion event.

- [x] **Step 4: Implement explicit lifecycle rendering**

In `AutofocusPopupController`, store `acquisition_state` and
`autofocus_active`. Render with:

```python
is_live = acquire_bar_controller.mode == "live"
can_start = (
    not self.autofocus_active
    and self.acquisition_state in ("idle", "running")
    and (self.acquisition_state == "idle" or is_live)
)
can_stop = self.acquisition_state == "running"
self.view.autofocus_btn.configure(state="normal" if can_start else "disabled")
self.view.stop_acquisition_btn.configure(state="normal" if can_stop else "disabled")
```

Initialize newly opened popups from the parent's acquisition and autofocus
flags. Enter `"stopping"` before routing Stop Acquisition.

In `Controller`, own `is_autofocusing`. Set it true for accepted standalone
and live autofocus commands. Pass `"starting"` for standalone dispatch,
`"running"` from `_on_capture_started`, and `"idle"` from completion or
startup error. Enter `"stopping"` for global `stop_acquire`.

In `Model.reset_feature_list`, emit `autofocus_sequence_complete` after
clearing the injected flag and restoring the normal live feature list. Handle
that event in `Controller.update_event` by clearing `is_autofocusing`.

- [x] **Step 5: Run focused tests and verify GREEN**

Run the command from Step 3. Expected: all selected tests pass.

- [x] **Step 6: Run regression and formatting checks**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest \
  -o addopts='' -q --disable-warnings \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/sub_controllers/test_acquire_bar.py \
  test/controller/test_controller.py \
  test/model/features/test_autofocus.py \
  test/model/test_model.py

pre-commit run black --files \
  src/navigate/controller/controller.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py

pre-commit run ruff --files \
  src/navigate/controller/controller.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py

git diff --check
```

Expected: 111 or more tests pass; Black, Ruff, and `git diff --check` pass.

- [x] **Step 7: Perform a local smoke-test handoff**

Leave implementation changes uncommitted and give the user the verified
worktree launch command:

```bash
PYTHONPATH="$PWD/src" /opt/anaconda3/envs/navigate/bin/python -m navigate.main -sh
```
