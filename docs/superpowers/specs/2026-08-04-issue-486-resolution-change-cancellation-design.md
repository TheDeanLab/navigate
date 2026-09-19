# Issue 486 Resolution-Change Cancellation Design

## Summary

Issue #486 remains present on `origin/develop`: changing resolution starts a
blocking model operation, and the controller joins the worker from the Tk event
loop. While a stage is executing the resolution offset, Stop Stage cannot
reliably reach the model or the stage driver. This is a physical-safety concern
because continued motion could cause a collision.

Stop Stage must cancel the active resolution-change task, immediately attempt
to stop every stage device participating in that transition, and prevent the
worker from scheduling any later motion. After the worker acknowledges
cancellation and Navigate reads the stopped positions, the user may either keep
the stages where they stopped or explicitly return them to their pre-movement
positions.

## Safety Contract

The implementation must preserve this ordering:

1. Record cancellation before issuing any hardware command so the resolution
   worker cannot begin another stage move.
2. Attempt `stop()` on every unique stage device participating in the
   transition. An exception from one device must not prevent stopping the
   remaining devices.
3. Require the resolution worker to check cancellation before and after each
   blocking movement and before any later configuration or acquisition work.
4. Wait for worker acknowledgement before enabling recovery movement.
5. Read the actual stopped positions and update the GUI.
6. Start return movement only after an explicit user selection.

"Immediately" means that the Stop Stage event has no Tk `after()` debounce,
controller-side worker join, or intentional delay before the hardware stop is
dispatched. Physical stopping latency remains controlled by the hardware and
its driver.

If stop or position readback fails, Navigate must preserve the safest known
state, report the error, and withhold Return to Previous Position. It must never
guess a recovery coordinate.

## Architecture

### Model-owned resolution task

The model process will own a private resolution-task coordinator protected by a
lock. At most one resolution change or recovery return may be active. Its task
record contains:

- a monotonically unique task ID;
- a cancellation event;
- the lifecycle state (`changing`, `cancel_requested`, `cancelled`,
  `returning`, or `completed`);
- former and target microscope and zoom values;
- the affected microscope and unique stage devices;
- stopped positions and, when recovery support is present, pre-movement
  positions;
- the worker thread and any terminal error.

Manual resolution changes will ask the model to start the worker and then
return, leaving the ObjectInSubprocess command channel available for Stop Stage.
Feature-driven `ChangeResolution` operations will register their existing
signal thread with the same coordinator and obey the same cancellation checks.

A concurrent resolution request will be rejected with a warning. It will not
be queued behind a moving stage, because an out-of-date queued resolution can
produce unexpected motion after the current task ends.

### Cooperative movement cancellation

The current `Model.change_resolution`, `Microscope.move_stage_offset`, and
`Microscope.move_stage` paths will be extended with optional cooperative
cancellation. Movement code checks the cancellation event immediately before
and after every blocking device call. A cancellation after one device stops the
loop before another device can begin moving.

The model's Stop Stage entry point will set the task cancellation event before
calling hardware `stop()`. Calls made internally only to refresh stage state at
the successful end of a resolution change must not cancel their own task.

The controller will remove the 250-ms Stage Stop debounce and will not join the
resolution worker from the Tk thread. Its safety-stop worker will retry the
transient ObjectInSubprocess concurrency error currently handled for acquisition
stopping, while logging why the retry is necessary. It will not silently lose a
stop request in `ThreadPool` exception handling.

### Cancellation completion event

After all stop attempts, the resolution worker must reach a terminal cancelled
state before the model emits the cancellation-complete event. The core
serializable event payload contains the task ID, actual microscope and zoom,
stopped position, and any stop/readback error. The recovery PR enriches that
payload with the pre-movement position and Return eligibility.

The controller's existing model event queue remains the only child-to-GUI event
route. The Tk event pump creates or updates the recovery dialog on the Tk thread.
Duplicate task events cannot create duplicate dialogs or return movements.

### Recovery semantics

"Previous position" means the coordinates read from each affected physical
stage immediately before the first stage movement caused by the resolution
change. For a cross-microscope transition, Navigate selects the target stage
hardware and records its position before applying the configured microscope
offset. Shared stage devices are deduplicated.

Return to Previous Position:

- moves the affected stages to those exact saved coordinates;
- leaves the currently active microscope and resolution selected;
- preserves the configured stage-limit policy and never disables limits;
- begins only after the cancelled worker is quiescent;
- runs as a new model-owned worker so the command channel stays available;
- can itself be cancelled with Stop Stage; and
- leaves the stages at their newest stopped positions after failure or a second
  cancellation.

If positions are missing, invalid, or cannot be associated with the affected
stage devices, Return is unavailable.

### Recovery dialog

The dialog title is **Resolution Change Cancelled**. Its body explains that the
stages are stopped at the positions shown in Navigate and that returning will
move them again. It presents two explicit choices:

- **Keep Current Position** (safe default)
- **Return to Previous Position**

Closing the window or pressing Escape is identical to Keep Current Position.
The dialog closes before a return worker starts, ensuring the normal Stop Stage
control is available during return. Other stage and resolution controls remain
disabled while return motion is active; Stop Stage remains enabled.

### Acquisition state

Cancellation must not resume live or customized acquisition. It must not
calculate or publish new waveforms, prepare the next feature, or restart a signal
thread after an interrupted resolution change. The GUI is reconciled to the
microscope, zoom, and stage positions reported by the model. The user explicitly
restarts acquisition after choosing Keep or Return.

Application termination cancels any outstanding resolution or recovery worker,
issues the normal stage stop, and joins the worker before device teardown.

## Reuse Analysis

The closest existing lifecycle and transport mechanisms are:

- `Controller.execute("resolution")` and
  `Model.run_command("update_setting", "resolution")` for resolution requests;
- `Model.change_resolution` for microscope and zoom transitions;
- `Microscope.move_stage_offset` and `Microscope.move_stage` for physical
  movement;
- `Controller.execute("stop_stage")`, `Controller.stop_stage`,
  `Model.stop_stage`, and `Microscope.stop_stage` for stage stopping;
- `Controller.sloppy_stop` for retrying a safety command rejected by
  ObjectInSubprocess concurrency protection;
- the model event queue and controller event listeners for child-to-GUI state;
  and
- `PopUp` for transient modal dialogs.

The implementation extends these symbols rather than adding a second stage
executor, stop lifecycle, event transport, or public cancellation wrapper. Any
changed user-callable signatures will receive complete Numpydoc documentation,
including cancellation behavior, return meaning, side effects, and error
semantics. Reference documentation and tests will be updated with the code.

Brief comments will explain only the non-obvious safety constraints: why the
cancel flag precedes hardware stop, why cancellation is checked on both sides of
a blocking driver call, why the controller retries proxy contention, and why a
return cannot start before worker acknowledgement.

## Testing Strategy

Tests will be written before production changes and observed failing for the
expected missing behavior. A blocking stage double will model a real
`move_absolute(..., wait_until_done=True)` operation that releases only after
`stop()`.

Core tests cover:

- the Stop Stage handler dispatching without a 250-ms Tk delay;
- the manual resolution command returning while movement remains active;
- cancellation being recorded before the first hardware stop call;
- all participating stage devices receiving a stop attempt despite one failure;
- no subsequent stage, zoom-offset, waveform, or acquisition work after
  cancellation;
- cancellation between distinct stage-device moves;
- same-microscope zoom and cross-microscope offset transitions;
- feature-driven resolution changes terminating their feature/acquisition path;
- model-proxy contention retrying instead of dropping Stop Stage;
- stopped-position readback and event payload correctness; and
- cancellation recovery waiting for stop attempts and position readback before
  validating or displaying Return; and
- termination cancelling and joining outstanding workers.

Recovery tests cover:

- dialog creation on the Tk thread and deduplication by task ID;
- Close, Escape, and Keep causing no movement;
- Return using literal saved coordinates exactly once;
- invalid or missing snapshots disabling Return;
- configured stage limits remaining enabled;
- return movement remaining cancellable; and
- acquisition staying stopped after either recovery choice.

Focused model and controller tests run locally without launching Aqua Tk. GUI
widget tests run under native Windows CI and, if a Linux Tk test lane is added,
under `xvfb-run -a`. The Homebrew Xvfb server cannot isolate this environment's
Aqua/AppKit Tk build because it is not an X11 client.

### Headless coverage for both Stop Stage buttons

The Stage Control tab and acquisition bar expose separate Stop Stage buttons,
but both must invoke the same immediate `StageController.stop_button_handler`
path. Two independent regression tests will construct the real controller
bindings around lightweight button doubles that store a configured command and
execute it through `invoke()`. One test clicks the Stage Control tab button and
the other clicks the acquisition bar button; each asserts the resulting
`"stop_stage"` command recorded at the parent-controller boundary.

These tests will not construct Tk widgets or open windows. Their mutation check
is binding-specific: deleting either production binding must fail its own test
without relying on the direct handler unit test. No production refactor or new
public API is required for this coverage.

## Rollout and Review Boundaries

The work will be prepared as two stacked, independently reviewable pull
requests unless implementation reveals an unsafe boundary:

1. **Core cancellation and hardware stop.** Removes GUI blocking, adds the
   model-owned resolution lifecycle, cooperatively cancels movement, strengthens
   Stop Stage delivery, prevents acquisition restart, and supplies focused
   safety tests. This PR independently resolves the collision hazard.
2. **Recovery dialog and cancellable return.** Builds on the terminal
   cancellation event, adds the two-choice popup, position snapshots, validated
   return movement, GUI state management, and focused UI/recovery tests.

The first PR must be safe and useful without the second. If the recovery work
requires changing the first PR's core lifecycle contract, the branches will be
recombined into one PR rather than exposing an unstable stacked interface.

Each PR will use a detailed description, request the repository's designated
reviewer when known, and link its plan and reuse analysis. The core PR will use
`Closes #486`; the stacked recovery PR will reference the core PR without a
second closing directive.

## Acceptance Criteria

- Stop Stage remains clickable during every resolution-change stage movement.
- Its handler dispatches without a Tk debounce or controller-side join.
- The cancellation flag is set before stage stop commands are attempted.
- Every participating stage device receives a stop attempt.
- No resolution or acquisition operation schedules new motion after
  cancellation.
- The GUI shows the actual stopped stage coordinates.
- The recovery dialog is not emitted until hardware stop attempts and stopped-position
  readback finish.
- Recovery movement never starts without explicit Return selection.
- Close, Escape, and Keep leave the stages stopped where they are.
- Return uses the recorded pre-movement coordinates and can be stopped again.
- Live and customized acquisitions remain stopped after cancellation.
- Focused tests, formatting, lint, and relevant broader tests pass.
