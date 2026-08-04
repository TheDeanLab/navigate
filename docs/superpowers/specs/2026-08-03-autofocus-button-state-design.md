# Autofocus Button State Design

## Purpose

Prevent users from starting a second autofocus routine while an autofocus
acquisition is starting, running, or stopping. Keep the existing separate Start
Autofocus and Stop Acquisition controls and make their enabled states describe
the current acquisition lifecycle.

## State Model

The autofocus popup will use four UI states:

| Acquisition state | Start Autofocus | Stop Acquisition |
| --- | --- | --- |
| Idle | Enabled | Disabled |
| Starting | Disabled | Disabled |
| Running | Disabled | Enabled |
| Stopping | Disabled | Disabled |

Normal completion, cancellation completion, and startup failure return the popup
to Idle.

## Controller Behavior

The existing popup state method will set both button states rather than only the
Stop Acquisition state. The existing controller lifecycle callbacks remain the
authority for entering Running and returning to Idle.

Pressing Start Autofocus will enter Starting before dispatching the acquisition.
Pressing Stop Acquisition will enter Stopping and reuse the existing
`execute("stop_acquire")` route. Start will not be re-enabled by the button
click itself; it will be re-enabled when acquisition cleanup reaches the
existing completion callback.

If the popup is opened during an acquisition, it will initialize in Running.
If it is opened while idle, it will initialize in Idle.

## Error Handling

The existing capture-start error callback will restore Idle, ensuring a failed
autofocus launch does not leave Start Autofocus disabled.

## Testing

Controller tests will verify:

- Idle enables Start and disables Stop.
- Starting disables both controls immediately after Start is invoked.
- Running keeps Start disabled and enables Stop.
- Stopping disables both controls.
- Completion and startup failure restore Idle.

The existing global stop-route and model cancellation tests remain unchanged.
The documentation screenshot already represents Idle and therefore does not
need regeneration.
