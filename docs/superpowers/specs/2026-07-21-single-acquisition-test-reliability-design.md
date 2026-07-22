# Reliable Single-Acquisition Test Design

## Context

The Windows `develop` workflow failed in `test_single_acquisition` after the
synthetic camera acquired three frames but the display pipe emitted only two
notifications. `Model.run_data_process()` deliberately sends the newest frame
identifier from each camera batch rather than every identifier in the batch.
The test currently counts pipe notifications, so a valid batch sequence such
as `[0]` followed by `[1, 2]` is miscounted as two frames.

The test is marked for reruns and uses a module-scoped model. Its thread join
and pipe release occur after the assertion, so a failed attempt skips cleanup
and contaminates subsequent reruns.

## Design

Keep the production acquisition and display-pipe behavior unchanged. Update
`test_single_acquisition` to track the most recent integer frame identifier
received from the pipe and assert that it reaches the expected final frame
identifier. This reflects the pipe's contract: intermediate display frames may
be coalesced, but the newest acquired frame is delivered.

Wrap acquisition, pipe reads, and assertions in `try/finally`. In `finally`,
join the data thread when it exists and release `show_img_pipe`, ensuring that
an assertion failure cannot leave shared module-scoped state behind.

## Regression Coverage

Add a small helper for interpreting display-pipe messages and test it with the
split-batch notification sequence `0, 2, "stop"`. The regression must fail
under notification counting and pass when progress is inferred from the final
frame identifier.

Run the updated single-acquisition test together with the existing batch-drain
test in the project `navigate` Conda environment. Then run formatting and lint
checks on the modified test file.

## Scope

This change modifies test code only. It does not alter camera acquisition,
threading, display-pipe messages, or user-visible behavior.
