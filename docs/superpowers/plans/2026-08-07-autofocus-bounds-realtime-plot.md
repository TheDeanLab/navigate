# Autofocus Bounds Validation and Real-Time Plot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject unsafe autofocus trajectories with immediate, continuously refreshed popup feedback, then render autofocus measurements in real time without blocking acquisition.

**Architecture:** A single internal scan-position planner will define frame counts, popup preflight, and model execution. The popup will perform advisory validation from current configuration while the model performs authoritative validation immediately before each knowable scan and treats failed moves as fatal. Real-time plotting will publish accumulated metric snapshots through a dedicated one-slot queue and use Tk-thread coalescing plus a persistent Matplotlib artist, with histogram-style blitting and a full-draw fallback. Popup-independent calibration processing preserves completion bookkeeping if the window is closed mid-run.

**Tech Stack:** Python, Tkinter/ttk, Matplotlib, NumPy/SciPy, pytest, Navigate's feature/event architecture.

## Global Constraints

- Implement and verify Tasks 1–4 before beginning any real-time plotting work.
- Never shift, clamp, truncate, or otherwise rewrite an invalid trajectory.
- When limits are enabled, execute the exact requested trajectory or reject it.
- Do not queue an autofocus frame position when the associated stage move fails.
- Keep all Tk and Matplotlib mutation on the Tk main thread.
- Do not open native Tk windows on the active macOS desktop; use headless tests.
- Preserve the current autofocus start/stop lifecycle and event names used for final results.

## Reuse Analysis

No new user-callable API is needed. Extend the existing `Autofocus` feature, `ValidatedSpinbox` error state, controller stage-update paths, event pump, and `HistogramController` rendering pattern. The internal scan planner replaces the duplicated arithmetic already present in `get_autofocus_frame_num`, `get_steps`, and signal execution; it does not introduce a parallel autofocus abstraction. Replaceable real-time updates use a dedicated one-slot transport so final fit/results, warnings, and completion metadata retain reliable queue capacity.

---

## Task 1: Establish the Focused Baseline

**Files:**

- Test: `test/model/features/test_autofocus.py`
- Test: `test/controller/sub_controllers/test_autofocus.py`
- Test: `test/controller/test_controller.py`
- Test: `test/controller/sub_controllers/test_histogram.py`

- [x] **Step 1: Run the existing focused autofocus tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py -q
```

Expected: PASS. If an unrelated pre-existing failure appears, record it before editing and narrow the baseline to the directly affected tests.

- [x] **Step 2: Run the existing histogram tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_histogram.py -q
```

Expected: PASS. These tests establish that the blitting pattern being reused is healthy before autofocus adopts it.

## Task 2: Centralize Exact Autofocus Scan Planning

**Files:**

- Modify: `src/navigate/model/features/autofocus.py`
- Test: `test/model/features/test_autofocus.py`

- [x] **Step 1: Write failing tests for exact planned positions**

Add literal expected-position tests for the internal planner, including:

```python
assert plan_autofocus_positions(0, 500, 50) == tuple(range(-250, 251, 50))
assert plan_autofocus_positions(0, 10, 2) == (-6, -4, -2, 0, 2, 4)
```

Also cover a non-zero center and a range that is not an exact multiple of the step size. Expected positions must be written independently rather than calculated with production helpers.

- [x] **Step 2: Run the planner tests and confirm the expected failure**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -k 'plan_autofocus_positions' -q
```

Expected: FAIL because the shared planner does not exist.

- [x] **Step 3: Implement one internal pure planner**

Add `plan_autofocus_positions(center, scan_range, step_size)` in `autofocus.py`. Preserve the current acquisition sequence exactly: compute `int(scan_range // step_size) + 1` frames, center the existing even/odd sequence on `center`, and return an immutable tuple.

Update `get_autofocus_frame_num`, `get_steps`, and signal-position selection to derive their counts/targets from this planner instead of repeating arithmetic. Do not change scan ordering or fitting behavior.

- [x] **Step 4: Run the planner and existing model tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -q
```

Expected: PASS.

## Task 3: Add Authoritative Model Bounds and Move Validation

**Files:**

- Modify: `src/navigate/model/features/autofocus.py`
- Test: `test/model/features/test_autofocus.py`

- [x] **Step 1: Write failing bounds-policy tests**

Cover these cases with literal limits and expected error text:

- an in-bounds trajectory;
- lower-bound, upper-bound, and both-bound violations;
- limits disabled;
- coarse-only rejection before acquisition preparation;
- fine-only rejection before acquisition preparation;
- combined scan validates coarse initially and validates the measured-center fine path before its first move;
- a valid move queues the achieved requested position; and
- a `False` stage-move result raises a user-visible error and does not append to `autofocus_pos_queue`.

- [x] **Step 2: Run the new model safety tests and confirm the failures**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -k 'bound or limit or failed_move' -q
```

Expected: FAIL on missing bounds validation and ignored move results.

- [x] **Step 3: Implement shared bounds diagnostics**

Add internal helpers that:

- compare the planned minimum and maximum with configured axis limits;
- bypass only the configured soft-limit check when stage limits are disabled;
- format one consistent message containing scan label, requested interval, allowed interval, and stage-axis label; and
- avoid rounding away an actual violation.

Use `focus-stage` for the focus axis and an axis-specific stage label for other supported stage autofocus axes.

- [x] **Step 4: Preflight immediately knowable model paths**

Before acquisition preparation, read the selected stage-axis current position and reject an invalid coarse path, or an invalid fine-only path. For combined scans, validate only coarse at this point because the fine center is not yet known.

Remote-focus autofocus retains its current non-stage behavior.

- [x] **Step 5: Validate the combined fine path at the transition**

After coarse analysis determines the fine center, construct and validate the exact fine trajectory before its first stage move. Raise `UserVisibleException` with the shared diagnostic on failure.

- [x] **Step 6: Make failed moves fatal before queueing**

Check the boolean return from each autofocus stage move, including restoration/final positioning. On `False`, raise `UserVisibleException` and do not put that target on `autofocus_pos_queue`.

- [x] **Step 7: Run all focused model tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -q
```

Expected: PASS.

## Task 4: Add Live Popup Bounds Feedback and Refresh Hooks

**Files:**

- Modify: `src/navigate/view/popups/autofocus_setting_popup.py`
- Modify: `src/navigate/controller/sub_controllers/autofocus.py`
- Modify: `src/navigate/controller/controller.py`
- Test: `test/view/popups/test_autofocuspopup.py`
- Test: `test/controller/sub_controllers/test_autofocus.py`
- Test: `test/controller/test_controller.py`

- [x] **Step 1: Write failing popup-structure tests**

Assert that the Scan Parameters frame exposes a blank warning variable/label on the row below Fine, spans the scan columns, and uses the active theme danger color when populated.

- [x] **Step 2: Write failing controller-validation tests**

Test `refresh_bounds_validation()` with mocked stage state for:

- valid coarse and fine-only scans;
- invalid coarse and invalid fine-only scans;
- combined coarse+fine showing only a knowable coarse error;
- both immediately knowable scans invalid, with newline-separated messages;
- limits disabled;
- non-stage/remote-focus selection;
- numeric spinbox errors remaining independent; and
- correction clearing the warning and restoring only the bounds error state.

Assert that only the offending Range spinbox uses `_toggle_error(True)`.

- [x] **Step 3: Write failing final-preflight tests**

When Start Autofocus is clicked with an invalid path, assert that the controller shows an error dialog containing the inline diagnostic and does not call the parent controller's autofocus dispatch. A valid path must retain the current dispatch behavior.

- [x] **Step 4: Write failing stage-refresh-hook tests**

Assert that an open autofocus controller refreshes after:

- `update_stage_controller_silent` changes the selected axis position;
- configured stage minimum or maximum changes; and
- stage limits are enabled or disabled.

The hook must be safe when the popup is closed or not initialized.

- [x] **Step 5: Run the new GUI/controller tests and confirm failure**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/view/popups/test_autofocuspopup.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py -k 'autofocus or stage_limit' -q
```

Expected: FAIL on missing warning widgets, validation, and refresh hooks.

- [x] **Step 6: Implement the reserved warning row**

Add a `StringVar`-backed warning label at row 3 of the scan-parameter frame, spanning all scan columns. It is blank by default and uses the theme's danger foreground.

- [x] **Step 7: Implement advisory controller validation**

Use the model's shared planner/diagnostic helpers with:

- `ConfigurationController.get_stage_position_limits` for current min/max;
- the configured `StageParameters` axis position and limits-enabled state; and
- the current device/ref selection.

Keep separate bounds-error bookkeeping so clearing a bounds violation cannot erase an unrelated numeric validation error. Call refresh from existing setting-variable traces and when the selected device/ref changes.

- [x] **Step 8: Add final controller preflight**

At the start of `start_autofocus`, refresh bounds validation. If any immediately knowable path is invalid, show the shared message via `messagebox.showerror` and return before dispatch.

- [x] **Step 9: Add stage position/limit refresh hooks**

Add one guarded helper in the main controller to refresh an existing autofocus popup controller. Invoke it after silent position updates, stage limit-value updates, and limit-enabled toggles. Keep the configuration's limits-enabled value synchronized before refreshing.

- [x] **Step 10: Run the full phase-1 focused suite**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py \
  test/view/popups/test_autofocuspopup.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py -q
```

Expected: PASS.

- [x] **Step 11: Lint phase-1 changes**

Run:

```bash
ruff check \
  src/navigate/model/features/autofocus.py \
  src/navigate/view/popups/autofocus_setting_popup.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  src/navigate/controller/controller.py \
  test/model/features/test_autofocus.py \
  test/view/popups/test_autofocuspopup.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py
```

Expected: PASS.

- [x] **Step 12: Commit the independently verified safety phase**

```bash
git add src/navigate/model/features/autofocus.py \
  src/navigate/view/popups/autofocus_setting_popup.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  src/navigate/controller/controller.py \
  test/model/features/test_autofocus.py \
  test/view/popups/test_autofocuspopup.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/test_controller.py
git commit -m "Prevent unsafe autofocus stage trajectories"
```

Commit body must mention reuse of the existing planner lifecycle, validation widgets, and stage-update paths.

## Task 5: Publish Incremental Autofocus Measurements

**Files:**

- Modify: `src/navigate/model/features/autofocus.py`
- Test: `test/model/features/test_autofocus.py`

- [x] **Step 1: Write failing progress-event tests**

For each successfully processed image, assert one progress event is published after entropy calculation. Assert that successive payload snapshots contain all measurements so far and are copied snapshots rather than aliases of mutable `plot_data`.

- [x] **Step 2: Run the progress tests and confirm failure**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -k 'progress' -q
```

Expected: FAIL because only final autofocus results are currently emitted.

- [x] **Step 3: Emit explicit progress payloads**

After appending each `[position, entropy]` measurement, publish an `autofocus` event whose payload explicitly identifies it as progress and contains a defensive snapshot of accumulated points. Do not include image arrays and do not wait for the GUI.

Preserve the current final event's measured points, fitted curves, and peak information, with an explicit final marker so the controller does not confuse it with progress.

- [x] **Step 4: Run the model tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py -q
```

Expected: PASS.

## Task 6: Coalesce Real-Time Plot Updates on the Tk Thread

**Files:**

- Modify: `src/navigate/controller/sub_controllers/autofocus.py`
- Test: `test/controller/sub_controllers/test_autofocus.py`

- [x] **Step 1: Write failing coalescing and persistent-artist tests**

Cover:

- a progress event received off the Tk thread stores a pending snapshot and schedules at most one `after_idle` callback;
- multiple events before the callback replace the pending data with the latest snapshot;
- flushing occurs on the Tk thread;
- one persistent measured-point artist is updated with `set_data`; and
- repeated progress updates do not accumulate Line2D artists.

- [x] **Step 2: Run the new controller tests and confirm failure**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_autofocus.py -k 'progress or coalesc or persistent' -q
```

Expected: FAIL on missing pending-update state and persistent artist.

- [x] **Step 3: Implement latest-value-wins scheduling**

Mirror `CameraViewController`/`HistogramController`:

- store `_pending_autofocus_data`;
- store one `_autofocus_after_id`;
- use the popup's Tk widget `after_idle` to schedule `_flush_pending_autofocus_update`;
- replace stale pending snapshots; and
- catch/log rendering exceptions without affecting acquisition.

- [x] **Step 4: Initialize and update one measured-point artist**

Create the points artist once when preparing the plot. Ordinary progress updates call `set_data` and do not clear axes, recreate the artist, or call `tight_layout`.

- [x] **Step 5: Run the coalescing/controller tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_autofocus.py -q
```

Expected: PASS.

## Task 7: Add Histogram-Style Blitting, Fallback, and Final Rendering

**Files:**

- Modify: `src/navigate/controller/sub_controllers/autofocus.py`
- Test: `test/controller/sub_controllers/test_autofocus.py`

- [x] **Step 1: Write failing rendering-path tests**

Test:

- capability detection for `copy_from_bbox`, `restore_region`, and `blit`;
- cached-background restore, artist draw, and axes blit on an ordinary update;
- cache invalidation after a draw/resize signal;
- axis expansion causing a full draw and new background before later blits;
- non-blit fallback using a normal nonblocking/full draw;
- final render retaining every measured point and adding fit/peak overlays; and
- cancellation leaving partial measured data visible.

- [x] **Step 2: Run the rendering tests and confirm failure**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_autofocus.py -k 'blit or background or axis or cancel or final_plot' -q
```

Expected: FAIL on missing blit state and cache lifecycle.

- [x] **Step 3: Implement blit capability and cache lifecycle**

Mirror `HistogramController` names and behavior where practical:

- `_blit_supported`;
- `_autofocus_background`;
- `_force_full_redraw`;
- `_invalidate_blit_cache`;
- a draw-event callback that refreshes the cache; and
- full-draw fallback when the backend lacks required methods.

- [x] **Step 4: Implement controlled axis expansion**

Expand x/y limits only when a new point falls outside the current visible interval. Axis changes invalidate the cache and perform one full draw. Subsequent in-range points resume blitting.

- [x] **Step 5: Preserve final overlays and cancellation state**

On a final result, perform one full render containing the complete measured series plus fit curves and peak indicators. On cancellation, cancel any scheduled idle callback safely but leave the most recent measured data/artist visible.

- [x] **Step 6: Run all real-time plotting tests**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py \
  test/controller/sub_controllers/test_autofocus.py -q
```

Expected: PASS.

- [x] **Step 7: Lint phase-2 changes**

Run:

```bash
ruff check \
  src/navigate/model/features/autofocus.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  test/model/features/test_autofocus.py \
  test/controller/sub_controllers/test_autofocus.py
```

Expected: PASS.

- [x] **Step 8: Commit the independently verified plotting phase**

```bash
git add src/navigate/model/features/autofocus.py \
  src/navigate/controller/sub_controllers/autofocus.py \
  test/model/features/test_autofocus.py \
  test/controller/sub_controllers/test_autofocus.py
git commit -m "Plot autofocus measurements during acquisition"
```

Commit body must mention reuse of the existing event pump and histogram blitting pattern.

## Task 8: Final Regression and Documentation Verification

**Files:**

- Verify: `docs/superpowers/specs/2026-08-07-autofocus-bounds-realtime-plot-design.md`
- Verify: `docs/superpowers/plans/2026-08-07-autofocus-bounds-realtime-plot.md`
- Verify: all files changed by Tasks 2–7

- [x] **Step 1: Run the complete focused regression set**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/model/features/test_autofocus.py \
  test/view/popups/test_autofocuspopup.py \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/sub_controllers/test_histogram.py \
  test/controller/test_controller.py -q
```

Expected: PASS.

- [x] **Step 2: Run repository-configured lint on all changed Python files**

Run `ruff check` on every changed Python source and test file. If the repository requires formatting, run `ruff format --check` on that same explicit list.

- [x] **Step 3: Inspect the final diff for scope and safety**

Run:

```bash
git diff origin/develop...HEAD --check
git diff origin/develop...HEAD --stat
git status --short
```

Confirm that no generated artifacts, unrelated user changes, or speculative public APIs were introduced.

- [x] **Step 4: Re-read the issue acceptance path**

Confirm from tests and code that:

- the unsafe initial trajectory cannot prepare acquisition;
- a combined fine scan cannot make its first move before exact validation;
- moving the stage or changing/toggling limits refreshes the open popup;
- final preflight blocks dispatch and explains why;
- every processed metric can be displayed during acquisition; and
- plotting failures cannot stop autofocus.

- [x] **Step 5: Commit any final test/document-only adjustments**

Use an intentional commit message describing only the remaining scope. Do not squash or publish unless requested.

## Task 9: Review Hardening for Event Reliability and Popup Lifetime

- [x] **Step 1: Reproduce reliable-event starvation and close-mid-calibration**

Add failing tests for a saturated progress transport followed by final delivery,
and for reference capture after the autofocus popup has been destroyed.

- [x] **Step 2: Isolate replaceable progress**

Pass a dedicated one-slot multiprocessing queue to the model. Replace a stale
snapshot without blocking, and have the existing Tk event pump drain only the
newest snapshot before reliable events.

- [x] **Step 3: Separate completion processing from popup lifetime**

Keep defocus-calibration reference and configuration updates in a persistent
main-controller-owned object. Limit popup event registration to view-specific
plot events.

- [x] **Step 4: Run focused regressions and lint**

Verify model autofocus, popup controller, main controller, the complete focused
suite, Ruff, and `git diff --check` before requesting final review.
