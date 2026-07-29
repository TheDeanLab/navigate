# PR #1225 GUI Documentation Design

## Goal

Update the documentation for PR #1225 so the screenshots and prose accurately
explain the channel-aware defocus reference and autofocus calibration controls.

## Scope

- Work on the existing `kdean/defocus` PR branch in an isolated worktree.
- Preserve local `develop` on the remote preservation branch, then keep local
  `develop` aligned with `origin/develop`.
- Regenerate the two Channel Settings assets affected by the new defocus
  reference status row:
  - `docs/source/images/ChannelsTab.png`
  - `docs/source/images/channel-selector.png`
- Regenerate the autofocus asset affected by the new channel, calibration, and
  reference controls:
  - `docs/source/images/popup_autofocus_settings.png`
- Improve the related reStructuredText so users understand the difference
  between the runtime zero-defocus reference and the temporary autofocus
  calibration reference.

Application behavior, unrelated screenshots, and broad screenshot refreshes are
out of scope.

## Capture Behavior

`docs/capture_gui.py` will continue to use the existing focused capture IDs and
will build its controller from the repository's canonical configuration files
instead of the active user experiment. The autofocus capture will populate
deterministic representative values for the new controls before taking the
screenshot. Channel Settings captures will show the
default `Defocus Reference: Not Set` state because that is the state users first
encounter before acquisition establishes a runtime reference.

Only the three named assets will be generated. Any unexpected image changes or
additional generated files will be removed from the change set.

## Documentation Content

The Channels documentation will define per-channel defocus as an offset from a
zero-defocus plane and explain what the visible reference status means. The
Autofocus documentation will describe the four calibration actions using the
labels shown by the GUI:

- `Regular`
- `Capture Reference`
- `Populate Defocus`
- `Auto Defocus`

The text will state which values persist in the experiment configuration and
which reference state is temporary. reStructuredText roles will use valid
syntax, including no whitespace between role names and their backticks.

## Verification

- Run the focused screenshot captures in the project `navigate` conda
  environment while importing the worktree checkout.
- Inspect all three generated PNGs for complete controls, readable labels,
  consistent theme, and clean cropping.
- Build the Sphinx HTML documentation with warnings treated as errors.
- Run `ruff` against `docs/capture_gui.py` if that script changes, excluding the
  file's existing `E402` exceptions for checkout-path bootstrapping.
- Run `git diff --check` and confirm the final diff contains only the intended
  design, capture, image, and documentation files.
