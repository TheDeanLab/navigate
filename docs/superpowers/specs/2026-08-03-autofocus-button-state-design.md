# Autofocus Button State Design

## Purpose

Prevent users from starting a second autofocus routine while autofocus is
starting, running, or stopping. Preserve Navigate's existing ability to inject
autofocus into a Continuous Scan. Keep the separate Start Autofocus and Stop
Acquisition controls and make their enabled states describe both the acquisition
and autofocus lifecycles.

## State Model

The popup will combine acquisition state with an autofocus-active flag:

| Acquisition state | Autofocus active | Start Autofocus | Stop Acquisition |
| --- | --- | --- | --- |
| Idle | No | Enabled | Disabled |
| Starting autofocus | Yes | Disabled | Disabled |
| Continuous Scan | No | Enabled | Enabled |
| Continuous Scan | Yes | Disabled | Enabled |
| Non-live acquisition | No | Disabled | Enabled |
| Stopping | Either | Disabled | Disabled |

Normal acquisition completion, cancellation completion, and startup failure
return the popup to Idle. Completion of autofocus injected into a Continuous
Scan clears only the autofocus-active flag, so Start is re-enabled while Stop
remains enabled.

## Controller Behavior

The popup will track acquisition state separately from autofocus activity and
render both button states from those values. The main controller will own the
autofocus-active flag so closing and reopening the popup cannot bypass the Start
button guard.

Pressing Start Autofocus will mark autofocus active before dispatch. For
standalone autofocus, acquisition also enters Starting. For live injection, the
existing Continuous Scan remains Running. Pressing Stop Acquisition will enter
Stopping and reuse the existing `execute("stop_acquire")` route. Start will not
be re-enabled by the Stop click itself.

The model will emit one `autofocus_sequence_complete` event after an injected
autofocus feature sequence has fully completed and the normal live feature list
has been restored. The controller will clear the autofocus-active flag on that
event. Per-channel `autofocus_complete` events remain responsible only for
calibration metadata.

If the popup is reopened, it will initialize from the controller's current
acquisition and autofocus state.

## Error Handling

The existing capture-start error callback will clear autofocus activity and
restore Idle, ensuring a failed standalone launch does not leave Start
Autofocus disabled. Stopping an acquisition disables both buttons until existing
acquisition cleanup finishes.

## Testing

Controller tests will verify:

- Idle enables Start and disables Stop.
- Starting standalone autofocus disables both controls.
- Continuous Scan enables both controls before autofocus.
- Live autofocus disables Start but leaves Stop enabled.
- Completing live autofocus re-enables Start while leaving Stop enabled.
- Non-live acquisitions disable Start and enable Stop.
- Stopping disables both controls.
- Acquisition completion and startup failure restore Idle.

Model tests will verify the sequence-complete event is emitted only after the
live feature list is restored. The existing global stop-route and cancellation
tests remain unchanged. The documentation screenshot already represents Idle
and therefore does not need regeneration.
