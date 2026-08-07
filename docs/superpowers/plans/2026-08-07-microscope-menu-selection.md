# Microscope Menu Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the active microscope immediately legible in Navigate's Microscope Configuration menu on Windows and explicit on every platform.

**Architecture:** Extend the existing global Tk option database with themed menu-selection and disabled-text colors. Add a read-only status entry to the existing microscope menu and update it through the same `resolution_value` trace that already dispatches microscope and zoom changes.

**Tech Stack:** Python, tkinter/Tk 8.6, pytest, unittest.mock

## Global Constraints

- Preserve the existing `resolution_value` radiobutton as the authority for microscope and zoom selection.
- Apply menu colors globally without platform-specific branches.
- Display `Current microscope: <name>` as a disabled first menu entry followed by a separator.
- Retain the configured microscope name if the resolution value is empty during startup.
- Do not change microscope-selection or zoom-selection semantics.
- Native Windows smoke testing remains the final visual validation; macOS Tk cannot reproduce Windows menu rendering.

---

## File Structure

- `src/navigate/view/theme.py`: owns global Tk menu color defaults.
- `src/navigate/controller/sub_controllers/menus.py`: owns microscope-menu construction and synchronization with `resolution_value`.
- `test/view/test_theme.py`: verifies observable option-database writes during theme application.
- `test/controller/sub_controllers/test_menus_additional.py`: verifies status-row construction and synchronization behavior without opening a GUI.

### Task 1: Add global themed menu indicator colors

**Files:**
- Modify: `src/navigate/view/theme.py:1137-1141`
- Test: `test/view/test_theme.py`

**Interfaces:**
- Consumes: existing `text` and `muted_text` palette values in `apply_theme(root, gui_settings)`.
- Produces: Tk option database entries `*Menu.SelectColor` and `*Menu.DisabledForeground`.

- [ ] **Step 1: Write the failing test**

Add a test that supplies a `MagicMock` root and style, bypasses rounded-tab image generation, calls `apply_theme`, and checks the actual option writes:

```python
def test_apply_theme_sets_legible_menu_state_colors(monkeypatch):
    root = MagicMock()
    style = MagicMock()
    style.theme_names.return_value = ("clam",)
    monkeypatch.setattr(theme.ttk, "Style", lambda _root: style)
    monkeypatch.setattr(theme, "_apply_rounded_notebook_tabs", lambda *args, **kwargs: None)

    _, palette = theme.apply_theme(root)

    assert call("*Menu.SelectColor", palette["text"]) in root.option_add.call_args_list
    assert call(
        "*Menu.DisabledForeground", palette["muted_text"]
    ) in root.option_add.call_args_list
```

Import `MagicMock` and `call` from `unittest.mock` at the top of the test file.

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH="$PWD/src" /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q test/view/test_theme.py::test_apply_theme_sets_legible_menu_state_colors
```

Expected: FAIL because neither menu option is registered.

- [ ] **Step 3: Add the minimal global theme options**

Immediately after the existing menu foreground options in `apply_theme`, add:

```python
root.option_add("*Menu.DisabledForeground", muted_text)
root.option_add("*Menu.SelectColor", text)
```

- [ ] **Step 4: Run the focused theme test**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Commit the independently testable theme change**

```bash
git add src/navigate/view/theme.py test/view/test_theme.py
git commit -m "fix: improve themed menu indicator contrast"
```

### Task 2: Add and synchronize the current-microscope status row

**Files:**
- Modify: `src/navigate/controller/sub_controllers/menus.py:580-615`
- Test: `test/controller/sub_controllers/test_menus_additional.py`

**Interfaces:**
- Consumes: `self.resolution_value.get()`, configured `MicroscopeState.microscope_name`, and `self.view.menubar.menu_resolution`.
- Produces: `MenuController._on_resolution_value_changed(*args) -> None`, which updates menu entry index `0` and dispatches the unchanged `resolution` command.

- [ ] **Step 1: Write failing status-row tests**

Extend the `menu_controller` fixture's `DummyVar` so `set()` invokes registered write callbacks. Add focused tests using the existing mocked menu boundary:

```python
def test_initialize_menus_starts_with_current_microscope_status(menu_controller):
    controller, _ = menu_controller

    controller.initialize_menus()

    menu = controller.view.menubar.menu_resolution
    assert menu.add_command.call_args_list[0] == call(
        label="Current microscope: ScopeA", state="disabled"
    )
    assert menu.add_separator.call_args_list[0] == call()


def test_resolution_change_refreshes_current_microscope_status(menu_controller):
    controller, parent_controller = menu_controller
    controller.initialize_menus()
    menu = controller.view.menubar.menu_resolution
    menu.reset_mock()

    controller.resolution_value.set("ScopeB 20x")

    menu.entryconfigure.assert_called_once_with(
        0, label="Current microscope: ScopeB"
    )
    parent_controller.execute.assert_called_with("resolution", "ScopeB 20x")
```

Also add a direct empty-value test that calls `_on_resolution_value_changed()` after clearing the variable and verifies no status-label replacement occurs while the existing resolution dispatch still happens.

- [ ] **Step 2: Run the status-row tests to verify they fail**

Run:

```bash
PYTHONPATH="$PWD/src" /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/controller/sub_controllers/test_menus_additional.py::test_initialize_menus_starts_with_current_microscope_status \
  test/controller/sub_controllers/test_menus_additional.py::test_resolution_change_refreshes_current_microscope_status \
  test/controller/sub_controllers/test_menus_additional.py::test_empty_resolution_retains_current_microscope_status
```

Expected: FAIL because the status row and callback do not exist.

- [ ] **Step 3: Add the status entry before microscope choices**

At the start of the Zoom menu section, add:

```python
microscope_name = self.parent_controller.configuration["experiment"][
    "MicroscopeState"
]["microscope_name"]
self.view.menubar.menu_resolution.add_command(
    label=f"Current microscope: {microscope_name}",
    state="disabled",
)
self.view.menubar.menu_resolution.add_separator()
```

- [ ] **Step 4: Consolidate synchronization in one callback**

Replace the trace lambda with:

```python
self.resolution_value.trace_add("write", self._on_resolution_value_changed)
```

Add this private method near `initialize_menus`:

```python
def _on_resolution_value_changed(self, *args) -> None:
    """Synchronize the microscope menu label and dispatch a resolution change."""
    resolution_value = self.resolution_value.get()
    if resolution_value:
        microscope_name = resolution_value.rsplit(" ", 1)[0]
        self.view.menubar.menu_resolution.entryconfigure(
            0, label=f"Current microscope: {microscope_name}"
        )
    self.parent_controller.execute("resolution", resolution_value)
```

Using `rsplit(" ", 1)` preserves microscope names containing spaces while treating the final token as the zoom value.

- [ ] **Step 5: Run the focused status tests**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 6: Run the complete affected test modules**

```bash
PYTHONPATH="$PWD/src" /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/view/test_theme.py \
  test/controller/sub_controllers/test_menus.py \
  test/controller/sub_controllers/test_menus_additional.py
```

Expected: all tests PASS.

- [ ] **Step 7: Run formatting and static checks**

```bash
/opt/anaconda3/bin/black --check \
  src/navigate/view/theme.py \
  src/navigate/controller/sub_controllers/menus.py \
  test/view/test_theme.py \
  test/controller/sub_controllers/test_menus_additional.py
/Users/Dean/.local/bin/ruff check \
  src/navigate/view/theme.py \
  src/navigate/controller/sub_controllers/menus.py \
  test/view/test_theme.py \
  test/controller/sub_controllers/test_menus_additional.py
git diff --check
```

Expected: all commands exit successfully.

- [ ] **Step 8: Commit the menu status behavior**

```bash
git add src/navigate/controller/sub_controllers/menus.py \
  test/controller/sub_controllers/test_menus_additional.py \
  docs/superpowers/plans/2026-08-07-microscope-menu-selection.md
git commit -m "feat: show active microscope in configuration menu"
```

### Task 3: Final verification and handoff

**Files:**
- Verify only; no planned modifications.

**Interfaces:**
- Consumes: committed Task 1 and Task 2 behavior.
- Produces: an evidence-backed handoff that separates automated checks from pending native Windows visual validation.

- [ ] **Step 1: Run final focused verification from a clean tree**

```bash
git status --short
PYTHONPATH="$PWD/src" /opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' -q \
  test/view/test_theme.py \
  test/controller/sub_controllers/test_menus.py \
  test/controller/sub_controllers/test_menus_additional.py
```

Expected: clean status and all tests PASS.

- [ ] **Step 2: Record the native Windows smoke-test procedure**

On Windows, launch Navigate with a configuration containing at least two microscopes, open **Microscope Configuration**, and verify:

1. The selected radiobutton checkmark is clearly visible both normally and while hovered.
2. `Current microscope: <name>` appears at the top of the menu.
3. Selecting a different microscope updates both the status row and checkmark.
4. A microscope with multiple zoom positions updates the status row after choosing a zoom from its submenu.

Do not report this visual validation as complete unless it is actually run on native Windows.
