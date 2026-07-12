# Optional OpenGL Import and User Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `navigate.main` importable without OpenGL extras and give beginner-friendly terminal and log guidance when the optional viewer is requested without its dependencies.

**Architecture:** Move the standalone viewer import behind a small loader in `navigate.main`. The loader owns missing-package mapping, actionable terminal output, and technical logging; `main()` owns cleanup of UI and logging resources when viewer startup cannot proceed.

**Tech Stack:** Python 3.9, Tkinter, standard-library logging, pytest, subprocess-based import isolation.

## Global Constraints

- Standard **navigate** imports and non-viewer launches must not import `OpenGL`, `glfw`, `glm`, or `tkinterdnd2`.
- Terminal guidance must use the active `sys.executable` and include commands for both a source checkout and an installed package.
- Terminal guidance must explain Conda or virtual-environment activation and show `navigate --viewer` as the retry command.
- Technical exceptions and tracebacks must be logged without showing beginners a raw traceback by default.
- Failed viewer startup must destroy the splash/root where possible and stop the logging listener exactly once.
- Do not modify renderer behavior or address other PR review findings in this change.

---

### Task 1: Add the optional-import regression test

**Files:**
- Create: `test/test_main_optional_dependencies.py`
- Modify: `src/navigate/main.py:40-130`

**Interfaces:**
- Consumes: the public import path `navigate.main`.
- Produces: `test_main_import_does_not_require_opengl_dependencies()` as the regression guard for normal installations.

- [ ] **Step 1: Write the failing subprocess test**

```python
import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_main_import_does_not_require_opengl_dependencies():
    repository_root = Path(__file__).resolve().parents[1]
    source_root = repository_root / "src"
    script = textwrap.dedent(
        """
        import builtins

        original_import = builtins.__import__
        blocked = {"OpenGL", "glfw", "glm", "tkinterdnd2"}

        def block_optional_imports(name, *args, **kwargs):
            root_name = name.split(".", 1)[0]
            if root_name in blocked:
                raise ModuleNotFoundError(
                    f"No module named '{root_name}'", name=root_name
                )
            return original_import(name, *args, **kwargs)

        builtins.__import__ = block_optional_imports
        import navigate.main
        """
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(source_root), environment.get("PYTHONPATH", "")])
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main_optional_dependencies.py -q
```

Expected: FAIL because importing `navigate.main` reaches the module-level standalone viewer import and the subprocess raises `ModuleNotFoundError: No module named 'tkinterdnd2'`.

- [ ] **Step 3: Make the minimal lazy-import change**

Remove the module-level `VolumeViewer` import from `src/navigate/main.py` and
replace the existing `import OpenGL` guard in the viewer branch with:

```python
    elif command_line_args.viewer:
        from navigate.view.display_backends.volume_viewer_standalone import (
            VolumeViewer,
        )

        volume_viewer = VolumeViewer(root=root, splash_screen=splash_screen)
        root = volume_viewer
```

This is intentionally the smallest change that keeps normal imports isolated;
the next task adds the approved reporting and error handling.

- [ ] **Step 4: Run the import test and verify GREEN**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main_optional_dependencies.py -q
```

Expected: 1 passed.

- [ ] **Step 5: Commit the import isolation**

```bash
git add src/navigate/main.py test/test_main_optional_dependencies.py
git commit -m "Load the OpenGL viewer only when requested"
```

### Task 2: Implement lazy import and actionable reporting

**Files:**
- Modify: `src/navigate/main.py:33-147`
- Modify: `test/test_main_optional_dependencies.py`

**Interfaces:**
- Produces: `_missing_viewer_distribution(error: BaseException) -> Optional[str]`.
- Produces: `_build_volume_viewer_error_message(error: BaseException) -> str`.
- Produces: `_load_volume_viewer() -> Optional[type]`.
- Consumes: `sys.executable`, module `logger`, and the optional `VolumeViewer` class.

- [ ] **Step 1: Add failing tests for package mapping, terminal guidance, and logging**

Add imports and tests to `test/test_main_optional_dependencies.py`:

```python
import builtins
import logging

import navigate.main as main_module


def test_load_volume_viewer_reports_actionable_dependency_guidance(
    monkeypatch, capsys, caplog
):
    original_import = builtins.__import__

    def fail_viewer_import(name, *args, **kwargs):
        if name == "navigate.view.display_backends.volume_viewer_standalone":
            raise ModuleNotFoundError(
                "No module named 'tkinterdnd2'", name="tkinterdnd2"
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_viewer_import)

    with caplog.at_level(logging.ERROR, logger="navigate.main"):
        viewer_class = main_module._load_volume_viewer()

    terminal_message = capsys.readouterr().err
    quoted_python = f'"{sys.executable}"'
    assert viewer_class is None
    assert "Unable to start the optional navigate Volume Viewer" in terminal_message
    assert "tkinterdnd2" in terminal_message
    assert "activate" in terminal_message.lower()
    assert f'{quoted_python} -m pip install -e ".[opengl]"' in terminal_message
    assert (
        f'{quoted_python} -m pip install "navigate-micro[opengl]"'
        in terminal_message
    )
    assert "navigate --viewer" in terminal_message
    assert "ModuleNotFoundError: No module named 'tkinterdnd2'" in terminal_message
    assert "Unable to import the optional Volume Viewer" in caplog.text
```

- [ ] **Step 2: Run the reporting test and verify RED**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main_optional_dependencies.py::test_load_volume_viewer_reports_actionable_dependency_guidance -q
```

Expected: ERROR with `AttributeError` because `_load_volume_viewer` does not exist.

- [ ] **Step 3: Implement the loader and message builder**

In `src/navigate/main.py`, remove the module-level `VolumeViewer` import; add `logging`, `sys`, and `Optional`; define:

```python
logger = logging.getLogger(__name__)

VIEWER_IMPORT_TO_DISTRIBUTION = {
    "OpenGL": "PyOpenGL",
    "glfw": "glfw",
    "glm": "PyGLM",
    "tkinterdnd2": "tkinterdnd2",
}


def _missing_viewer_distribution(error: BaseException) -> Optional[str]:
    module_name = getattr(error, "name", None)
    if not module_name:
        return None
    root_name = str(module_name).split(".", 1)[0]
    return VIEWER_IMPORT_TO_DISTRIBUTION.get(root_name, str(module_name))


def _build_volume_viewer_error_message(error: BaseException) -> str:
    python_command = f'"{sys.executable}"'
    distribution = _missing_viewer_distribution(error)
    dependency_line = (
        f"Missing or unavailable Python package: {distribution}."
        if distribution
        else "An optional viewer dependency could not be loaded."
    )
    return "\n".join(
        [
            "Unable to start the optional navigate Volume Viewer.",
            "The standard navigate application is still available.",
            "",
            dependency_line,
            "The Volume Viewer dependencies are not included in a standard installation.",
            "If you use Conda or a virtual environment, activate the environment",
            "that you normally use to run navigate before installing anything.",
            "",
            "From a navigate source checkout, run:",
            f'  {python_command} -m pip install -e ".[opengl]"',
            "",
            "If navigate was installed as a package, run:",
            f'  {python_command} -m pip install "navigate-micro[opengl]"',
            "",
            "Then retry:",
            "  navigate --viewer",
            "",
            "If the viewer still does not start, check the navigate log and report",
            "the technical error shown below:",
            f"  {type(error).__name__}: {error}",
        ]
    )


def _load_volume_viewer() -> Optional[type]:
    try:
        from navigate.view.display_backends.volume_viewer_standalone import (
            VolumeViewer,
        )
    except (ImportError, OSError) as error:
        logger.exception("Unable to import the optional Volume Viewer")
        print(_build_volume_viewer_error_message(error), file=sys.stderr)
        return None
    return VolumeViewer
```

- [ ] **Step 4: Run import and reporting tests and verify GREEN**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main_optional_dependencies.py -q
```

Expected: 2 passed.

- [ ] **Step 5: Commit the loader and reporting**

```bash
git add src/navigate/main.py test/test_main_optional_dependencies.py
git commit -m "Explain missing OpenGL viewer dependencies"
```

### Task 3: Clean up failed viewer startup and repair existing tests

**Files:**
- Modify: `src/navigate/main.py:108-147`
- Modify: `test/test_main.py:47-58`
- Modify: `test/test_main_additional.py:7-111`
- Modify: `test/test_main_optional_dependencies.py`

**Interfaces:**
- Consumes: `_load_volume_viewer() -> Optional[type]`.
- Produces: clean failure behavior in `main()` with no Tk main loop and one logging-listener stop.

- [ ] **Step 1: Add a failing viewer-branch cleanup test**

Extend `_FakeRoot` with `self.destroy = MagicMock()`, set `viewer=False` in existing non-viewer argument fixtures, and add:

```python
def test_main_cleans_up_when_optional_viewer_is_unavailable(monkeypatch):
    root = _FakeRoot()
    splash = MagicMock()
    args = SimpleNamespace(configurator=False, viewer=True)
    listener = MagicMock()

    monkeypatch.setattr(main_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(main_module.tk, "Tk", lambda: root)
    monkeypatch.setattr(main_module, "SplashScreen", MagicMock(return_value=splash))
    monkeypatch.setattr(
        main_module,
        "create_parser",
        lambda: SimpleNamespace(parse_args=lambda: args),
    )
    monkeypatch.setattr(
        main_module,
        "evaluate_parser_input_arguments",
        lambda parsed_args: _evaluation_result(),
    )
    monkeypatch.setattr(
        main_module, "log_setup", MagicMock(return_value=("queue", listener))
    )
    monkeypatch.setattr(main_module, "_load_volume_viewer", lambda: None)

    main_module.main()

    splash.destroy.assert_called_once_with()
    root.destroy.assert_called_once_with()
    root.mainloop.assert_not_called()
    listener.stop.assert_called_once_with()
```

- [ ] **Step 2: Run focused main tests and verify RED**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main.py test/test_main_additional.py test/test_main_optional_dependencies.py -q
```

Expected: the cleanup test fails because `main()` still uses the old inline guard and does not destroy startup UI on failure.

- [ ] **Step 3: Replace the viewer branch with the lazy loader and cleanup**

Replace the current viewer branch with:

```python
    elif command_line_args.viewer:
        volume_viewer_class = _load_volume_viewer()
        if volume_viewer_class is None:
            for startup_window in (splash_screen, root):
                try:
                    startup_window.destroy()
                except (AttributeError, tk.TclError):
                    logger.debug(
                        "Unable to destroy viewer startup window",
                        exc_info=True,
                    )
            log_listener.stop()
            return

        root = volume_viewer_class(root=root, splash_screen=splash_screen)
```

Set `args.viewer = False` in `test/test_main.py::get_args` and use `SimpleNamespace(configurator=False, viewer=False)` plus `SimpleNamespace(configurator=True, viewer=False)` in `test/test_main_additional.py`.

- [ ] **Step 4: Run focused main tests and verify GREEN**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main.py test/test_main_additional.py test/test_main_optional_dependencies.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Run formatting and whitespace verification**

Run:

```bash
/opt/anaconda3/envs/navigate/bin/black --check src/navigate/main.py test/test_main.py test/test_main_additional.py test/test_main_optional_dependencies.py
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit the cleanup and test updates**

```bash
git add src/navigate/main.py test/test_main.py test/test_main_additional.py test/test_main_optional_dependencies.py
git commit -m "Clean up unavailable volume viewer startup"
```

### Task 4: Final regression verification

**Files:**
- Verify: `src/navigate/main.py`
- Verify: `test/test_main.py`
- Verify: `test/test_main_additional.py`
- Verify: `test/test_main_optional_dependencies.py`

**Interfaces:**
- Consumes: all behavior from Tasks 1-3.
- Produces: evidence that standard imports and focused launch branches work without OpenGL extras.

- [ ] **Step 1: Run the focused regression suite without optional dependency injection**

```bash
/opt/anaconda3/envs/navigate/bin/python -m pytest -o addopts='' test/test_main.py test/test_main_additional.py test/test_main_optional_dependencies.py -q
```

Expected: all focused tests pass.

- [ ] **Step 2: Verify a direct standard import**

```bash
PYTHONPATH=src /opt/anaconda3/envs/navigate/bin/python -c "import navigate.main; print('navigate.main import ok')"
```

Expected: `navigate.main import ok` and exit 0 without OpenGL optional dependencies.

- [ ] **Step 3: Inspect final scope**

```bash
git status --short --branch
git diff origin/opengl-volume-viewer...HEAD --stat
git log --oneline origin/opengl-volume-viewer..HEAD
```

Expected: only the specification, plan, targeted main implementation, and regression tests are included.
