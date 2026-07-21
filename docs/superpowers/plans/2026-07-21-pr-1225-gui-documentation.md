# PR #1225 GUI Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate the three screenshots affected by PR #1225 and make the channel-defocus and autofocus-calibration documentation match the GUI and implemented behavior.

**Architecture:** Keep the existing capture registry and focused capture IDs. Build the capture controller from the repository's canonical configuration files, route only the autofocus capture through the real controller so the popup contains realistic values, generate the affected assets in an empty temporary directory, and rewrite only the three existing defocus/autofocus passages.

**Tech Stack:** Python 3.9 in the `navigate` conda environment, Tk/ttk, `docs/capture_gui.py`, PNG, Sphinx 5.3, reStructuredText.

## Global Constraints

- Work on `kdean/defocus` in `/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs`.
- Put the worktree `src` first on `PYTHONPATH`; do not import the restored `develop` checkout.
- Regenerate only `ChannelsTab.png`, `channel-selector.png`, and `popup_autofocus_settings.png`.
- Show `Defocus Reference: Not Set` in Channel Settings and `Auto Defocus` in the autofocus popup.
- Use the repository's Mesoscale example configuration rather than the active user's selected microscope.
- Do not change application behavior or unrelated screenshots.
- Use valid reStructuredText role syntax with no whitespace before role backticks.

---

### Task 1: Capture controller-populated GUI states

**Files:**
- Modify: `docs/capture_gui.py:220-255`
- Modify: `docs/capture_gui.py:1590-1597`
- Modify: `docs/source/images/ChannelsTab.png`
- Modify: `docs/source/images/channel-selector.png`
- Modify: `docs/source/images/popup_autofocus_settings.png`
- Test: visual red/green capture of `popup-autofocus-settings`

**Interfaces:**
- Consumes: `controller.menu_controller.popup_autofocus_setting()`, `controller.af_popup_controller`, `_popup_capture_target()`, `_prepare_for_capture()`, `_capture_widget()`, and `_cleanup_controller_popup_attr()`.
- Produces: the existing capture ID with controller-populated values and three updated PNG assets at their existing paths.

- [x] **Step 1: Capture the failing visual baseline**

```bash
capture_before="$(mktemp -d /tmp/navigate-pr1225-before.XXXXXX)"
PYTHONPATH=/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs/src \
  /opt/anaconda3/envs/navigate/bin/python docs/capture_gui.py \
  --capture popup-autofocus-settings --output-root "$capture_before"
```

Expected: the PNG is created, but Device Type, Focusing Axis, Channel, and selected Calibration values are blank; `Auto Defocus` is not visible as the selected action.

- [x] **Step 2: Make the controller context use canonical documentation inputs**

```python
config_dir = SRC_DIR / "navigate" / "config"
parser = create_parser()
args = parser.parse_args(
    [
        "-sh",
        "--config-file",
        str(config_dir / "configuration.yaml"),
        "--experiment-file",
        str(config_dir / "experiment.yml"),
        "--gui-config-file",
        str(config_dir / "gui_configuration.yml"),
    ]
)
```

Expected: captures use the repository's Mesoscale example, including its filter-wheel columns, regardless of the active user experiment.

- [x] **Step 3: Replace `_capture_popup_autofocus()` with the real controller path**

```python
def _capture_popup_autofocus(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    controller = ctx["controller"]
    out_path, should_skip = _popup_capture_target(
        cli_args, "autofocus_settings"
    )
    if should_skip:
        return out_path

    _cleanup_controller_popup_attr(controller, "af_popup_controller")
    controller.menu_controller.popup_autofocus_setting()
    popup_controller = controller.af_popup_controller
    popup_controller.widgets["calibration_action"].set("Auto Defocus")
    popup = popup_controller.view.popup

    try:
        _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _cleanup_controller_popup_attr(controller, "af_popup_controller")
```

- [x] **Step 4: Capture the green visual result**

```bash
capture_after="$(mktemp -d /tmp/navigate-pr1225-after.XXXXXX)"
PYTHONPATH=/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs/src \
  /opt/anaconda3/envs/navigate/bin/python docs/capture_gui.py \
  --capture popup-autofocus-settings --output-root "$capture_after"
```

Expected: the popup shows populated Device Type and Focusing Axis controls, an active `CHn`, `Auto Defocus`, `Reference: none`, and populated scan parameters without clipping or tooltip artifacts.

- [x] **Step 5: Generate exactly the three affected assets**

```bash
capture_final="$(mktemp -d /tmp/navigate-pr1225-final.XXXXXX)"
PYTHONPATH=/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs/src \
  /opt/anaconda3/envs/navigate/bin/python docs/capture_gui.py \
  --capture settings-channels --capture channel-selector \
  --capture popup-autofocus-settings --output-root "$capture_final"
cp "$capture_final/ChannelsTab.png" docs/source/images/ChannelsTab.png
cp "$capture_final/channel-selector.png" docs/source/images/channel-selector.png
cp "$capture_final/popup_autofocus_settings.png" docs/source/images/popup_autofocus_settings.png
```

Expected: only the three named image paths change.

- [x] **Step 6: Inspect the three installed PNGs at original resolution**

Inspect `docs/source/images/ChannelsTab.png`, `docs/source/images/channel-selector.png`, and `docs/source/images/popup_autofocus_settings.png` with the image viewer. Confirm the complete `Defocus Reference: Not Set` row, all autofocus labels and values, clean borders, and legible text.

- [x] **Step 7: Lint and commit the capture update**

```bash
/Users/Dean/.local/bin/ruff check --ignore E402 docs/capture_gui.py
git diff --check
git add docs/capture_gui.py docs/source/images/ChannelsTab.png \
  docs/source/images/channel-selector.png \
  docs/source/images/popup_autofocus_settings.png \
  docs/superpowers/plans/2026-07-21-pr-1225-gui-documentation.md \
  docs/superpowers/specs/2026-07-21-pr-1225-gui-documentation-design.md
git commit -m "docs: refresh defocus GUI screenshots"
```

Expected: Ruff and whitespace validation exit 0 before the capture commit is created. `E402` is excluded because this script intentionally adds the checkout's `src` directory before its Navigate imports; the same five `E402` findings are present before this change.

---

### Task 2: Clarify channel defocus and autofocus calibration

**Files:**
- Modify: `docs/source/01_getting_started/06_acquiring_data.rst:54-55`
- Modify: `docs/source/02_user_guide/03_user_interface_walkthrough/03_acquisition_and_settings_notebooks.rst:56-57`
- Modify: `docs/source/02_user_guide/03_user_interface_walkthrough/06_popups_and_tools.rst:36-66`
- Test: Sphinx HTML build with warnings treated as errors

**Interfaces:**
- Consumes: the GUI labels and behavior implemented by PR #1225 and the screenshots from Task 1.
- Produces: beginner instructions and reference text that distinguish the acquisition reference from the popup's calibration reference.

- [ ] **Step 1: Replace the beginner Defocus bullet**

```rst
    * Set :guilabel:`Defocus` to ``0`` unless the channel has a measured chromatic focus offset. Defocus is a per-channel offset from the zero-defocus focus position, not an absolute focus coordinate. At acquisition start, **navigate** derives that zero-defocus position from the current focus and the active channel's defocus, then applies each channel's offset. The status below the table reports the current reference; see :ref:`Autofocus Settings <ui_autofocus>` to measure channel offsets automatically.
```

- [ ] **Step 2: Make the Channels reference concise and explain its status row**

```rst
6. :guilabel:`Defocus`: channel-specific offset from the zero-defocus focus position.

At acquisition start, **navigate** derives the zero-defocus position from the
current focus and the active channel's defocus. It then moves each channel to
that reference position plus the channel's offset. :guilabel:`Defocus Reference`
shows the reference channel and, when an acquisition reference is active, its
focus position. Manual focus motion invalidates the active acquisition reference.
```

- [ ] **Step 3: Replace the autofocus calibration paragraphs with action-specific guidance**

```rst
The :guilabel:`Channel` must be active in Channel Settings. Choose a
:guilabel:`Calibration` action before pressing :guilabel:`Start Autofocus`:

* :guilabel:`Regular` focuses the selected channel without calculating a channel
  offset.
* :guilabel:`Capture Reference` focuses the selected channel, makes it the
  zero-defocus calibration channel, and retains its best-focus position for the
  current calibration sequence.
* :guilabel:`Populate Defocus` focuses the selected channel and writes the
  difference from the previously captured reference into that channel's
  :guilabel:`Defocus` value. Capture a reference first.
* :guilabel:`Auto Defocus` uses the selected channel as the reference, focuses
  every other active channel, and populates all active channel offsets in one
  sequence. Stop any acquisition before starting it.

The popup's :guilabel:`Reference` status reports the calibration reference.
:guilabel:`Populate Defocus` requires the captured focus retained by the current
popup session. The resulting per-channel :guilabel:`Defocus` values are stored
with the experiment settings and are used during acquisition.
```

- [ ] **Step 4: Build the HTML documentation with strict warnings**

```bash
PYTHONPATH=/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs/src \
  /opt/anaconda3/envs/navigate/bin/sphinx-build \
  -W --keep-going -b html docs/source docs/build/html
```

Expected: exit 0 with no malformed roles, missing image errors, or other warnings.

- [ ] **Step 5: Run the focused PR tests against the worktree source**

```bash
PYTHONPATH=/Users/Dean/.config/superpowers/worktrees/navigate/pr-1225-docs/src \
  /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' \
  test/controller/sub_controllers/test_autofocus.py \
  test/controller/sub_controllers/test_channels_tab.py \
  test/model/test_microscope.py -q
```

Expected: `30 passed` and no failures.

- [ ] **Step 6: Verify and commit the documentation**

```bash
git diff --check
git diff -- docs/source/01_getting_started/06_acquiring_data.rst \
  docs/source/02_user_guide/03_user_interface_walkthrough/03_acquisition_and_settings_notebooks.rst \
  docs/source/02_user_guide/03_user_interface_walkthrough/06_popups_and_tools.rst
git add docs/source/01_getting_started/06_acquiring_data.rst \
  docs/source/02_user_guide/03_user_interface_walkthrough/03_acquisition_and_settings_notebooks.rst \
  docs/source/02_user_guide/03_user_interface_walkthrough/06_popups_and_tools.rst
git commit -m "docs: explain channel defocus calibration"
```

- [ ] **Step 7: Push and verify PR #1225**

```bash
git push origin kdean/defocus
git rev-parse HEAD
git ls-remote --heads origin kdean/defocus
gh pr view 1225 --json headRefOid,url,statusCheckRollup
```

Expected: local `HEAD`, the remote branch SHA, and PR #1225's `headRefOid` are identical.
