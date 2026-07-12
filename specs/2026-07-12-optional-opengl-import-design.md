# Optional OpenGL Import and User Guidance Design

## Goal

Keep the standard **navigate** application importable and launchable when the
optional OpenGL viewer dependencies are not installed. When a user explicitly
requests the standalone volume viewer without those dependencies, explain the
problem in plain language, identify the missing component when possible, show
copy-and-paste installation commands for the active Python environment, record
technical details in the application log, and exit cleanly.

## Scope

This change addresses only the optional-import regression and its user-facing
error path. It does not change the renderer architecture, OpenGL version,
shader packaging, TIFF parsing, or other findings from the broader PR review.

## Design

### Import boundary

`navigate.main` must not import the standalone volume viewer at module load
time. The viewer class and its optional dependency graph will be imported only
after command-line parsing confirms that `--viewer` was requested.

A small loader function in `navigate.main` will own this boundary. It returns
the viewer class after a successful import and returns `None` after reporting
an optional-dependency failure. Keeping this logic in one function makes the
normal import path easy to regression-test and keeps terminal guidance
consistent.

### Beginner-oriented terminal guidance

If the lazy import raises `ImportError`, `ModuleNotFoundError`, or an operating
system library loading error, the terminal message will:

1. State that the optional Volume Viewer could not start, while the standard
   **navigate** application remains available.
2. Name the missing Python package when the exception identifies one, mapping
   import names such as `OpenGL`, `glm`, `glfw`, and `tkinterdnd2` to the package
   names users see during installation.
3. Explain that optional viewer dependencies are not included in a standard
   installation.
4. Tell Conda or virtual-environment users to activate the environment they use
   for **navigate** before installing anything.
5. Show commands built from `sys.executable`, ensuring that `pip` runs under the
   same Python interpreter that launched **navigate**:

   - Source checkout: `<python> -m pip install -e '.[opengl]'`
   - Installed package: `<python> -m pip install 'navigate-micro[opengl]'`

6. Tell the user to retry `navigate --viewer` after installation and to inspect
   the log or report the displayed technical error if installation succeeds but
   startup still fails.

The message will be written to standard error so it remains visible and can be
captured by scripts.

### Logging and cleanup

The complete technical exception and traceback will be logged through the
module logger. The terminal output will remain concise and explanatory rather
than exposing a raw traceback to a beginner.

Because the current command flow creates a Tk root, splash screen, and logging
listener before entering the viewer branch, a failed viewer import will destroy
the splash and root where possible, stop the logging listener, and return
without entering a Tk main loop. Cleanup failures must not hide the original
dependency guidance.

### Tests

Tests will be written before production changes and will cover:

- Importing `navigate.main` while optional OpenGL-related imports are blocked.
- Mapping a missing import name to a recognizable installation package.
- Terminal output containing an explanation, the active-interpreter commands,
  environment-activation guidance, and a retry command.
- Logging the technical exception.
- Cleaning up Tk and the logging listener when `--viewer` is requested but the
  lazy import fails.
- Existing non-viewer and configurator branches explicitly using
  `viewer=False` in their argument fixtures.

The focused main tests will run both without the optional dependency target and
with the existing project environment. Formatting and whitespace checks will
be limited to the files changed by this fix.

## Success criteria

- `import navigate.main` succeeds without the OpenGL optional dependencies.
- Normal and configurator launches do not import the standalone viewer.
- `navigate --viewer` without the extra prints actionable instructions and
  exits cleanly.
- The technical error appears in logs.
- Focused regression tests pass in the `navigate` Conda environment.
