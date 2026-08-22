# Navigate Repository Guide

## Project context

- Navigate is performance-sensitive microscope-control software.
- Application code lives under `src/navigate/` and follows a model-view-controller
  structure. The model runs in a subprocess; queues, pipes, and shared memory carry
  data between the model and controller.
- Tests live under `test/` and should mirror the source layout.
- Treat `pyproject.toml` and the files under `constraints/` as the canonical
  dependency records. Do not copy version inventories into agent instructions.

## Required local guidance

- Before changing `src/navigate/controller/` or controller-facing GUI behavior,
  read `src/navigate/controller/README.md` and preserve its Tk main-thread rules.
- Before changing documentation, read `docs/AGENTS.md`. Sphinx sources under
  `docs/source/` use reStructuredText.

## Development workflow

- Keep blocking hardware I/O and image processing off the Tk main thread.
- Prefer focused changes and add or update tests for changed behavior.
- Use type hints for new or modified interfaces.
- Use NumPy-style docstrings; keep Sphinx-compatible `#:` attribute comments.
- Format modified Python files with Black.
- Run focused tests first, then the broadest practical suite with the reviewed
  checkout forced onto the import path, for example:

  ```bash
  PYTHONPATH=src pytest -p no:cov -o addopts=
  ```

- Hardware tests require the matching SDK or device environment. Do not treat a
  synthetic or mocked test as proof of physical hardware behavior.
- Run `git diff --check` before committing.
