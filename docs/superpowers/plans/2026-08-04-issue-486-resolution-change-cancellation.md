# Issue 486 Resolution-Change Cancellation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Stop Stage cancel an in-progress resolution change, immediately stop every participating stage, prevent later motion, and offer an explicit keep-or-return recovery choice.

**Architecture:** The model owns one private resolution-change task with a cancellation event and terminal event payload. Manual resolution updates run in a model-owned worker so ObjectInSubprocess remains available for Stop Stage; feature-driven updates register their signal thread with the same lifecycle. A stacked recovery change consumes the terminal cancellation event, presents a `PopUp`, and starts any requested return as a second cancellable model worker.

**Tech Stack:** Python 3.9, `threading`, Tk/ttk, Navigate's `Model`/`Microscope`/controller event queue, pytest, Ruff, Black.

## Global Constraints

- Stop Stage records cancellation before attempting any hardware stop.
- Every unique stage device in the former and target microscopes receives a stop attempt; one driver failure cannot skip the rest.
- No Tk `after()` debounce or controller-side resolution-worker `join()` may delay Stop Stage.
- Cancellation is checked before and after every blocking resolution-induced stage movement.
- Cancelled resolution changes do not restart live or customized acquisition.
- Return never begins implicitly; Close and Escape mean Keep Current Position.
- Return moves to the literal pre-movement coordinates, keeps the selected microscope/resolution, preserves stage limits, and is itself cancellable.
- Local focused tests must not instantiate Aqua Tk. Native GUI checks run on Windows CI or Linux X11 Tk under `xvfb-run -a`.
- Comments explain only non-obvious safety ordering, proxy retry, and worker-acknowledgement constraints.
- Python tests use `PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts=''`.

## File Structure

- Create `src/navigate/model/resolution_change.py`: private task state shared by model resolution, stop, and recovery paths.
- Modify `src/navigate/model/microscope.py`: cooperative movement cancellation and deduplicated best-effort stage stopping.
- Modify `src/navigate/model/model.py`: task ownership, asynchronous manual resolution update, terminal events, cancellation-safe acquisition cleanup, and recovery commands.
- Modify `src/navigate/model/features/update_setting.py`: keep customized resolution changes inside the same cancellable lifecycle.
- Modify `src/navigate/controller/controller.py`: nonblocking resolution submission, reliable Stop Stage proxy retries, and recovery event handling.
- Modify `src/navigate/controller/sub_controllers/stages.py`: remove the Stop Stage debounce.
- Create `src/navigate/view/popups/resolution_change_popup.py`: two-choice modal recovery view.
- Create `test/model/test_resolution_change.py`: focused task, stop-order, async, and return tests using blocking stage doubles.
- Modify `test/model/test_model.py`: preserve successful-resolution behavior and add acquisition cancellation coverage.
- Modify `test/controller/test_controller.py`: nonblocking submission, proxy retry, event deduplication, and recovery dispatch tests without Tk.
- Modify `test/controller/sub_controllers/test_stages.py`: direct Stop Stage dispatch test without using the Tk fixture.
- Create `test/view/popups/test_resolution_change_popup.py`: callback semantics tested through the real popup methods without constructing Tk widgets locally.
- Modify `docs/source/05_reference/_autosummary/navigate.model.model.Model.rst`: synchronize changed user-callable model contracts when needed.

## Reuse Analysis

- Closest existing symbols: `Controller.execute("resolution")`, `Model.run_command("update_setting", "resolution")`, `Model.change_resolution`, `Microscope.move_stage_offset`, `Microscope.move_stage`, `Controller.stop_stage`, `Model.stop_stage`, `Microscope.stop_stage`, `Controller.sloppy_stop`, the model event queue, and `PopUp`.
- Decision: extend the existing resolution, stage-movement, Stop Stage, event, and popup lifecycles. Keep task coordination private to the model.
- Rejected alternative: a controller-only cancellation flag would not cross ObjectInSubprocess safely and would leave feature-driven changes and multi-device movement unprotected.
- Rejected alternative: a second emergency pipe would duplicate device ownership and require a new thread-safety contract for every stage driver.
- Documentation updates: full Numpydoc for changed public method signatures and returns, existing model autosummary synchronization, the committed design, and this executable plan.

---

### Task 1: Direct GUI safety dispatch

**Files:**
- Modify: `test/controller/sub_controllers/test_stages.py`
- Modify: `test/controller/test_controller.py`
- Modify: `src/navigate/controller/sub_controllers/stages.py`
- Modify: `src/navigate/controller/controller.py`

**Interfaces:**
- Consumes: existing `StageController.parent_controller.execute(command)` and `SynchronizedThreadPool.createThread(resourceName, target)`.
- Produces: `StageController.stop_button_handler()` dispatches `"stop_stage"` synchronously; `Controller.execute("resolution")` submits without joining; `Controller._stop_stage_safely() -> None` retries transient proxy contention.

- [x] **Step 1: Write failing controller tests**

```python
def test_stop_button_handler_dispatches_immediately():
    controller = SimpleNamespace(parent_controller=MagicMock())
    StageController.stop_button_handler(controller)
    controller.parent_controller.execute.assert_called_once_with("stop_stage")


def test_execute_resolution_does_not_join_worker(controller):
    worker = MagicMock()
    controller.threads_pool.createThread = MagicMock(return_value=worker)
    controller.execute("resolution", controller.menu_controller.resolution_value.get())
    worker.join.assert_not_called()


def test_stop_stage_retries_proxy_contention(controller):
    controller.model.stop_stage = MagicMock(
        side_effect=[RuntimeError("pipe busy"), None]
    )
    controller._stop_stage_safely()
    assert controller.model.stop_stage.call_count == 2
```

- [x] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/controller/sub_controllers/test_stages.py::test_stop_button_handler_dispatches_immediately \
  test/controller/test_controller.py::test_execute_resolution_does_not_join_worker \
  test/controller/test_controller.py::test_stop_stage_retries_proxy_contention
```

Expected: failures show the Tk debounce, worker `join()`, and missing retry helper.

- [x] **Step 3: Implement the minimal controller fixes**

```python
def stop_button_handler(self, *args: Iterable) -> None:
    """Request an immediate stop for all stages."""
    self.parent_controller.execute("stop_stage")


def _stop_stage_safely(self) -> None:
    """Retry a stage stop rejected by transient model-proxy contention."""
    while True:
        try:
            self.model.stop_stage()
            return
        except RuntimeError:
            # A safety stop must not disappear in the thread-pool exception handler.
            time.sleep(0.001)
```

Use `_stop_stage_safely` as the `"stop_stage"` thread target and remove the resolution worker assignment and `join()`.

- [x] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: all three pass without constructing Tk.

- [x] **Step 5: Commit the direct-dispatch slice**

```bash
git add src/navigate/controller/controller.py \
  src/navigate/controller/sub_controllers/stages.py \
  test/controller/test_controller.py \
  test/controller/sub_controllers/test_stages.py
git commit -m "fix: dispatch stage stops without GUI delay"
```

### Task 2: Cooperative microscope movement cancellation

**Files:**
- Create: `test/model/test_resolution_change.py`
- Modify: `src/navigate/model/microscope.py`

**Interfaces:**
- Consumes: `threading.Event`, existing stage `move_absolute`, `move_axis_absolute`, `stop`, and `verify_abs_position` contracts.
- Produces: `Microscope.move_stage_offset(former_microscope=None, cancel_event=None) -> bool`; `Microscope.move_stage(..., cancel_event=None) -> bool`; `Microscope.stop_stage(stopped_stage_ids=None) -> list[str]`.

- [x] **Step 1: Write failing movement tests with literal expected order**

```python
def test_move_stage_stops_before_second_device_after_cancellation():
    cancel_event = threading.Event()
    calls = []
    first = RecordingStage("first", calls, cancel_event_on_move=cancel_event)
    second = RecordingStage("second", calls)
    microscope = make_microscope_with_stages(first, second)

    assert microscope.move_stage(
        {"x_abs": 10.0, "z_abs": 20.0},
        wait_until_done=True,
        cancel_event=cancel_event,
    ) is False
    assert calls == [("move", "first", {"x_abs": 10.0})]


def test_stop_stage_attempts_each_unique_device_after_error():
    calls = []
    shared = RecordingStage("shared", calls, stop_error=RuntimeError("failed"))
    other = RecordingStage("other", calls)
    microscope = make_microscope_with_stages(shared, shared, other)

    errors = microscope.stop_stage()

    assert calls == [("stop", "shared"), ("stop", "other")]
    assert len(errors) == 1
```

The test helpers implement only stage-driver behavior and live in the test module.

- [x] **Step 2: Run the movement tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/model/test_resolution_change.py -k 'move_stage or stop_stage'
```

Expected: current signatures reject `cancel_event` and stopping aborts on the first error or repeats a shared stage.

- [x] **Step 3: Extend the existing microscope methods**

```python
def _movement_cancelled(cancel_event: Optional[threading.Event]) -> bool:
    return cancel_event is not None and cancel_event.is_set()
```

Check this helper before and after each blocking move. Return `False` on cancellation. Extend `stop_stage` with a caller-provided set of attempted stage object IDs, add IDs before invoking `stop()`, catch and log each exception, and return error strings after attempting all devices.

- [x] **Step 4: Complete Numpydoc and run focused tests**

Document the cancellation-event ownership, blocking behavior, Boolean return, deduplication set, best-effort stop semantics, and returned errors. Run the Step 2 command and the existing microscope/model resolution test; expected: pass.

- [x] **Step 5: Commit the movement primitive**

```bash
git add src/navigate/model/microscope.py test/model/test_resolution_change.py
git commit -m "fix: make resolution stage moves cancellable" -m \
  "Reuse analysis: extended Microscope.move_stage, move_stage_offset, and stop_stage. A second movement executor would duplicate stage mapping, limit enforcement, and device ownership."
```

### Task 3: Model-owned resolution lifecycle and hardware-stop ordering

**Files:**
- Create: `src/navigate/model/resolution_change.py`
- Modify: `test/model/test_resolution_change.py`
- Modify: `src/navigate/model/model.py`

**Interfaces:**
- Consumes: Task 2 cancellation-aware movement and best-effort stop methods.
- Produces: private `_ResolutionChangeTask`; `Model._begin_resolution_change(resolution_value)`, `_perform_resolution_change(task)`, `_finish_resolution_change(task, succeeded)`, `_start_resolution_setting_update()`, cancellation-aware `Model.stop_stage(cancel_resolution_change=True)`, and `Model.move_stage(..., cancel_event=None) -> bool`; `Model.change_resolution(resolution_value) -> bool` remains the synchronous public entry point.

- [x] **Step 1: Write failing task and stop-order tests**

```python
def test_stop_stage_records_cancellation_before_hardware_stop():
    observed = []
    model, task = make_model_with_resolution_task()
    model.active_microscope.stop_stage = lambda *args, **kwargs: observed.append(
        task.cancel_event.is_set()
    ) or []

    model.stop_stage()

    assert observed == [True]


def test_resolution_worker_cannot_start_second_stage_after_stop():
    model, first, second = make_blocking_resolution_model()
    assert model._start_resolution_setting_update() is True
    assert first.move_started.wait(1.0)
    worker = model._resolution_change_task.worker

    model.stop_stage()
    worker.join(1.0)

    assert first.stop_called.is_set()
    assert second.move_started.is_set() is False


def test_terminate_cancels_and_joins_resolution_worker():
    model, first, _ = make_blocking_resolution_model()
    model._start_resolution_setting_update()
    assert first.move_started.wait(1.0)
    worker = model._resolution_change_task.worker

    model.terminate()

    assert first.stop_called.is_set()
    assert worker.is_alive() is False
```

- [x] **Step 2: Run the task tests and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/model/test_resolution_change.py \
  -k 'records_cancellation or worker_cannot or terminate_cancels'
```

Expected: the private lifecycle is absent and current Stop Stage cannot cancel the worker.

- [x] **Step 3: Add the private task record and model initialization**

```python
@dataclass
class _ResolutionChangeTask:
    task_id: int
    resolution_value: str
    former_microscope_name: str
    target_microscope_name: str
    cancel_event: threading.Event = field(default_factory=threading.Event)
    state: str = "changing"
    worker: Optional[threading.Thread] = None
    previous_position: Optional[dict[str, float]] = None
    stopped_position: Optional[dict[str, float]] = None
    stop_errors: list[str] = field(default_factory=list)
```

Initialize a lock, counter, and optional current task in `Model.__init__`. `_begin_resolution_change` rejects an existing active task with a model warning event.

- [x] **Step 4: Refactor successful resolution movement behind the task**

Move the physical body of `change_resolution` into `_perform_resolution_change(task)`. Capture the target stage position immediately before the first resolution-induced stage move, pass `task.cancel_event` through Task 2 methods, and check cancellation before zoom, offset, final stage update, waveform work, and acquisition restart. Extend `Model.move_stage` with an optional `cancel_event` that forwards to `Microscope.move_stage`. The public `change_resolution` creates and finishes a synchronous task and returns success.

```python
def _perform_resolution_change(self, task: _ResolutionChangeTask) -> bool:
    if task.cancel_event.is_set():
        return False
    former_microscope = task.former_microscope_name
    if task.target_microscope_name != former_microscope:
        self.get_active_microscope()
        task.previous_position = {
            key.replace("_pos", "_abs"): value
            for key, value in self.get_stage_position().items()
        }
        if not self.active_microscope.move_stage_offset(
            former_microscope, cancel_event=task.cancel_event
        ):
            return False
    if task.cancel_event.is_set():
        return False
    # Existing zoom-offset logic continues here and passes task.cancel_event.
```

- [x] **Step 5: Make manual setting updates model-owned and asynchronous**

Extract the existing `run_command("update_setting")` body to `_update_setting(command, resolution_task=None)`. For `"resolution"`, create the task before starting a `ThreadWithWarning` worker and return immediately. For other settings such as `"galvo"`, retain synchronous behavior. On cancellation set acquisition stop flags, release a paused data thread, avoid waveform publication/restart, and complete the task as cancelled.

```python
elif command == "update_setting":
    if args[0] == "resolution":
        self._start_resolution_setting_update()
        return
    self._update_setting(args[0])
```

- [x] **Step 6: Implement ordered best-effort Stop Stage**

Set the active task's cancellation event and state under its lock before calling any device. Stop former, target, and active microscopes with one shared set of attempted stage IDs. Record errors, read the actual active position, update configuration, and publish `update_stage`. Do not wait for the worker before issuing stops. The worker publishes `resolution_change_cancelled` only after reaching terminal state. Extend `Model.terminate` to set cancellation, issue the same stage stop, and join the active worker before microscope teardown.

```python
def stop_stage(self, *, cancel_resolution_change: bool = True) -> None:
    task = self._resolution_change_task
    if cancel_resolution_change and task is not None:
        # Prevent the worker from scheduling another move before stopping hardware.
        task.cancel_event.set()
        task.state = "cancel_requested"
    attempted_stage_ids = set()
    stop_errors = []
    for microscope_name in self._stage_stop_microscope_names(task):
        stop_errors.extend(
            self.microscopes[microscope_name].stop_stage(attempted_stage_ids)
        )
    if task is not None:
        task.stop_errors.extend(stop_errors)
    stopped_position = self.get_stage_position()
    self.event_queue.put(("update_stage", stopped_position))
```

- [x] **Step 7: Run focused and existing resolution tests**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/model/test_resolution_change.py \
  test/model/test_model.py::test_change_resolution \
  test/model/concurrency/test_concurrency_tools.py::test_incorrect_thread_management
```

Expected: all pass and no worker remains alive after test cleanup.

- [x] **Step 8: Commit the model lifecycle**

```bash
git add src/navigate/model/model.py src/navigate/model/resolution_change.py \
  test/model/test_resolution_change.py
git commit -m "fix: cancel active resolution changes before stopping stages" -m \
  "Reuse analysis: kept Model.change_resolution and Model.stop_stage as canonical entry points and used the existing model event queue. The private task record coordinates their lifecycle without adding a parallel public executor or stop API."
```

### Task 4: Feature-driven cancellation and safe acquisition termination

**Files:**
- Create: `test/model/features/test_update_setting.py`
- Modify: `src/navigate/model/features/update_setting.py`
- Modify: `test/model/test_model.py`
- Modify: `docs/source/05_reference/_autosummary/navigate.model.model.Model.rst`

**Interfaces:**
- Consumes: Task 3 `_begin_resolution_change`, `_perform_resolution_change`, and `_finish_resolution_change` lifecycle.
- Produces: `ChangeResolution.signal_func() -> bool` returns `False` after cancellation and never prepares/resumes the acquisition path; successful behavior remains unchanged.

- [x] **Step 1: Write a failing feature cancellation test**

```python
def test_change_resolution_feature_does_not_prepare_after_cancellation():
    model = make_feature_model(
        microscopes={
            "low": {"1x": (2048, 2048)},
            "high": {"1x": (2048, 2048)},
        },
        active_microscope="low",
    )
    feature = ChangeResolution(model, "high", "1x")
    model._perform_resolution_change.return_value = False

    assert feature.signal_func() is False
    model.active_microscope.prepare_acquisition.assert_not_called()
    assert model.stop_acquisition is True
```

- [x] **Step 2: Run the feature test and verify RED**

Run:

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/model/features/test_update_setting.py
```

Expected: current feature ignores the resolution result and prepares the new acquisition.

- [x] **Step 3: Keep the whole feature operation inside the task lifecycle**

Begin the task before pausing data or changing configuration. Use `try/finally` to finish it. If cancelled, set acquisition stop flags, release the paused data thread so it can terminate, skip microscope preparation, waveform event, next-channel preparation, and normal resume, then return `False`.

```python
task = self.model._begin_resolution_change(self.resolution_mode)
if task is None:
    return False
succeeded = False
try:
    self.model.pause_data_thread()
    if not self.model._perform_resolution_change(task):
        self.model.stop_acquisition = True
        self.model.stop_send_signal = True
        self.model.resume_data_thread()
        return False
    waveform_dict = self.model.active_microscope.prepare_acquisition()
    self.model.event_queue.put(("waveform", waveform_dict))
    self.model.active_microscope.prepare_next_channel()
    self.model.resume_data_thread()
    succeeded = True
    return True
finally:
    self.model._finish_resolution_change(task, succeeded)
```

- [x] **Step 4: Synchronize API documentation and run focused tests**

Document the Boolean result and cancellation side effects for `Model.change_resolution` and the keyword-only cancellation behavior of `Model.stop_stage`. Keep the autosummary reference to the existing symbols; do not add the private task class. Run Task 3 tests plus the feature test and existing feature-container tests touching `ChangeResolution`.

- [x] **Step 5: Commit the feature integration**

```bash
git add src/navigate/model/features/update_setting.py \
  test/model/features/test_update_setting.py test/model/test_model.py \
  docs/source/05_reference/_autosummary/navigate.model.model.Model.rst
git commit -m "fix: terminate cancelled resolution features safely" -m \
  "Reuse analysis: ChangeResolution now participates in the model-owned resolution lifecycle. No feature-specific stop path or duplicate acquisition cleanup API was added."
```

### Task 5: Verify and publish the core safety PR

**Files:**
- Modify: `docs/superpowers/plans/2026-08-04-issue-486-resolution-change-cancellation.md` (checkbox status only)

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: a mergeable core branch that independently prevents collision-causing continuation.

- [ ] **Step 1: Run core formatting and lint**

```bash
ruff check src/navigate/model/model.py src/navigate/model/microscope.py \
  src/navigate/model/resolution_change.py \
  src/navigate/model/features/update_setting.py \
  src/navigate/controller/controller.py \
  src/navigate/controller/sub_controllers/stages.py \
  test/model/test_resolution_change.py \
  test/model/features/test_update_setting.py \
  test/controller/test_controller.py \
  test/controller/sub_controllers/test_stages.py
black --check src/navigate/model/model.py src/navigate/model/microscope.py \
  src/navigate/model/resolution_change.py \
  src/navigate/model/features/update_setting.py \
  src/navigate/controller/controller.py \
  src/navigate/controller/sub_controllers/stages.py \
  test/model/test_resolution_change.py \
  test/model/features/test_update_setting.py \
  test/controller/test_controller.py \
  test/controller/sub_controllers/test_stages.py
```

- [ ] **Step 2: Run the relevant broader test set**

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/model/test_resolution_change.py \
  test/model/features/test_update_setting.py \
  test/model/test_model.py \
  test/controller/test_controller.py
```

Do not run the Tk-backed `stage_controller` package fixture locally; its direct-handler test has no fixture dependency.

- [ ] **Step 3: Inspect the core diff and commit plan progress**

```bash
git diff origin/develop --check
git diff origin/develop --stat
git log --oneline origin/develop..HEAD
```

Verify comments are brief and limited to the four non-obvious constraints in Global Constraints. Commit checkbox progress with `docs: record issue 486 core implementation`.

- [ ] **Step 4: Push and open the core PR**

Push `kdean/issue-486-stop-resolution-change` and open a draft PR targeting `develop`. The body links the design and plan, summarizes focused and broader test evidence, records Xvfb/Aqua limitations, requests the designated reviewer if discoverable, and includes `Closes #486`.

### Task 6: Preserve a recovery snapshot and run cancellable return movement

**Files:**
- Modify: `test/model/test_resolution_change.py`
- Modify: `src/navigate/model/resolution_change.py`
- Modify: `src/navigate/model/model.py`

**Interfaces:**
- Consumes: core terminal `resolution_change_cancelled` event and Task 2 cancellation-aware `move_stage`.
- Produces: `Model.run_command("resolution_recovery", task_id, choice)` accepting literal choices `"keep"` and `"return"`; terminal `resolution_return_complete` event.

- [ ] **Step 1: Write failing recovery tests**

```python
def test_keep_resolution_position_discards_snapshot_without_motion():
    model, recovery = make_cancelled_resolution_model(previous={"x_abs": 4.0})
    model.run_command("resolution_recovery", recovery.task_id, "keep")
    assert model.active_microscope.move_stage_calls == []
    assert model._resolution_recovery is None


def test_return_moves_to_literal_snapshot_and_can_be_cancelled():
    model, recovery = make_cancelled_resolution_model(
        previous={"x_abs": 4.0, "z_abs": -2.0}
    )
    model.run_command("resolution_recovery", recovery.task_id, "return")
    assert model.return_move_started.wait(1.0)
    worker = model._resolution_change_task.worker
    model.stop_stage()
    worker.join(1.0)
    assert model.return_move_arguments == {"x_abs": 4.0, "z_abs": -2.0}
    assert model.return_stage.stop_called.is_set()
```

- [ ] **Step 2: Run recovery tests and verify RED**

Run the two named tests. Expected: the recovery command and snapshot store are absent.

- [ ] **Step 3: Add recovery ownership and validation**

On terminal cancellation, retain an immutable copy of the pre-movement coordinates in a separate private recovery record after clearing the active task. Mark Return eligible only when every requested axis passes the affected stage's existing strict absolute-position validation. A newer resolution task invalidates an older recovery record.

```python
@dataclass(frozen=True)
class _ResolutionRecovery:
    task_id: int
    microscope_name: str
    previous_position: dict[str, float]
    return_allowed: bool
```

- [ ] **Step 4: Implement keep and return commands**

Keep atomically clears the matching snapshot and emits no movement. Return validates task ID and eligibility, creates a `returning` task before starting its worker, clears the popup snapshot exactly once, calls the existing cancellation-aware `Model.move_stage(..., wait_until_done=True)`, updates actual positions, and emits `resolution_return_complete` with success or cancellation.

```python
elif command == "resolution_recovery":
    task_id, choice = args
    if choice == "keep":
        self._keep_resolution_position(task_id)
    elif choice == "return":
        self._start_resolution_return(task_id)
    else:
        self.event_queue.put(("warning", f"Unknown resolution recovery: {choice}"))
```

- [ ] **Step 5: Run all model recovery and core tests**

Run `test/model/test_resolution_change.py`, the existing `test_change_resolution`, and the concurrency guard. Expected: pass.

- [ ] **Step 6: Commit recovery movement**

Create branch `kdean/issue-486-resolution-recovery` from the core branch before this commit, then:

```bash
git add src/navigate/model/model.py src/navigate/model/resolution_change.py \
  test/model/test_resolution_change.py
git commit -m "feat: add cancellable resolution position recovery" -m \
  "Reuse analysis: return movement uses Model.move_stage and the existing Stop Stage lifecycle. No recovery-specific stage executor, limit validator, or stop API was added."
```

### Task 7: Add the two-choice recovery dialog

**Files:**
- Create: `src/navigate/view/popups/resolution_change_popup.py`
- Create: `test/view/popups/test_resolution_change_popup.py`
- Modify: `src/navigate/controller/controller.py`
- Modify: `test/controller/test_controller.py`

**Interfaces:**
- Consumes: `resolution_change_cancelled` and `resolution_return_complete` events; Task 6 recovery command.
- Produces: `ResolutionChangeCancelledPopup(root, keep_command, return_command, return_enabled)`; controller handlers `_show_resolution_change_cancelled(payload)` and `_finish_resolution_return(payload)`.

- [ ] **Step 1: Write failing popup callback tests without Tk construction**

```python
def test_popup_close_keeps_current_position():
    popup = ResolutionChangeCancelledPopup.__new__(ResolutionChangeCancelledPopup)
    popup.popup = MagicMock()
    popup._keep_command = MagicMock()
    popup._keep()
    popup.popup.dismiss.assert_called_once_with()
    popup._keep_command.assert_called_once_with()


def test_popup_return_dismisses_before_starting_motion():
    order = []
    popup = ResolutionChangeCancelledPopup.__new__(ResolutionChangeCancelledPopup)
    popup.popup = MagicMock(dismiss=lambda: order.append("dismiss"))
    popup._return_command = lambda: order.append("return")
    popup._return()
    assert order == ["dismiss", "return"]
```

- [ ] **Step 2: Write failing controller event tests**

Patch the popup class with a complete fake exposing `showup`/`dismiss`. Assert that two events with the same task ID create one popup; Keep dispatches `("resolution_recovery", task_id, "keep")`; Return dispatches `"return"`; and `resolution_return_complete` clears the tracked popup/task state.

- [ ] **Step 3: Run popup/controller tests and verify RED**

Run only the new popup tests and named controller tests. Expected: imports and event handlers are absent.

- [ ] **Step 4: Implement the view**

Build a `PopUp` titled `Resolution Change Cancelled` with the approved explanatory text and buttons `Keep Current Position` and `Return to Previous Position`. Focus Keep, bind Escape and `WM_DELETE_WINDOW` to `_keep`, disable Return when `return_enabled` is false, and dismiss before either callback. Do not start model work from the view itself.

```python
def _keep(self, *_args) -> None:
    self.popup.dismiss()
    self._keep_command()


def _return(self) -> None:
    self.popup.dismiss()
    self._return_command()
```

- [ ] **Step 5: Implement controller event handling**

Register the two event handlers through the existing event-listener dictionary. Track the displayed task ID to deduplicate and dispatch choices through the existing model thread pool. Before Return, call `stage_controller.view.toggle_button_states(True, stage_controller.stage_axes)` after the modal closes; the separate Stop Stage frame remains enabled. On `resolution_return_complete`, call `stage_controller.force_enable_all_axes()` and clear the tracked task ID.

```python
def _return_resolution_position(self, task_id: int) -> None:
    self.stage_controller.view.toggle_button_states(
        True, self.stage_controller.stage_axes
    )
    self.threads_pool.createThread(
        resourceName="model",
        target=lambda: self.model.run_command(
            "resolution_recovery", task_id, "return"
        ),
    )
```

- [ ] **Step 6: Run popup/controller tests and verify GREEN**

Run the Step 3 tests. Expected: pass without creating `tk.Tk()` locally.

- [ ] **Step 7: Commit the recovery UI**

```bash
git add src/navigate/view/popups/resolution_change_popup.py \
  src/navigate/controller/controller.py \
  test/view/popups/test_resolution_change_popup.py \
  test/controller/test_controller.py
git commit -m "feat: offer safe resolution-change recovery choices"
```

### Task 8: Verify and publish the stacked recovery PR

**Files:**
- Modify: `docs/superpowers/plans/2026-08-04-issue-486-resolution-change-cancellation.md` (checkbox status only)

**Interfaces:**
- Consumes: Tasks 6-7 and the core PR branch.
- Produces: a focused stacked recovery PR whose base is the core branch until the core merges.

- [ ] **Step 1: Run formatting, lint, and focused tests**

Run Ruff and Black on all recovery-modified files. Run the full model resolution test file, feature test, controller tests, and popup callback tests.

- [ ] **Step 2: Run a native GUI smoke check outside Aqua**

Use Windows CI or a Linux X11 Tk environment:

```bash
xvfb-run -a /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/view/popups/test_resolution_change_popup.py
```

If the available environment is macOS Aqua Tk, skip window construction and explicitly report that Xvfb cannot isolate it.

- [ ] **Step 3: Review the stacked diff**

```bash
git diff kdean/issue-486-stop-resolution-change --check
git diff kdean/issue-486-stop-resolution-change --stat
git log --oneline kdean/issue-486-stop-resolution-change..HEAD
```

Confirm that the recovery PR contains no duplicate stage executor, stop path, or acquisition restart.

- [ ] **Step 4: Push and open the recovery PR**

Push `kdean/issue-486-resolution-recovery` and open a draft PR based on `kdean/issue-486-stop-resolution-change`. Link the design, plan, and core PR; list test evidence and Xvfb limitation; request the designated reviewer if known; and reference #486 without a second closing directive.
