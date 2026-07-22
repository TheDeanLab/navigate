# Single-Acquisition Test Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent `test_single_acquisition` from mistaking coalesced display notifications for dropped camera frames and guarantee cleanup after failures.

**Architecture:** Keep production acquisition behavior unchanged. Add a test-local pipe reader that returns the newest integer frame identifier observed before the `"stop"` sentinel, use it in the integration test, and move thread/pipe cleanup into `finally`.

**Tech Stack:** Python 3.9, pytest 8, multiprocessing pipes, Navigate's `navigate` Conda environment.

## Global Constraints

- Modify test code only; do not alter camera acquisition or display-pipe behavior.
- Preserve Python 3.9 compatibility.
- Run repository-aware tests with `conda run -n navigate python -m pytest`.
- Format modified Python with Black and lint it with Ruff.

---

### Task 1: Make single-acquisition frame accounting batch-safe

**Files:**
- Modify: `test/model/test_model.py:116-156`
- Test: `test/model/test_model.py`

**Interfaces:**
- Consumes: pipe objects exposing `recv()` and messages containing integer frame identifiers followed by the `"stop"` sentinel.
- Produces: `_receive_last_frame_id(show_img_pipe: Any, max_messages: int = 20) -> Optional[int]`.

- [ ] **Step 1: Write the failing split-batch regression**

Add a fake readable pipe and a focused test before defining the helper:

```python
class FakeReadablePipe:
    def __init__(self, messages):
        self.messages = iter(messages)

    def recv(self):
        return next(self.messages)


def test_receive_last_frame_id_handles_coalesced_batches():
    show_img_pipe = FakeReadablePipe([0, 2, "stop"])

    assert _receive_last_frame_id(show_img_pipe) == 2
```

- [ ] **Step 2: Run the regression to verify RED**

Run:

```bash
conda run -n navigate python -m pytest test/model/test_model.py::test_receive_last_frame_id_handles_coalesced_batches -q
```

Expected: FAIL with `NameError: name '_receive_last_frame_id' is not defined`.

- [ ] **Step 3: Implement the minimal pipe reader**

Add `Any` and `Optional` to the imports and define:

```python
def _receive_last_frame_id(
    show_img_pipe: Any, max_messages: int = 20
) -> Optional[int]:
    last_frame_id = None
    for _ in range(max_messages):
        message = show_img_pipe.recv()
        if message == "stop":
            break
        if isinstance(message, int):
            last_frame_id = message
    return last_frame_id
```

- [ ] **Step 4: Verify the focused regression is GREEN**

Run:

```bash
conda run -n navigate python -m pytest test/model/test_model.py::test_receive_last_frame_id_handles_coalesced_batches -q
```

Expected: `1 passed`.

- [ ] **Step 5: Replace notification counting and guarantee cleanup**

Update `test_single_acquisition` to compare the final frame identifier and always clean up:

```python
show_img_pipe = model.create_pipe("show_img_pipe")
try:
    model.run_command("acquire")
    last_frame_id = _receive_last_frame_id(show_img_pipe)
    assert last_frame_id == n_frames_expected - 1
finally:
    if model.data_thread is not None:
        model.data_thread.join()
    model.release_pipe("show_img_pipe")
```

- [ ] **Step 6: Run focused acquisition verification**

Run:

```bash
conda run -n navigate python -m pytest \
  test/model/test_model.py::test_receive_last_frame_id_handles_coalesced_batches \
  test/model/test_model.py::test_single_acquisition \
  test/model/test_model.py::test_run_data_process_drains_pending_frames_after_signal_completion \
  -q
```

Expected: `3 passed`.

- [ ] **Step 7: Format, lint, and inspect**

Run:

```bash
conda run -n navigate black --check test/model/test_model.py
conda run -n navigate ruff check test/model/test_model.py
git diff --check
git status --short --branch
```

Expected: Black and Ruff exit successfully, `git diff --check` emits no output, and only the planned files are modified.

- [ ] **Step 8: Commit the implementation**

```bash
git add test/model/test_model.py docs/superpowers/plans/2026-07-21-single-acquisition-test-reliability.md
git commit -m "Fix single-acquisition test frame accounting"
```
