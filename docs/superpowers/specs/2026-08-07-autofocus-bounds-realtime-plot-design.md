# Autofocus Bounds Validation and Real-Time Plot Design

## Purpose

Resolve GitHub issue #315 by preventing autofocus from commanding focus-stage
positions outside enabled stage limits. Give users immediate, continuously
updated feedback in the Autofocus Settings popup, while retaining a final
fail-closed check before acquisition. After the bounds work is independently
tested, update the autofocus graph as each image's focus metric becomes
available without slowing acquisition.

## Delivery Order

The work has two sequential phases:

1. Implement bounds planning, live popup validation, and model-side safety
   checks. Complete focused tests before starting phase 2.
2. Implement coalesced real-time plot updates using the existing histogram
   blitting pattern and complete a separate set of focused tests.

The phases may share internal scan-planning data, but phase 2 must not be used
to justify weakening or postponing phase 1 safety checks.

## Scan Planning and Bounds Policy

Autofocus will construct the exact sequence of requested positions before it
moves a stage. The same internal planning function will be used for frame
counts, popup validation, and signal execution so the displayed bounds and
executed path cannot disagree.

When stage limits are enabled, every planned position must lie within the
selected stage axis's configured minimum and maximum. If any position is
outside that interval, autofocus will not shift, clamp, truncate, or otherwise
alter the trajectory. It will reject the scan before the first affected move.
This preserves the user's intended motion envelope and avoids duplicate
measurements at a clamped boundary.

The controller check provides early feedback, but the model remains
authoritative. Model-side validation protects autofocus started through other
entry points and handles configuration or position changes between the popup
check and acquisition. A stage move that returns `False` is also a hard failure:
the associated frame position must not be placed on the autofocus processing
queue.

If software stage limits are disabled, configured soft limits do not block the
scan. Individual device or hardware failures still abort autofocus through the
failed-move check.

### Coarse and Fine Centers

- A coarse scan is centered on the current selected stage-axis position and can
  be validated immediately.
- A fine-only scan is centered on the current selected stage-axis position and
  can be validated immediately.
- When coarse and fine scans are both selected, the fine center is the measured
  coarse result and is not known before acquisition. The popup will validate
  the coarse path immediately. After the coarse result is available, the model
  will construct and validate the exact fine path before its first move. If it
  is invalid, autofocus stops safely and reports the fine-scan bounds error.

The popup must not show a definitive fine-scan error based on an assumed coarse
result. That would be misleading. The final model-side check guarantees safety
at the point where the fine center becomes known.

## Immediate Popup Feedback

The Scan Parameters panel will reserve a warning row directly below the Fine
row. A themed label spanning the panel columns will normally be blank. When an
immediately knowable scan is invalid, it will show red text such as:

> The requested coarse scan (-250 to 250 µm) exceeds the focus-stage limits
> (0 to 1000 µm).

The offending scan's Range spinbox text will use the existing validation danger
color. The Step Size spinbox will retain its normal color unless its own numeric
validation fails. If both immediately knowable scans are invalid, the warning
row will show both messages on separate lines and both Range spinboxes will be
red.

Validation will refresh when any relevant state changes:

- coarse or fine selection, range, or step size;
- selected autofocus device or axis;
- current position of the selected stage axis;
- configured minimum or maximum for that axis; or
- stage-limit enablement.

When the user moves the focus stage or edits/toggles limits while the popup is
open, the warning and spinbox color will update immediately. Correcting the
condition clears the warning and restores the normal text color.

The Start Autofocus button remains governed by the existing acquisition-state
logic. Clicking it with a bounds error performs one final controller preflight,
shows an error dialog with the same actionable message, and does not dispatch
autofocus. Keeping the button available preserves that explicit final
notification rather than silently disabling the action.

## Real-Time Autofocus Plot

After each image's DCT entropy value is calculated, the model will publish an
autofocus-progress event containing the accumulated position/metric data. It
will not publish image pixels for plotting. Acquisition and metric calculation
must not wait for the GUI.

The popup controller will follow the image-display and histogram "latest value
wins" pattern:

1. Store the newest pending progress dataset.
2. Schedule at most one Tk `after_idle` callback.
3. Replace older pending data if another event arrives before that callback.
4. Update a persistent Matplotlib point artist on the Tk thread.

The plot will reuse the intensity histogram's blitting strategy:

- detect whether the canvas supports `copy_from_bbox`, `restore_region`, and
  `blit`;
- mark the changing point artist as animated when blitting is supported;
- cache the static axes background after a full draw;
- restore the background, draw only the changing artist, and blit the axes
  region for ordinary point updates;
- invalidate and rebuild the cache after resize, theme/layout changes, or axis
  limit changes; and
- fall back to a normal nonblocking draw when blitting is unavailable.

The controller will not clear the axes, recreate artists, or run
`tight_layout()` for every measurement. X and Y limits will expand only when
new data require it; such an expansion performs one full redraw and refreshes
the cached background. Ordinary points inside the current limits use blitting.

At autofocus completion, one full render will preserve all measured points and
add the selected fitted curve and peak indicators. Cancellation will leave the
partial measured curve visible rather than replacing it with nonexistent final
data.

## Event and Thread Boundaries

The model data thread owns focus-metric calculation and progress publication.
The main controller's existing event pump transfers progress to the popup
controller. All Tk and Matplotlib artist mutation occurs on the Tk main thread.
Progress events are snapshots and may be coalesced for display; the model's
authoritative `plot_data` retains every measurement for fitting and final
reporting.

## Error Handling

- Invalid coarse or fine-only paths are rejected before acquisition begins.
- An invalid combined fine path is rejected after coarse analysis and before
  the first fine move.
- A failed stage move aborts autofocus and is never represented as a successful
  measurement position.
- Controller and model errors use the same scan label, requested interval, and
  allowed interval so immediate and final feedback agree.
- Plot-rendering failures are logged and isolated from acquisition; they do not
  stop autofocus.
- Unsupported blitting backends use the full-draw fallback.

## Testing

Phase 1 tests will cover:

- exact position planning for odd and even frame counts;
- valid paths and lower-bound, upper-bound, and both-bound violations;
- limits enabled and disabled;
- coarse-only, fine-only, and combined coarse-to-fine behavior;
- rejection before acquisition preparation or the first affected move;
- failed moves not entering the autofocus frame queue;
- red Range spinbox and inline warning behavior;
- warning clearance after stage movement, limit edits, or limit toggles; and
- the final dialog and absence of autofocus dispatch for an invalid path.

Phase 2 tests will cover:

- one progress publication per processed autofocus measurement;
- snapshots retaining every calculated point;
- coalescing multiple pending updates into the newest dataset;
- persistent artist updates without artist accumulation;
- the blit path, cache invalidation, and non-blit fallback;
- axis expansion causing a full redraw before blitting resumes;
- final fit and peak overlays; and
- cancellation preserving the partial plot.

Focused model and controller tests will run after each phase. No native Tk
windows will be opened on the active macOS desktop; GUI behavior will be
covered by the repository's headless controller/view tests.

## Reuse Analysis

This design extends existing mechanisms rather than adding parallel lifecycle
or rendering abstractions:

- retain the existing Autofocus feature and event queue;
- centralize and reuse its current step/range calculation instead of adding a
  second scan algorithm;
- use `ConfigurationController.get_stage_position_limits` and existing stage
  limit state as the controller authority;
- use `ValidatedSpinbox` error coloring and the active theme's danger color;
- refresh from the existing stage-position and stage-limit update paths;
- reuse the controller event pump for progress delivery; and
- mirror `HistogramController`'s `after_idle` coalescing, persistent artist,
  background invalidation, blitting, and fallback behavior.

No new user-callable public API or independent plotting framework is required.
